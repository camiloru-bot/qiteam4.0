"""Decisión de entrenamiento — Qi Team V4.1.

Este módulo traduce el diagnóstico descriptivo en un estado de decisión
explicable. No prescribe sesiones ni modifica automáticamente el plan.
El entrenador conserva la decisión final.
"""

DECISIONES_VALIDAS = (
    "MANTENER",
    "PROGRESAR",
    "REDUCIR",
    "RECUPERAR",
    "REVISAR",
)


def clasificar_decision(estado_diagnostico):
    """Propone una dirección de decisión a partir del diagnóstico."""
    mapa = {
        "🟠 Atención — aumento de carga": "REDUCIR",
        "🟡 Atención — progresión": "REVISAR",
        "🔵 Descarga / reinicio": "RECUPERAR",
        "🔵 Datos insuficientes": "REVISAR",
        "🟢 Estable": "MANTENER",
        "🟢 Progresión controlada": "PROGRESAR",
    }
    return mapa.get(estado_diagnostico, "REVISAR")


def construir_decision(
    *,
    estado_diagnostico,
    nivel=None,
    meta=None,
    semanas_faltantes=None,
    comparacion=None,
):
    """Construye una decisión sugerida y sus razones, sin prescribir."""
    decision = clasificar_decision(estado_diagnostico)
    razones = []

    if estado_diagnostico:
        razones.append(f"Diagnóstico actual: {estado_diagnostico}.")

    if comparacion:
        tss = comparacion.get("tss")
        horas = comparacion.get("horas")
        if tss is not None:
            razones.append(f"Variación TSS vs bloque anterior: {tss:+.0f}%.")
        if horas is not None:
            razones.append(f"Variación de tiempo vs bloque anterior: {horas:+.0f}%.")

    if semanas_faltantes is not None:
        razones.append(f"Semanas faltantes al objetivo: {semanas_faltantes}.")

    return {
        "decision_sugerida": decision,
        "estado_diagnostico": estado_diagnostico,
        "nivel": nivel,
        "meta": meta,
        "semanas_faltantes": semanas_faltantes,
        "razones": razones,
        "requiere_decision_entrenador": True,
        "prescribe_automaticamente": False,
    }


def registrar_decision(
    historial,
    *,
    decision_sugerida,
    decision_entrenador,
    comentario="",
    fecha=None,
):
    """Añade una decisión explícita del entrenador al historial."""
    from datetime import datetime

    if decision_entrenador not in DECISIONES_VALIDAS:
        raise ValueError(f"Decisión no válida: {decision_entrenador}")

    registro = {
        "fecha": fecha or datetime.now().isoformat(timespec="seconds"),
        "decision_sugerida": decision_sugerida,
        "decision_entrenador": decision_entrenador,
        "comentario": comentario.strip(),
    }

    historial = list(historial or [])
    historial.append(registro)
    return historial
