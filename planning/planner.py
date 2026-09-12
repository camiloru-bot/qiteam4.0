"""Motor de planificación de Qi Team V4.1.

Orquesta selección, sustituciones y claves de trazabilidad sin depender de
Streamlit. La interfaz puede consumir estas funciones como servicio de dominio.
"""

from datetime import date

from data.catalogo import CATALOGO_MAESTRO, fase_por_semanas, objetivos_por_foco
from domain.structure import (
    normalizar_dia_es,
    preparar_sesion,
    rol_estructural,
    rol_estructural_para_dia,
    seleccionar_para_estructura,
    validar_y_corregir_planeacion_estructura,
)


def construir_semana(nivel, meta, objetivo_semana, semanas_faltantes):
    """Construye la semana respetando estrictamente la estructura semanal."""
    return seleccionar_para_estructura(
        nivel, meta, objetivo_semana, semanas_faltantes
    )


def auditar_semana(plan, nivel, meta, objetivo_semana, semanas_faltantes):
    """Audita/reconstruye una semana contra los espacios estructurales."""
    return validar_y_corregir_planeacion_estructura(
        plan, nivel, meta, objetivo_semana, semanas_faltantes
    )


def buscar_nueva_sugerencia(
    sesion_actual,
    nivel,
    meta,
    objetivo_semana,
    semanas_faltantes,
    feedback="",
    ids_excluidos=None,
    dia_objetivo=None,
    rol_objetivo=None,
    roles_excluidos=None,
    categorias_excluidas=None,
):
    """Busca una sustitución respetando primero el rol estructural del día.

    V3.9 corregida:
    1) nunca cambia el rol estructural del día;
    2) intenta mismo nivel + misma meta;
    3) si se agotan alternativas, permite un nivel inferior compatible;
    4) jamás vuelve a ofrecer el rol/categoría rechazados.
    """
    ids_excluidos = set(ids_excluidos or [])
    ids_excluidos.add(sesion_actual.get("ID"))
    roles_excluidos = set(roles_excluidos or [])
    categorias_excluidas = set(categorias_excluidas or [])

    dia_objetivo = normalizar_dia_es(dia_objetivo) if dia_objetivo else None
    rol_objetivo = rol_objetivo or (
        rol_estructural_para_dia(nivel, dia_objetivo) if dia_objetivo else None
    ) or rol_estructural(sesion_actual)

    nivel_atleta = nivel_num(nivel)
    fase = fase_por_semanas(semanas_faltantes)
    objetivos = objetivos_por_foco(objetivo_semana)
    texto = (feedback or "").lower()

    pide_mas_carga = any(p in texto for p in [
        "más carga", "mas carga", "más volumen", "mas volumen",
        "más tiempo", "mas tiempo", "insuficiente", "aumentar"
    ])
    pide_menos_carga = any(p in texto for p in [
        "menos carga", "menos volumen", "menos tiempo",
        "reducir", "fatiga", "descarga"
    ])

    duracion_actual = float(sesion_actual.get("Duración (h)", sesion_actual.get("Horas Estimadas", 0)))
    tss_actual = float(sesion_actual.get("TSS", sesion_actual.get("TSS Estimado", 0)))

    def candidatos_para(mismo_nivel=True, permitir_ids_excluidos=False):
        candidatos = []
        for s in CATALOGO_MAESTRO:
            if not permitir_ids_excluidos and s["ID"] in ids_excluidos:
                continue
            if meta not in s["Meta"]:
                continue
            if nivel_num(s["Nivel"]) > nivel_atleta:
                continue
            if mismo_nivel and s["Nivel"] != nivel:
                continue
            if rol_estructural(s) != rol_objetivo:
                continue
            if rol_estructural(s) in roles_excluidos:
                continue
            if s.get("Categoría", "") in categorias_excluidas:
                continue

            score = 100
            if s["Nivel"] == nivel:
                score += 35
            if s["Objetivo"] in objetivos:
                score += 25
            if s["Fase"] == fase:
                score += 15
            if dia_objetivo and normalizar_dia_es(s.get("Día Preferente")) == dia_objetivo:
                score += 25
            if pide_mas_carga:
                if s["Duración (h)"] > duracion_actual:
                    score += 35
                if s["TSS"] > tss_actual:
                    score += 25
            if pide_menos_carga:
                if s["Duración (h)"] < duracion_actual:
                    score += 35
                if s["TSS"] < tss_actual:
                    score += 25
            candidatos.append((score, s))
        candidatos.sort(key=lambda x: (x[0], x[1]["TSS"]), reverse=True)
        return candidatos

    candidatos = candidatos_para(mismo_nivel=True)

    # Fallback controlado: nivel inferior, mismo rol y misma meta.
    if not candidatos:
        candidatos = candidatos_para(mismo_nivel=False)

    if not candidatos:
        return None

    nueva = dict(candidatos[0][1])
    if dia_objetivo:
        nueva["Día"] = dia_objetivo
    nueva["Rol Estructural"] = rol_objetivo
    nueva["Doble Jornada"] = bool(sesion_actual.get("Doble Jornada", False))
    nueva["Tipo de Sesión"] = nueva.get("Categoría", "")
    nueva["Estructura Breve"] = f"{nueva['Título']} | {nueva['Objetivo']} | {nueva['Intensidad']}"
    nueva["Estructura Detallada para TP"] = nueva["Estructura TP"]
    nueva["TSS Estimado"] = nueva["TSS"]
    nueva["Horas Estimadas"] = nueva["Duración (h)"]
    return nueva


def clave_sesion(fecha, session_id):
    return f"{fecha.strftime('%Y-%m-%d')}|{session_id}"


def clave_espacio(fecha, rol):
    """V4.0: identidad estable del espacio semanal.

    La decisión del entrenador pertenece al espacio estructural (fecha + rol),
    no al ID concreto del entrenamiento. Si el catálogo cambia la sesión,
    la decisión y el historial siguen ligados al mismo espacio.
    """
    return f"{fecha.strftime('%Y-%m-%d')}|{rol}"


