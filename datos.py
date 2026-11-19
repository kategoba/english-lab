"""Todo lo que tiene que ver con guardar y leer los datos de English Lab.

La app funciona con dos tipos de base de datos sin cambiar nada más:
- En el PC: SQLite, una base de datos que vive en un solo archivo (english_lab.db).
- En internet: PostgreSQL en la nube, para que el PC y el celular vean los mismos datos.

SQLAlchemy es la herramienta que "traduce" nuestras instrucciones para cada una.
"""
import os
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
from sqlalchemy import Column, Float, ForeignKey, Integer, MetaData, Table, Text, create_engine, text

import logica

# ---------- ¿Dónde está la base de datos? ----------
# En la nube, la dirección llega en la variable DATABASE_URL. Es un "secreto":
# se configura en el servicio de publicación y nunca se sube a GitHub.
# En el PC no existe esa variable, así que usamos el archivo english_lab.db.
ARCHIVO_LOCAL = Path(os.environ.get("ENGLISH_LAB_BD", Path(__file__).parent / "english_lab.db"))
URL_BD = os.environ.get("DATABASE_URL") or f"sqlite:///{ARCHIVO_LOCAL}"
# Le indicamos a SQLAlchemy que use psycopg, el conector de PostgreSQL que instalamos.
for prefijo in ("postgres://", "postgresql://"):
    if URL_BD.startswith(prefijo):
        URL_BD = "postgresql+psycopg://" + URL_BD[len(prefijo):]

motor = create_engine(URL_BD, pool_pre_ping=True)  # pool_pre_ping: revisa que la conexión siga viva

# Usamos la hora de Colombia aunque la app corra en un servidor de otro país.
ZONA_HORARIA = ZoneInfo("America/Bogota")

# ---------- Las tablas ----------
tablas = MetaData()

palabras = Table(
    "palabras", tablas,
    Column("id", Integer, primary_key=True),
    Column("palabra", Text, nullable=False),
    Column("significado", Text, nullable=False),
    Column("ejemplo", Text),
    Column("nivel", Integer, nullable=False, server_default="0"),
    Column("proximo_repaso", Text, nullable=False),
    Column("ultimo_repaso", Text),
    Column("creada", Text, nullable=False),
)

# Cada repaso queda registrado: son los datos para el análisis y el modelo de predicción.
repasos = Table(
    "repasos", tablas,
    Column("id", Integer, primary_key=True),
    Column("palabra_id", Integer, ForeignKey("palabras.id"), nullable=False),
    Column("fecha_hora", Text, nullable=False),
    Column("recordada", Integer, nullable=False),
    Column("tiempo_respuesta_seg", Float),
    Column("tipo_ejercicio", Text, nullable=False),
    Column("dias_desde_ultimo_repaso", Integer),
    Column("nivel_antes", Integer, nullable=False),
)

tablas.create_all(motor)  # crea las tablas solo si todavía no existen


def ahora() -> datetime:
    return datetime.now(ZONA_HORARIA)


def hoy() -> date:
    return ahora().date()


# "with motor.begin()" abre la conexión y, al terminar, guarda los cambios y la cierra.

def agregar_palabra(palabra: str, significado: str, ejemplo: str = "") -> bool:
    """Guarda una palabra nueva para repasarla hoy mismo. Devuelve False si ya existía."""
    with motor.begin() as con:
        repetida = con.execute(
            text("SELECT 1 FROM palabras WHERE lower(palabra) = lower(:palabra)"),
            {"palabra": palabra},
        ).first()
        if repetida:
            return False
        con.execute(
            text("""INSERT INTO palabras (palabra, significado, ejemplo, nivel, proximo_repaso, creada)
                    VALUES (:palabra, :significado, :ejemplo, 0, :proximo, :creada)"""),
            {"palabra": palabra, "significado": significado, "ejemplo": ejemplo or None,
             "proximo": hoy().isoformat(), "creada": ahora().isoformat(timespec="seconds")},
        )
    return True


def palabras_para_hoy() -> list:
    """Palabras cuya fecha de repaso ya llegó, empezando por las más atrasadas."""
    with motor.begin() as con:
        return con.execute(
            text("SELECT * FROM palabras WHERE proximo_repaso <= :hoy ORDER BY proximo_repaso, id"),
            {"hoy": hoy().isoformat()},
        ).mappings().all()


def registrar_repaso(palabra_id: int, recordada: bool, tiempo_respuesta_seg: float, tipo_ejercicio: str = "repaso"):
    """Guarda el resultado de un repaso y programa la siguiente fecha."""
    with motor.begin() as con:
        palabra = con.execute(
            text("SELECT * FROM palabras WHERE id = :id"), {"id": palabra_id}
        ).mappings().one()
        momento = ahora()

        # Días desde el último repaso (o desde que la guardaste, si es la primera vez).
        referencia = date.fromisoformat((palabra["ultimo_repaso"] or palabra["creada"])[:10])
        dias_desde_ultimo = (momento.date() - referencia).days

        nivel = logica.nuevo_nivel(palabra["nivel"], recordada)
        proximo = logica.proxima_fecha(nivel, momento.date())

        con.execute(
            text("""INSERT INTO repasos (palabra_id, fecha_hora, recordada, tiempo_respuesta_seg,
                                         tipo_ejercicio, dias_desde_ultimo_repaso, nivel_antes)
                    VALUES (:palabra_id, :fecha_hora, :recordada, :tiempo,
                            :tipo, :dias, :nivel_antes)"""),
            {"palabra_id": palabra_id, "fecha_hora": momento.isoformat(timespec="seconds"),
             "recordada": int(recordada), "tiempo": round(tiempo_respuesta_seg, 1),
             "tipo": tipo_ejercicio, "dias": dias_desde_ultimo, "nivel_antes": palabra["nivel"]},
        )
        con.execute(
            text("UPDATE palabras SET nivel = :nivel, proximo_repaso = :proximo, ultimo_repaso = :ultimo WHERE id = :id"),
            {"nivel": nivel, "proximo": proximo.isoformat(),
             "ultimo": momento.isoformat(timespec="seconds"), "id": palabra_id},
        )


def tabla_palabras() -> pd.DataFrame:
    with motor.begin() as con:
        return pd.read_sql_query(text("SELECT * FROM palabras ORDER BY creada DESC"), con)


def tabla_repasos() -> pd.DataFrame:
    """Todos los repasos, con la palabra al lado. Es la copia que se exporta para GitHub."""
    with motor.begin() as con:
        return pd.read_sql_query(
            text("""SELECT r.id, r.fecha_hora, p.palabra, p.significado, r.tipo_ejercicio, r.recordada,
                           r.tiempo_respuesta_seg, r.dias_desde_ultimo_repaso, r.nivel_antes
                    FROM repasos r JOIN palabras p ON p.id = r.palabra_id
                    ORDER BY r.fecha_hora"""),
            con,
        )
