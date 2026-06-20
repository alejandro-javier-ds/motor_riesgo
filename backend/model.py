from __future__ import annotations

import json
import logging
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final

import polars as pl
from catboost import CatBoostClassifier, Pool
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

RANDOM_SEED: Final[int] = 42
TARGET_COL: Final[str] = "TARGET_MOROSIDAD"
DROPPED_FEATURES: Final[list[str]] = ["EDAD", "SITUACION LABORAL"]
TEST_SIZE: Final[float] = 0.20
VAL_SIZE_FROM_TEMP: Final[float] = 0.25
TOP_FEATURES_TO_REPORT: Final[int] = 10
MODEL_FILENAME: Final[str] = "catboost_thin_file.cbm"
METRICS_FILENAME: Final[str] = "metrics.json"


@dataclass(frozen=True)
class Hyperparameters:
    iterations: int = 2000
    depth: int = 3
    learning_rate: float = 0.01
    l2_leaf_reg: float = 15.0
    auto_class_weights: str = "Balanced"
    early_stopping_rounds: int = 100
    bootstrap_type: str = "Bayesian"
    bagging_temperature: float = 0.5


@dataclass(frozen=True)
class EvaluationReport:
    trees_used: int
    auc_train: float
    auc_validation: float
    auc_test: float
    train_test_gap: float
    accuracy: float
    precision_riesgo: float
    recall_riesgo: float
    f1_riesgo: float


@dataclass(frozen=True)
class FeatureImportanceEntry:
    rank: int
    name: str
    relative_percentage: float


def configure_logger() -> logging.Logger:
    logger = logging.getLogger("CatBoostEngine")
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


def load_and_prepare(path: Path) -> pl.DataFrame:
    df = pl.read_csv(path)
    df = df.with_columns(
        pl.when(pl.col(TARGET_COL) == "Sí").then(1).otherwise(0).alias(TARGET_COL)
    )
    return df.drop(DROPPED_FEATURES)


def stratified_three_way_split(df: pl.DataFrame):
    X = df.drop(TARGET_COL).to_pandas()
    y = df.select(TARGET_COL).to_pandas().squeeze()
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp,
        y_temp,
        test_size=VAL_SIZE_FROM_TEMP,
        random_state=RANDOM_SEED,
        stratify=y_temp,
    )
    return X_train, X_val, X_test, y_train, y_val, y_test


def build_model(hp: Hyperparameters) -> CatBoostClassifier:
    return CatBoostClassifier(
        iterations=hp.iterations,
        depth=hp.depth,
        learning_rate=hp.learning_rate,
        l2_leaf_reg=hp.l2_leaf_reg,
        auto_class_weights=hp.auto_class_weights,
        early_stopping_rounds=hp.early_stopping_rounds,
        bootstrap_type=hp.bootstrap_type,
        bagging_temperature=hp.bagging_temperature,
        random_seed=RANDOM_SEED,
        verbose=False,
    )


def fit_with_validation(model, train_pool: Pool, val_pool: Pool) -> None:
    model.fit(train_pool, eval_set=val_pool, use_best_model=True)


def evaluate(model, train_pool, val_pool, test_pool, y_train, y_val, y_test) -> EvaluationReport:
    proba_train = model.predict_proba(train_pool)[:, 1]
    proba_val = model.predict_proba(val_pool)[:, 1]
    proba_test = model.predict_proba(test_pool)[:, 1]
    pred_test = model.predict(test_pool)
    auc_train = roc_auc_score(y_train, proba_train)
    auc_val = roc_auc_score(y_val, proba_val)
    auc_test = roc_auc_score(y_test, proba_test)
    return EvaluationReport(
        trees_used=int(model.tree_count_),
        auc_train=auc_train,
        auc_validation=auc_val,
        auc_test=auc_test,
        train_test_gap=auc_train - auc_test,
        accuracy=accuracy_score(y_test, pred_test),
        precision_riesgo=precision_score(y_test, pred_test),
        recall_riesgo=recall_score(y_test, pred_test),
        f1_riesgo=f1_score(y_test, pred_test),
    )


def log_classification_artifacts(logger, model, test_pool, y_test) -> None:
    pred_test = model.predict(test_pool)
    report = classification_report(
        y_test, pred_test, target_names=["Viable (0)", "Riesgo (1)"], digits=4
    )
    matrix = confusion_matrix(y_test, pred_test)
    logger.info(f"Classification Report:\n{report}")
    logger.info(
        "Confusion Matrix:\n"
        f"  TN={matrix[0][0]:>4d}  FP={matrix[0][1]:>4d}\n"
        f"  FN={matrix[1][0]:>4d}  TP={matrix[1][1]:>4d}"
    )


