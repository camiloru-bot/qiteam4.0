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
        sesiones=("fecha", "count"), tss=("tss", "sum"),
        duracion_seg=("duracion_seg", "sum"), distancia=("distancia", "sum")
    )
    if w.empty:
        return w
    calendario = pd.DataFrame({"semana": pd.date_range(w.semana.min(), w.semana.max(), freq="7D")})
    w = calendario.merge(w, on="semana", how="left")
    for c in ["sesiones", "tss", "duracion_seg", "distancia"]:
        w[c] = w[c].fillna(0)
    w["horas"] = w["duracion_seg"] / 3600
    w["tss_cambio"] = w["tss"].pct_change() * 100
    return w


def tendencia_4_vs_4(w, col):
    if len(w) < 8:
        return None
    anterior = w.iloc[-8:-4][col].mean()
    reciente = w.tail(4)[col].mean()
    if pd.isna(anterior) or anterior == 0:
        return None
    return (reciente / anterior - 1) * 100


def estado_carga(w):
    if len(w) < 2:
        return "🔵 Primer registro", "Se necesita más de una semana para comparar la tendencia."
    a, p = w.iloc[-1], w.iloc[-2]
    if a.tss == 0 and p.tss == 0:
        return "⚪ Sin TSS", "No hay TSS comparable en las semanas recientes."
    if p.tss == 0 and a.tss > 0:
        return "🟢 Reinicio de carga", "Hay carga registrada después de una semana sin TSS; revisar el contexto antes de progresar."
    cambio = (a.tss / p.tss - 1) * 100
    if cambio > 30:
        return "🟠 Aumento importante", f"El TSS subió {cambio:.0f}% frente a la semana anterior. Revisar volumen, intensidad y recuperación."
    if cambio < -30:
        return "🔵 Descarga / menor carga", f"El TSS bajó {abs(cambio):.0f}% frente a la semana anterior. Revisar si corresponde al plan."
    return "🟢 Tendencia estable", f"El TSS cambió {cambio:+.0f}% frente a la semana anterior."


def render_evolucion():
    st.title("📈 Qi Team — Evolución y Estado del Atleta")
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
    estado, explicacion = estado_carga(w)
    actual = w.iloc[-1]

    st.markdown("### 🧭 Contexto del histórico")
    c1, c2, c3 = st.columns(3)
    c1.metric("Desde", df.fecha.min().strftime("%d/%m/%Y"))
    c2.metric("Hasta", df.fecha.max().strftime("%d/%m/%Y"))
    c3.metric("Actividades", f"{len(df):,}".replace(",", "."))

    st.markdown("### 🚦 Estado actual de carga")
    st.subheader(estado)
    st.write(explicacion)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sesiones — última semana", int(actual.sesiones))
    c2.metric("TSS — última semana", f"{actual.tss:.0f}")
    c3.metric("Tiempo — última semana", formatear_horas(actual.duracion_seg))
    c4.metric("Distancia — última semana", f"{actual.distancia:.1f}")

    st.markdown("### 📊 Curva histórica")
    opciones = ["TSS", "Horas", "Distancia", "Sesiones"]
    seleccion = st.multiselect("Variables", opciones, default=["TSS", "Horas"])
    mapa = {"TSS":"tss", "Horas":"horas", "Distancia":"distancia", "Sesiones":"sesiones"}
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
    st.caption("Esta lectura describe patrones observables. La decisión de entrenamiento debe considerar objetivo, fase, recuperación, intensidad y contexto individual.")

    with st.expander("🔎 Ver actividades utilizadas"):
        vista = df.copy()
        vista["fecha"] = vista.fecha.dt.strftime("%Y-%m-%d")
        vista["duracion"] = vista.duracion_seg.apply(formatear_horas)
        cols = [c for c in ["fecha", "titulo", "tipo", "duracion", "distancia", "tss", "fc_media", "fuente"] if c in vista.columns]
        st.dataframe(vista[cols].sort_values("fecha", ascending=False).head(500), use_container_width=True, hide_index=True)
