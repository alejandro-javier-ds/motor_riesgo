import os
import json
import logging
import re
import sys
from difflib import get_close_matches
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import polars as pl
import shap
import psycopg2
from catboost import CatBoostClassifier
from pathlib import Path
import uvicorn
from dotenv import load_dotenv

load_dotenv()

LIKERT_PREFIX_PATTERN = re.compile(
    r"^Indica qué tan identificado te sientes con las siguientes afirmaciones cotidianas\.\s*\[(.+)\]\s*$"
)


def configure_logger() -> logging.Logger:
    logger = logging.getLogger("MotorRiesgo")
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


logger = configure_logger()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

base_dir = Path(__file__).parent
model = CatBoostClassifier()
model.load_model(str(base_dir / "catboost_thin_file.cbm"))
logger.info(f"Model loaded. Expected features: {len(model.feature_names_)}")

explainer = None

conn_str = os.getenv("DB_CONNECTION_STRING", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "senati2026")


class ClientData(BaseModel):
    data: dict
    user_info: dict


def strip_likert_prefix(key: str) -> str:
    match = LIKERT_PREFIX_PATTERN.match(key.strip())
    return match.group(1).strip() if match else key.strip()


def normalize_survey_keys(raw_data: dict, model_features: list) -> dict:
    normalized = {}
    for key, value in raw_data.items():
        clean_key = strip_likert_prefix(key)
        if clean_key not in model_features:
            candidates = get_close_matches(clean_key, model_features, n=1, cutoff=0.85)
            if candidates:
                logger.info(f"Fuzzy match: '{clean_key[:50]}' → '{candidates[0][:50]}'")
                clean_key = candidates[0]
        normalized[clean_key] = value
    return normalized


def asignar_politica(prob: float):
    if prob < 0.30:
        return "Pre-aprobado", 800.0
    elif prob < 0.35:
        return "Pre-aprobado", 300.0
    else:
        return "Denegado", 0.0


def calcular_shap_individual(X_pandas):
    global explainer
    if explainer is None:
        logger.info("Initializing SHAP explainer...")
        explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_pandas)
    feature_names = list(X_pandas.columns)
    valores = shap_values[0].tolist()
    contribuciones = sorted(
        [
            {
                "feature": feature_names[i],
                "shap_value": float(valores[i]),
                "input_value": str(X_pandas.iloc[0, i]),
            }
            for i in range(len(feature_names))
        ],
        key=lambda x: abs(x["shap_value"]),
        reverse=True,
    )
    return {
        "base_value": (
            float(explainer.expected_value)
            if not hasattr(explainer.expected_value, "__len__")
            else float(explainer.expected_value[0])
        ),
        "top_features": contribuciones[:10],
    }


def get_connection():
    return psycopg2.connect(conn_str)


def persistir_datos(user_data, eval_data, pred_data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO tbl_usuarios (nombre_completo, edad, distrito_residencia, nivel_educativo, situacion_laboral)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING usuario_id
        """,
        (
            user_data.get("nombre", ""),
            user_data.get("edad", 0),
            user_data.get("distrito", ""),
            user_data.get("nivel_educativo", ""),
            user_data.get("situacion_laboral", ""),
        ),
    )
    user_id = cursor.fetchone()[0]
    cursor.execute(
        """
        INSERT INTO tbl_evaluacion_conductual (usuario_id, datos_json)
        VALUES (%s, %s)
        RETURNING evaluacion_id
        """,
        (user_id, json.dumps(eval_data)),
    )
    eval_id = cursor.fetchone()[0]
    cursor.execute(
        """
        INSERT INTO tbl_predicciones (evaluacion_id, probabilidad_viabilidad, estado_final, shap_explicacion, monto_aprobado)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            eval_id,
            pred_data["prob"],
            pred_data["estado"],
            pred_data["shap"],
            pred_data["monto"],
        ),
    )
    conn.commit()
    cursor.close()
    conn.close()


@app.post("/predict")
async def predict(client: ClientData):
    try:
        logger.info("=== /predict called ===")

        model_features = list(model.feature_names_)
        survey_data = normalize_survey_keys(dict(client.data), model_features)
        survey_data["DISTRITO"] = client.user_info.get("distrito", "")
        survey_data["NIVEL_EDUCATIVO"] = client.user_info.get("nivel_educativo", "")

        survey_data_lists = {
            k: v if isinstance(v, list) else [v]
            for k, v in survey_data.items()
        }

        df = pl.DataFrame(survey_data_lists)
        df = df.rename({col: col.strip() for col in df.columns})

        missing = [col for col in model_features if col not in df.columns]
        if missing:
            logger.info(f"Missing features ({len(missing)}): {missing[:3]}")
            raise ValueError(f"Faltan features requeridas por el modelo: {missing}")

        X = df.select(model_features)
        X_pandas = X.to_pandas()

        for col in X_pandas.columns:
            X_pandas[col] = X_pandas[col].astype(str)

        prob = float(model.predict_proba(X_pandas)[0][1])
        decision, monto = asignar_politica(prob)
        logger.info(f"Prediction: P(moroso)={prob:.4f} → {decision} S/{monto}")

        shap_data = calcular_shap_individual(X_pandas)

        pred_data = {
            "prob": prob,
            "estado": decision,
            "monto": monto,
            "shap": json.dumps(shap_data),
        }

        persistir_datos(client.user_info, client.data, pred_data)
        logger.info("Data persisted to DB successfully.")

        return {"Decision": decision, "Monto": monto, "Probabilidad": prob}

    except Exception as e:
        logger.info(f"ERROR in /predict: {str(e)[:300]}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/resultados")
async def admin_resultados(x_admin_password: str = Header(None)):
    if x_admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                u.nombre_completo,
                u.edad,
                u.distrito_residencia,
                u.nivel_educativo,
                u.situacion_laboral,
                u.fecha_registro,
                p.probabilidad_viabilidad,
                p.estado_final,
                p.monto_aprobado,
                p.shap_explicacion
            FROM tbl_usuarios u
            INNER JOIN tbl_evaluacion_conductual e ON u.usuario_id = e.usuario_id
            INNER JOIN tbl_predicciones p ON e.evaluacion_id = p.evaluacion_id
            ORDER BY u.fecha_registro DESC
            LIMIT 50
        """)
        columns = [col[0] for col in cursor.description]
        resultados = []
        for row in cursor.fetchall():
            registro = dict(zip(columns, row))
            registro["fecha_registro"] = (
                registro["fecha_registro"].isoformat()
                if registro["fecha_registro"]
                else None
            )
            registro["monto_aprobado"] = (
                float(registro["monto_aprobado"])
                if registro["monto_aprobado"]
                else 0.0
            )
            try:
                registro["shap_explicacion"] = (
                    json.loads(registro["shap_explicacion"])
                    if registro["shap_explicacion"]
                    else None
                )
            except Exception:
                registro["shap_explicacion"] = None
            resultados.append(registro)

        cursor.close()
        conn.close()
        return {"total": len(resultados), "resultados": resultados}

    except Exception as e:
        logger.info(f"ERROR in /admin/resultados: {str(e)[:300]}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)