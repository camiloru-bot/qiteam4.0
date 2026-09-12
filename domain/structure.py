"""Reglas estructurales de Qi Team V4.1.

Fuente de verdad para días, roles y estructura semanal. Esta extracción
mantiene las reglas de V4.0 sin alterar su comportamiento.
"""

from datetime import datetime, timedelta

FRECUENCIA_OBJETIVO_POR_NIVEL = {
    "Principiante": 3,
    "Medio": 4,
    "Experto": 5,
}

# ============================================================
# V3.9 — MOTOR DE ESTRUCTURA SEMANAL + RESTRICCIONES
# ============================================================
# La estructura decide primero QUÉ espacios existen en la semana.
# El Catálogo Maestro decide DESPUÉS qué sesión concreta ocupa cada espacio.

ESTRUCTURA_SEMANAL = {
    "Principiante": [
        {"dia": "Martes", "rol": "Aeróbico", "etiqueta": "Carrera"},
        {"dia": "Jueves", "rol": "Aeróbico", "etiqueta": "Carrera"},
        {"dia": "Domingo", "rol": "Long Run", "etiqueta": "Long Run"},
    ],
    "Medio": [
        {"dia": "Martes", "rol": "Intervalos", "etiqueta": "Calidad"},
        {"dia": "Jueves", "rol": "Tempo", "etiqueta": "Umbral"},
        {"dia": "Sábado", "rol": "Aeróbico", "etiqueta": "Carrera aeróbica"},
        {"dia": "Domingo", "rol": "Long Run", "etiqueta": "Long Run"},
    ],
    "Experto": [
        {"dia": "Martes", "rol": "Intervalos", "etiqueta": "Calidad"},
        {"dia": "Miércoles", "rol": "Aeróbico", "etiqueta": "Carrera AM + Fuerza PM", "doble_jornada": True},
        {"dia": "Jueves", "rol": "Tempo", "etiqueta": "Umbral"},
        {"dia": "Sábado", "rol": "Aeróbico", "etiqueta": "Carrera aeróbica"},
        {"dia": "Domingo", "rol": "Long Run", "etiqueta": "Long Run"},
    ],
}

DIAS_FUERZA_POR_NIVEL = {
    "Principiante": ["Miércoles", "Viernes"],
    "Medio": ["Miércoles", "Viernes"],
    "Experto": ["Miércoles", "Viernes"],
}

FRECUENCIA_OBJETIVO_POR_NIVEL = {
    "Principiante": 3,
    "Medio": 4,
    "Experto": 5,
}

PRIORIDAD_CATEGORIA = {
    "Qi Long Run": 100, "Long Run": 100,
    "Qi Tempo": 90, "Tempo": 90,
    "Qi Intervalos": 85, "Intervalos": 85,
    "Qi Aeróbico": 70, "Aeróbico": 70,
    "Recuperación": 65, "Regenerativo": 65,
    "Qi Fartlek": 60, "Fartlek": 60,
}

# V4.0: esta estructura es la única fuente de verdad para los espacios
# semanales. El catálogo NO puede crear, mover ni intercambiar días.

def frecuencia_objetivo_nivel(nivel):
    return FRECUENCIA_OBJETIVO_POR_NIVEL.get(nivel, 4)


def rol_estructural(sesion):
    categoria = sesion.get("Categoría", sesion.get("Tipo de Sesión", ""))
    if categoria in ("Qi Long Run", "Long Run"):
        return "Long Run"
    if categoria in ("Qi Intervalos", "Intervalos"):
        return "Intervalos"
    if categoria in ("Qi Tempo", "Tempo"):
        return "Tempo"
    if categoria in ("Qi Aeróbico", "Aeróbico", "Recuperación", "Regenerativo"):
        return "Aeróbico"
    if categoria in ("Qi Fartlek", "Fartlek"):
        return "Fartlek"
    return "Otro"


