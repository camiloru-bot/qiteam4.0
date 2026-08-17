import json
import os
import pandas as pd
import streamlit as st

DB_FILE = "atletas_db.json"
VERSION_EVOLUCION = "Evolución v1.3 — Ventanas visibles"

VENTANAS = {
    "1 semana": 1,
    "1 mes": 4,
    "3 meses": 12,
    "6 meses": 24,
    "12 meses": 52,
    "Histórico completo": None,
}


def cargar_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def formatear_horas(segundos):
    if segundos is None or pd.isna(segundos):
        return "—"
    total = max(0, int(round(float(segundos))))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}h {m:02d}m {s:02d}s"


def historico_df(perfil):
    rows = perfil.get("historico_actividades", [])
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows).copy()
    df["fecha"] = pd.to_datetime(df.get("fecha"), errors="coerce")
    for col in ["duracion_seg", "distancia", "tss", "fc_media"]:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df.dropna(subset=["fecha"]).sort_values("fecha")


def construir_semanal(df):
    x = df.copy()
    x["semana"] = x["fecha"] - pd.to_timedelta(x["fecha"].dt.weekday, unit="D")
    w = x.groupby("semana", as_index=False).agg(
        sesiones=("fecha", "count"),
        tss=("tss", "sum"),
        duracion_seg=("duracion_seg", "sum"),
        distancia=("distancia", "sum"),
    )
    if w.empty:
        return w
    calendario = pd.DataFrame({"semana": pd.date_range(w.semana.min(), w.semana.max(), freq="7D")})
    w = calendario.merge(w, on="semana", how="left")
    for c in ["sesiones", "tss", "duracion_seg", "distancia"]:
        w[c] = w[c].fillna(0)
    w["horas"] = w["duracion_seg"] / 3600
    w["tss_hora"] = w.apply(lambda r: r.tss / r.horas if r.horas > 0 else 0, axis=1)
    return w


def pct(actual, referencia):
    if referencia is None or pd.isna(referencia) or referencia == 0:
        return None
    return (actual / referencia - 1) * 100


def comparar_bloques(w, semanas):
    if semanas is None or len(w) < semanas * 2:
        return None
    reciente = w.tail(semanas)
    anterior = w.iloc[-semanas * 2:-semanas]
    return {
        "tss": pct(reciente.tss.mean(), anterior.tss.mean()),
        "horas": pct(reciente.horas.mean(), anterior.horas.mean()),
        "distancia": pct(reciente.distancia.mean(), anterior.distancia.mean()),
        "sesiones": pct(reciente.sesiones.mean(), anterior.sesiones.mean()),
        "tss_hora": pct(reciente.tss_hora.mean(), anterior.tss_hora.mean()),
    }


def diagnostico(w, semanas):
    if len(w) < 4:
        return "🔵 Datos insuficientes", "Se necesitan al menos cuatro semanas para interpretar una tendencia reciente.", []
    n = 4 if semanas is None else min(semanas, len(w))
    reciente = w.tail(n)
    anterior_n = min(n, len(w) - n)
    comp = comparar_bloques(w, n) if anterior_n >= n else None
    factores = []
    riesgo = 0
    if comp:
        if comp["tss"] is not None and comp["tss"] > 25:
            riesgo += 2; factores.append(f"TSS: +{comp['tss']:.0f}% frente al bloque anterior.")
        elif comp["tss"] is not None and comp["tss"] > 10:
            riesgo += 1; factores.append(f"TSS: +{comp['tss']:.0f}% frente al bloque anterior.")
        elif comp["tss"] is not None and comp["tss"] < -25:
            factores.append(f"TSS: {comp['tss']:.0f}% frente al bloque anterior.")
        if comp["horas"] is not None and comp["horas"] > 25:
            riesgo += 1; factores.append(f"Tiempo: +{comp['horas']:.0f}% frente al bloque anterior.")
        if comp["distancia"] is not None and comp["distancia"] > 25:
            riesgo += 1; factores.append(f"Distancia: +{comp['distancia']:.0f}% frente al bloque anterior.")
        if comp["tss_hora"] is not None and comp["tss_hora"] > 15:
            riesgo += 1; factores.append(f"TSS/hora: +{comp['tss_hora']:.0f}% frente al bloque anterior.")
    activas = int((reciente.sesiones > 0).sum())
    if activas < max(1, n * 0.5):
        factores.append(f"Continuidad baja: {activas} de {n} semanas activas.")
    if riesgo >= 4:
        return "🟠 Atención — aumento de carga", "La ventana seleccionada presenta varias señales de aumento. Revisar contexto antes de progresar.", factores
    if riesgo >= 2:
        return "🟡 Atención — progresión", "La carga está creciendo y merece revisión de volumen, intensidad y recuperación.", factores
    if activas < max(1, n * 0.5):
        return "🔵 Descarga / reinicio", "La continuidad de la ventana es baja. Hay que distinguir descarga planificada de interrupción.", factores
    if comp and comp["tss"] is not None and abs(comp["tss"]) <= 10:
        return "🟢 Estable", "La carga se mantiene relativamente estable dentro de la ventana seleccionada.", factores
    return "🟢 Progresión controlada", "Se observan cambios moderados sin una señal dominante de aumento brusco.", factores


