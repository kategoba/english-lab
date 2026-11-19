"""Reglas de English Lab: cuándo repasar cada palabra y cómo medir la constancia.

Este archivo no guarda ni muestra nada; solo hace cálculos.
Así es fácil de probar y de entender.
"""
from datetime import date, timedelta

# Repetición espaciada: días de espera antes del siguiente repaso, según el nivel.
# Nivel 0 = palabra nueva u olvidada; cada vez que la recuerdas sube un nivel.
INTERVALOS_DIAS = [1, 3, 7, 14, 30, 60]

# Desde este nivel (repaso cada 14 días o más) consideramos la palabra "aprendida".
NIVEL_APRENDIDA = 3


def nuevo_nivel(nivel_actual: int, recordada: bool) -> int:
    """Si la recordaste, sube un nivel (sin pasar del máximo). Si no, vuelve a 0."""
    if recordada:
        return min(nivel_actual + 1, len(INTERVALOS_DIAS) - 1)
    return 0


def proxima_fecha(nivel: int, desde: date) -> date:
    """Fecha del siguiente repaso según el nivel de la palabra."""
    return desde + timedelta(days=INTERVALOS_DIAS[nivel])


def calcular_racha(dias_con_estudio, hoy: date) -> int:
    """Cuántos días seguidos llevas estudiando.

    Si hoy todavía no has estudiado, la racha se cuenta hasta ayer,
    para que no se "pierda" en la mañana antes de practicar.
    """
    dias = set(dias_con_estudio)
    dia = hoy if hoy in dias else hoy - timedelta(days=1)
    racha = 0
    while dia in dias:
        racha += 1
        dia -= timedelta(days=1)
    return racha
