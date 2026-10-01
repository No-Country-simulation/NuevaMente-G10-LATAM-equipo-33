import sys
from pathlib import Path
import streamlit as st

RAIZ_DIR = Path(__file__).resolve().parent.parent
if str(RAIZ_DIR) not in sys.path:
    sys.path.append(str(RAIZ_DIR))

from theme import PALETTE

FORMATOS = [
    "Flashcards de Memorización",
    "Quiz Interactivo con Justificaciones",
    "Guía Práctica Paso a Paso (Tutorial)",
    "Resumen Ejecutivo (TL;DR)",
    "Guion de Video / Podcast Curado",
]


PERFILES = ["Perfil 1", "Perfil 2"]
NIVELES_DETALLE = ["Básico", "Intermedio", "Avanzado"]


def volver_al_paso_1():
    st.session_state["paso_actual"] = 1


def generar():
    # Guardar los parámetros en session_state para Backend
    st.session_state["solicitud"] = {
        "documento_titulo": st.session_state.get("documento_titulo", ""),
        "documento_contenido": st.session_state.get("documento_contenido", ""),
        "perfil_destinatario": st.session_state["param_perfil"],
        "formato_salida": st.session_state["param_formato"],
        "nicho_sector": st.session_state["param_nicho"].strip(),
        "nivel_detalle": st.session_state["param_nivel"],
    }
   
def render():
    col_izq, col_centro, col_der = st.columns([0.8, 3.4, 0.8])

    with col_centro:
        with st.container(border=True):
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
                    <span style="color: {PALETTE.get('primary', '#0094F0')}; font-weight: bold; font-size: 13px;">PASO 2 DE 3</span>
                    <span style="color: {PALETTE.get('text', '#FFFFFF')}; opacity: 0.5; font-size: 12px;">• Parámetros</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"<h3 style='text-align: center; color: {PALETTE.get('accent', '#F59F0A')};'>"
                "Personaliza tu material</h3>",
                unsafe_allow_html=True,
            )

            titulo = st.session_state.get("documento_titulo")
            if titulo:
                st.caption(f"📄 Documento: {titulo}")

            st.selectbox("¿Para quién es el contenido?", PERFILES, key="param_perfil")
            st.selectbox("Formato de salida", FORMATOS, key="param_formato")
            st.text_input("Nicho o sector", key="param_nicho",
                          placeholder="Ej.: salud, educación, finanzas")
            st.selectbox("Nivel de detalle", NIVELES_DETALLE, key="param_nivel")

            col_a, col_b = st.columns(2)
            with col_a:
                st.button("← Volver", on_click=volver_al_paso_1, use_container_width=True)
            with col_b:
                st.button("Generar", type="primary", on_click=generar, use_container_width=True)


if __name__ == "__main__":
    render()