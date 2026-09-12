import streamlit as st
from datetime import datetime

from core.config import VERSION_APP, NOMBRE_VERSION, DB_FILE
from core.persistence import cargar_db
from evolucion_diagnostico import diagnostico, historico_df, construir_semanal, VENTANAS
from planning.decision import construir_semana_desde_diagnostico


st.set_page_config(
    page_title=f"Qi Team {VERSION_APP}",
    page_icon="🏃‍♂️",
    layout="wide",
)

st.title("🏃‍♂️ Qi Team")
st.caption(NOMBRE_VERSION)

db = cargar_db(DB_FILE)
if not db:
    st.warning("No hay atletas disponibles.")
    st.stop()

atleta = st.sidebar.selectbox("Atleta", list(db.keys()), key="v41_atleta")
perfil = db[atleta]

tab1, tab2, tab3 = st.tabs([
    "📊 Evolución",
    "🧠 Diagnóstico",
    "🗓️ Planificación",
])

with tab1:
    st.subheader("Evolución del atleta")
    df = historico_df(perfil)
    if df.empty:
        st.info("Este atleta todavía no tiene actividades en el histórico.")
    else:
        w = construir_semanal(df)
        ventana = st.radio(
            "Período de análisis",
            list(VENTANAS.keys()),
            horizontal=True,
            key="v41_ventana",
        )
        semanas = VENTANAS[ventana]
        vista = w if semanas is None else w.tail(min(semanas, len(w)))
        st.line_chart(vista.set_index("semana")[["tss", "horas", "distancia"]])
        st.dataframe(
            vista[["semana", "sesiones", "tss", "horas", "distancia"]]
            .sort_values("semana", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

with tab2:
    st.subheader("Diagnóstico")
    df = historico_df(perfil)
    if df.empty:
        estado = "🔵 Datos insuficientes"
        resumen = "No hay suficiente histórico para construir una tendencia."
        factores = []
    else:
        w = construir_semanal(df)
        ventana = st.radio(
            "Ventana diagnóstica",
            list(VENTANAS.keys()),
            horizontal=True,
            key="v41_diag_ventana",
        )
        semanas = VENTANAS[ventana]
        estado, resumen, factores = diagnostico(w, semanas)

    st.markdown(f"### {estado}")
    st.write(resumen)
    if factores:
        for factor in factores:
            st.write(f"• {factor}")

with tab3:
    st.subheader("Propuesta de planificación")
    st.caption("QI propone; el entrenador decide y puede revisar la propuesta antes de aplicarla.")

    nivel = perfil.get("nivel", "Medio")
    meta = perfil.get("meta", "10K")
    fecha_objetivo = perfil.get("fecha_objetivo")

    if isinstance(fecha_objetivo, str):
        try:
            fecha_objetivo = datetime.strptime(fecha_objetivo, "%Y-%m-%d")
        except ValueError:
            fecha_objetivo = None

    if fecha_objetivo:
        semanas_faltantes = max(
            1,
            (fecha_objetivo.date() - datetime.now().date()).days // 7,
        )
    else:
        semanas_faltantes = 8

    df = historico_df(perfil)
    if df.empty:
        estado_plan = "🔵 Datos insuficientes"
    else:
        w = construir_semanal(df)
        estado_plan, _, _ = diagnostico(w, min(4, len(w)))

    st.write(f"**Atleta:** {atleta}")
    st.write(f"**Nivel:** {nivel} · **Meta:** {meta}")
    st.write(f"**Semanas estimadas a objetivo:** {semanas_faltantes}")
    st.write(f"**Estado utilizado:** {estado_plan}")

    if st.button("Generar propuesta de semana", type="primary"):
        decision, semana = construir_semana_desde_diagnostico(
            estado_plan,
            nivel,
            meta,
            semanas_faltantes,
        )

        st.markdown("### Decisión del motor")
        st.json(decision)

        st.markdown("### Semana propuesta")
        if not semana:
            st.warning("El motor no encontró sesiones para alguno de los espacios estructurales.")
        else:
            for sesion in semana:
                st.write(
                    f"**{sesion.get('Día', 'Sin día')}** · "
                    f"{sesion.get('Título', sesion.get('ID', 'Sesión'))}"
                )

st.sidebar.divider()
st.sidebar.caption(f"Qi Team {VERSION_APP} · Propuesta experimental V4.1")
