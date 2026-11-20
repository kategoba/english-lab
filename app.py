"""English Lab: la app que ves en el navegador.

Para abrirla, en una terminal dentro de esta carpeta:
    python -m streamlit run app.py
"""
import hmac
import json
import os
import time

import altair as alt
import pandas as pd
import streamlit as st

import logica

AZUL_MEDIO = "#3B82F6"

st.set_page_config(page_title="English Lab", page_icon="💙", layout="centered")

# Los secretos de Streamlit Cloud también llegan como variables de entorno.
# Por si acaso, los copiamos nosotras mismas antes de abrir la base de datos.
try:
    for nombre in ("DATABASE_URL", "APP_PASSWORD"):
        if nombre in st.secrets and not os.environ.get(nombre):
            os.environ[nombre] = str(st.secrets[nombre])
except Exception:
    pass  # en el PC no hay archivo de secretos, y está bien

try:
    import datos
except RuntimeError as error:  # en internet sin base de datos: mejor detenerse que perder datos
    st.title("💙 English Lab")
    st.error(f"⚠️ {error}")
    st.stop()


def boton_escuchar(texto: str):
    """Botones para oír un texto en inglés con la voz del navegador (gratis, funciona en PC y celular)."""
    # Convierte el texto a un formato seguro para JavaScript (y evita que "</" cierre el script).
    texto_js = json.dumps(texto).replace("</", "<\\/")
    st.iframe(
        f"""
        <style>
          body {{ margin: 4px 0; overflow: hidden; }}
          button {{ font-size: 15px; padding: 8px 14px; margin-right: 6px; border-radius: 8px;
                   border: 1px solid #93C5FD; background: #DBEAFE; color: #0B2545; cursor: pointer; }}
        </style>
        <button onclick="hablar(1)">🔊 Escuchar</button>
        <button onclick="hablar(0.6)">🐢 Despacio</button>
        <script>
          function hablar(velocidad) {{
            const voz = new SpeechSynthesisUtterance({texto_js});
            voz.lang = "en-US";
            voz.rate = velocidad;
            speechSynthesis.cancel();
            speechSynthesis.speak(voz);
          }}
        </script>
        """,
        height=52,
    )


# ---------- Pantalla 1: repasar las palabras de hoy ----------
def pantalla_repasar():
    pendientes = datos.palabras_para_hoy()
    if not pendientes:
        st.success("🎉 No tienes palabras pendientes hoy. ¡Laboratorio al día!")
        st.write("Agrega palabras nuevas de tus audios en **➕ Agregar**.")
        return

    faltan = len(pendientes)
    st.write(f"Te {'falta' if faltan == 1 else 'faltan'} **{faltan}** "
             f"{'palabra' if faltan == 1 else 'palabras'} por repasar hoy.")
    palabra = pendientes[0]

    # Cuando aparece una palabra nueva, ocultamos el significado y empezamos a medir el tiempo.
    if st.session_state.get("palabra_actual") != palabra["id"]:
        st.session_state.palabra_actual = palabra["id"]
        st.session_state.inicio = time.time()
        st.session_state.mostrar = False

    with st.container(border=True):
        st.markdown(f"## {palabra['palabra']}")
        boton_escuchar(palabra["palabra"])
        if st.session_state.mostrar:
            st.markdown(f"**Significado:** {palabra['significado']}")
            if palabra["ejemplo"]:
                st.markdown(f"*{palabra['ejemplo']}*")
                boton_escuchar(palabra["ejemplo"])

    if not st.session_state.mostrar:
        st.caption("Piensa qué significa y luego revisa.")
        if st.button("👀 Mostrar significado", type="primary", width="stretch"):
            # Tiempo que tardaste en intentar recordarla: es un dato para el modelo de predicción.
            st.session_state.tiempo = time.time() - st.session_state.inicio
            st.session_state.mostrar = True
            st.rerun()
    else:
        col_si, col_no = st.columns(2)
        if col_si.button("✅ La recordé", width="stretch"):
            responder(palabra["id"], recordada=True)
        if col_no.button("❌ No la recordé", width="stretch"):
            responder(palabra["id"], recordada=False)


def responder(palabra_id: int, recordada: bool):
    datos.registrar_repaso(palabra_id, recordada, st.session_state.tiempo)
    del st.session_state["palabra_actual"]
    st.rerun()