def preparar_sesion(sesion, dia, rol=None, doble_jornada=False):
    sesion_plan = dict(sesion)
    rol = rol or rol_estructural(sesion)
    sesion_plan.update({
        "Día": dia,
        "Tipo de Sesión": sesion.get("Categoría", ""),
        "Rol Estructural": rol,
        "Doble Jornada": bool(doble_jornada),
        "Estructura Breve": (
            f"{sesion['Título']} | {sesion['Objetivo']} | {sesion['Intensidad']}"
        ),
        "Estructura Detallada para TP": sesion["Estructura TP"],
        "TSS Estimado": sesion["TSS"],
        "Horas Estimadas": sesion["Duración (h)"]
    })
    return sesion_plan


def seleccionar_para_estructura(nivel, meta, objetivo_semana, semanas_faltantes):
    """V4.0: construye la semana desde la estructura, no desde el catálogo.

    Jerarquía obligatoria:
        nivel -> día/rol -> catálogo -> sesión concreta

    Un entrenamiento solo puede ocupar un espacio si su rol coincide con
    el rol estructural de ese día. No existe fallback de día ni de rol.
    Si no hay candidato, el espacio queda vacío y se reporta como hueco.
    """
    estructura = ESTRUCTURA_SEMANAL.get(nivel, ESTRUCTURA_SEMANAL["Medio"])
    fase_preferida = fase_por_semanas(semanas_faltantes)
    objetivos = objetivos_por_foco(objetivo_semana)
    nivel_atleta = nivel_num(nivel)
    resultado = []
    ids_usados = set()

    for slot in estructura:
        candidatos = []
        dia = normalizar_dia_es(slot["dia"])
        rol_objetivo = slot["rol"]

        for s in CATALOGO_MAESTRO:
            if s["ID"] in ids_usados:
                continue
            if meta not in s["Meta"]:
                continue
            if nivel_num(s["Nivel"]) > nivel_atleta:
                continue
            # REGLA FUERTE: el rol del catálogo debe coincidir exactamente
            # con el rol que la estructura asignó al día.
            if rol_estructural(s) != rol_objetivo:
                continue

            score = 100
            if s["Nivel"] == nivel:
                score += 50
            if s["Objetivo"] in objetivos:
                score += 20
            if s["Fase"] == fase_preferida:
                score += 15
            if normalizar_dia_es(s.get("Día Preferente")) == dia:
                score += 30

            candidatos.append((score, s))

        candidatos.sort(
            key=lambda x: (x[0], x[1]["Nivel"] == nivel, x[1]["TSS"]),
            reverse=True
        )

        if candidatos:
            s = candidatos[0][1]
            resultado.append(
                preparar_sesion(
                    s, dia, rol_objetivo, slot.get("doble_jornada", False)
                )
            )
            ids_usados.add(s["ID"])
        else:
            # No inventamos ni movemos una sesión. El hueco se registra.
            resultado.append({
                "ID": f"HUECO-{dia.upper()}",
                "Título": f"Sin sesión compatible para {rol_objetivo}",
                "Categoría": "Sin asignar",
                "Objetivo": "Requiere ampliar catálogo",
                "Nivel": nivel,
                "Meta": [meta],
                "Duración (h)": 0.0,
                "TSS": 0.0,
                "TSS Estimado": 0.0,
                "Horas Estimadas": 0.0,
                "Intensidad": "N/A",
                "Fase": fase_preferida,
                "Día Preferente": dia,
                "Día": dia,
                "Rol Estructural": rol_objetivo,
                "Tipo de Sesión": "Sin asignar",
                "Doble Jornada": bool(slot.get("doble_jornada", False)),
                "Estructura Breve": f"Falta sesión de rol {rol_objetivo}",
                "Estructura Detallada para TP": "No existe una sesión compatible en el Catálogo Maestro.",
                "Estructura TP": "No existe una sesión compatible en el Catálogo Maestro.",
                "Etiquetas": "hueco estructural"
            })

    return resultado


def construir_planeacion_catalogo(nivel, meta, objetivo_semana, semanas_faltantes):
    return seleccionar_para_estructura(
        nivel, meta, objetivo_semana, semanas_faltantes
    )


