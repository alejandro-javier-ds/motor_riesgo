from __future__ import annotations

import logging
import re
import sys
from dataclasses import dataclass
from difflib import get_close_matches
from pathlib import Path
from typing import Final

import pandas as pd
from catboost import CatBoostClassifier, Pool
from rich.console import Console
from rich.table import Table

MODEL_FILENAME: Final[str] = "catboost_thin_file.cbm"
REAL_DATA_FILENAME: Final[str] = "raw_data.csv"
MOROSIDAD_QUESTION_FRAGMENT: Final[str] = "Pregunta 100% ANÓNIMA"
EXCLUDED_COLUMNS: Final[list[str]] = [
    "Marca temporal",
    "Consentimiento",
    "EDAD",
    "SITUACION LABORAL",
]
COLUMN_RENAMES: Final[dict[str, str]] = {
    "DISTRITO DE RESIDENCIA": "DISTRITO",
    "NIVEL EDUCATIVO": "NIVEL_EDUCATIVO",
}
LIKERT_PREFIX_PATTERN: Final[re.Pattern] = re.compile(
    r"^Indica qué tan identificado te sientes con las siguientes afirmaciones cotidianas\.\s*\[(.+)\]\s*$"
)
FUZZY_MATCH_CUTOFF: Final[float] = 0.85
THRESHOLD_S800: Final[float] = 0.30
THRESHOLD_S300: Final[float] = 0.35

MOROSIDAD_OPCIONES: Final[dict[str, str]] = {
    "imputed": "No, siempre he pagado todas mis obligaciones a tiempo",
    "sin_obligaciones": "No he tenido obligaciones de pago en los últimos 12 meses",
    "moroso_declarado": "Sí, me he retrasado en alguna obligación",
}


@dataclass(frozen=True)
class CreditDecision:
    probability: float
    tramo: str
    monto: int


@dataclass(frozen=True)
class RealCandidatePrediction:
    candidate_id: int
    probability_imputed: float
    decision_imputed: CreditDecision
    probability_sin_obligaciones: float
    decision_sin_obligaciones: CreditDecision
    probability_moroso: float
    decision_moroso: CreditDecision
    tramo_changes_count: int


def configure_logger() -> logging.Logger:
    logger = logging.getLogger("RealDataInference")
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


def extract_likert_bare_question(column_name: str) -> str | None:
    match = LIKERT_PREFIX_PATTERN.match(column_name)
    return match.group(1).strip() if match else None


