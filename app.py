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
import streamlit.components.v1 as components

import datos
import logica

AZUL_MEDIO = "#3B82F6"

st.set_page_config(page_title="English Lab", page_icon="💙", layout="centered")


def boton_escuchar(texto: str):
    """Botones para oír un texto en inglés con la voz del navegador (gratis, funciona en PC y celular)."""
    texto_js = json.dumps(texto)  # convierte el texto a un formato seguro para JavaScript
    components.html(
        f"""
        <style>
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
    st.write(f"Tienes **{len(palabras)}** palabras en tu laboratorio.")
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

    # Contenedor horizontal: en el celular las métricas quedan de a dos por fila.
    with st.container(horizontal=True):
        st.metric("📚 Guardadas", len(palabras), border=True)
        st.metric("🧠 Aprendidas", int((palabras["nivel"] >= logica.NIVEL_APRENDIDA).sum()), border=True)
        st.metric("✅ Aciertos", f"{repasos['recordada'].mean():.0%}", border=True)
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
