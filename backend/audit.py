from __future__ import annotations

import hashlib
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import polars as pl
from catboost import CatBoostClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

RANDOM_SEED: Final[int] = 42
TARGET_COL: Final[str] = "TARGET_MOROSIDAD"
DROPPED_FEATURES: Final[list[str]] = ["EDAD", "SITUACION LABORAL"]
MODEL_FILENAME: Final[str] = "catboost_thin_file.cbm"
METRICS_FILENAME: Final[str] = "metrics.json"
DATASET_FILENAME: Final[str] = "simulated_thin_file_data.csv"
SMOKE_TEST_SAMPLES: Final[int] = 5
AUC_TOLERANCE: Final[float] = 1e-6


@dataclass(frozen=True)
class AuditResult:
    model_path_exists: bool
    metrics_path_exists: bool
    model_size_kb: float
    model_sha256: str
    persisted_auc_test: float
    recomputed_auc_test: float
    auc_drift: float
    integrity_passed: bool
    smoke_test_passed: bool


def configure_logger() -> logging.Logger:
    logger = logging.getLogger("ModelAudit")
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


def compute_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handler:
        for chunk in iter(lambda: handler.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_persisted_metrics(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handler:
        return json.load(handler)


def load_model(path: Path) -> CatBoostClassifier:
    model = CatBoostClassifier()
    model.load_model(str(path))
    return model


def reconstruct_test_partition(dataset_path: Path):
    df = pl.read_csv(dataset_path)
    df = df.with_columns(
        pl.when(pl.col(TARGET_COL) == "Sí").then(1).otherwise(0).alias(TARGET_COL)
    )
    df = df.drop(DROPPED_FEATURES)
    X = df.drop(TARGET_COL).to_pandas()
    y = df.select(TARGET_COL).to_pandas().squeeze()
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_SEED, stratify=y
    )
    return X_test, y_test


def run_smoke_test(model: CatBoostClassifier, X_test, logger: logging.Logger) -> bool:
    sample = X_test.head(SMOKE_TEST_SAMPLES)
    try:
        proba = model.predict_proba(sample)[:, 1]
        for idx, probability in enumerate(proba, start=1):
            logger.info(f"  Sample {idx} → P(moroso) = {probability:.4f}")
        return True
    except Exception as exc:
        logger.error(f"Smoke test failed: {exc}")
        return False


def audit_model(base_dir: Path, logger: logging.Logger) -> AuditResult:
    model_path = base_dir / MODEL_FILENAME
    metrics_path = base_dir / METRICS_FILENAME
    dataset_path = base_dir / DATASET_FILENAME

    logger.info("=" * 70)
    logger.info("PHASE 1 — Filesystem integrity")
    logger.info("=" * 70)
    model_exists = model_path.exists()
    metrics_exists = metrics_path.exists()
    logger.info(f"Model artifact present:   {model_exists} ({model_path.name})")
    logger.info(f"Metrics artifact present: {metrics_exists} ({metrics_path.name})")

    model_size_kb = model_path.stat().st_size / 1024.0
    model_hash = compute_sha256(model_path)
    logger.info(f"Model size:    {model_size_kb:.2f} KB")
    logger.info(f"Model SHA256:  {model_hash}")

    logger.info("")
    logger.info("=" * 70)
    logger.info("PHASE 2 — Metrics deserialization")
    logger.info("=" * 70)
    persisted = load_persisted_metrics(metrics_path)
    persisted_auc = float(persisted["auc_test"])
    logger.info(f"Persisted AUC Test:        {persisted_auc:.6f}")
    logger.info(f"Persisted gap:             {persisted['train_test_gap']:+.6f}")
    logger.info(f"Persisted F1 Riesgo:       {persisted['f1_riesgo']:.6f}")
    logger.info(f"Persisted trees used:      {persisted['trees_used']}")

    logger.info("")
    logger.info("=" * 70)
    logger.info("PHASE 3 — Model deserialization and reproducibility check")
    logger.info("=" * 70)
    model = load_model(model_path)
    logger.info(f"Model loaded successfully. Feature count: {model.feature_names_.__len__()}")
    logger.info(f"Tree count from binary:    {model.tree_count_}")

    X_test, y_test = reconstruct_test_partition(base_dir / DATASET_FILENAME)
    proba_test = model.predict_proba(X_test)[:, 1]
    recomputed_auc = roc_auc_score(y_test, proba_test)
    auc_drift = abs(recomputed_auc - persisted_auc)
    logger.info(f"Recomputed AUC Test:       {recomputed_auc:.6f}")
    logger.info(f"AUC drift (persisted vs reconstructed): {auc_drift:.2e}")
    integrity_passed = auc_drift < AUC_TOLERANCE
    logger.info(f"Reproducibility check:     {'PASSED' if integrity_passed else 'FAILED'}")

    logger.info("")
    logger.info("=" * 70)
    logger.info("PHASE 4 — Smoke test (live predictions)")
    logger.info("=" * 70)
    smoke_test_passed = run_smoke_test(model, X_test, logger)
    logger.info(f"Smoke test result:         {'PASSED' if smoke_test_passed else 'FAILED'}")

    return AuditResult(
        model_path_exists=model_exists,
        metrics_path_exists=metrics_exists,
        model_size_kb=model_size_kb,
        model_sha256=model_hash,
        persisted_auc_test=persisted_auc,
        recomputed_auc_test=recomputed_auc,
        auc_drift=auc_drift,
        integrity_passed=integrity_passed,
        smoke_test_passed=smoke_test_passed,
    )


def print_audit_summary(result: AuditResult, logger: logging.Logger) -> None:
    logger.info("")
    logger.info("=" * 70)
    logger.info("AUDIT SUMMARY")
    logger.info("=" * 70)
    overall = result.integrity_passed and result.smoke_test_passed
    logger.info(f"  Model artifact:        {'OK' if result.model_path_exists else 'MISSING'}")
    logger.info(f"  Metrics artifact:      {'OK' if result.metrics_path_exists else 'MISSING'}")
    logger.info(f"  Reproducibility:       {'OK' if result.integrity_passed else 'DRIFT DETECTED'}")
    logger.info(f"  Smoke test:            {'OK' if result.smoke_test_passed else 'FAILED'}")
    logger.info(f"  OVERALL STATUS:        {'PRODUCTION READY' if overall else 'AUDIT FAILED'}")


def main() -> None:
    logger = configure_logger()
    logger.info("Initializing Model Audit Pipeline...")

    base_dir = Path(__file__).parent
    result = audit_model(base_dir, logger)
    print_audit_summary(result, logger)


if __name__ == "__main__":
    main()