def normalize_column_names(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    df = df.copy()
    df.columns = [col.strip() for col in df.columns]
    rename_map: dict[str, str] = {}
    for column in df.columns:
        bare_question = extract_likert_bare_question(column)
        if bare_question is not None:
            rename_map[column] = bare_question
    df = df.rename(columns=rename_map)
    df = df.rename(columns=COLUMN_RENAMES)
    logger.info(f"Columnas Likert despojadas de prefijo: {len(rename_map)}")
    return df


def drop_non_model_columns(df: pd.DataFrame) -> pd.DataFrame:
    columns_to_drop: list[str] = []
    for column in df.columns:
        column_stripped = column.strip()
        if column_stripped == "Marca temporal":
            columns_to_drop.append(column)
        elif column_stripped.startswith("Consentimiento"):
            columns_to_drop.append(column)
        elif column_stripped == "EDAD":
            columns_to_drop.append(column)
        elif column_stripped == "SITUACION LABORAL":
            columns_to_drop.append(column)
    return df.drop(columns=columns_to_drop)


def reconcile_with_model_schema(
    df: pd.DataFrame,
    expected_features: list[str],
    logger: logging.Logger,
) -> pd.DataFrame:
    df = df.copy()
    csv_columns = list(df.columns)
    rename_map: dict[str, str] = {}
    for expected in expected_features:
        if expected in csv_columns:
            continue
        candidates = get_close_matches(expected, csv_columns, n=1, cutoff=FUZZY_MATCH_CUTOFF)
        if candidates:
            best_match = candidates[0]
            rename_map[best_match] = expected
            logger.info(f"Fuzzy match: '{best_match[:60]}...' → '{expected[:60]}...'")
        else:
            raise ValueError(f"No se encontró match para columna requerida: '{expected}'")
    df = df.rename(columns=rename_map)
    return df


def find_morosidad_column(df: pd.DataFrame) -> str:
    for column in df.columns:
        if MOROSIDAD_QUESTION_FRAGMENT in column:
            return column
    raise ValueError("No se encontró la columna de morosidad en el CSV real.")


def impute_morosidad(df: pd.DataFrame, value: str) -> pd.DataFrame:
    df = df.copy()
    morosidad_col = find_morosidad_column(df)
    df[morosidad_col] = value
    return df


def align_to_model_schema(df: pd.DataFrame, expected_features: list[str]) -> pd.DataFrame:
    return df[expected_features]


def classify_decision(probability: float) -> CreditDecision:
    if probability < THRESHOLD_S800:
        return CreditDecision(probability, "S/800 — Pre-aprobado", 800)
    if probability < THRESHOLD_S300:
        return CreditDecision(probability, "S/300 — Crédito limitado", 300)
    return CreditDecision(probability, "S/0 — Denegado", 0)


def predict_batch(model: CatBoostClassifier, df_aligned: pd.DataFrame, cat_features: list[str]) -> list[float]:
    pool = Pool(df_aligned, cat_features=cat_features)
    probabilities = model.predict_proba(pool)[:, 1]
    return [float(p) for p in probabilities]


def run_counterfactual_predictions(
    model: CatBoostClassifier,
    df_normalized: pd.DataFrame,
    expected_features: list[str],
    cat_features: list[str],
) -> list[RealCandidatePrediction]:
    predictions_per_scenario: dict[str, list[float]] = {}
    for scenario_label, morosidad_value in MOROSIDAD_OPCIONES.items():
        df_scenario = impute_morosidad(df_normalized, morosidad_value)
        df_aligned = align_to_model_schema(df_scenario, expected_features)
        predictions_per_scenario[scenario_label] = predict_batch(model, df_aligned, cat_features)

    results: list[RealCandidatePrediction] = []
    for idx in range(len(df_normalized)):
        prob_imp = predictions_per_scenario["imputed"][idx]
        prob_sin = predictions_per_scenario["sin_obligaciones"][idx]
        prob_mor = predictions_per_scenario["moroso_declarado"][idx]
        dec_imp = classify_decision(prob_imp)
        dec_sin = classify_decision(prob_sin)
        dec_mor = classify_decision(prob_mor)
        tramos = {dec_imp.tramo, dec_sin.tramo, dec_mor.tramo}
        results.append(RealCandidatePrediction(
            candidate_id=idx + 1,
            probability_imputed=prob_imp,
            decision_imputed=dec_imp,
            probability_sin_obligaciones=prob_sin,
            decision_sin_obligaciones=dec_sin,
            probability_moroso=prob_mor,
            decision_moroso=dec_mor,
            tramo_changes_count=len(tramos) - 1,
        ))
    return results


def render_individual_table(results: list[RealCandidatePrediction]) -> None:
    console = Console()
    table = Table(
        title="\n[bold cyan]Predicción individual sobre los 28 respondedores reales[/bold cyan]",
        show_header=True,
        header_style="bold magenta",
        show_lines=False,
    )
    table.add_column("ID", justify="right", style="cyan", no_wrap=True)
    table.add_column("P (imputado)", justify="right", style="green")
    table.add_column("Decisión imputado", style="white")
    table.add_column("P (sin oblig.)", justify="right")
    table.add_column("Decisión sin oblig.", style="white")
    table.add_column("P (moroso)", justify="right", style="yellow")
    table.add_column("Decisión moroso", style="white")
    table.add_column("Δ tramo", justify="center", style="bold")

    for result in results:
        delta_marker = "estable" if result.tramo_changes_count == 0 else f"+{result.tramo_changes_count}"
        delta_color = "green" if result.tramo_changes_count == 0 else "yellow" if result.tramo_changes_count == 1 else "red"
        table.add_row(
            f"{result.candidate_id:02d}",
            f"{result.probability_imputed:.4f}",
            result.decision_imputed.tramo,
            f"{result.probability_sin_obligaciones:.4f}",
            result.decision_sin_obligaciones.tramo,
            f"{result.probability_moroso:.4f}",
            result.decision_moroso.tramo,
            f"[{delta_color}]{delta_marker}[/{delta_color}]",
        )
    console.print(table)


def render_sensitivity_summary(results: list[RealCandidatePrediction]) -> None:
    from collections import Counter
    console = Console()

    tramo_counts_imp = Counter(r.decision_imputed.tramo for r in results)
    tramo_counts_sin = Counter(r.decision_sin_obligaciones.tramo for r in results)
    tramo_counts_mor = Counter(r.decision_moroso.tramo for r in results)
    stable_count = sum(1 for r in results if r.tramo_changes_count == 0)
    one_change = sum(1 for r in results if r.tramo_changes_count == 1)
    two_changes = sum(1 for r in results if r.tramo_changes_count == 2)

    summary = Table(
        title="\n[bold cyan]Resumen agregado — Análisis de sensibilidad contrafactual[/bold cyan]",
        show_header=True,
        header_style="bold magenta",
    )
    summary.add_column("Escenario", style="cyan")
    summary.add_column("S/800", justify="right", style="green")
    summary.add_column("S/300", justify="right", style="yellow")
    summary.add_column("S/0", justify="right", style="red")

    for label, counts in [
        ("Imputado (No, siempre pagué)", tramo_counts_imp),
        ("Sin obligaciones previas", tramo_counts_sin),
        ("Moroso declarado", tramo_counts_mor),
    ]:
        summary.add_row(
            label,
            str(counts.get("S/800 — Pre-aprobado", 0)),
            str(counts.get("S/300 — Crédito limitado", 0)),
            str(counts.get("S/0 — Denegado", 0)),
        )
    console.print(summary)

    stability = Table(
        title="[bold cyan]Estabilidad de decisión bajo perturbación de morosidad[/bold cyan]",
        show_header=False,
        box=None,
    )
    stability.add_column("Métrica", style="cyan")
    stability.add_column("Valor", style="white")
    stability.add_row("Candidatos con tramo estable (los 3 escenarios coinciden)", f"[bold green]{stable_count}/28[/bold green]")
    stability.add_row("Candidatos con 1 cambio de tramo entre escenarios", f"[bold yellow]{one_change}/28[/bold yellow]")
    stability.add_row("Candidatos con 2 cambios de tramo (alta sensibilidad)", f"[bold red]{two_changes}/28[/bold red]")
    console.print(stability)


def main() -> None:
    logger = configure_logger()
    logger.info("Initializing Real Data Inference Pipeline...")

    base_dir = Path(__file__).parent
    model = load_model(base_dir / MODEL_FILENAME)
    expected_features = list(model.feature_names_)
    logger.info(f"Model loaded. Expected features: {len(expected_features)}")

    raw_df = pd.read_csv(base_dir / REAL_DATA_FILENAME)
    logger.info(f"Real data loaded. Shape: {raw_df.shape}")

    normalized = normalize_column_names(raw_df, logger)
    normalized = drop_non_model_columns(normalized)
    logger.info(f"Post-normalization shape: {normalized.shape}")

    normalized = reconcile_with_model_schema(normalized, expected_features, logger)
    logger.info("Schema reconciliation completed.")

    morosidad_col = find_morosidad_column(normalized)
    missing_count = normalized[morosidad_col].isna().sum()
    logger.info(f"Morosidad column missing values: {missing_count}/{len(normalized)}")
    logger.info(f"Imputation strategy: '{MOROSIDAD_OPCIONES['imputed']}'")

    for col in expected_features:
        normalized[col] = normalized[col].fillna("Desconocido").astype(str)

    cat_features = list(expected_features)

    logger.info("Running counterfactual predictions across 3 morosidad scenarios...")
    results = run_counterfactual_predictions(model, normalized, expected_features, cat_features)
    logger.info(f"Predictions completed for {len(results)} real candidates.")

    render_individual_table(results)
    render_sensitivity_summary(results)


if __name__ == "__main__":
    main()