from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Final

import mlflow
import mlflow.catboost
import polars as pl
from catboost import CatBoostClassifier, Pool
from imblearn.over_sampling import SMOTEN, SMOTENC
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

RANDOM_SEED: Final[int] = 42
TARGET_COL: Final[str] = "TARGET_MOROSIDAD"
EXPERIMENT_NAME: Final[str] = "CatBoost_ThinFile_Iterations"
DATASET_FILENAME: Final[str] = "simulated_thin_file_data.csv"
TEST_SIZE: Final[float] = 0.20
VAL_SIZE_FROM_TEMP: Final[float] = 0.25


def configure_logger() -> logging.Logger:
    logger = logging.getLogger("MLflowTracker")
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


def load_dataset(base_dir: Path) -> pl.DataFrame:
    df = pl.read_csv(base_dir / DATASET_FILENAME)
    return df.with_columns(
        pl.when(pl.col(TARGET_COL) == "Sí").then(1).otherwise(0).alias(TARGET_COL)
    )


def evaluate_model(model, X_train, X_test, y_train, y_test) -> dict:
    y_pred = model.predict(X_test)
    proba_train = model.predict_proba(X_train)[:, 1]
    proba_test = model.predict_proba(X_test)[:, 1]
    auc_train = roc_auc_score(y_train, proba_train)
    auc_test = roc_auc_score(y_test, proba_test)
    report = classification_report(y_test, y_pred, target_names=["Viable", "Riesgo"], output_dict=True)
    return {
        "auc_train": round(auc_train, 6),
        "auc_test": round(auc_test, 6),
        "train_test_gap": round(auc_train - auc_test, 6),
        "accuracy_test": round(accuracy_score(y_test, y_pred), 6),
        "precision_viable": round(report["Viable"]["precision"], 6),
        "recall_viable": round(report["Viable"]["recall"], 6),
        "f1_viable": round(report["Viable"]["f1-score"], 6),
        "precision_riesgo": round(report["Riesgo"]["precision"], 6),
        "recall_riesgo": round(report["Riesgo"]["recall"], 6),
        "f1_riesgo": round(report["Riesgo"]["f1-score"], 6),
    }


def run_iteration_1(df: pl.DataFrame, logger: logging.Logger):
    logger.info("Running Iteration 1: Baseline")
    X = df.drop(TARGET_COL).to_pandas()
    y = df.select(TARGET_COL).to_pandas().squeeze()
    cat_features = list(X.select_dtypes(include=["object", "string"]).columns)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y
    )
    params = {"iterations": 500, "learning_rate": 0.1, "depth": 6, "random_seed": RANDOM_SEED}
    model = CatBoostClassifier(**params, verbose=False)
    model.fit(X_train, y_train, cat_features=cat_features)
    metrics = evaluate_model(model, X_train, X_test, y_train, y_test)
    tags = {"smote": "None", "ablation": "No", "categorical_handling": "Native"}
    return params, metrics, model, tags


def run_iteration_2(df: pl.DataFrame, logger: logging.Logger):
    logger.info("Running Iteration 2: SMOTE-NC")
    X = df.drop(TARGET_COL).to_pandas()
    y = df.select(TARGET_COL).to_pandas().squeeze()
    cat_features = list(X.select_dtypes(include=["object", "string"]).columns)
    cat_indices = [X.columns.get_loc(c) for c in cat_features]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y
    )
    X_train_r, y_train_r = SMOTENC(categorical_features=cat_indices, random_state=RANDOM_SEED).fit_resample(X_train, y_train)
    params = {"iterations": 500, "learning_rate": 0.05, "depth": 4, "l2_leaf_reg": 5, "random_seed": RANDOM_SEED}
    model = CatBoostClassifier(**params, verbose=False)
    model.fit(X_train_r, y_train_r, cat_features=cat_features)
    metrics = evaluate_model(model, X_train_r, X_test, y_train_r, y_test)
    tags = {"smote": "SMOTE-NC", "ablation": "No", "categorical_handling": "Native"}
    return params, metrics, model, tags


