"""Catálogo Maestro de Qi Team V4.1.

Este módulo contiene las sesiones disponibles y las utilidades de selección
que pertenecen al catálogo. La lógica de estructura semanal permanece en
domain.structure.
"""

import pandas as pd

from domain.structure import nivel_num

CATALOGO_MAESTRO = [
    {
        "ID": "INT-001", "Categoría": "Qi Intervalos",
        "Título": "8x 3:30 / 1' Recuperación",
        "Objetivo": "VO2Max", "Nivel": "Medio",
        "Meta": ["5K", "10K", "Media Maratón"],
        "Duración (h)": 0.78, "TSS": 70.6,
        "Intensidad": "Alto (Z4-Z5)", "Fase": "Desarrollo",
        "Día Preferente": "Martes",
        "Estructura TP": """• Calentamiento: 15 min | Z1-Z2
• 8 repeticiones:
  - 3:30 min | Z4-Z5
  - 1 min | Z1 recuperación
• Enfriamiento: 10 min | Z1""",
        "Etiquetas": "VO2Max, intervalos, velocidad"
    },
    {
        "ID": "INT-002", "Categoría": "Qi Intervalos",
        "Título": "5x 800m / 90'' Recuperación",
        "Objetivo": "Ritmo específico / VO2Max", "Nivel": "Medio",
        "Meta": ["5K", "10K"],
        "Duración (h)": 0.75, "TSS": 78.0,
        "Intensidad": "Alto (Z4-Z5)", "Fase": "Específica",
        "Día Preferente": "Martes",
        "Estructura TP": """• Calentamiento: 15 min | Z1-Z2
• 5 x 800m | Z4-Z5
• Recuperación: 90 seg | Z1
• Enfriamiento: 10 min | Z1""",
        "Etiquetas": "800m, ritmo, específico"
    },
    {
        "ID": "INT-004", "Categoría": "Qi Intervalos",
        "Título": "6x 4' / 2' Recuperación",
        "Objetivo": "Umbral / VO2Max", "Nivel": "Medio",
        "Meta": ["10K", "Media Maratón", "Maratón"],
        "Duración (h)": 0.85, "TSS": 82.0,
        "Intensidad": "Alto (Z4)", "Fase": "Desarrollo",
        "Día Preferente": "Martes",
        "Estructura TP": """• Calentamiento: 15 min | Z1-Z2
• 6 x 4 min | Z4
• Recuperación: 2 min | Z1-Z2
• Enfriamiento: 10 min | Z1""",
        "Etiquetas": "intervalos, umbral, media maratón, alternativa"
    },
    {
        "ID": "INT-003", "Categoría": "Qi Intervalos",
        "Título": "6x 1000m / 90'' Recuperación",
        "Objetivo": "Ritmo específico", "Nivel": "Experto",
        "Meta": ["10K", "Media Maratón", "Maratón"],
        "Duración (h)": 0.95, "TSS": 105.0,
        "Intensidad": "Alto (Z4-Z5)", "Fase": "Específica",
        "Día Preferente": "Martes",
        "Estructura TP": """• Calentamiento: 15 min | Z1-Z2
• 6 x 1000m | Z4-Z5 / ritmo específico
• Recuperación: 90 seg | Z1
• Enfriamiento: 15 min | Z1""",
        "Etiquetas": "1000m, específico, resistencia"
    },
    {
        "ID": "TMP-001", "Categoría": "Qi Tempo",
        "Título": "3x 9' Tempo Progresivo",
        "Objetivo": "Umbral / Sostenido", "Nivel": "Medio",
        "Meta": ["5K", "10K", "Media Maratón"],
        "Duración (h)": 0.75, "TSS": 73.7,
        "Intensidad": "Sostenido (Z3-Z4)", "Fase": "Desarrollo",
        "Día Preferente": "Jueves",
        "Estructura TP": """• Calentamiento: 15 min | Z1-Z2
• 3 x 9 min | Z3-Z4 progresivo
• Recuperación: 2 min | Z1
• Enfriamiento: 10 min | Z1""",
        "Etiquetas": "tempo, umbral, progresivo"
    },
    {
        "ID": "TMP-002", "Categoría": "Qi Tempo",
        "Título": "30' Tempo Sostenido",
        "Objetivo": "Umbral / Sostenido", "Nivel": "Medio",
        "Meta": ["10K", "Media Maratón", "Maratón"],
        "Duración (h)": 0.80, "TSS": 85.0,
        "Intensidad": "Sostenido (Z3-Z4)", "Fase": "Específica",
        "Día Preferente": "Jueves",
        "Estructura TP": """• Calentamiento: 15 min | Z1-Z2
• 30 min continuos | Z3-Z4
• Enfriamiento: 10 min | Z1""",
        "Etiquetas": "tempo, umbral, continuo"
    },
    {
        "ID": "TMP-003", "Categoría": "Qi Tempo",
        "Título": "40' Tempo Base",
        "Objetivo": "Resistencia aeróbica / Umbral", "Nivel": "Experto",
        "Meta": ["10K", "Media Maratón", "Maratón"],
        "Duración (h)": 1.00, "TSS": 105.0,
        "Intensidad": "Sostenido (Z3)", "Fase": "Desarrollo",
        "Día Preferente": "Jueves",
        "Estructura TP": """• Calentamiento: 15 min | Z1-Z2
• 40 min | Z3 continuo
• Enfriamiento: 15 min | Z1""",
        "Etiquetas": "tempo, aeróbico, resistencia"
    },
    {
        "ID": "FAR-001", "Categoría": "Qi Fartlek",
        "Título": "Fartlek Sueco 1' x 1' / 20'",
        "Objetivo": "Variabilidad de ritmo", "Nivel": "Principiante",
        "Meta": ["5K", "10K"],
        "Duración (h)": 0.60, "TSS": 55.0,
        "Intensidad": "Variable (Z2-Z4)", "Fase": "Base",
        "Día Preferente": "Jueves",
        "Estructura TP": """• Calentamiento: 10 min | Z1-Z2
• 20 min alternando:
  - 1 min alegre | Z3-Z4
  - 1 min suave | Z1-Z2
• Enfriamiento: 10 min | Z1""",
        "Etiquetas": "fartlek, variabilidad, principiante"
    },
    {
        "ID": "FAR-002", "Categoría": "Qi Fartlek",
        "Título": "Fartlek de Ritmos Mixtos",
        "Objetivo": "Cambios de ritmo", "Nivel": "Medio",
        "Meta": ["5K", "10K", "Media Maratón"],
        "Duración (h)": 0.75, "TSS": 75.0,
        "Intensidad": "Variable (Z2-Z4)", "Fase": "Desarrollo",
        "Día Preferente": "Sábado",
        "Estructura TP": """• Calentamiento: 15 min | Z1-Z2
• Bloque Fartlek Z2-Z4
• Cambios de ritmo controlados
• Enfriamiento: 10 min | Z1""",
        "Etiquetas": "fartlek, mixto, sábado"
    },
    {
        "ID": "FAR-003", "Categoría": "Qi Fartlek",
        "Título": "Fartlek Avanzado de Velocidad",
        "Objetivo": "Velocidad / VO2Max", "Nivel": "Experto",
        "Meta": ["10K", "Media Maratón", "Maratón"],
        "Duración (h)": 0.90, "TSS": 92.0,
        "Intensidad": "Alto (Z4-Z5)", "Fase": "Desarrollo",
        "Día Preferente": "Miércoles",
        "Estructura TP": """• Calentamiento: 15 min | Z1-Z2
• Fartlek estructurado Z4-Z5
• Recuperaciones activas en Z1-Z2
• Enfriamiento: 15 min | Z1""",
        "Etiquetas": "fartlek, velocidad, avanzado"
    },
    {
        "ID": "LNG-001", "Categoría": "Qi Long Run",
        "Título": "Long Run Aeróbico",
        "Objetivo": "Base aeróbica", "Nivel": "Principiante",
        "Meta": ["5K", "10K", "Media Maratón"],
        "Duración (h)": 0.75, "TSS": 55.0,
        "Intensidad": "Base (Z1-Z2)", "Fase": "Base",
        "Día Preferente": "Domingo",
        "Estructura TP": """• Bloque único: 50 min | Z1-Z2
• Mantener esfuerzo conversacional
• Sin progresión obligatoria""",
        "Etiquetas": "fondo, base, aeróbico"
    },
    {
        "ID": "LNG-002", "Categoría": "Qi Long Run",
        "Título": "Long Run Aeróbico 90'",
        "Objetivo": "Resistencia aeróbica", "Nivel": "Medio",
        "Meta": ["10K", "Media Maratón", "Maratón"],
        "Duración (h)": 1.50, "TSS": 115.0,
        "Intensidad": "Base (Z1-Z2)", "Fase": "Desarrollo",
        "Día Preferente": "Domingo",
        "Estructura TP": """• Bloque único: 1h 30 min | Z1-Z2
• Ritmo aeróbico controlado""",
        "Etiquetas": "fondo, resistencia, aeróbico"
    },
    {
        "ID": "LNG-003", "Categoría": "Qi Long Run",
        "Título": "Long Run Aeróbico + Últimos 5K Progresivos",
        "Objetivo": "Resistencia específica", "Nivel": "Experto",
        "Meta": ["10K", "Media Maratón", "Maratón"],
        "Duración (h)": 1.80, "TSS": 135.0,
        "Intensidad": "Base (Z1-Z3)", "Fase": "Específica",
        "Día Preferente": "Domingo",
        "Estructura TP": """• Bloque aeróbico inicial | Z1-Z2
• Últimos 5 km progresivos | Z2-Z3
• Final controlado, sin llegar a esfuerzo máximo""",
        "Etiquetas": "fondo, específico, progresivo, maratón"
    },
    {
        "ID": "LNG-004", "Categoría": "Qi Long Run",
        "Título": "Long Run Avanzado con Bloques Específicos",
        "Objetivo": "Resistencia específica de competencia", "Nivel": "Experto",
        "Meta": ["Maratón"],
        "Duración (h)": 2.00, "TSS": 160.0,
        "Intensidad": "Z1-Z3", "Fase": "Específica",
        "Día Preferente": "Domingo",
        "Estructura TP": """• 2h totales
• Base aeróbica Z1-Z2
• Bloques específicos integrados según objetivo
• Control estricto de fatiga""",
        "Etiquetas": "fondo, maratón, específico, avanzado"
    },
    # Extensión V3.3: alternativa de Long Run para permitir una
    # nueva sugerencia cuando el entrenador pide más volumen.
    {
        "ID": "LNG-005", "Categoría": "Qi Long Run",
        "Título": "Long Run Aeróbico 105'",
        "Objetivo": "Resistencia aeróbica / incremento de volumen", "Nivel": "Medio",
        "Meta": ["10K", "Media Maratón", "Maratón"],
        "Duración (h)": 1.75, "TSS": 130.0,
        "Intensidad": "Base (Z1-Z2)", "Fase": "Desarrollo",
        "Día Preferente": "Domingo",
        "Estructura TP": """• Bloque único: 1h 45 min | Z1-Z2
• Ritmo aeróbico controlado
• Prioridad: incremento progresivo del volumen""",
        "Etiquetas": "fondo, volumen, resistencia, aeróbico"
    },
    {
        "ID": "REC-001", "Categoría": "Recuperación",
        "Título": "Trote Regenerativo 35'",
        "Objetivo": "Recuperación", "Nivel": "Principiante",
        "Meta": ["5K", "10K", "Media Maratón", "Maratón"],
        "Duración (h)": 0.58, "TSS": 30.0,
        "Intensidad": "Muy bajo (Z1)", "Fase": "Recuperación",
        "Día Preferente": "Martes",
        "Estructura TP": """• 35 min | Z1 estricto
• Sensación cómoda
• Sin progresivos ni bloques intensos""",
        "Etiquetas": "recuperación, regenerativo"
    },
    {
        "ID": "REC-002", "Categoría": "Recuperación",
        "Título": "Trote Regenerativo 50'",
        "Objetivo": "Recuperación", "Nivel": "Experto",
        "Meta": ["10K", "Media Maratón", "Maratón"],
        "Duración (h)": 0.83, "TSS": 45.0,
        "Intensidad": "Muy bajo (Z1)", "Fase": "Recuperación",
        "Día Preferente": "Jueves",
        "Estructura TP": """• 50 min | Z1
• Mantener esfuerzo muy cómodo
• Prioridad: asimilación""",
        "Etiquetas": "recuperación, descarga, regenerativo"
    },
    {
        "ID": "AER-001", "Categoría": "Qi Aeróbico",
        "Título": "Rodaje Aeróbico Fácil 40'",
        "Objetivo": "Base aeróbica", "Nivel": "Principiante",
        "Meta": ["5K", "10K", "Media Maratón", "Maratón"],
        "Duración (h)": 0.67, "TSS": 38.0,
        "Intensidad": "Bajo (Z1-Z2)", "Fase": "Base",
        "Día Preferente": "Martes",
        "Estructura TP": """• 40 min | Z1-Z2\n• Ritmo cómodo y conversacional\n• Sin bloques de intensidad""",
        "Etiquetas": "aeróbico, base, principiante"
    },
    {
        "ID": "AER-002", "Categoría": "Qi Aeróbico",
        "Título": "Rodaje Aeróbico Controlado 60'",
        "Objetivo": "Resistencia aeróbica", "Nivel": "Medio",
        "Meta": ["5K", "10K", "Media Maratón", "Maratón"],
        "Duración (h)": 1.00, "TSS": 60.0,
        "Intensidad": "Bajo (Z1-Z2)", "Fase": "Base",
        "Día Preferente": "Sábado",
        "Estructura TP": """• 60 min | Z1-Z2\n• Ritmo aeróbico estable\n• Prioridad: volumen sin fatiga excesiva""",
        "Etiquetas": "aeróbico, volumen, medio"
    },
    {
        "ID": "AER-006", "Categoría": "Qi Aeróbico",
        "Título": "Rodaje Aeróbico Progresivo 70'", "Objetivo": "Resistencia aeróbica",
        "Nivel": "Medio", "Meta": ["10K", "Media Maratón", "Maratón"],
        "Duración (h)": 1.17, "TSS": 70.0,
        "Intensidad": "Bajo-Moderado (Z1-Z3)", "Fase": "Desarrollo",
        "Día Preferente": "Sábado",
        "Estructura TP": """• 50 min | Z1-Z2
• 15 min progresivos | Z2-Z3
• 5 min | Z1
• Sin llegar a umbral""",
        "Etiquetas": "aeróbico, progresivo, sábado, alternativa"
    },
    {
        "ID": "AER-003", "Categoría": "Qi Aeróbico",
        "Título": "Rodaje Aeróbico Controlado 50'",
        "Objetivo": "Resistencia aeróbica", "Nivel": "Experto",
        "Meta": ["10K", "Media Maratón", "Maratón"],
        "Duración (h)": 0.83, "TSS": 50.0,
        "Intensidad": "Bajo (Z1-Z2)", "Fase": "Base",
        "Día Preferente": "Miércoles",
        "Estructura TP": """• 50 min | Z1-Z2\n• Carrera aeróbica controlada\n• AM: dejar margen para fortalecimiento PM""",
        "Etiquetas": "aeróbico, doble jornada, experto"
    },
    {
        "ID": "AER-004", "Categoría": "Qi Aeróbico",
        "Título": "Rodaje Aeróbico Controlado 60'",
        "Objetivo": "Resistencia aeróbica", "Nivel": "Experto",
        "Meta": ["10K", "Media Maratón", "Maratón"],
        "Duración (h)": 1.00, "TSS": 62.0,
        "Intensidad": "Bajo (Z1-Z2)", "Fase": "Base",
        "Día Preferente": "Sábado",
        "Estructura TP": """• 60 min | Z1-Z2\n• Rodaje aeróbico estable\n• Evitar convertirlo en sesión de intensidad""",
        "Etiquetas": "aeróbico, volumen, experto"
    },
    {
        "ID": "AER-005", "Categoría": "Qi Aeróbico",
        "Título": "Rodaje Aeróbico Fácil 45'",
        "Objetivo": "Base aeróbica", "Nivel": "Principiante",
        "Meta": ["5K", "10K", "Media Maratón", "Maratón"],
        "Duración (h)": 0.75, "TSS": 42.0,
        "Intensidad": "Bajo (Z1-Z2)", "Fase": "Base",
        "Día Preferente": "Jueves",
        "Estructura TP": """• 45 min | Z1-Z2\n• Ritmo cómodo\n• Finalizar con sensación de reserva""",
        "Etiquetas": "aeróbico, base, principiante"
    },
]