def compute_feature_importance(model, feature_names) -> list[FeatureImportanceEntry]:
    raw_importance = model.get_feature_importance()
    total = float(raw_importance.sum())
    paired = sorted(
        zip(feature_names, raw_importance), key=lambda item: item[1], reverse=True
    )
    return [
        FeatureImportanceEntry(
            rank=rank,
            name=name,
            relative_percentage=float(importance) / total * 100.0,
        )
        for rank, (name, importance) in enumerate(paired, start=1)
    ]


def log_feature_importance(logger, entries: list[FeatureImportanceEntry], top_n: int) -> None:
    logger.info(f"Top {top_n} Feature Importances:")
    for entry in entries[:top_n]:
        truncated = (entry.name[:65] + "...") if len(entry.name) > 68 else entry.name
        logger.info(f"  {entry.rank:>2d}. {truncated:<70s} {entry.relative_percentage:>5.2f}%")
    top5_cum = sum(e.relative_percentage for e in entries[:5])
    top10_cum = sum(e.relative_percentage for e in entries[:10])
    logger.info(f"Top 5 cumulative concentration:  {top5_cum:.2f}%")
    logger.info(f"Top 10 cumulative concentration: {top10_cum:.2f}%")


def persist_artifacts(model, report: EvaluationReport, base_dir: Path, logger) -> None:
    model_path = base_dir / MODEL_FILENAME
    metrics_path = base_dir / METRICS_FILENAME
    model.save_model(str(model_path))
    with metrics_path.open("w", encoding="utf-8") as handler:
        json.dump(asdict(report), handler, indent=2)
    logger.info(f"Hardened model serialized at: {model_path}")
    logger.info(f"Metrics serialized at: {metrics_path}")


def main() -> None:
    logger = configure_logger()
    logger.info("Initializing Hardened Production Pipeline...")

    base_dir = Path(__file__).parent
    input_file = base_dir / "simulated_thin_file_data.csv"

    df = load_and_prepare(input_file)
    logger.info(f"Dataset loaded and ablated. Shape: {df.shape}")
    logger.info(f"Dropped demographic features: {DROPPED_FEATURES}")

    X_train, X_val, X_test, y_train, y_val, y_test = stratified_three_way_split(df)
    logger.info(
        f"Stratified split → Train: {X_train.shape} | "
        f"Validation: {X_val.shape} | Test: {X_test.shape}"
    )

    cat_features = list(X_train.select_dtypes(include=["object", "string"]).columns)
    logger.info(f"Categorical features detected: {len(cat_features)}")
    logger.info(f"Class distribution in train: {y_train.value_counts().to_dict()}")
    logger.info("Class balancing strategy: auto_class_weights='Balanced' (no SMOTE)")

    hp = Hyperparameters()
    logger.info(
        f"Hyperparameters: iterations={hp.iterations}, depth={hp.depth}, "
        f"learning_rate={hp.learning_rate}, l2_leaf_reg={hp.l2_leaf_reg}, "
        f"auto_class_weights={hp.auto_class_weights}, "
        f"early_stopping_rounds={hp.early_stopping_rounds}, "
        f"bootstrap_type={hp.bootstrap_type}, "
        f"bagging_temperature={hp.bagging_temperature}"
    )

    train_pool = Pool(X_train, y_train, cat_features=cat_features)
    val_pool = Pool(X_val, y_val, cat_features=cat_features)
    test_pool = Pool(X_test, y_test, cat_features=cat_features)

    model = build_model(hp)
    fit_with_validation(model, train_pool, val_pool)
    logger.info(f"Training stopped at iteration: {model.tree_count_}")

    result = evaluate(
        model, train_pool, val_pool, test_pool,
        y_train, y_val, y_test,
    )

    logger.info(f"ROC-AUC Train:      {result.auc_train:.4f}")
    logger.info(f"ROC-AUC Validation: {result.auc_validation:.4f}")
    logger.info(f"ROC-AUC Test:       {result.auc_test:.4f}")
    logger.info(f"Train-Test AUC gap: {result.train_test_gap:+.4f}")
    logger.info(f"Accuracy Test:      {result.accuracy:.4f}")
    logger.info(f"Precision Riesgo:   {result.precision_riesgo:.4f}")
    logger.info(f"Recall Riesgo:      {result.recall_riesgo:.4f}")
    logger.info(f"F1 Riesgo:          {result.f1_riesgo:.4f}")

    log_classification_artifacts(logger, model, test_pool, y_test)

    importance_ranking = compute_feature_importance(model, list(X_train.columns))
    log_feature_importance(logger, importance_ranking, TOP_FEATURES_TO_REPORT)

    persist_artifacts(model, result, base_dir, logger)


if __name__ == "__main__":
    main()