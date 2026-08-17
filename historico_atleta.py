import io
import json
import os
import shutil
import zipfile
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET

import pandas as pd
import streamlit as st

DB_FILE = "atletas_db.json"
HIST_VERSION = "V4.1-HISTORICO"


def _json_safe(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def cargar_db():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        st.error(f"No se pudo leer {DB_FILE}: {exc}")
        return {}


def guardar_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2, default=_json_safe)


def backup_db():
    if not os.path.exists(DB_FILE):
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"atletas_db_backup_{stamp}.json"
    shutil.copy2(DB_FILE, path)
    return path


def inicializar_atleta(perfil):
    perfil.setdefault("historico_actividades", [])
    perfil.setdefault("historico_fuentes", [])
    perfil.setdefault("historico_archivos", [])
    perfil.setdefault("historico_desde", None)
    perfil.setdefault("historico_hasta", None)
    perfil.setdefault("historico_ultima_semana_cerrada", None)
    perfil.setdefault("historico_version", HIST_VERSION)
    return perfil


def _first(row, names, default=None):
    for name in names:
        if name in row and pd.notna(row[name]):
            return row[name]
    return default


def _to_float(value):
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        return float(str(value).replace(",", "."))
    except Exception:
        return None


def _duration_seconds(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        return float(value) * 3600 if float(value) < 30 else float(value)
    text = str(value).strip()
    try:
        parts = [float(x) for x in text.split(":")]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        return float(text) * 3600
    except Exception:
        return None


def _date_value(value):
    if value is None:
        return None
    dt = pd.to_datetime(value, errors="coerce")
    if pd.isna(dt):
        return None
    return dt.strftime("%Y-%m-%d")


def normalizar_df(df, fuente, archivo):
    if df is None or df.empty:
        return []
    registros = []
    for _, row in df.iterrows():
        data = row.to_dict()
        fecha = _date_value(_first(data, [
            "WorkoutDay", "Date", "date", "StartTime", "start_time",
            "Activity Date", "Fecha", "fecha"
        ]))
        if not fecha:
            continue
        duracion_s = _duration_seconds(_first(data, [
            "TimeTotalInHours", "Duration", "duration", "Elapsed Time",
            "Moving Time", "Time"
        ]))
        distancia = _to_float(_first(data, [
            "Distance", "distance", "DistanceInMiles", "DistanceInKilometers",
            "Distancia", "Km", "km"
        ]))
        tss = _to_float(_first(data, ["TSS", "tss", "Training Stress Score"]))
        fc = _to_float(_first(data, [
            "HeartRateAverage", "AvgHR", "Average Heart Rate", "HR Avg", "FC"
        ]))
        titulo = str(_first(data, [
            "Title", "title", "Activity Name", "Name", "Workout", "Actividad"
        ], "Actividad"))
        tipo = str(_first(data, [
            "WorkoutType", "Sport", "sport", "Activity Type", "Tipo"
        ], "Running"))
        key = "|".join([
            fecha,
            titulo.strip().lower(),
            str(round(duracion_s or 0, 1)),
            str(round(distancia or 0, 3)),
        ])
        registros.append({
            "id_unico": key,
            "fecha": fecha,
            "titulo": titulo,
            "tipo": tipo,
            "duracion_seg": duracion_s,
            "distancia": distancia,
            "tss": tss,
            "fc_media": fc,
            "fuente": fuente,
            "archivo_origen": archivo,
        })
    return registros


def parse_csv_bytes(data, fuente, archivo):
    return normalizar_df(pd.read_csv(io.BytesIO(data)), fuente, archivo)


def parse_tcx_bytes(data, fuente, archivo):
    root = ET.fromstring(data)
    ns = {"tcx": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}
    rows = []
    for activity in root.findall(".//tcx:Activity", ns):
        sport = activity.attrib.get("Sport", "Running")
        first_tp = activity.find(".//tcx:Trackpoint", ns)
        start = activity.find("tcx:Id", ns)
        fecha = start.text if start is not None else None
        if not fecha and first_tp is not None:
            tm = first_tp.find("tcx:Time", ns)
            fecha = tm.text if tm is not None else None
        if not fecha:
            continue
        duration = 0.0
        distance = 0.0
        for lap in activity.findall("tcx:Lap", ns):
            d = lap.find("tcx:TotalTimeSeconds", ns)
            dist = lap.find("tcx:DistanceMeters", ns)
            if d is not None:
                duration += float(d.text or 0)
            if dist is not None:
                distance += float(dist.text or 0) / 1000
        rows.append({
            "WorkoutDay": fecha,
            "Title": f"{sport} — {archivo}",
            "WorkoutType": sport,
            "Duration": duration,
            "Distance": distance,
        })
    return normalizar_df(pd.DataFrame(rows), fuente, archivo)


def parse_fit_bytes(data, fuente, archivo):
    try:
        from fitparse import FitFile
    except ImportError:
        raise RuntimeError(
            "Para importar FIT instala fitparse con: py -m pip install fitparse"
        )
    fit = FitFile(io.BytesIO(data))
    rows = []
    for message in fit.get_messages("session"):
        row = {field.name: field.value for field in message.fields}
        rows.append({
            "WorkoutDay": row.get("start_time"),
            "Title": row.get("sport", "Running"),
            "WorkoutType": row.get("sport", "Running"),
            "Duration": row.get("total_timer_time") or row.get("total_elapsed_time"),
            "Distance": (
                (row.get("total_distance") or 0) / 1000
                if row.get("total_distance") is not None else None
            ),
            "TSS": row.get("training_stress_score"),
            "HeartRateAverage": row.get("avg_heart_rate"),
        })
    return normalizar_df(pd.DataFrame(rows), fuente, archivo)


def parse_file(name, data):
    lower = name.lower()
    if lower.endswith(".csv"):
        fuente = "TrainingPeaks" if "training" in lower or "workout" in lower else "CSV"
        return parse_csv_bytes(data, fuente, name)
    if lower.endswith(".tcx"):
        return parse_tcx_bytes(data, "COROS/TCX", name)
    if lower.endswith(".fit"):
        return parse_fit_bytes(data, "COROS/FIT", name)
    if lower.endswith(".zip"):
        rows = []
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for info in z.infolist():
                if not info.is_dir() and info.filename.lower().endswith((".csv", ".fit", ".tcx")):
                    rows.extend(parse_file(info.filename, z.read(info.filename)))
        return rows
    raise ValueError(f"Formato no soportado: {name}")


def merge_records(existing, incoming):
    by_id = {r.get("id_unico"): r for r in existing if r.get("id_unico")}
    for r in incoming:
        key = r.get("id_unico")
        if not key:
            continue
        if key in by_id:
            old = by_id[key]
            fuentes = set(str(old.get("fuente", "")).split(" + "))
            fuentes.add(str(r.get("fuente", "")))
            old["fuente"] = " + ".join(sorted(x for x in fuentes if x))
            if old.get("tss") is None and r.get("tss") is not None:
                old["tss"] = r["tss"]
            if old.get("fc_media") is None and r.get("fc_media") is not None:
                old["fc_media"] = r["fc_media"]
        else:
            by_id[key] = r
    return sorted(by_id.values(), key=lambda x: (x.get("fecha") or "", x.get("titulo") or ""))


def historico_df(perfil):
    rows = perfil.get("historico_actividades", [])
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    return df.sort_values("fecha")


def actualizar_rango(perfil):
    df = historico_df(perfil)
    if df.empty:
        perfil["historico_desde"] = None
        perfil["historico_hasta"] = None
        perfil["historico_ultima_semana_cerrada"] = None
        return
    perfil["historico_desde"] = df["fecha"].min().strftime("%Y-%m-%d")
    perfil["historico_hasta"] = df["fecha"].max().strftime("%Y-%m-%d")
    max_fecha = df["fecha"].max().date()
    lunes = max_fecha - timedelta(days=max_fecha.weekday())
    domingo = lunes + timedelta(days=6)
    if max_fecha < domingo:
        domingo -= timedelta(days=7)
    perfil["historico_ultima_semana_cerrada"] = domingo.strftime("%Y-%m-%d")


def render_historico():
    st.set_page_config(page_title="Qi Team V4.1 — Histórico", page_icon="🏃‍♂️", layout="wide")
    st.title("🏃‍♂️ Qi Team — Histórico del Atleta")
    st.caption("V4.1 | Reconstrucción segura del histórico + actualización incremental")
    db = cargar_db()
    if not db:
        st.warning("No se encontró atletas_db.json. Primero crea o copia la base de atletas.")
        st.stop()
    atleta = st.selectbox("Atleta", list(db.keys()))
    perfil = inicializar_atleta(db[atleta])

    st.markdown("### 📥 Importar / reconstruir histórico")
    st.info(
        "Para tu caso podemos reconstruir desde 2017. Para otros atletas puedes usar una fecha distinta. "
        "El sistema agrega nuevas semanas sin borrar el histórico existente."
    )
    c1, c2 = st.columns(2)
    with c1:
        fecha_inicio = st.date_input(
            "Fecha inicial del histórico",
            value=pd.to_datetime(perfil.get("historico_desde") or "2017-01-01").date()
        )
    with c2:
        modo_importacion = st.radio(
            "Modo", ["Agregar al histórico", "Reconstruir desde archivos seleccionados"], horizontal=True
        )

    archivos = st.file_uploader(
        "Sube CSV de TrainingPeaks, FIT/TCX de COROS o ZIP con varios archivos",
        type=["csv", "fit", "tcx", "zip"], accept_multiple_files=True, key=f"hist_files_{atleta}"
    )

    if archivos:
        if st.button("🔎 Analizar archivos", key=f"analyze_{atleta}"):
            nuevos, errores = [], []
            for archivo in archivos:
                try:
                    nuevos.extend(parse_file(archivo.name, archivo.getvalue()))
                except Exception as exc:
                    errores.append(f"{archivo.name}: {exc}")
            st.session_state["hist_preview"] = nuevos
            st.session_state["hist_errors"] = errores

        nuevos = st.session_state.get("hist_preview", [])
        errores = st.session_state.get("hist_errors", [])
        for error in errores:
            st.error(error)

        if nuevos:
            preview = pd.DataFrame(nuevos)
            preview["fecha"] = pd.to_datetime(preview["fecha"], errors="coerce")
            preview = preview[preview["fecha"].dt.date >= fecha_inicio]
            st.success(f"Se detectaron {len(preview)} actividades válidas desde {fecha_inicio.strftime('%d/%m/%Y')}.")
            st.dataframe(preview.head(100), use_container_width=True, hide_index=True)
            if st.button("💾 Confirmar importación", key=f"confirm_{atleta}"):
                backup = backup_db()
                existentes = [] if modo_importacion.startswith("Reconstruir") else perfil.get("historico_actividades", [])
                filtrados = [r for r in nuevos if r.get("fecha") and r["fecha"] >= fecha_inicio.strftime("%Y-%m-%d")]
                perfil["historico_actividades"] = merge_records(existentes, filtrados)
                perfil["historico_archivos"] = sorted(set(perfil.get("historico_archivos", []) + [a.name for a in archivos]))
                perfil["historico_fuentes"] = sorted(set(perfil.get("historico_fuentes", []) + [r.get("fuente") for r in filtrados if r.get("fuente")]))
                perfil["historico_version"] = HIST_VERSION
                actualizar_rango(perfil)
                db[atleta] = perfil
                guardar_db(db)
                st.session_state.pop("hist_preview", None)
                st.session_state.pop("hist_errors", None)
                st.success(f"Histórico actualizado. Backup creado: {backup or 'no había base previa'}")
                st.rerun()

    st.markdown("---")
    st.markdown("### 🔄 Resetear / reconstruir")
    st.warning("Resetear no elimina al atleta. Crea un backup de atletas_db.json y reinicia solamente el histórico de actividades.")
    confirm = st.checkbox("Confirmo que quiero reconstruir el histórico de este atleta", key=f"confirm_reset_{atleta}")
    if confirm and st.button("🔄 Resetear histórico de este atleta", key=f"reset_hist_{atleta}"):
        backup = backup_db()
        perfil["historico_actividades"] = []
        perfil["historico_fuentes"] = []
        perfil["historico_archivos"] = []
        perfil["historico_desde"] = None
        perfil["historico_hasta"] = None
        perfil["historico_ultima_semana_cerrada"] = None
        perfil["historico_version"] = HIST_VERSION
        db[atleta] = perfil
        guardar_db(db)
        st.success(f"Histórico reiniciado. Backup: {backup or 'no disponible'}")
        st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Curva histórica")
    df = historico_df(perfil)
    if df.empty:
        st.info("Todavía no hay actividades históricas cargadas.")
        return
    df = df[df["fecha"].dt.date >= fecha_inicio]
    df["semana"] = df["fecha"].dt.to_period("W-SUN").apply(lambda p: p.start_time)
    weekly = df.groupby("semana", as_index=False).agg(
        actividades=("id_unico", "count"), tss=("tss", "sum"),
        distancia=("distancia", "sum"), segundos=("duracion_seg", "sum")
    )
    weekly["horas"] = weekly["segundos"] / 3600
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Actividades", f"{len(df):,}")
    c2.metric("Desde", df["fecha"].min().strftime("%d/%m/%Y"))
    c3.metric("Hasta", df["fecha"].max().strftime("%d/%m/%Y"))
    c4.metric("Semanas", f"{len(weekly):,}")
    st.line_chart(weekly.set_index("semana")[["tss"]], height=260)
    st.line_chart(weekly.set_index("semana")[["horas"]], height=260)
    st.line_chart(weekly.set_index("semana")[["distancia"]], height=260)
    st.markdown("### 🗓️ Última semana cerrada detectada")
    st.success(perfil.get("historico_ultima_semana_cerrada") or "No disponible")
    st.markdown("### 📚 Fuentes integradas")
    st.write(", ".join(perfil.get("historico_fuentes", [])) or "Ninguna")
    st.markdown("### 📋 Últimas actividades")
    cols = [c for c in ["fecha", "titulo", "tipo", "duracion_seg", "distancia", "tss", "fc_media", "fuente"] if c in df.columns]
    st.dataframe(df.sort_values("fecha", ascending=False)[cols].head(100), use_container_width=True, hide_index=True)


if __name__ == "__main__":
    render_historico()
