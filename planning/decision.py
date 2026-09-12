"""Puente Diagnóstico → Planificación de Qi Team V4.1.

Convierte el estado descriptivo de Evolución en una decisión inicial de
planificación. No reemplaza al entrenador: produce una recomendación
estructurada y explicable para el motor de planificación.
"""

MAPA_OBJETIVO = {
    "🟠 Atención — aumento de carga": "Recuperación / Regenerativo",
    "🟡 Atención — progresión": "Base aeróbica / Resistencia",
    "🔵 Descarga / reinicio": "Recuperación / Regenerativo",
    "🔵 Datos insuficientes": "Base aeróbica / Resistencia",
    "🟢 Estable": "Base aeróbica / Resistencia",
    "🟢 Progresión controlada": "Desarrollo de VO2Max / Velocidad",
}


def objetivo_desde_diagnostico(estado):
    """Traduce el estado diagnóstico a un foco de planificación."""
    return MAPA_OBJETIVO.get(
        estado,
        "Base aeróbica / Resistencia",
    )


def construir_decision_planificacion(
    estado,
    nivel,
    meta,
    semanas_faltantes,
    *,
    objetivo_override=None,
):
    """Genera una decisión explicable para la siguiente semana."""
    objetivo = objetivo_override or objetivo_desde_diagnostico(estado)

    if estado in {
        "🟠 Atención — aumento de carga",
        "🔵 Descarga / reinicio",
        "🔵 Datos insuficientes",
    }:
        prioridad = "Reducir riesgo y favorecer recuperación"
    elif estado == "🟡 Atención — progresión":
        prioridad = "Consolidar carga antes de progresar"
    else:
        prioridad = "Progresar de forma controlada"

    return {
        "estado_diagnostico": estado,
        "nivel": nivel,
        "meta": meta,
        "semanas_faltantes": semanas_faltantes,
        "objetivo_semana": objetivo,
        "prioridad": prioridad,
        "requiere_revision_entrenador": True,
    }


def construir_semana_desde_diagnostico(
    estado,
    nivel,
    meta,
    semanas_faltantes,
    *,
    objetivo_override=None,
):
    """Genera una propuesta de semana a partir del diagnóstico."""
    from planning.planner import construir_semana

    decision = construir_decision_planificacion(
        estado,
        nivel,
        meta,
        semanas_faltantes,
        objetivo_override=objetivo_override,
    )
    semana = construir_semana(
        nivel,
        meta,
        decision["objetivo_semana"],
        semanas_faltantes,
    )
    return decision, semana
