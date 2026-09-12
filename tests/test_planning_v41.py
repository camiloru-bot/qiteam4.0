"""Pruebas mínimas del motor de planificación V4.1."""

from planning.decision import construir_decision_planificacion, objetivo_desde_diagnostico
from planning.planner import construir_semana


def test_diagnostico_alto_riesgo_prioriza_recuperacion():
    d = construir_decision_planificacion(
        "🟠 Atención — aumento de carga", "Medio", "10K", 8
    )
    assert d["objetivo_semana"] == "Recuperación / Regenerativo"
    assert d["requiere_revision_entrenador"] is True


def test_diagnostico_estable_no_fuerza_recuperacion():
    assert objetivo_desde_diagnostico("🟢 Estable") == "Base aeróbica / Resistencia"


def test_motor_devuelve_estructura():
    semana = construir_semana("Medio", "10K", "Base aeróbica / Resistencia", 8)
    assert isinstance(semana, list)
    assert len(semana) > 0
