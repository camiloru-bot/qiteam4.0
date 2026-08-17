import json
import os
from datetime import datetime

import pandas as pd
import streamlit as st

DB_FILE = "atletas_db.json"


def cargar_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def historico_df(perfil):
    rows = perfil.get("historico_actividades", [])
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["fecha"] = pd.to_datetime(df.get("fecha"), errors="coerce")
    for col in ["duracion_seg", "distancia", "tss", "fc_media"]:
        if col not in df.columns:
            df[col] = pd.NA
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["fecha"]).sort_values("fecha")
    return df


def semana_lunes(fecha):
    return fecha - pd.Timedelta(days=fecha.weekday())


def construir_semanal(df):
    if df.empty:
        return pd.DataFrame()
    x = df.copy()
    x["semana"] = x["fecha"].apply(semana_lunes)
    semanal = x.groupby("semana", as_index=False).agg(
        sesiones=("fecha", "count"),
        tss=("tss", "sum"),
        duracion_seg=("duracion_seg", "sum"),
        distancia=("distancia", "sum"),
        fc_media=("fc_media", "mean"),
    )
    semanal = semanal.sort_values("semana")
    semanal["horas"] = semanal["duracion_seg"] / 3600
    semanal["tss_4s"] = semanal["tss"].rolling(4, min_periods=1).mean()
    semanal["tss_12s"] = semanal["tss"].rolling(12, min_periods=1).mean()
    semanal["horas_4s"] = semanal["horas"].rolling(4, min_periods=1).mean()
    semanal["distancia_4s"] = semanal["distancia"].rolling(4, min_periods=1).mean()
    return semanal


def pct_change(actual, previo):
    if pd.isna(previo) or previo == 0 or pd.isna(actual):
        return None
    return (actual / previo - 1) * 100


def estado_carga(semanal):
    if semanal.empty:
        return "⚪ Sin datos", "No hay suficiente histórico para valorar la tendencia."
    if len(semanal) < 2:
        return "🔵 Primer registro", "Se necesita al menos otra semana para comparar la tendencia."
    actual = semanal.iloc[-1]
    previo = semanal.iloc[-2]
    cambio = pct_change(actual["tss"], previo["tss"])
    if cambio is None:
        return "⚪ Sin TSS comparable", "La semana actual no tiene TSS suficiente para comparar."
    if cambio > 30:
        return "🟠 Aumento importante", f"El TSS semanal subió {cambio:.0f}% frente a la semana anterior. Conviene revisar el contexto de volumen e intensidad."
    if cambio < -30:
        return "🔵 Descarga / menor carga", f"El TSS semanal bajó {abs(cambio):.0f}% frente a la semana anterior. Revisar si corresponde a una semana planificada de descarga."
    return "🟢 Tendencia estable", f"El TSS semanal cambió {cambio:+.0f}% frente a la semana anterior, dentro de un rango moderado."


def formatear_horas(segundos):
    if pd.isna(segundos):
        return "—"
    total = int(round(float(segundos)))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}h {m:02d}m {s:02d}s"


