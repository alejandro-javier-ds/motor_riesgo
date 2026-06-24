from __future__ import annotations

import logging
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import polars as pl
import shap
from catboost import CatBoostClassifier, Pool

RANDOM_SEED = 42
TARGET_COL = "TARGET_MOROSIDAD"
DROPPED_FEATURES = ["EDAD", "SITUACION LABORAL"]
MODEL_FILENAME = "catboost_thin_file.cbm"
DATASET_FILENAME = "simulated_thin_file_data.csv"
OUTPUT_FILENAME = "shap_audit_report.png"
TOP_N_FEATURES = 15


def configure_logger():
    logger = logging.getLogger("SHAPReport")
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
    logger.info("Initializing SHAP Audit Report Pipeline...")

    base_dir = Path(__file__).parent

    logger.info("Loading model...")
    model = CatBoostClassifier()
    model.load_model(str(base_dir / MODEL_FILENAME))
    logger.info(f"Model loaded. Trees: {model.tree_count_}")

    logger.info("Loading and preparing dataset...")
    df = pl.read_csv(base_dir / DATASET_FILENAME)
    df = df.with_columns(
        pl.when(pl.col(TARGET_COL) == "Sí").then(1).otherwise(0).alias(TARGET_COL)
    )
    df = df.drop(DROPPED_FEATURES)
    X = df.drop(TARGET_COL).to_pandas()
    logger.info(f"Dataset shape: {X.shape}")

    cat_features = list(X.select_dtypes(include=["object", "string"]).columns)
    logger.info(f"Categorical features: {len(cat_features)}")

    logger.info("Computing SHAP values (TreeExplainer)...")
    explainer = shap.TreeExplainer(model)
    pool = Pool(X, cat_features=cat_features)
    shap_values = explainer.shap_values(pool)
    logger.info("SHAP values computed successfully.")

    logger.info(f"Generating SHAP Summary Plot (Top {TOP_N_FEATURES} features)...")
    plt.figure(figsize=(12, 8))
    shap.summary_plot(
        shap_values,
        X,
        max_display=TOP_N_FEATURES,
        show=False,
        plot_type="dot",
    )
    plt.title(
        f"SHAP Summary — Top {TOP_N_FEATURES} Features\n"
        f"CatBoost Hardened Model · Full Dataset (5000 samples)",
        fontsize=13,
        pad=15,
    )
    plt.tight_layout()
    output_path = base_dir / OUTPUT_FILENAME
    plt.savefig(str(output_path), dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"SHAP report saved: {output_path}")
    logger.info("Pipeline completed successfully.")


if __name__ == "__main__":
    main()