# ---------- Pantalla: dictado (entrenar el oído) ----------
def pantalla_dictado():
    # Escogemos una frase y la mantenemos hasta que pidas otra.
    if "dictado_id" not in st.session_state:
        palabra = datos.palabra_al_azar()
        if palabra is None:
            st.info("Agrega palabras en **➕ Agregar** para practicar el dictado.")
            return
        st.session_state.dictado_id = palabra["id"]
        st.session_state.dictado_inicio = time.time()
        st.session_state.dictado_resultado = None

    palabra = datos.palabra_por_id(st.session_state.dictado_id)
    frase = palabra["ejemplo"] or palabra["palabra"]  # si tiene ejemplo, dictamos la frase completa

    st.write("Escucha y escribe lo que oyes. Puedes repetir el audio las veces que quieras.")
    with st.container(border=True):
        boton_escuchar(frase)

    if st.session_state.dictado_resultado is None:
        with st.form("dictado"):
            escrito = st.text_input("Lo que escuché", placeholder="Escribe aquí en inglés")
            revisar = st.form_submit_button("✔️ Revisar", type="primary", width="stretch")
        if revisar:
            if not escrito.strip():
                st.error("Escribe lo que escuchaste.")
                return
            puntaje, detalle = logica.comparar_dictado(frase, escrito)
            tiempo = time.time() - st.session_state.dictado_inicio
            datos.registrar_dictado(palabra["id"], puntaje, tiempo)
            st.session_state.dictado_resultado = (puntaje, detalle, escrito)
            st.rerun()
        return

    puntaje, detalle, escrito = st.session_state.dictado_resultado
    acertadas = sum(1 for _, bien in detalle if bien)
    if puntaje == 1:
        st.success(f"🎯 ¡Perfecto! Acertaste las {len(detalle)} palabras.")
    elif puntaje >= logica.DICTADO_APROBADO:
        st.success(f"👏 Muy bien: {acertadas} de {len(detalle)} palabras ({puntaje:.0%}).")
    else:
        st.warning(f"💪 {acertadas} de {len(detalle)} palabras ({puntaje:.0%}). ¡Escúchala otra vez!")

    # La frase original: en rojo las palabras que se te escaparon.
    marcada = " ".join(f"**{p}**" if bien else f":red[**{p}**]" for p, bien in detalle)
    st.markdown(f"**La frase era:** {marcada}")
    st.markdown(f"**Tú escribiste:** {escrito}")
    st.caption(f"Significado: {palabra['significado']}")

    if st.button("➡️ Otra frase", type="primary", width="stretch"):
        del st.session_state["dictado_id"]
        st.rerun()


# ---------- Pantalla 2: agregar una palabra ----------
def pantalla_agregar():
    st.write("Anota aquí lo nuevo que escuches en tus audios.")
    with st.form("nueva_palabra", clear_on_submit=True):
        palabra = st.text_input("Palabra o frase en inglés", placeholder="to figure out")
        significado = st.text_input("Significado en español", placeholder="entender, descifrar")
        ejemplo = st.text_area("Ejemplo (opcional)", placeholder="I can't figure out this problem.")
        guardar = st.form_submit_button("💾 Guardar", type="primary", width="stretch")

    if guardar:
        if not palabra.strip() or not significado.strip():
            st.error("Escribe la palabra y su significado.")
        elif datos.agregar_palabra(palabra.strip(), significado.strip(), ejemplo.strip()):
            st.success(f"Guardada: **{palabra.strip()}**. La repasarás hoy mismo.")
        else:
            st.warning(f"**{palabra.strip()}** ya estaba en tu laboratorio.")


# ---------- Pantalla 3: todas mis palabras ----------
def pantalla_mis_palabras():
    palabras = datos.tabla_palabras()
    if palabras.empty:
        st.info("Todavía no has guardado palabras.")
        return
    total = len(palabras)
    st.write(f"Tienes **{total}** {'palabra' if total == 1 else 'palabras'} en tu laboratorio.")
    tabla = palabras[["palabra", "significado", "nivel", "proximo_repaso"]].rename(
        columns={"palabra": "Palabra", "significado": "Significado",
                 "nivel": "Nivel", "proximo_repaso": "Próximo repaso"}
    )
    st.dataframe(tabla, hide_index=True, width="stretch")
    st.caption(f"Nivel 0 = nueva u olvidada · Nivel {logica.NIVEL_APRENDIDA} o más = aprendida.")


