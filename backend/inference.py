from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
import polars as pl
import shap
from catboost import CatBoostClassifier, Pool

RANDOM_SEED: Final[int] = 42
TARGET_COL: Final[str] = "TARGET_MOROSIDAD"
DROPPED_FEATURES: Final[list[str]] = ["EDAD", "SITUACION LABORAL"]
MODEL_FILENAME: Final[str] = "catboost_thin_file.cbm"
DATASET_FILENAME: Final[str] = "simulated_thin_file_data.csv"
THRESHOLD_S800: Final[float] = 0.35
THRESHOLD_S300: Final[float] = 0.55
SAMPLE_INDEX: Final[int] = 17
SENSITIVITY_PERTURBATIONS: Final[list[int]] = [1, 2, 3, 5]
LIKERT_LEVELS: Final[list[str]] = [
    "Totalmente en desacuerdo",
    "En desacuerdo",
    "Neutral",
    "De acuerdo",
    "Totalmente de acuerdo",
]


@dataclass(frozen=True)
class CreditDecision:
    probability: float
    tramo: str
    monto: int


@dataclass(frozen=True)
class SensitivityRow:
    perturbations: int
    original_probability: float
    perturbed_probability: float
    delta: float
    tramo_changed: bool
    new_tramo: str


def configure_logger() -> logging.Logger:
    logger = logging.getLogger("InferenceEngine")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)
    return logger


def load_model(path: Path) -> CatBoostClassifier:
    model = CatBoostClassifier()
    model.load_model(str(path))
    return model


def load_features_and_target(path: Path):
    df = pl.read_csv(path)
    df = df.with_columns(
        pl.when(pl.col(TARGET_COL) == "Sí").then(1).otherwise(0).alias(TARGET_COL)
    )
    df = df.drop(DROPPED_FEATURES)
    X = df.drop(TARGET_COL).to_pandas()
    y = df.select(TARGET_COL).to_pandas().squeeze()
    return X, y


def classify_credit_decision(probability: float) -> CreditDecision:
    if probability < THRESHOLD_S800:
        return CreditDecision(probability=probability, tramo="S/800 — Pre-aprobado", monto=800)
    if probability < THRESHOLD_S300:
        return CreditDecision(probability=probability, tramo="S/300 — Crédito limitado", monto=300)
    return CreditDecision(probability=probability, tramo="S/0 — Denegado", monto=0)


def predict_single(model: CatBoostClassifier, candidate: pd.DataFrame, cat_features: list[str]) -> float:
    pool = Pool(candidate, cat_features=cat_features)
    proba = model.predict_proba(pool)[:, 1]
    return float(proba[0])


def compute_individual_shap(model: CatBoostClassifier, candidate: pd.DataFrame, cat_features: list[str]):
    explainer = shap.TreeExplainer(model)
    pool = Pool(candidate, cat_features=cat_features)
    raw_values = explainer.shap_values(pool)
    if isinstance(raw_values, list):
        raw_values = raw_values[1]
    return raw_values[0], explainer.expected_value


def log_top_shap_contributors(shap_row: np.ndarray, feature_names: list[str], logger: logging.Logger, top_n: int = 10) -> None:
    paired = sorted(
        zip(feature_names, shap_row),
        key=lambda item: abs(item[1]),
        reverse=True,
    )
    logger.info(f"Top {top_n} SHAP contributors for this candidate:")
    for rank, (name, value) in enumerate(paired[:top_n], start=1):
        truncated = (name[:60] + "...") if len(name) > 63 else name
        direction = "↑ risk" if value > 0 else "↓ risk"
        logger.info(f"  {rank:>2d}. {truncated:<65s} SHAP={value:+.4f}  {direction}")


def perturb_candidate(
    base_candidate: pd.DataFrame,
    n_perturbations: int,
    rng: np.random.Generator,
    cat_features: list[str],
) -> pd.DataFrame:
    perturbed = base_candidate.copy()
    eligible_columns = [c for c in base_candidate.columns if base_candidate[c].iloc[0] in LIKERT_LEVELS]
    columns_to_change = rng.choice(eligible_columns, size=min(n_perturbations, len(eligible_columns)), replace=False)
    for column in columns_to_change:
        current_value = perturbed[column].iloc[0]
        alternatives = [level for level in LIKERT_LEVELS if level != current_value]
        new_value = rng.choice(alternatives)
        perturbed.at[perturbed.index[0], column] = new_value
    return perturbed