def run_iteration_3(df: pl.DataFrame, logger: logging.Logger):
    logger.info("Running Iteration 3: Ablation + SMOTEN")
    df = df.drop(["EDAD", "SITUACION LABORAL"])
    X = df.drop(TARGET_COL).to_pandas()
    y = df.select(TARGET_COL).to_pandas().squeeze()
    cat_features = list(X.select_dtypes(include=["object", "string"]).columns)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y
    )
    X_train_r, y_train_r = SMOTEN(random_state=RANDOM_SEED).fit_resample(X_train, y_train)
    params = {"iterations": 500, "learning_rate": 0.05, "depth": 5, "l2_leaf_reg": 5, "random_seed": RANDOM_SEED}
    model = CatBoostClassifier(**params, verbose=False)
    model.fit(X_train_r, y_train_r, cat_features=cat_features)
    metrics = evaluate_model(model, X_train_r, X_test, y_train_r, y_test)
    tags = {"smote": "SMOTEN", "ablation": "Yes", "categorical_handling": "Native"}
    return params, metrics, model, tags


def run_iteration_4(df: pl.DataFrame, logger: logging.Logger):
    logger.info("Running Iteration 4: Hardened Final")
    df = df.drop(["EDAD", "SITUACION LABORAL"])
    X = df.drop(TARGET_COL).to_pandas()
    y = df.select(TARGET_COL).to_pandas().squeeze()
    cat_features = list(X.select_dtypes(include=["object", "string"]).columns)

    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=VAL_SIZE_FROM_TEMP, random_state=RANDOM_SEED, stratify=y_temp
    )

    params = {
        "iterations": 2000,
        "learning_rate": 0.01,
        "depth": 3,
        "l2_leaf_reg": 15,
        "auto_class_weights": "Balanced",
        "bootstrap_type": "Bayesian",
        "bagging_temperature": 0.5,
        "random_seed": RANDOM_SEED,
    }

    train_pool = Pool(X_train, y_train, cat_features=cat_features)
    val_pool = Pool(X_val, y_val, cat_features=cat_features)
    test_pool = Pool(X_test, y_test, cat_features=cat_features)

    model = CatBoostClassifier(**params, early_stopping_rounds=100, verbose=False)
    model.fit(train_pool, eval_set=val_pool, use_best_model=True)

    proba_val = model.predict_proba(val_pool)[:, 1]
    auc_val = roc_auc_score(y_val, proba_val)

    metrics = evaluate_model(model, train_pool, test_pool, y_train, y_test)
    metrics["auc_validation"] = round(auc_val, 6)
    metrics["trees_used"] = int(model.tree_count_)

    tags = {
        "smote": "None",
        "ablation": "Yes",
        "balancing": "auto_class_weights=Balanced",
        "bootstrap": "Bayesian",
        "split_strategy": "3-way (60/20/20)",
    }
    return params, metrics, model, tags


def main() -> None:
    logger = configure_logger()
    base_dir = Path(__file__).parent
    mlflow_db_path = base_dir / "mlflow.db"

    mlflow.set_tracking_uri(f"sqlite:///{mlflow_db_path}")
    mlflow.set_experiment(EXPERIMENT_NAME)
    logger.info(f"MLflow experiment: {EXPERIMENT_NAME}")
    logger.info(f"Tracking URI: sqlite:///{mlflow_db_path}")

    df = load_dataset(base_dir)
    logger.info(f"Dataset loaded. Shape: {df.shape}")

    iteraciones = [
        ("Iteration_1_Baseline", run_iteration_1),
        ("Iteration_2_SMOTE_NC", run_iteration_2),
        ("Iteration_3_Ablation_SMOTEN", run_iteration_3),
        ("Iteration_4_Hardened_Final", run_iteration_4),
    ]

    for run_name, run_function in iteraciones:
        with mlflow.start_run(run_name=run_name):
            params, metrics, model, tags = run_function(df, logger)
            mlflow.log_params(params)
            mlflow.log_metrics(metrics)
            for key, value in tags.items():
                mlflow.set_tag(key, value)
            mlflow.catboost.log_model(model, name="model")
            logger.info(
                f"{run_name} → AUC Test: {metrics['auc_test']:.4f} | "
                f"Gap: {metrics['train_test_gap']:+.4f}"
            )

    logger.info("All 4 iterations logged successfully to MLflow.")
    logger.info(f"Launch UI: mlflow ui --backend-store-uri sqlite:///{mlflow_db_path}")


if __name__ == "__main__":
    main()