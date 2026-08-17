import streamlit as st

from core.config import VERSION_APP, NOMBRE_VERSION, DB_FILE
from core.persistence import cargar_db


st.set_page_config(
    page_title=f"Qi Team {VERSION_APP}",
    page_icon="🏃‍♂️",
    layout="wide",
)

st.title("🏃‍♂️ Qi Team")
st.subheader("V4.1 — primera prueba de arquitectura")

st.success("La aplicación V4.1 está funcionando y los módulos core están conectados.")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Versión", VERSION_APP)
with col2:
    st.metric("Atletas cargados", len(cargar_db(DB_FILE)))
with col3:
    st.metric("Persistencia", "OK")

st.divider()
st.write("### Estado de la arquitectura")
st.write("**Configuración central:** conectada")
st.write("**Persistencia de atletas:** conectada")
st.write("**Planificador V4.0:** conservado sin modificaciones")

st.info(
    "Esta pantalla es una prueba controlada. No reemplaza todavía el planificador principal; "
    "nos permite validar V4.1 antes de mover funciones de la aplicación grande."
)

with st.expander("Ver atletas detectados"):
    db = cargar_db(DB_FILE)
    for nombre, datos in db.items():
        st.write(f"**{nombre}** — {datos.get('meta', 'Sin meta')} — {datos.get('nivel', 'Sin nivel')}")

st.caption(NOMBRE_VERSION)