def validar_y_corregir_planeacion_estructura(plan, nivel, meta, objetivo_semana, semanas_faltantes):
    """V4.0: auditor estructural absoluto.

    No reubica sesiones. Reconstruye cada espacio desde la estructura y solo
    conserva una sesión existente cuando su rol coincide con el rol esperado.
    Así se corrigen también planes heredados de V3.x que dejaron Long Run en
    martes o Tempo en domingo.
    """
    estructura = ESTRUCTURA_SEMANAL.get(nivel, ESTRUCTURA_SEMANAL["Medio"])
    por_dia = {normalizar_dia_es(s.get("Día")): s for s in plan if s.get("Día")}
    resultado = []
    usados = set()

    fase_preferida = fase_por_semanas(semanas_faltantes)
    objetivos = objetivos_por_foco(objetivo_semana)
    nivel_atleta = nivel_num(nivel)

    for slot in estructura:
        dia = normalizar_dia_es(slot["dia"])
        rol_esperado = slot["rol"]
        actual = por_dia.get(dia)

        if (
            actual
            and rol_estructural(actual) == rol_esperado
            and actual.get("ID") not in usados
            and not str(actual.get("ID", "")).startswith("HUECO-")
        ):
            corregida = preparar_sesion(
                actual, dia, rol_esperado, slot.get("doble_jornada", False)
            )
            resultado.append(corregida)
            usados.add(corregida["ID"])
            continue

        # Si el espacio está vacío o tiene un rol incorrecto, buscamos de
        # nuevo EXCLUSIVAMENTE dentro del rol estructural esperado.
        candidatos = []
        for s in CATALOGO_MAESTRO:
            if s["ID"] in usados or meta not in s["Meta"]:
                continue
            if nivel_num(s["Nivel"]) > nivel_atleta:
                continue
            if rol_estructural(s) != rol_esperado:
                continue

            score = 100
            if s["Nivel"] == nivel:
                score += 50
            if s["Objetivo"] in objetivos:
                score += 20
            if s["Fase"] == fase_preferida:
                score += 15
            if normalizar_dia_es(s.get("Día Preferente")) == dia:
                score += 30
            candidatos.append((score, s))

        candidatos.sort(
            key=lambda x: (x[0], x[1]["Nivel"] == nivel, x[1]["TSS"]),
            reverse=True
        )

        if candidatos:
            s = candidatos[0][1]
            corregida = preparar_sesion(
                s, dia, rol_esperado, slot.get("doble_jornada", False)
            )
            resultado.append(corregida)
            usados.add(s["ID"])
        else:
            resultado.append({
                "ID": f"HUECO-{dia.upper()}",
                "Título": f"Sin sesión compatible para {rol_esperado}",
                "Categoría": "Sin asignar",
                "Objetivo": "Requiere ampliar catálogo",
                "Nivel": nivel,
                "Meta": [meta],
                "Duración (h)": 0.0,
                "TSS": 0.0,
                "TSS Estimado": 0.0,
                "Horas Estimadas": 0.0,
                "Intensidad": "N/A",
                "Fase": fase_preferida,
                "Día Preferente": dia,
                "Día": dia,
                "Rol Estructural": rol_esperado,
                "Tipo de Sesión": "Sin asignar",
                "Doble Jornada": bool(slot.get("doble_jornada", False)),
                "Estructura Breve": f"Falta sesión de rol {rol_esperado}",
                "Estructura Detallada para TP": "No existe una sesión compatible en el Catálogo Maestro.",
                "Estructura TP": "No existe una sesión compatible en el Catálogo Maestro.",
                "Etiquetas": "hueco estructural"
            })

    return resultado

DIAS_ES = [
    "Lunes", "Martes", "Miércoles", "Jueves",
    "Viernes", "Sábado", "Domingo"
]

