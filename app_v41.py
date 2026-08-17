import streamlit as st

from historico_atleta import render_historico
from evolucion_diagnostico import render_evolucion

VERSION_QI = "V4.1"
VERSION_EVOLUCION = "Evolución v1.2 — Ventanas + Diagnóstico"

st.set_page_config(page_title=f"Qi Team {VERSION_QI}", page_icon="🏃‍♂️", layout="wide")

st.sidebar.title(f"🏃‍♂️ Qi Team {VERSION_QI}")
st.sidebar.caption(f"🔖 {VERSION_EVOLUCION}")
st.sidebar.divider()

modulo = st.sidebar.radio(
    "Módulo",
    ["📥 Histórico del Atleta", "📈 Evolución y Estado"],
)

if modulo == "📥 Histórico del Atleta":
    render_historico()
else:
    render_evolucion()

st.sidebar.divider()
st.sidebar.caption(f"Qi Team {VERSION_QI} · {VERSION_EVOLUCION}")
