"""Motor de recomendación V4.1.

Reglas explicables para comparar carga ejecutada contra referencia y orientar
la siguiente decisión. No sustituye el criterio del entrenador.
"""


def generar_recomendacion(
    tss_real, tss_plan, horas_real, horas_plan,
    sesiones_real, nivel, semanas_faltantes
):
    recomendaciones = []
    alertas = []

    porcentaje_tss = (
        ((tss_real - tss_plan) / tss_plan) * 100 if tss_plan > 0 else 0
    )
    porcentaje_horas = (
        ((horas_real - horas_plan) / horas_plan) * 100 if horas_plan > 0 else 0
    )

    if porcentaje_tss > 20:
        recomendaciones.append("La carga ejecutada estuvo claramente por encima de la referencia.")
        alertas.append("⚠️ TSS significativamente superior al plan.")
    elif porcentaje_tss > 10:
        recomendaciones.append("La carga ejecutada estuvo moderadamente por encima de la referencia.")
    elif porcentaje_tss < -20:
        recomendaciones.append("La carga ejecutada estuvo significativamente por debajo de la referencia.")
        alertas.append("⚠️ TSS significativamente inferior al plan.")
    elif porcentaje_tss < -10:
        recomendaciones.append("La carga ejecutada estuvo moderadamente por debajo de la referencia.")
    else:
        recomendaciones.append("La carga ejecutada se mantuvo relativamente cercana a la referencia.")

    if porcentaje_horas > 15:
        recomendaciones.append("El volumen de tiempo también estuvo por encima de lo previsto.")
        alertas.append("⏱️ Volumen superior al plan.")
    elif porcentaje_horas < -15:
        recomendaciones.append("El volumen de tiempo quedó por debajo de lo previsto.")
        alertas.append("⏱️ Volumen inferior al plan.")

    if sesiones_real == 0:
        alertas.append("🚨 No se detectaron sesiones en el periodo analizado.")

    if porcentaje_tss > 20:
        general = "🟠 Considerar una reducción o asimilación de carga antes de incrementar nuevamente."
        decision = "Reducir carga"
    elif porcentaje_tss < -20:
        general = "🟡 Revisar las causas del bajo cumplimiento antes de aumentar automáticamente la carga."
        decision = "Revisar / Mantener"
    elif semanas_faltantes <= 3:
        general = "🔴 Estamos cerca de la competencia. La prioridad debe ser especificidad, asimilación y control de fatiga."
        decision = "Mantener / Afinar"
    else:
        general = "🟢 La carga parece razonablemente controlada. Puede continuarse con la progresión prevista, siempre bajo criterio del entrenador."
        decision = "Mantener"

    return {
        "recomendaciones": recomendaciones,
        "alertas": alertas,
        "general": general,
        "decision_sugerida": decision,
        "porcentaje_tss": porcentaje_tss,
        "porcentaje_horas": porcentaje_horas,
    }


def construir_contexto_decision(
    tss_real, tss_plan, horas_real, horas_plan,
    sesiones_real, nivel, semanas_faltantes, estado_diagnostico=None
):
    """Normaliza los datos que verá la interfaz antes de mostrar la recomendación."""
    recomendacion = generar_recomendacion(
        tss_real, tss_plan, horas_real, horas_plan,
        sesiones_real, nivel, semanas_faltantes,
    )
    return {
        "nivel": nivel,
        "semanas_faltantes": semanas_faltantes,
        "estado_diagnostico": estado_diagnostico,
        "recomendacion": recomendacion,
        "requiere_revision_entrenador": True,
    }
