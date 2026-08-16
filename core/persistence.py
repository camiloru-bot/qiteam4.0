"""Persistencia de atletas para Qi Team V4.1.

Extraído de la lógica existente en `planificador` sin cambiar su contrato.
La aplicación principal seguirá usando su implementación actual hasta que
la integración sea validada.
"""

import json
import os
from datetime import datetime


def convertir_fechas_para_json(db):
    """Convierte fechas objetivo a texto ISO antes de serializar la DB."""
    db_serializable = {}
    for nombre, datos in db.items():
        datos_copia = datos.copy()
        if isinstance(datos_copia.get("fecha_objetivo"), datetime):
            datos_copia["fecha_objetivo"] = datos_copia["fecha_objetivo"].strftime("%Y-%m-%d")
        db_serializable[nombre] = datos_copia
    return db_serializable


def cargar_db(db_file="atletas_db.json"):
    """Carga atletas existentes y garantiza las claves estructurales actuales."""
    defaults = {
        "Deportista Principal": {
            "genero": "Masculino",
            "nivel": "Medio",
            "meta": "10K",
            "fecha_objetivo": datetime(2026, 10, 15),
            "fase_ciclo": "N/A",
            "csv_data_historico": None,
            "archivos_cargados": [],
            "decisiones_entrenador": [],
            "decisiones_sesiones": {},
        },
        "Atleta Femenina Ejemplo": {
            "genero": "Femenino",
            "nivel": "Principiante",
            "meta": "5K",
            "fecha_objetivo": datetime(2026, 9, 20),
            "fase_ciclo": "Fase Folicular / Normal",
            "csv_data_historico": None,
            "archivos_cargados": [],
            "decisiones_entrenador": [],
            "decisiones_sesiones": {},
        },
    }

    if os.path.exists(db_file):
        try:
            with open(db_file, "r", encoding="utf-8") as f:
                db_cruda = json.load(f)

            for nombre, datos in db_cruda.items():
                if isinstance(datos.get("fecha_objetivo"), str):
                    datos["fecha_objetivo"] = datetime.strptime(
                        datos["fecha_objetivo"], "%Y-%m-%d"
                    )
                datos.setdefault("csv_data_historico", None)
                datos.setdefault("archivos_cargados", [])
                datos.setdefault("decisiones_entrenador", [])
                datos.setdefault("decisiones_sesiones", {})
                defaults[nombre] = datos
        except Exception:
            # El comportamiento de UI/errores se mantiene en el planificador
            # durante esta fase de extracción.
            pass

    return defaults


def guardar_db(db, db_file="atletas_db.json"):
    """Guarda la base respetando el formato JSON actual de Qi Team."""
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(
            convertir_fechas_para_json(db),
            f,
            ensure_ascii=False,
            indent=4,
        )
