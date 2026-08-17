import streamlit as st

from historico_atleta import render_historico
from evolucion_diagnostico import render_evolucion

st.set_page_config(page_title="Qi Team V4.1", page_icon="🏃‍♂️", layout="wide")

st.sidebar.title("🏃‍♂️ Qi Team V4.1")
modulo = st.sidebar.radio(
    "Módulo",
    ["📥 Histórico del Atleta", "📈 Evolución y Estado"],
)

if modulo == "📥 Histórico del Atleta":
    render_historico()
else:
    render_evolucion()
