import json
import os
import pandas as pd
import streamlit as st

DB_FILE = "atletas_db.json"


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
            df[col] = pd.NA
        df[col] = pd.to_numeric(df[col], errors="coerce")
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
    w["tss_cambio"] = w["tss"].pct_change() * 100
    w["tss_hora"] = w.apply(lambda r: r.tss / r.horas if r.horas > 0 else 0, axis=1)
    return w


def tendencia_4_vs_4(w, col):
    if len(w) < 8:
        return None
    anterior = w.iloc[-8:-4][col].mean()
    reciente = w.tail(4)[col].mean()
    if pd.isna(anterior) or anterior == 0:
        return None
    return (reciente / anterior - 1) * 100


def diagnostico_estado(w):
    """Diagnóstico descriptivo. No sustituye la decisión del entrenador."""
    if len(w) < 4:
        return {
            "estado": "🔵 Datos insuficientes",
            "nivel": "info",
            "resumen": "Todavía no hay cuatro semanas útiles para establecer una línea reciente de comparación.",
            "carga": "Sin comparación suficiente",
            "volumen": "Sin comparación suficiente",
            "intensidad": "Sin comparación suficiente",
            "consistencia": "En construcción",
            "factores": [],
        }

    r4 = w.tail(4)
    p4 = w.iloc[-8:-4] if len(w) >= 8 else pd.DataFrame()
    r12 = w.tail(12)

    tss4 = r4.tss.mean()
    hrs4 = r4.horas.mean()
    dist4 = r4.distancia.mean()
    ses4 = r4.sesiones.mean()

    tss12 = r12.tss.mean()
    hrs12 = r12.horas.mean()
    dist12 = r12.distancia.mean()
    ses12 = r12.sesiones.mean()

    tss_t = tendencia_4_vs_4(w, "tss")
    hrs_t = tendencia_4_vs_4(w, "horas")
    dist_t = tendencia_4_vs_4(w, "distancia")

    semanas_activas = int((r4.sesiones > 0).sum())
    semanas_vacias_12 = int((r12.sesiones == 0).sum())
    ultima = w.iloc[-1]
    anterior = w.iloc[-2]

    cambio_ultima = None
    if anterior.tss > 0:
        cambio_ultima = (ultima.tss / anterior.tss - 1) * 100

    # Intensidad: se usa TSS por hora solo como indicador interno cuando existe TSS.
    intensidad4 = r4[r4.horas > 0].tss_hora.mean()
    intensidad12 = r12[r12.horas > 0].tss_hora.mean()
    intensidad_t = None
    if intensidad12 and intensidad12 > 0 and not pd.isna(intensidad4):
        intensidad_t = (intensidad4 / intensidad12 - 1) * 100

    factores = []
    riesgo = 0
    señales_descarga = 0

    if cambio_ultima is not None:
        if cambio_ultima > 30:
            riesgo += 2
            factores.append(f"La última semana aumentó {cambio_ultima:.0f}% de TSS frente a la anterior.")
        elif cambio_ultima > 15:
            riesgo += 1
            factores.append(f"La última semana aumentó {cambio_ultima:.0f}% de TSS frente a la anterior.")
        elif cambio_ultima < -30:
            señales_descarga += 2
            factores.append(f"La última semana redujo {abs(cambio_ultima):.0f}% de TSS frente a la anterior.")

    if tss_t is not None:
        if tss_t > 25:
            riesgo += 2
            factores.append(f"El promedio de TSS de las últimas 4 semanas está {tss_t:.0f}% por encima del bloque anterior.")
        elif tss_t > 10:
            riesgo += 1
            factores.append(f"El promedio de TSS reciente está {tss_t:.0f}% por encima del bloque anterior.")
        elif tss_t < -25:
            señales_descarga += 2
            factores.append(f"El promedio de TSS reciente está {abs(tss_t):.0f}% por debajo del bloque anterior.")

    if hrs_t is not None and hrs_t > 25:
        riesgo += 1
        factores.append(f"El tiempo de entrenamiento aumentó {hrs_t:.0f}% entre bloques de 4 semanas.")
    if dist_t is not None and dist_t > 25:
        riesgo += 1
        factores.append(f"La distancia aumentó {dist_t:.0f}% entre bloques de 4 semanas.")

    if intensidad_t is not None and intensidad_t > 15:
        riesgo += 1
        factores.append(f"El TSS por hora reciente está {intensidad_t:.0f}% por encima de su referencia de 12 semanas.")
    elif intensidad_t is not None and intensidad_t < -15:
        señales_descarga += 1
        factores.append(f"El TSS por hora reciente está {abs(intensidad_t):.0f}% por debajo de su referencia de 12 semanas.")

    if semanas_activas <= 1:
        señales_descarga += 2
        factores.append("Solo hay una semana activa dentro de las últimas cuatro.")
    elif semanas_vacias_12 >= 3:
        factores.append(f"Hay {semanas_vacias_12} semanas completamente vacías en las últimas 12 semanas.")

    if riesgo >= 4:
        estado = "🟠 Atención — aumento de carga"
        nivel = "warning"
        resumen = "La carga reciente muestra varias señales de aumento. Conviene revisar el contexto antes de progresar nuevamente."
    elif riesgo >= 2:
        estado = "🟡 Atención — progresión"
        nivel = "warning"
        resumen = "El atleta está progresando, pero hay señales que justifican revisar volumen, intensidad y recuperación."
    elif señales_descarga >= 3:
        estado = "🔵 Descarga / reinicio"
        nivel = "info"
        resumen = "La carga reciente es claramente menor o presenta interrupciones. Conviene interpretar si responde al plan o a una pérdida de continuidad."
    elif tss_t is not None and abs(tss_t) <= 10 and semanas_activas >= 3:
        estado = "🟢 Estable"
        nivel = "success"
        resumen = "La carga reciente se mantiene relativamente estable y la continuidad es adecuada."
    else:
        estado = "🟢 Progresión controlada"
        nivel = "success"
        resumen = "La evolución reciente muestra cambios moderados sin una señal dominante de aumento brusco."

    carga = "Estable"
    if tss_t is not None:
        if tss_t > 15:
            carga = f"En aumento ({tss_t:+.0f}% vs bloque anterior)"
        elif tss_t < -15:
            carga = f"En descenso ({tss_t:+.0f}% vs bloque anterior)"
        else:
            carga = f"Estable ({tss_t:+.0f}% vs bloque anterior)"

    volumen = "Estable"
    if hrs_t is not None:
        if hrs_t > 15:
            volumen = f"En aumento ({hrs_t:+.0f}% tiempo)"
        elif hrs_t < -15:
            volumen = f"En descenso ({hrs_t:+.0f}% tiempo)"
        else:
            volumen = f"Estable ({hrs_t:+.0f}% tiempo)"

    if intensidad_t is None:
        intensidad = "Sin referencia suficiente"
    elif intensidad_t > 15:
        intensidad = f"Más alta ({intensidad_t:+.0f}% TSS/h)"
    elif intensidad_t < -15:
        intensidad = f"Más baja ({intensidad_t:+.0f}% TSS/h)"
    else:
        intensidad = f"Moderada/estable ({intensidad_t:+.0f}% TSS/h)"

    if semanas_activas == 4:
        consistencia = "Alta — 4/4 semanas activas"
    elif semanas_activas >= 3:
        consistencia = f"Adecuada — {semanas_activas}/4 semanas activas"
    elif semanas_activas == 2:
        consistencia = "Irregular — 2/4 semanas activas"
    else:
        consistencia = "Baja — 1/4 semanas activas"

    return {
        "estado": estado,
        "nivel": nivel,
        "resumen": resumen,
        "carga": carga,
        "volumen": volumen,
        "intensidad": intensidad,
        "consistencia": consistencia,
        "factores": factores,
        "tss_t": tss_t,
        "hrs_t": hrs_t,
        "dist_t": dist_t,
        "tss4": tss4,
        "hrs4": hrs4,
        "dist4": dist4,
        "ses4": ses4,
        "tss12": tss12,
        "hrs12": hrs12,
        "dist12": dist12,
        "ses12": ses12,
        "semanas_vacias_12": semanas_vacias_12,
    }