def render_evolucion():
    st.title("📈 Qi Team — Evolución y Diagnóstico del Atleta")
    st.caption(f"{VERSION_EVOLUCION} · Elige una ventana y todos los indicadores se recalculan sobre ese período.")

    db = cargar_db()
    if not db:
        st.warning("No se encontró atletas_db.json.")
        st.stop()

    atleta = st.selectbox("Atleta", list(db.keys()), key="evolucion_atleta")
    df = historico_df(db[atleta])
    if df.empty:
        st.info("Este atleta todavía no tiene actividades en el histórico.")
        st.stop()

    w = construir_semanal(df)

    st.markdown("## 🗓️ Ventana de evolución")
    st.caption("Selecciona cuánto historial quieres analizar:")
    with st.container(border=True):
        ventana = st.radio(
            "Período de análisis",
            list(VENTANAS.keys()),
            horizontal=True,
            key="ventana_evolucion_v13",
            label_visibility="visible",
        )
        semanas = VENTANAS[ventana]
        st.success(f"Ventana seleccionada: **{ventana}**")

    vista = w if semanas is None else w.tail(min(semanas, len(w)))
    actual = w.iloc[-1]

    st.markdown(f"## 🩺 Diagnóstico de estado — {ventana}")
    estado, resumen, factores = diagnostico(w, semanas)
    st.subheader(estado)
    st.write(resumen)
    if factores:
        with st.expander("🔎 ¿Por qué Qi Team llega a este diagnóstico?", expanded=True):
            for f in factores:
                st.write(f"• {f}")

    st.markdown("### 📊 Resumen de la ventana")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sesiones", int(vista.sesiones.sum()))
    c2.metric("TSS", f"{vista.tss.sum():.0f}")
    c3.metric("Tiempo", formatear_horas(vista.duracion_seg.sum()))
    c4.metric("Distancia", f"{vista.distancia.sum():.1f}")

    st.markdown("### 📈 Curva de evolución")
    opciones = ["TSS", "Horas", "Distancia", "Sesiones"]
    seleccion = st.multiselect("Variables", opciones, default=["TSS", "Horas"])
    mapa = {"TSS": "tss", "Horas": "horas", "Distancia": "distancia", "Sesiones": "sesiones"}
    if seleccion:
        chart = vista.set_index("semana")[[mapa[x] for x in seleccion]].copy()
        chart.columns = seleccion
        st.line_chart(chart, use_container_width=True)

    st.markdown("### 📐 Comparación con el bloque anterior")
    comp = comparar_bloques(w, semanas) if semanas is not None else None
    if comp:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("TSS", "—" if comp["tss"] is None else f"{comp['tss']:+.0f}%")
        c2.metric("Tiempo", "—" if comp["horas"] is None else f"{comp['horas']:+.0f}%")
        c3.metric("Distancia", "—" if comp["distancia"] is None else f"{comp['distancia']:+.0f}%")
        c4.metric("TSS/hora", "—" if comp["tss_hora"] is None else f"{comp['tss_hora']:+.0f}%")
    else:
        st.info("No hay un bloque anterior de igual duración para comparar esta ventana.")

    st.markdown("### 📌 Última semana registrada")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sesiones", int(actual.sesiones))
    c2.metric("TSS", f"{actual.tss:.0f}")
    c3.metric("Tiempo", formatear_horas(actual.duracion_seg))
    c4.metric("Distancia", f"{actual.distancia:.1f}")

    st.markdown("### 🧠 Lectura para el entrenador")
    st.write(f"La ventana activa es **{ventana}**. Úsala para contextualizar la semana reciente antes de construir la siguiente semana de entrenamiento.")
    if semanas is None:
        st.write("El modo Histórico completo utiliza todas las semanas disponibles en la base del atleta.")
    elif len(w) >= semanas * 2:
        st.write("La comparación mostrada enfrenta la ventana seleccionada contra el bloque inmediatamente anterior de igual duración.")
    else:
        st.write("Todavía no existe suficiente histórico para una comparación completa de bloques.")

    st.markdown("### 🗓️ Detalle semanal")
    tabla = vista.copy()
    tabla["Semana"] = tabla.semana.dt.strftime("%d/%m/%Y")
    tabla["Tiempo"] = tabla.duracion_seg.apply(formatear_horas)
    tabla["TSS"] = tabla.tss.round(0).astype(int)
    tabla["Distancia"] = tabla.distancia.round(2)
    tabla["Sesiones"] = tabla.sesiones.astype(int)
    tabla = tabla[["Semana", "Sesiones", "TSS", "Tiempo", "Distancia"]]
    st.dataframe(tabla.sort_values("Semana", ascending=False), use_container_width=True, hide_index=True)

    with st.expander("🔎 Ver actividades utilizadas"):
        vista_act = df.copy()
        vista_act["fecha"] = vista_act.fecha.dt.strftime("%Y-%m-%d")
        vista_act["duracion"] = vista_act.duracion_seg.apply(formatear_horas)
        cols = [c for c in ["fecha", "titulo", "tipo", "duracion", "distancia", "tss", "fc_media", "fuente"] if c in vista_act.columns]
        st.dataframe(vista_act[cols].sort_values("fecha", ascending=False).head(500), use_container_width=True, hide_index=True)

    st.caption(f"Qi Team V4.1 · {VERSION_EVOLUCION} · Diagnóstico descriptivo para apoyo al entrenador.")