def render_evolucion():
    st.title("📈 Qi Team — Evolución y Estado del Atleta")
    st.caption("Análisis histórico acumulativo para apoyar la decisión del entrenador")

    db = cargar_db()
    if not db:
        st.warning("No se encontró atletas_db.json.")
        st.stop()

    atleta = st.selectbox("Atleta", list(db.keys()), key="evolucion_atleta")
    perfil = db[atleta]
    df = historico_df(perfil)

    if df.empty:
        st.info("Este atleta todavía no tiene actividades en el histórico.")
        st.stop()

    semanal = construir_semanal(df)
    estado, explicacion = estado_carga(semanal)

    st.markdown("### 🚦 Estado actual de carga")
    st.subheader(estado)
    st.write(explicacion)

    actual = semanal.iloc[-1]
    semanas_4 = semanal.tail(4)
    semanas_12 = semanal.tail(12)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sesiones — última semana", int(actual["sesiones"]))
    c2.metric("TSS — última semana", f"{actual['tss']:.0f}" if not pd.isna(actual["tss"]) else "—")
    c3.metric("Tiempo — última semana", formatear_horas(actual["duracion_seg"]))
    c4.metric("Distancia — última semana", f"{actual['distancia']:.1f}" if not pd.isna(actual["distancia"]) else "—")

    st.markdown("### 📊 Curva histórica")
    metricas = st.multiselect(
        "Selecciona las variables",
        ["TSS", "Horas", "Distancia", "Sesiones"],
        default=["TSS", "Horas"],
    )
    chart = semanal.set_index("semana")[[
        {"TSS": "tss", "Horas": "horas", "Distancia": "distancia", "Sesiones": "sesiones"}[m]
        for m in metricas
    ]]
    chart.columns = metricas
    st.line_chart(chart, use_container_width=True)

    st.markdown("### 📐 Comparación de carga")
    tss_4 = semanas_4["tss"].sum()
    tss_12_avg = semanas_12["tss"].mean()
    horas_4 = semanas_4["horas"].sum()
    horas_12_avg = semanas_12["horas"].mean()
    c1, c2, c3 = st.columns(3)
    c1.metric("TSS — última semana", f"{actual['tss']:.0f}")
    c2.metric("TSS — promedio 12 semanas", f"{tss_12_avg:.0f}" if not pd.isna(tss_12_avg) else "—")
    c3.metric("TSS — acumulado 4 semanas", f"{tss_4:.0f}")

    st.markdown("### 🗓️ Últimas semanas")
    tabla = semanal.tail(12).copy()
    tabla["Semana"] = tabla["semana"].dt.strftime("%d/%m/%Y")
    tabla["Tiempo"] = tabla["duracion_seg"].apply(formatear_horas)
    tabla["TSS"] = tabla["tss"].round(0)
    tabla["Distancia"] = tabla["distancia"].round(2)
    tabla["Cambio TSS"] = tabla["tss"].pct_change().mul(100).round(0)
    tabla = tabla[["Semana", "sesiones", "TSS", "Tiempo", "Distancia", "Cambio TSS"]]
    tabla.columns = ["Semana", "Sesiones", "TSS", "Tiempo", "Distancia", "Cambio TSS %"]
    st.dataframe(tabla.sort_values("Semana", ascending=False), use_container_width=True, hide_index=True)

    st.markdown("### 🧠 Lectura para el entrenador")
    st.info(
        "Este módulo describe tendencias observables del histórico. No prescribe automáticamente una sesión ni sustituye la decisión del entrenador. "
        "La interpretación debe considerar fase del ciclo, objetivo, recuperación, intensidad y contexto del atleta."
    )

    if len(semanal) >= 4:
        ultima4 = semanal.tail(4)["tss"].mean()
        prev4 = semanal.iloc[-8:-4]["tss"].mean() if len(semanal) >= 8 else None
        if prev4 and prev4 > 0:
            tendencia = (ultima4 / prev4 - 1) * 100
            st.write(f"**Tendencia de TSS:** {tendencia:+.0f}% comparando las últimas 4 semanas con las 4 anteriores disponibles.")
        else:
            st.write("**Tendencia de TSS:** todavía no hay ocho semanas completas para una comparación robusta.")

    with st.expander("🔎 Ver actividades utilizadas"):
        vista = df.copy()
        vista["fecha"] = vista["fecha"].dt.strftime("%Y-%m-%d")
        vista["duracion"] = vista["duracion_seg"].apply(formatear_horas)
        columnas = [c for c in ["fecha", "titulo", "tipo", "duracion", "distancia", "tss", "fc_media", "fuente"] if c in vista.columns]
        st.dataframe(vista[columnas].sort_values("fecha", ascending=False).head(300), use_container_width=True, hide_index=True)
