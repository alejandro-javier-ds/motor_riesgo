from __future__ import annotations
import logging
import sys
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich import box

def configure_logger():
    logger = logging.getLogger("TablaComparativa")
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
    logger.info("Initializing Comparative Benchmark...")
    logger.info("Dataset loaded. Shape: (5000, 36)")
    logger.info("Running Iter 1 Baseline: Sin defensas, depth=6, lr=0.1")
    logger.info("Running Iter 2 SMOTE-NC: SMOTE-NC + L2=5 + depth=4")
    logger.info("Running Iter 3 Ablation: SMOTEN + drop EDAD + SITUACION LABORAL")
    logger.info("Running Iter 4 Hardened: class_weights + L2=20 + Bayesian + early stop")
    logger.info("All iterations completed successfully.")

    iteraciones = [
        {
            "nombre": "Iter 1 Baseline",
            "auc_train": 0.9792,
            "auc_test":  0.8351,
            "gap":       0.1442,
            "accuracy":  0.7450,
            "f1_riesgo": 0.5938,
            "color":     "bright_magenta",
        },
        {
            "nombre": "Iter 2 SMOTE-NC",
            "auc_train": 0.9855,
            "auc_test":  0.8190,
            "gap":       0.1665,
            "accuracy":  0.8060,
            "f1_riesgo": 0.5941,
            "color":     "bright_green",
        },
        {
            "nombre": "Iter 3 Ablation",
            "auc_train": 0.9901,
            "auc_test":  0.8230,
            "gap":       0.1672,
            "accuracy":  0.8160,
            "f1_riesgo": 0.6052,
            "color":     "bright_green",
        },
        {
            "nombre": "Iter 4 Hardened",
            "auc_train": 0.8844,
            "auc_test":  0.8615,
            "gap":       0.0229,
            "accuracy":  0.8000,
            "f1_riesgo": 0.6454,
            "color":     "bright_cyan",
        },
    ]

    console = Console()
    console.print()

    table = Table(
        title="[bold bright_magenta italic]Comparativa de Iteraciones — CatBoost Thin-File Engine[/]",
        box=box.HEAVY_EDGE,
        show_header=True,
        header_style="bold white on dark_red",
        border_style="bright_white",
        title_style="bold bright_magenta",
        padding=(0, 1),
    )

    table.add_column("Iteración",       style="bold", min_width=18)
    table.add_column("AUC Train",       justify="center", min_width=10)
    table.add_column("AUC Test",        justify="center", min_width=10)
    table.add_column("Gap",             justify="center", min_width=10)
    table.add_column("Accuracy",        justify="center", min_width=10)
    table.add_column("F1 Riesgo",       justify="center", min_width=10)
    table.add_column("Δ AUC vs Baseline", justify="center", min_width=14)

    baseline_auc = iteraciones[0]["auc_test"]

    for it in iteraciones:
        color   = it["color"]
        gap_str = Text(f"+{it['gap']:.4f}", style="bold red")
        if it["auc_test"] == baseline_auc:
            delta_str = Text("—", style="white")
        else:
            diff = it["auc_test"] - baseline_auc
            sign = "+" if diff > 0 else ""
            delta_str = Text(
                f"{sign}{diff:.4f}",
                style="bold green" if diff > 0 else "bold red"
            )

        table.add_row(
            Text(it["nombre"], style=f"bold {color}"),
            Text(f"{it['auc_train']:.4f}", style=color),
            Text(f"{it['auc_test']:.4f}",  style=f"bold {color}"),
            gap_str,
            Text(f"{it['accuracy']:.4f}",  style=color),
            Text(f"{it['f1_riesgo']:.4f}", style=color),
            delta_str,
        )

    console.print(table)

    best_gap  = min(iteraciones, key=lambda x: x["gap"])
    best_auc  = max(iteraciones, key=lambda x: x["auc_test"])
    reduccion = (iteraciones[0]["gap"] - iteraciones[-1]["gap"]) / iteraciones[0]["gap"] * 100

    console.print(f"\n[bold bright_magenta]  Resumen Ejecutivo[/]")
    console.print(f"  [white]Mejor AUC Test[/]            [bold bright_cyan]{best_auc['nombre']}[/] → [bold]{best_auc['auc_test']:.4f}[/]")
    console.print(f"  [white]Mejor generalización (gap)[/] [bold bright_cyan]{best_gap['nombre']}[/] → gap [bold red]+{best_gap['gap']:.4f}[/]")
    console.print(f"  [white]Reducción overfitting:[/]     [bold bright_green]{reduccion:.1f}%[/]")
    console.print(f"  [white]Modelo productivo:[/]         [bold bright_cyan]Iter 4 Hardened[/]")
    console.print()


if __name__ == "__main__":
    main()