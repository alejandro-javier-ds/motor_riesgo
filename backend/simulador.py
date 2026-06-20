import logging
import sys
from pathlib import Path
import numpy as np
import polars as pl

def configure_logger() -> logging.Logger:
    logger = logging.getLogger("Simulator")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(fmt="[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(console_handler)
    return logger

LIKERT_SCALE = ["Totalmente en desacuerdo", "En desacuerdo", "Neutral", "De acuerdo", "Totalmente de acuerdo"]

PREGUNTAS_CONFIG = {
    "Mi espacio de trabajo y mi habitación suelen estar siempre ordenados.": {"pilar": "ORDEN", "subdim": "orden_fisico", "invertida": False, "intensidad": "media"},
    "Prefiero terminar mis obligaciones urgentes antes de sentarme a relajarme o salir.": {"pilar": "ORDEN", "subdim": "disciplina", "invertida": False, "intensidad": "media"},
    "Me genera mucha ansiedad la idea de llegar tarde a un compromiso, aunque sea una reunión informal.": {"pilar": "ORDEN", "subdim": "puntualidad", "invertida": False, "intensidad": "alta"},
    "Me molesta profundamente cuando las personas cambian los planes a última hora sin avisar.": {"pilar": "ORDEN", "subdim": "puntualidad", "invertida": False, "intensidad": "media"},
    "Suelo revisar dos o tres veces los mensajes o correos importantes antes de enviarlos.": {"pilar": "ORDEN", "subdim": "perfeccionismo", "invertida": False, "intensidad": "baja"},
    "Cuando empiezo un proyecto personal o tarea en casa, lo termino aunque me tome más tiempo del planeado.": {"pilar": "ORDEN", "subdim": "disciplina", "invertida": False, "intensidad": "media"},
    "Llevo un registro mental o escrito de las tareas que debo hacer durante la semana.": {"pilar": "ORDEN", "subdim": "orden_fisico", "invertida": False, "intensidad": "media"},
    "A menudo dejo las cosas en cualquier lado y luego pierdo tiempo buscándolas.": {"pilar": "ORDEN", "subdim": "orden_fisico", "invertida": True, "intensidad": "media"},
    "Siento que es mi obligación cumplir con una promesa, incluso si la otra persona ya lo olvidó.": {"pilar": "ORDEN", "subdim": "integridad", "invertida": False, "intensidad": "alta"},
    "Frecuentemente postergo tareas aburridas hasta el último minuto posible.": {"pilar": "ORDEN", "subdim": "disciplina", "invertida": True, "intensidad": "media"},
    "A menudo actúo por impulso en el momento y luego me arrepiento de las consecuencias.": {"pilar": "DESCUENTO", "subdim": "impulsividad", "invertida": True, "intensidad": "media"},
    "Prefiero sacrificar mi tiempo libre hoy si sé que eso me traerá un gran beneficio el próximo año.": {"pilar": "DESCUENTO", "subdim": "persistencia", "invertida": False, "intensidad": "media"},
    "Cuando me encuentro con un problema difícil o tedioso, mi primer instinto es abandonarlo y hacer otra cosa.": {"pilar": "DESCUENTO", "subdim": "persistencia", "invertida": True, "intensidad": "media"},
    "Me cuesta mucho resistirme a mis antojos del momento, aunque sepa que después me arrepentiré.": {"pilar": "DESCUENTO", "subdim": "impulsividad", "invertida": True, "intensidad": "media"},
    "Si me dan a elegir, prefiero esperar un mes por una recompensa excelente que recibir una recompensa regular hoy mismo.": {"pilar": "DESCUENTO", "subdim": "persistencia", "invertida": False, "intensidad": "media"},
    "Me aburro rápido de los pasatiempos o proyectos nuevos y salto a otra cosa rápidamente.": {"pilar": "DESCUENTO", "subdim": "persistencia", "invertida": True, "intensidad": "media"},
    "Siempre evalúo los pros y contras antes de tomar una decisión importante en mi vida diaria.": {"pilar": "DESCUENTO", "subdim": "persistencia", "invertida": False, "intensidad": "alta"},
    "Si veo algo que me gusta mucho, busco la forma de tenerlo inmediatamente sin pensar mucho en el futuro.": {"pilar": "DESCUENTO", "subdim": "impulsividad", "invertida": True, "intensidad": "media"},
    "Creo firmemente que mis logros dependen exclusivamente de mi esfuerzo diario y no de la buena suerte.": {"pilar": "LOCUS", "subdim": "auto_responsabilidad", "invertida": False, "intensidad": "alta"},
    "Siento que la mayor parte de las cosas malas que me pasan son culpa de otras personas o de las circunstancias.": {"pilar": "LOCUS", "subdim": "atribucion_externa", "invertida": True, "intensidad": "media"},
    "Si fracaso en un objetivo, analizo qué hice mal para no repetirlo, en lugar de frustrarme con el entorno.": {"pilar": "LOCUS", "subdim": "auto_responsabilidad", "invertida": False, "intensidad": "media"},
    "A veces siento que no tiene sentido planificar demasiado porque el destino ya está escrito.": {"pilar": "LOCUS", "subdim": "atribucion_externa", "invertida": True, "intensidad": "media"},
    "Cuando trabajo en equipo y algo sale mal, asumo mi parte de la culpa en lugar de señalar a los demás de inmediato.": {"pilar": "LOCUS", "subdim": "auto_responsabilidad", "invertida": False, "intensidad": "media"},
    "Confío más en mi propia capacidad para resolver problemas inesperados que en esperar a que alguien más me ayude.": {"pilar": "LOCUS", "subdim": "auto_responsabilidad", "invertida": False, "intensidad": "media"},
    "Siento que el éxito de las personas a mi alrededor se debe más a sus contactos o suerte que a su talento.": {"pilar": "LOCUS", "subdim": "atribucion_externa", "invertida": True, "intensidad": "media"},
    "Jamás he dicho una mentira, ni siquiera una pequeña, para salir de un apuro o evitar un problema.": {"pilar": "MENTIRA", "subdim": "deseabilidad_social", "invertida": False, "intensidad": "extrema"},
    "Nunca he sentido envidia o celos por el éxito de otra persona.": {"pilar": "MENTIRA", "subdim": "deseabilidad_social", "invertida": False, "intensidad": "extrema"},
    "Siempre estoy dispuesto a admitir mis errores de inmediato, sin importar las consecuencias.": {"pilar": "MENTIRA", "subdim": "deseabilidad_social", "invertida": False, "intensidad": "alta"},
    "Jamás he perdido la paciencia, ni siquiera cuando estoy muy cansado o estresado.": {"pilar": "MENTIRA", "subdim": "deseabilidad_social", "invertida": False, "intensidad": "extrema"},
    "Nunca me he reído o sonreído ante un chiste de mal gusto o una situación inapropiada.": {"pilar": "MENTIRA", "subdim": "deseabilidad_social", "invertida": False, "intensidad": "extrema"},
}

MOROSIDAD = "(Pregunta 100% ANÓNIMA): En los últimos 12 meses, ¿te has retrasado más de 30 días en el pago de alguna obligación (tarjeta, préstamo, cuota de estudios, recibo de servicios)?"
MOROSIDAD_OPCIONES = [
    "Sí, me he retrasado o he tenido dificultades para pagar en la fecha indicada.",
    "No, siempre he pagado todas mis obligaciones a tiempo.",
    "No he tenido ninguna obligación o deuda a mi nombre en el último año."
]

DISTRITOS_LIMA = ["Ate", "Barranco", "Breña", "Carabayllo", "Chaclacayo", "Chorrillos", "Cieneguilla", "Comas", "El Agustino", "Independencia", "Jesús María", "La Molina", "La Victoria", "Lima", "Lince", "Los Olivos", "Lurigancho", "Lurín", "Magdalena del Mar", "Miraflores", "Pachacámac", "Pucusana", "Pueblo Libre", "Puente Piedra", "Punta Hermosa", "Punta Negra", "Rímac", "San Bartolo", "San Borja", "San Isidro", "San Juan de Lurigancho", "San Juan de Miraflores", "San Luis", "San Martín de Porres", "San Miguel", "Santa Anita", "Santa María del Mar", "Santa Rosa", "Santiago de Surco", "Surquillo", "Villa El Salvador", "Villa María del Triunfo"]
NIVELES_EDUCATIVOS = ["Secundaria Incompleta", "Secundaria Completa", "Instituto Técnico Incompleto", "Instituto Técnico Completo", "Escuela de Educación Superior Incompleta", "Escuela de Educación Superior Completa", "Universidad Incompleta", "Universidad Completa", "Postgrado"]
SITUACIONES_LABORALES = ["Estudiante", "Dependiente Formal", "Dependiente Informal", "Independiente Formal", "Independiente Informal", "Desempleado", "Jubilado"]

SUBDIMENSIONES = ["orden_fisico", "disciplina", "puntualidad", "perfeccionismo", "integridad", "impulsividad", "persistencia", "auto_responsabilidad", "atribucion_externa", "deseabilidad_social"]

def numeric_to_likert(valor):
    valor = int(np.clip(np.round(valor), 1, 5))
    return LIKERT_SCALE[valor - 1]

def generar_scores_correlacionados(perfil_tipo, subtipo, rng_local):
    if perfil_tipo == "HONEST" and subtipo == "RESPONSABLE":
        base = rng_local.normal(4.3, 0.4)
        scores = {
            "orden_fisico": np.clip(base + rng_local.normal(0, 0.4), 1, 5),
            "disciplina": np.clip(base + rng_local.normal(0, 0.4), 1, 5),
            "puntualidad": np.clip(base + rng_local.normal(0, 0.5), 1, 5),
            "perfeccionismo": np.clip(base + rng_local.normal(0, 0.6), 1, 5),
            "integridad": np.clip(base + rng_local.normal(0, 0.3), 1, 5),
            "impulsividad": np.clip(6 - base + rng_local.normal(0, 0.5), 1, 5),
            "persistencia": np.clip(base + rng_local.normal(0, 0.4), 1, 5),
            "auto_responsabilidad": np.clip(base + rng_local.normal(0, 0.4), 1, 5),
            "atribucion_externa": np.clip(6 - base + rng_local.normal(0, 0.5), 1, 5),
            "deseabilidad_social": np.clip(rng_local.normal(1.8, 0.5), 1, 5),
        }

    elif perfil_tipo == "HONEST" and subtipo == "IRRESPONSABLE":
        base = rng_local.normal(2.0, 0.5)
        scores = {
            "orden_fisico": np.clip(base + rng_local.normal(0, 0.5), 1, 5),
            "disciplina": np.clip(base + rng_local.normal(0, 0.5), 1, 5),
            "puntualidad": np.clip(base + rng_local.normal(0, 0.6), 1, 5),
            "perfeccionismo": np.clip(base + rng_local.normal(0, 0.7), 1, 5),
            "integridad": np.clip(base + rng_local.normal(0, 0.5), 1, 5),
            "impulsividad": np.clip(6 - base + rng_local.normal(0, 0.5), 1, 5),
            "persistencia": np.clip(base + rng_local.normal(0, 0.5), 1, 5),
            "auto_responsabilidad": np.clip(base + rng_local.normal(0, 0.5), 1, 5),
            "atribucion_externa": np.clip(6 - base + rng_local.normal(0, 0.6), 1, 5),
            "deseabilidad_social": np.clip(rng_local.normal(2.0, 0.6), 1, 5),
        }

    elif perfil_tipo == "LIAR" and subtipo == "DESCARADO":
        scores = {
            "orden_fisico": np.clip(rng_local.normal(4.7, 0.3), 1, 5),
            "disciplina": np.clip(rng_local.normal(4.7, 0.3), 1, 5),
            "puntualidad": np.clip(rng_local.normal(4.6, 0.3), 1, 5),
            "perfeccionismo": np.clip(rng_local.normal(4.5, 0.4), 1, 5),
            "integridad": np.clip(rng_local.normal(4.8, 0.2), 1, 5),
            "impulsividad": np.clip(rng_local.normal(1.3, 0.3), 1, 5),
            "persistencia": np.clip(rng_local.normal(4.7, 0.3), 1, 5),
            "auto_responsabilidad": np.clip(rng_local.normal(4.7, 0.3), 1, 5),
            "atribucion_externa": np.clip(rng_local.normal(1.3, 0.3), 1, 5),
            "deseabilidad_social": np.clip(rng_local.normal(4.8, 0.2), 1, 5),
        }

    elif perfil_tipo == "LIAR" and subtipo == "NORMAL":
        scores = {
            "orden_fisico": np.clip(rng_local.normal(4.0, 0.5), 1, 5),
            "disciplina": np.clip(rng_local.normal(4.0, 0.5), 1, 5),
            "puntualidad": np.clip(rng_local.normal(3.9, 0.5), 1, 5),
            "perfeccionismo": np.clip(rng_local.normal(3.7, 0.6), 1, 5),
            "integridad": np.clip(rng_local.normal(4.1, 0.5), 1, 5),
            "impulsividad": np.clip(rng_local.normal(2.0, 0.5), 1, 5),
            "persistencia": np.clip(rng_local.normal(4.0, 0.5), 1, 5),
            "auto_responsabilidad": np.clip(rng_local.normal(4.0, 0.5), 1, 5),
            "atribucion_externa": np.clip(rng_local.normal(2.0, 0.5), 1, 5),
            "deseabilidad_social": np.clip(rng_local.normal(4.0, 0.5), 1, 5),
        }

    elif perfil_tipo == "LIAR" and subtipo == "SUTIL":
        scores = {
            "orden_fisico": np.clip(rng_local.normal(3.5, 0.5), 1, 5),
            "disciplina": np.clip(rng_local.normal(3.5, 0.5), 1, 5),
            "puntualidad": np.clip(rng_local.normal(3.4, 0.5), 1, 5),
            "perfeccionismo": np.clip(rng_local.normal(3.3, 0.6), 1, 5),
            "integridad": np.clip(rng_local.normal(3.6, 0.5), 1, 5),
            "impulsividad": np.clip(rng_local.normal(2.5, 0.5), 1, 5),
            "persistencia": np.clip(rng_local.normal(3.5, 0.5), 1, 5),
            "auto_responsabilidad": np.clip(rng_local.normal(3.5, 0.5), 1, 5),
            "atribucion_externa": np.clip(rng_local.normal(2.5, 0.5), 1, 5),
            "deseabilidad_social": np.clip(rng_local.normal(3.4, 0.5), 1, 5),
        }

    else:
        scores = {subdim: rng_local.uniform(1, 5) for subdim in SUBDIMENSIONES}

    return scores

def aplicar_respuesta_por_pregunta(pregunta_config, scores, perfil_tipo, subtipo, rng_local):
    subdim = pregunta_config["subdim"]
    invertida = pregunta_config["invertida"]
    intensidad = pregunta_config["intensidad"]

    score_base = scores[subdim]

    if intensidad == "extrema":
        ruido_std = 0.4
    elif intensidad == "alta":
        ruido_std = 0.6
    elif intensidad == "media":
        ruido_std = 0.8
    else:
        ruido_std = 1.0

    if perfil_tipo == "NOISE":
        valor = rng_local.uniform(1, 5)
        if invertida:
            valor = 6 - valor
    else:
        ruido = rng_local.normal(0, ruido_std)
        valor = score_base + ruido
        if invertida:
            valor = 6 - valor

    if perfil_tipo == "LIAR" and subtipo == "SUTIL" and rng_local.uniform() < 0.08:
        valor = rng_local.uniform(1, 5)

    return numeric_to_likert(valor)

def generar_respuestas(perfil_tipo, subtipo, rng_local):
    scores = generar_scores_correlacionados(perfil_tipo, subtipo, rng_local)
    respuestas = {}

    for pregunta, config in PREGUNTAS_CONFIG.items():
        respuestas[pregunta] = aplicar_respuesta_por_pregunta(config, scores, perfil_tipo, subtipo, rng_local)

    return respuestas, scores

def calcular_target(perfil_tipo, subtipo, scores, respuesta_morosidad, rng_local):
    score_orden_promedio = np.mean([scores["orden_fisico"], scores["disciplina"], scores["puntualidad"], scores["perfeccionismo"], scores["integridad"]])
    score_descuento = np.mean([6 - scores["impulsividad"], scores["persistencia"]])
    score_locus = np.mean([scores["auto_responsabilidad"], 6 - scores["atribucion_externa"]])
    score_buenos = np.mean([score_orden_promedio, score_descuento, score_locus])
    score_mentira = scores["deseabilidad_social"]

    logit = 4.47 - 1.5 * score_buenos + 0.3 * score_mentira

    if respuesta_morosidad == MOROSIDAD_OPCIONES[0]:
        logit += 0.8
    elif respuesta_morosidad == MOROSIDAD_OPCIONES[1]:
        logit -= 0.2

    if perfil_tipo == "LIAR":
        if subtipo == "DESCARADO":
            logit += 0.7
        elif subtipo == "NORMAL":
            logit += 0.5
        else:
            logit += 0.6

    if perfil_tipo == "HONEST" and subtipo == "IRRESPONSABLE":
        logit += 0.7

    logit += rng_local.normal(0, 0.6)

    prob = 1 / (1 + np.exp(-logit))
    target = "Sí" if rng_local.uniform() < prob else "No"
    return target

def asignar_morosidad(perfil_tipo, subtipo, rng_local):
    if perfil_tipo == "LIAR":
        if subtipo == "DESCARADO":
            probs = [0.05, 0.85, 0.10]
        elif subtipo == "NORMAL":
            probs = [0.15, 0.75, 0.10]
        else:
            probs = [0.25, 0.65, 0.10]
    elif perfil_tipo == "HONEST":
        if subtipo == "RESPONSABLE":
            probs = [0.08, 0.70, 0.22]
        else:
            probs = [0.60, 0.20, 0.20]
    else:
        probs = [0.33, 0.34, 0.33]
    idx = rng_local.choice([0, 1, 2], p=probs)
    return MOROSIDAD_OPCIONES[idx]

def asignar_perfil(rng_local):
    tipo = rng_local.choice(["HONEST", "LIAR", "NOISE"], p=[0.60, 0.30, 0.10])
    if tipo == "HONEST":
        subtipo = "RESPONSABLE" if rng_local.uniform() < 0.65 else "IRRESPONSABLE"
    elif tipo == "LIAR":
        u = rng_local.uniform()
        if u < 0.20:
            subtipo = "DESCARADO"
        elif u < 0.70:
            subtipo = "NORMAL"
        else:
            subtipo = "SUTIL"
    else:
        subtipo = "ALEATORIO"
    return tipo, subtipo

def simular_registro(idx, base_seed):
    rng_local = np.random.default_rng(base_seed + idx)
    perfil_tipo, subtipo = asignar_perfil(rng_local)
    respuestas, scores = generar_respuestas(perfil_tipo, subtipo, rng_local)
    morosidad = asignar_morosidad(perfil_tipo, subtipo, rng_local)
    target = calcular_target(perfil_tipo, subtipo, scores, morosidad, rng_local)

    edad = int(np.clip(rng_local.normal(28, 8), 18, 65))
    distrito = str(rng_local.choice(DISTRITOS_LIMA))
    nivel_educativo = str(rng_local.choice(NIVELES_EDUCATIVOS))
    situacion_laboral = str(rng_local.choice(SITUACIONES_LABORALES))

    registro = {
        "EDAD": edad,
        "DISTRITO": distrito,
        "NIVEL_EDUCATIVO": nivel_educativo,
        "SITUACION LABORAL": situacion_laboral
    }
    registro.update(respuestas)
    registro[MOROSIDAD] = morosidad
    registro["TARGET_MOROSIDAD"] = target

    return registro

def main():
    logger = configure_logger()
    base_dir = Path(__file__).parent
    np.random.seed(42)

    n_registros = 5000
    logger.info(f"Generando {n_registros} registros sinteticos con perfiles psicometricos multidimensionales")
    logger.info("Distribucion principal: 60% HONEST | 30% LIAR | 10% NOISE")
    logger.info("HONEST: 65% Responsables | 35% Irresponsables")
    logger.info("LIAR: 20% Descarados | 50% Normales | 30% Sutiles")
    logger.info("NOISE: 100% Aleatorio uniforme")
    logger.info("Scores internos: 10 sub-dimensiones correlacionadas por perfil")
    logger.info("Ruido por intensidad: extrema=0.4 | alta=0.6 | media=0.8 | baja=1.0")

    registros = []
    for i in range(n_registros):
        registros.append(simular_registro(i, 42))
        if (i + 1) % 1000 == 0:
            logger.info(f"  Generados: {i+1}/{n_registros}")

    df = pl.DataFrame(registros)

    targets = df["TARGET_MOROSIDAD"].value_counts()
    logger.info("Distribucion del target:")
    for row in targets.iter_rows():
        valor, conteo = row
        pct = (conteo / n_registros) * 100
        logger.info(f"  {valor}: {conteo} ({pct:.1f}%)")

    output_path = base_dir / "simulated_thin_file_data.csv"
    df.write_csv(output_path)
    logger.info(f"Dataset guardado en: {output_path}")
    logger.info(f"Shape final: {df.shape}")

if __name__ == "__main__":
    main()