def run_sensitivity_analysis(
    model: CatBoostClassifier,
    base_candidate: pd.DataFrame,
    base_decision: CreditDecision,
    cat_features: list[str],
    logger: logging.Logger,
) -> list[SensitivityRow]:
    rng = np.random.default_rng(RANDOM_SEED)
    results: list[SensitivityRow] = []
    for n in SENSITIVITY_PERTURBATIONS:
        perturbed = perturb_candidate(base_candidate, n, rng, cat_features)
        new_proba = predict_single(model, perturbed, cat_features)
        new_decision = classify_credit_decision(new_proba)
        tramo_changed = new_decision.tramo != base_decision.tramo
        results.append(SensitivityRow(
            perturbations=n,
            original_probability=base_decision.probability,
            perturbed_probability=new_proba,
            delta=new_proba - base_decision.probability,
            tramo_changed=tramo_changed,
            new_tramo=new_decision.tramo,
        ))
    return results


def log_sensitivity_table(rows: list[SensitivityRow], logger: logging.Logger) -> None:
    logger.info(f"{'Perturbations':<15}{'P(orig)':<12}{'P(perturbed)':<15}{'Δ':<12}{'Tramo cambió':<15}{'Nuevo tramo'}")
    logger.info("-" * 95)
    for row in rows:
        flag = "SÍ" if row.tramo_changed else "no"
        logger.info(
            f"{row.perturbations:<15}"
            f"{row.original_probability:<12.4f}"
            f"{row.perturbed_probability:<15.4f}"
            f"{row.delta:+<12.4f}"
            f"{flag:<15}"
            f"{row.new_tramo}"
        )


def main() -> None:
    logger = configure_logger()
    logger.info("Initializing Inference & Sensitivity Pipeline...")

    base_dir = Path(__file__).parent
    model = load_model(base_dir / MODEL_FILENAME)
    logger.info(f"Model loaded: {MODEL_FILENAME}")

    X, y = load_features_and_target(base_dir / DATASET_FILENAME)
    cat_features = list(X.select_dtypes(include=["object", "string"]).columns)
    logger.info(f"Dataset loaded. Selecting candidate at index {SAMPLE_INDEX}...")

    candidate = X.iloc[[SAMPLE_INDEX]].copy()
    actual_target = int(y.iloc[SAMPLE_INDEX])

    logger.info("=" * 70)
    logger.info("PHASE 1 — Single inference")
    logger.info("=" * 70)
    probability = predict_single(model, candidate, cat_features)
    decision = classify_credit_decision(probability)
    logger.info(f"Predicted P(moroso):  {probability:.4f}")
    logger.info(f"Credit tramo:         {decision.tramo}")
    logger.info(f"Amount approved:      S/{decision.monto}")
    logger.info(f"Ground truth label:   {'Moroso' if actual_target == 1 else 'Viable'}")
    correct = (probability >= 0.5) == (actual_target == 1)
    logger.info(f"Prediction matches ground truth: {correct}")

    logger.info("")
    logger.info("=" * 70)
    logger.info("PHASE 2 — Individual SHAP explanation")
    logger.info("=" * 70)
    shap_row, expected_value = compute_individual_shap(model, candidate, cat_features)
    if isinstance(expected_value, (list, np.ndarray)):
        baseline = float(expected_value[1]) if len(np.atleast_1d(expected_value)) > 1 else float(expected_value[0])
    else:
        baseline = float(expected_value)
    log_top_shap_contributors(shap_row, list(candidate.columns), logger, top_n=10)
    logger.info(f"Expected value (baseline log-odds): {baseline:.4f}")
    logger.info(f"Sum of SHAP values:                 {shap_row.sum():+.4f}")

    logger.info("")
    logger.info("=" * 70)
    logger.info("PHASE 3 — Sensitivity analysis (response perturbation)")
    logger.info("=" * 70)
    logger.info("Perturbing N random Likert responses and re-predicting...")
    rows = run_sensitivity_analysis(model, candidate, decision, cat_features, logger)
    log_sensitivity_table(rows, logger)

    logger.info("")
    logger.info("=" * 70)
    logger.info("INFERENCE PIPELINE COMPLETED")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()