def render_evolucion():
    st.title("📈 Qi Team — Evolución y Diagnóstico del Atleta")
    st.caption("Histórico acumulativo para contextualizar la evolución y apoyar la decisión del entrenador")

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
    diag = diagnostico_estado(w)
    actual = w.iloc[-1]

    st.markdown("### 🧭 Contexto del histórico")
    c1, c2, c3 = st.columns(3)
    c1.metric("Desde", df.fecha.min().strftime("%d/%m/%Y"))
    c2.metric("Hasta", df.fecha.max().strftime("%d/%m/%Y"))
    c3.metric("Actividades", f"{len(df):,}".replace(",", "."))

    st.markdown("### 🩺 Diagnóstico de Estado del Atleta")
    st.subheader(diag["estado"])
    st.write(diag["resumen"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Carga", diag["carga"])
    c2.metric("Volumen", diag["volumen"])
    c3.metric("Intensidad", diag["intensidad"])
    c4.metric("Consistencia", diag["consistencia"])

    if diag["factores"]:
        with st.expander("🔎 ¿Por qué Qi Team llega a este diagnóstico?", expanded=True):
            for factor in diag["factores"]:
                st.write(f"• {factor}")
    else:
        st.info("No se detectaron factores adicionales con los datos disponibles.")

    st.markdown("### 📌 Foto de la última semana")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sesiones", int(actual.sesiones))
    c2.metric("TSS", f"{actual.tss:.0f}")
    c3.metric("Tiempo", formatear_horas(actual.duracion_seg))
    c4.metric("Distancia", f"{actual.distancia:.1f}")

    st.markdown("### 📊 Curva histórica")
    opciones = ["TSS", "Horas", "Distancia", "Sesiones"]
    seleccion = st.multiselect("Variables", opciones, default=["TSS", "Horas"])
    mapa = {"TSS": "tss", "Horas": "horas", "Distancia": "distancia", "Sesiones": "sesiones"}
    if seleccion:
        chart = w.set_index("semana")[[mapa[x] for x in seleccion]].copy()
        chart.columns = seleccion
        st.line_chart(chart, use_container_width=True)

    st.markdown("### 📐 Ventanas de carga")
    u4, u12 = w.tail(4), w.tail(12)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TSS — última semana", f"{actual.tss:.0f}")
    c2.metric("TSS — promedio 4 semanas", f"{u4.tss.mean():.0f}")
    c3.metric("TSS — promedio 12 semanas", f"{u12.tss.mean():.0f}")
    c4.metric("TSS — acumulado 4 semanas", f"{u4.tss.sum():.0f}")

    st.markdown("### 📈 Tendencias")
    tss_t = tendencia_4_vs_4(w, "tss")
    hrs_t = tendencia_4_vs_4(w, "horas")
    dst_t = tendencia_4_vs_4(w, "distancia")
    c1, c2, c3 = st.columns(3)
    c1.metric("TSS — 4 vs 4 anteriores", "—" if tss_t is None else f"{tss_t:+.0f}%")
    c2.metric("Tiempo — 4 vs 4 anteriores", "—" if hrs_t is None else f"{hrs_t:+.0f}%")
    c3.metric("Distancia — 4 vs 4 anteriores", "—" if dst_t is None else f"{dst_t:+.0f}%")

    st.markdown("### 🗓️ Últimas 12 semanas")
    tabla = w.tail(12).copy()
    tabla["Semana"] = tabla.semana.dt.strftime("%d/%m/%Y")
    tabla["Tiempo"] = tabla.duracion_seg.apply(formatear_horas)
    tabla["TSS"] = tabla.tss.round(0).astype(int)
    tabla["Distancia"] = tabla.distancia.round(2)
    tabla["Sesiones"] = tabla.sesiones.astype(int)
    tabla["Cambio TSS %"] = tabla.tss_cambio.round(0)
    tabla = tabla[["Semana", "Sesiones", "TSS", "Tiempo", "Distancia", "Cambio TSS %"]]
    st.dataframe(tabla.sort_values("Semana", ascending=False), use_container_width=True, hide_index=True)

    st.markdown("### 🧠 Lectura para el entrenador")
    notas = []
    if tss_t is not None:
        if tss_t > 20:
            notas.append(f"La carga TSS reciente está {tss_t:.0f}% por encima del bloque anterior de 4 semanas.")
        elif tss_t < -20:
            notas.append(f"La carga TSS reciente está {abs(tss_t):.0f}% por debajo del bloque anterior de 4 semanas.")
        else:
            notas.append(f"La carga TSS se mantiene relativamente estable ({tss_t:+.0f}% frente al bloque anterior).")
    if hrs_t is not None:
        notas.append(f"El tiempo de entrenamiento cambió {hrs_t:+.0f}% entre los dos bloques de 4 semanas.")
    vacias = int((w.tail(12).sesiones == 0).sum())
    notas.append(f"Hay {vacias} semana(s) sin sesiones registradas en las últimas 12 semanas." if vacias else "No hay semanas completamente vacías en las últimas 12 semanas.")
    for n in notas:
        st.write(f"• {n}")
    st.caption("El diagnóstico describe patrones observables en el histórico. No sustituye la decisión del entrenador ni evalúa por sí solo recuperación, dolor, sueño u otros factores no presentes en los datos.")

    with st.expander("🔎 Ver actividades utilizadas"):
        vista = df.copy()
        vista["fecha"] = vista.fecha.dt.strftime("%Y-%m-%d")
        vista["duracion"] = vista.duracion_seg.apply(formatear_horas)
        cols = [c for c in ["fecha", "titulo", "tipo", "duracion", "distancia", "tss", "fc_media", "fuente"] if c in vista.columns]
        st.dataframe(vista[cols].sort_values("fecha", ascending=False).head(500), use_container_width=True, hide_index=True)