# ---------- Pantalla 4: mi progreso ----------
def pantalla_progreso():
    palabras = datos.tabla_palabras()
    repasos = datos.tabla_repasos()

    if repasos.empty:
        st.info("Cuando hagas tus primeros repasos, aquí verás tu progreso.")
        return

    repasos["dia"] = pd.to_datetime(repasos["fecha_hora"].str[:10])
    dias_con_estudio = set(repasos["dia"].dt.date)
    # Separamos los ejercicios: la memoria (repasar) y el oído (dictado) se miden distinto.
    memoria = repasos[repasos["tipo_ejercicio"] == "repaso"]
    dictados = repasos[repasos["tipo_ejercicio"] == "dictado"]

    # Contenedor horizontal: en el celular las métricas quedan de a dos por fila.
    with st.container(horizontal=True):
        st.metric("📚 Guardadas", len(palabras), border=True)
        st.metric("🧠 Aprendidas", int((palabras["nivel"] >= logica.NIVEL_APRENDIDA).sum()), border=True)
        st.metric("✅ Memoria", f"{memoria['recordada'].mean():.0%}" if len(memoria) else "—", border=True)
        st.metric("🎧 Dictado", f"{dictados['puntaje'].mean():.0%}" if len(dictados) else "—", border=True)
        st.metric("🔥 Días seguidos", logica.calcular_racha(dias_con_estudio, datos.hoy()), border=True)

    st.subheader("Repasos por día")
    por_dia = (
        repasos.groupby("dia")
        .agg(repasos=("id", "count"), aciertos=("recordada", "mean"))
        .reset_index()
    )
    por_dia["fecha"] = por_dia["dia"].dt.strftime("%d/%m")
    grafico = (
        alt.Chart(por_dia)
        .mark_bar(color=AZUL_MEDIO, cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=28)
        .encode(
            x=alt.X("fecha:O", title=None, sort=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("repasos:Q", title="Repasos", axis=alt.Axis(tickMinStep=1, format="d")),
            tooltip=[
                alt.Tooltip("fecha:O", title="Día"),
                alt.Tooltip("repasos:Q", title="Repasos"),
                alt.Tooltip("aciertos:Q", title="Aciertos", format=".0%"),
            ],
        )
        .properties(height=240)
    )
    st.altair_chart(grafico, width="stretch")

    st.caption(f"Tus datos se guardan: **{datos.DONDE_SE_GUARDA}**")

    st.subheader("Exportar mis datos")
    st.write("Copia de todos tus repasos para subir a GitHub. No incluye datos personales.")
    st.download_button(
        "⬇️ Descargar CSV",
        repasos.drop(columns="dia").to_csv(index=False).encode("utf-8"),
        file_name=f"english_lab_repasos_{datos.hoy().isoformat()}.csv",
        mime="text/csv",
        width="stretch",
    )


def pedir_clave() -> bool:
    """En internet, la app pide una clave para que solo tú veas tus datos.

    La clave se guarda como secreto (APP_PASSWORD) en el servicio de publicación, nunca en el código.
    En el PC esa variable no existe, así que la app abre directo.
    """
    clave = os.environ.get("APP_PASSWORD")
    if not clave and datos.EN_LA_NUBE:
        # En internet, sin clave cualquiera con el link vería tus datos: no abrimos.
        st.error("⚠️ Falta el secreto APP_PASSWORD. Agrégalo en Streamlit: Settings → Secrets.")
        return False
    if not clave or st.session_state.get("autorizada"):
        return True
    with st.form("clave"):
        intento = st.text_input("Clave", type="password")
        if st.form_submit_button("Entrar", type="primary", width="stretch"):
            # compare_digest compara de forma segura, sin dar pistas sobre la clave
            if hmac.compare_digest(intento.encode(), clave.encode()):
                st.session_state.autorizada = True
                st.rerun()
            st.error("Clave incorrecta.")
    return False


# ---------- Encabezado y menú ----------
st.title("💙 English Lab")
st.caption("Practice. Measure. Predict. Improve.")

if not pedir_clave():
    st.stop()  # sin la clave correcta, la app no muestra nada más

secciones = {
    "🧠 Repasar": pantalla_repasar,
    "🎧 Dictado": pantalla_dictado,
    "➕ Agregar": pantalla_agregar,
    "📚 Palabras": pantalla_mis_palabras,
    "📊 Progreso": pantalla_progreso,
}
eleccion = st.segmented_control(
    "Sección", list(secciones), default="🧠 Repasar", label_visibility="collapsed"
)
secciones[eleccion or "🧠 Repasar"]()

st.divider()
st.caption("*What gets measured, gets improved.*")
