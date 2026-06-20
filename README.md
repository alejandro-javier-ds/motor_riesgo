# Motor de Riesgo Conductual — Tesis SENATI 2026

Sistema de evaluación de riesgo crediticio para perfiles sin historial financiero (thin-files) basado en un motor Gradient Boosting conductual con instrumentos psicométricos.

## Descripción

Este proyecto implementa un motor predictivo CatBoost entrenado sobre 30 ítems psicométricos organizados en 4 pilares conductuales:

- **Pilar 1 — Orden y Disciplina** (10 ítems)
- **Pilar 2 — Descuento Hiperbólico** (8 ítems)
- **Pilar 3 — Locus de Control** (7 ítems)
- **Pilar 4 — Escala de Deseabilidad Social (Marlowe-Crowne)** (5 ítems)

El modelo alcanza un **AUC-ROC de 0.8404** con un gap train-test de +0.018, demostrando alta capacidad de generalización sobre perfiles sin historial crediticio.

## Stack Tecnológico

| Capa | Tecnología |
|---|---|
| Modelo | CatBoost 1.2.10 + SHAP 0.51 |
| Backend | FastAPI + Uvicorn + Polars |
| Frontend | Next.js 15 + TypeScript + Tailwind |
| BD Desarrollo | SQL Server LocalDB |
| BD Producción | PostgreSQL (Railway) |
| MLOps | MLflow 3.13 + DVC |
| Deploy | Render (backend) + Vercel (frontend) |
| Contenedor | Docker |

## Estructura del Proyecto
motor_riesgo/

├── backend/

│   ├── simulador.py          # Generador de datos sintéticos (5000 registros)

│   ├── model.py              # Entrenamiento Iter 4 Hardened

│   ├── main.py               # API FastAPI (/predict + /admin/resultados)

│   ├── audit.py              # Validación del modelo serializado

│   ├── inference.py          # Inferencia sintética + sensibilidad

│   ├── inference_real_data.py # Inferencia sobre 28 respondedores reales

│   ├── mlflow_tracking.py    # Registro de 4 iteraciones en MLflow

│   ├── Dockerfile            # Imagen Docker para Render

│   ├── pyproject.toml        # Dependencias Poetry

│   └── requirements.txt      # Dependencias exportadas para Docker

├── frontend/

│   ├── app/                  # Páginas Next.js (13 pantallas)

│   ├── components/           # Componentes reutilizables

│   └── lib/api.ts            # Cliente API

├── dvc.yaml                  # Pipeline DVC

└── dvc.lock                  # Hashes de artefactos versionados

## Iteraciones del Modelo

| Iteración | AUC Test | Gap | Técnica |
|---|---|---|---|
| Iter 1 — Baseline | 0.8264 | +0.120 | Sin defensas |
| Iter 2 — SMOTE-NC | 0.8408 | +0.037 | Balanceo + L2 |
| Iter 3 — Ablation | 0.8408 | +0.051 | Sin demográficas |
| **Iter 4 — Hardened** | **0.8404** | **+0.018** | **Reg. agresiva + Bayesian** |

## Autores

- **Alejandro Javier Martínez Flores**
- **Fred Roland Jaramillo Jaramillo**

**Asesor**: Caroll Cynthia Camarena Vasquez

**Institución**: SENATI — Ingeniería de Ciencia de Datos e Inteligencia Artificial

**Año**: 2026