"""Pruebas del núcleo de decisión V4.1."""

from core.decision import clasificar_decision, construir_decision, registrar_decision


def test_clasificacion_diagnostico():
    assert clasificar_decision("🟠 Atención — aumento de carga") == "REDUCIR"
    assert clasificar_decision("🟢 Estable") == "MANTENER"
    assert clasificar_decision("🟢 Progresión controlada") == "PROGRESAR"


def test_decision_no_prescribe():
    d = construir_decision(
        estado_diagnostico="🟡 Atención — progresión",
        nivel="Medio",
        meta="10K",
        semanas_faltantes=8,
        comparacion={"tss": 12, "horas": 5},
    )
    assert d["decision_sugerida"] == "REVISAR"
    assert d["requiere_decision_entrenador"] is True
    assert d["prescribe_automaticamente"] is False


def test_registro_entrenador():
    historial = registrar_decision(
        [],
        decision_sugerida="MANTENER",
        decision_entrenador="PROGRESAR",
        comentario="Buena asimilación.",
        fecha="2026-09-12T08:00:00",
    )
    assert len(historial) == 1
    assert historial[0]["decision_entrenador"] == "PROGRESAR"