def nivel_num(nivel):
    return ORDEN_NIVEL.get(nivel, 2)


def catalogo_dataFrame():
    return pd.DataFrame([
        {
            "ID": s["ID"],
            "Categoría": s["Categoría"],
            "Título": s["Título"],
            "Objetivo": s["Objetivo"],
            "Nivel": s["Nivel"],
            "Meta": ", ".join(s["Meta"]),
            "Duración (h)": s["Duración (h)"],
            "TSS": s["TSS"],
            "Intensidad": s["Intensidad"],
            "Fase": s["Fase"],
            "Día Preferente": s["Día Preferente"],
            "Etiquetas": s["Etiquetas"]
        }
        for s in CATALOGO_MAESTRO
    ])


def fase_por_semanas(semanas):
    if semanas <= 3:
        return "Específica"
    if semanas <= 8:
        return "Desarrollo"
    return "Base"


def objetivos_por_foco(objetivo_semana):
    if objetivo_semana == "Desarrollo de VO2Max / Velocidad":
        return ["VO2Max", "Ritmo específico / VO2Max", "Velocidad / VO2Max"]
    if objetivo_semana == "Umbral / Sostenido":
        return ["Umbral / Sostenido", "Resistencia aeróbica / Umbral"]
    if objetivo_semana == "Recuperación / Regenerativo":
        return ["Recuperación"]
    return [
        "Base aeróbica",
        "Variabilidad de ritmo",
        "Resistencia aeróbica",
        "Resistencia aeróbica / incremento de volumen"
    ]


def seleccionar_sesiones(nivel, meta, objetivo_semana, semanas_faltantes):
    fase_preferida = fase_por_semanas(semanas_faltantes)
    objetivos = objetivos_por_foco(objetivo_semana)
    nivel_atleta = nivel_num(nivel)
    candidatos = []

    for sesion in CATALOGO_MAESTRO:
        if meta not in sesion["Meta"]:
            continue

        if nivel_num(sesion["Nivel"]) > nivel_atleta:
            continue

        score = 0
        if sesion["Objetivo"] in objetivos:
            score += 50
        if sesion["Fase"] == fase_preferida:
            score += 20
        if sesion["Nivel"] == nivel:
            score += 15
        if sesion["Día Preferente"]:
            score += 5

        candidatos.append((score, sesion))

    candidatos.sort(key=lambda x: x[0], reverse=True)
    return [x[1] for x in candidatos]