DIAS_ES_NORMALIZADOS = {
    "monday": "Lunes", "tuesday": "Martes", "wednesday": "Miércoles",
    "thursday": "Jueves", "friday": "Viernes", "saturday": "Sábado",
    "sunday": "Domingo", "lunes": "Lunes", "martes": "Martes",
    "miércoles": "Miércoles", "miercoles": "Miércoles", "jueves": "Jueves",
    "viernes": "Viernes", "sábado": "Sábado", "sabado": "Sábado",
    "domingo": "Domingo"
}

DIAS_CATEGORIA = {
    "Qi Intervalos": "Martes", "Intervalos": "Martes",
    "Qi Tempo": "Jueves", "Tempo": "Jueves",
    "Qi Fartlek": "Sábado", "Fartlek": "Sábado",
    "Qi Long Run": "Domingo", "Long Run": "Domingo",
    "Recuperación": "Miércoles", "Regenerativo": "Miércoles"
}


def normalizar_dia_es(dia):
    if not dia:
        return None
    texto = str(dia).strip()
    return DIAS_ES_NORMALIZADOS.get(texto.lower(), texto)


def nombre_dia_es(fecha):
    return DIAS_ES[fecha.weekday()]


def fecha_lunes_siguiente(fecha_base=None):
    fecha_base = fecha_base or datetime.now()
    dias = (7 - fecha_base.weekday()) % 7
    if dias == 0:
        dias = 7
    return (fecha_base + timedelta(days=dias)).date()


def fechas_plan_semana(lunes):
    return {dia: lunes + timedelta(days=i) for i, dia in enumerate(DIAS_ES)}


def fecha_sesion(plan, lunes):
    dia = normalizar_dia_es(plan.get("Día", ""))
    return fechas_plan_semana(lunes).get(dia, lunes)

# ============================================================
# V3.9 — RESTRICCIONES DERIVADAS DE DECISIONES DEL ENTRENADOR
# ============================================================

def rol_estructural_para_dia(nivel, dia):
    """Devuelve el rol que la estructura semanal asigna a un día."""
    dia = normalizar_dia_es(dia)
    estructura = ESTRUCTURA_SEMANAL.get(
        nivel,
        ESTRUCTURA_SEMANAL["Medio"]
    )
    for slot in estructura:
        if normalizar_dia_es(slot.get("dia")) == dia:
            return slot.get("rol")
    return None


def restricciones_rechazo_semana(
    decisiones_sesiones,
    lunes_plan,
    nivel
):
    """
    Construye restricciones activas para la semana.

    Una sesión rechazada deja de ser solamente un registro:
    se convierte en una restricción para nuevas sugerencias de esa
    misma fecha. El rol/categoría rechazados no se vuelven a proponer
    en ese espacio; el sistema intenta regresar al rol estructural
    definido para el nivel.
    """
    restricciones = {}

    if not decisiones_sesiones or lunes_plan is None:
        return restricciones

    inicio = lunes_plan
    fin = lunes_plan + timedelta(days=6)

    for key, registro in decisiones_sesiones.items():
        if not isinstance(registro, dict):
            continue

        if registro.get("estado") != "Rechazar":
            continue

        fecha_texto = registro.get("fecha")
        if not fecha_texto:
            continue

        try:
            fecha_rechazo = datetime.strptime(
                str(fecha_texto)[:10], "%Y-%m-%d"
            ).date()
        except Exception:
            continue

        if not (inicio <= fecha_rechazo <= fin):
            continue

        sesion_rechazada = registro.get("sesion_actual", {})
        if not isinstance(sesion_rechazada, dict):
            continue

        dia = nombre_dia_es(fecha_rechazo)
        rol_rechazado = rol_estructural(sesion_rechazada)
        categoria_rechazada = sesion_rechazada.get(
            "Categoría",
            sesion_rechazada.get("Tipo de Sesión", "")
        )

        restricciones[dia] = {
            "ids": {
                sesion_rechazada.get("ID")
            } if sesion_rechazada.get("ID") else set(),
            "roles": {rol_rechazado} if rol_rechazado else set(),
            "categorias": (
                {categoria_rechazada}
                if categoria_rechazada else set()
            ),
            "rol_estructural": rol_estructural_para_dia(
                nivel, dia
            )
        }

    return restricciones

