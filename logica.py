"""Reglas de English Lab: cuándo repasar cada palabra y cómo medir la constancia.

Este archivo no guarda ni muestra nada; solo hace cálculos.
Así es fácil de probar y de entender.
"""
import re
from datetime import date, timedelta
from difflib import SequenceMatcher

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


# ---------- Dictado ----------

# En el dictado consideramos "bien" una frase si acertaste al menos el 80% de las palabras.
DICTADO_APROBADO = 0.8


def palabras_de(texto: str) -> list:
    """Separa un texto en palabras, en minúsculas y sin signos de puntuación.

    "I can't figure it out!" -> ["i", "can't", "figure", "it", "out"]
    """
    texto = texto.lower().replace("’", "'")  # el apóstrofo del celular cuenta igual que el del PC
    return re.findall(r"[a-z0-9']+", texto)


def comparar_dictado(original: str, escrito: str):
    """Compara la frase que escuchaste con lo que escribiste, palabra por palabra.

    Devuelve dos cosas:
    - el puntaje: qué parte de las palabras acertaste (de 0 a 1);
    - cada palabra de la frase original, marcada con True si la escribiste bien.

    SequenceMatcher busca las partes que coinciden en el mismo orden,
    así una palabra que falta no daña el resto de la comparación.
    """
    esperadas = palabras_de(original)
    escritas = palabras_de(escrito)
    acertadas = [False] * len(esperadas)
    for bloque in SequenceMatcher(a=esperadas, b=escritas, autojunk=False).get_matching_blocks():
        for i in range(bloque.a, bloque.a + bloque.size):
            acertadas[i] = True
    puntaje = sum(acertadas) / len(esperadas) if esperadas else 0.0
    return puntaje, list(zip(esperadas, acertadas))
