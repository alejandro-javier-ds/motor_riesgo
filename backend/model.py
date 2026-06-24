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
    iterations: int        = 3000
    depth: int             = 3
    learning_rate: float   = 0.005
    l2_leaf_reg: float     = 20.0
    random_strength: float = 12.0
    min_data_in_leaf: int  = 25
    auto_class_weights: str     = "Balanced"
    early_stopping_rounds: int  = 150
    bootstrap_type: str         = "Bayesian"
    bagging_temperature: float  = 1.0


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


def configure_logger():
    logger = logging.getLogger("Iter4")
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


def main():
    logger = configure_logger()
    logger.info("=" * 60)
    logger.info("ITERACION 4 ")
    logger.info("=" * 60)

    base_dir = Path(__file__).parent
    df = pl.read_csv(base_dir / "simulated_thin_file_data.csv")
    df = df.with_columns(
        pl.when(pl.col(TARGET_COL) == "Sí").then(1).otherwise(0).alias(TARGET_COL)
    )
    df = df.drop(DROPPED_FEATURES)

    logger.info(f"Dataset loaded and ablated. Shape: {df.shape}")
    logger.info(f"Dropped demographic features: {DROPPED_FEATURES}")
    logger.info("Balanceo: auto_class_weights='Balanced' (sin SMOTE)")
    logger.info("Split estratificado 3-way: 60/20/20 (Train/Val/Test)")

    X = df.drop(TARGET_COL).to_pandas()
    y = df.select(TARGET_COL).to_pandas().squeeze()

    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp,
        test_size=VAL_SIZE_FROM_TEMP,
        random_state=RANDOM_SEED,
        stratify=y_temp,
    )

    logger.info(
        f"Stratified split → Train: {X_train.shape} | "
        f"Val: {X_val.shape} | Test: {X_test.shape}"
    )

    cat_features = list(X_train.select_dtypes(include=["object", "string"]).columns)
    logger.info(f"Categorical features detected: {len(cat_features)}")
    logger.info(f"Class distribution train: {y_train.value_counts().to_dict()}")

    hp = Hyperparameters()
    logger.info(
        f"Hyperparameters: iterations={hp.iterations}, depth={hp.depth}, "
        f"learning_rate={hp.learning_rate}, l2_leaf_reg={hp.l2_leaf_reg}, "
        f"random_strength={hp.random_strength}, min_data_in_leaf={hp.min_data_in_leaf}, "
        f"auto_class_weights={hp.auto_class_weights}, "
        f"early_stopping_rounds={hp.early_stopping_rounds}, "
        f"bootstrap_type={hp.bootstrap_type}, "
        f"bagging_temperature={hp.bagging_temperature}"
    )

    train_pool = Pool(X_train, y_train, cat_features=cat_features)
    val_pool   = Pool(X_val,   y_val,   cat_features=cat_features)
    test_pool  = Pool(X_test,  y_test,  cat_features=cat_features)

    model = CatBoostClassifier(
        iterations=hp.iterations,
        depth=hp.depth,
        learning_rate=hp.learning_rate,
        l2_leaf_reg=hp.l2_leaf_reg,
        random_strength=hp.random_strength,
        min_data_in_leaf=hp.min_data_in_leaf,
        auto_class_weights=hp.auto_class_weights,
        early_stopping_rounds=hp.early_stopping_rounds,
        bootstrap_type=hp.bootstrap_type,
        bagging_temperature=hp.bagging_temperature,
        random_seed=RANDOM_SEED,
        verbose=False,
    )
    model.fit(train_pool, eval_set=val_pool, use_best_model=True)
    logger.info(f"Training stopped at tree: {model.tree_count_}")

    proba_train = model.predict_proba(train_pool)[:, 1]
    proba_val   = model.predict_proba(val_pool)[:, 1]
    proba_test  = model.predict_proba(test_pool)[:, 1]
    pred_test   = model.predict(test_pool)

    auc_train = roc_auc_score(y_train, proba_train)
    auc_val   = roc_auc_score(y_val,   proba_val)
    auc_test  = roc_auc_score(y_test,  proba_test)
    gap       = auc_train - auc_test

    logger.info(f"ROC-AUC Train:      {auc_train:.4f}")
    logger.info(f"ROC-AUC Validation: {auc_val:.4f}")
    logger.info(f"ROC-AUC Test:       {auc_test:.4f}")
    logger.info(f"Train-Test AUC gap: {gap:+.4f}")
    logger.info(f"Accuracy Test:      {accuracy_score(y_test, pred_test):.4f}")
    logger.info(f"Precision Riesgo:   {precision_score(y_test, pred_test):.4f}")
    logger.info(f"Recall Riesgo:      {recall_score(y_test, pred_test):.4f}")
    logger.info(f"F1 Riesgo:          {f1_score(y_test, pred_test):.4f}")

    report = classification_report(
        y_test, pred_test,
        target_names=["Viable (0)", "Riesgo (1)"],
        digits=4,
    )
    matrix = confusion_matrix(y_test, pred_test)
    logger.info(f"Classification Report:\n{report}")
    logger.info(
        "Confusion Matrix:\n"
        f"  TN={matrix[0][0]:>4d}  FP={matrix[0][1]:>4d}\n"
        f"  FN={matrix[1][0]:>4d}  TP={matrix[1][1]:>4d}"
    )

    raw_imp = model.get_feature_importance()
    total   = float(raw_imp.sum())
    paired  = sorted(
        zip(list(X_train.columns), raw_imp),
        key=lambda x: x[1], reverse=True
    )
    logger.info(f"Top {TOP_FEATURES_TO_REPORT} Feature Importances:")
    for rank, (name, imp) in enumerate(paired[:TOP_FEATURES_TO_REPORT], 1):
        truncated = (name[:65] + "...") if len(name) > 68 else name
        logger.info(f"  {rank:>2d}. {truncated:<70s} {imp/total*100:>5.2f}%")

    report_data = EvaluationReport(
        trees_used=int(model.tree_count_),
        auc_train=auc_train,
        auc_validation=auc_val,
        auc_test=auc_test,
        train_test_gap=gap,
        accuracy=accuracy_score(y_test, pred_test),
        precision_riesgo=precision_score(y_test, pred_test),
        recall_riesgo=recall_score(y_test, pred_test),
        f1_riesgo=f1_score(y_test, pred_test),
    )

    model.save_model(str(base_dir / MODEL_FILENAME))
    with (base_dir / METRICS_FILENAME).open("w", encoding="utf-8") as f:
        json.dump(asdict(report_data), f, indent=2)

    logger.info(f"Model saved: {MODEL_FILENAME}")
    logger.info(f"Metrics saved: {METRICS_FILENAME}")


if __name__ == "__main__":
    main()