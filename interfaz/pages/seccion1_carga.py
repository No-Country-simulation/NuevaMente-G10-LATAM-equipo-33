import sys
from pathlib import Path
import streamlit as st

# Permite encontrar el archivo theme.py que está en la carpeta raíz (interfaz/)
RAIZ_DIR = Path(__file__).resolve().parent.parent
if str(RAIZ_DIR) not in sys.path:
    sys.path.append(str(RAIZ_DIR))

from theme import PALETTE

def render():
    # CSS para la estructura, márgenes y proporciones adaptados al tema
    st.markdown(f"""
        <style>
        /* 1. Limita el ancho de la tarjeta */
        div[data-testid="stColumn"]:nth-of-type(2) {{
            max-width: 540px !important;
            margin: 0 auto;
        }}

        /* 2. Contenedor principal: le da padding interno */
        [data-testid="stVerticalBlock"] > div:has(div.tarjeta-contenedor) {{
            padding: 10px;
        }}

        .tarjeta-contenedor {{
            padding: 30px 25px !important;
        }}

        /* 3. Área de subida de archivos (Dropzone) adaptada a la paleta */
        [data-testid="stFileUploaderDropzone"] {{
            padding: 30px 20px !important;
            min-height: 200px !important;
            border: 2px dashed rgba(240, 240, 240, 0.15) !important;
            background-color: rgba(240, 240, 240, 0.02) !important;
            border-radius: 12px !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }}

        [data-testid="stFileUploaderDropzone"] > div {{
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            gap: 8px !important;
        }}

        /* Oculta la etiqueta redundante sobre el cargador */
        [data-testid="stFileUploader"] label {{
            display: none !important;
        }}

        /* Centrado de la etiqueta Badge */
        .badge-wrapper {{
            display: flex;
            justify-content: center;
            margin: 12px 0;
        }}
        </style>
    """, unsafe_allow_html=True)

    # Centrado de pantalla mediante columnas
    col_izq, col_centro, col_der = st.columns([0.8, 3.4, 0.8])

    with col_centro:
        # Contenedor de la tarjeta
        with st.container(border=True):
            st.markdown('<div class="tarjeta-contenedor">', unsafe_allow_html=True)

            # Header superior (Paso / Upload) usando el color primary
            col_paso, col_tipo = st.columns([1, 1])
            with col_paso:
                st.markdown(f"<span style='color: {PALETTE['primary']}; font-weight: bold; font-size: 13px;'>STEP 1 / 3</span>", unsafe_allow_html=True)
            with col_tipo:
                st.markdown(f"<div style='text-align: right; color: {PALETTE['text']}; opacity: 0.6; font-size: 12px;'>Upload</div>", unsafe_allow_html=True)

            # Etiqueta / Badge centrada con estilo oficial
            st.markdown(
                "<div class='badge-wrapper'>"
                "<span class='nm-pill-accent'>Paso 1 · Añade tu material</span>"
                "</div>", 
                unsafe_allow_html=True
            )

            # Título y Descripción centrados con la paleta
            st.markdown(f"<h3 style='text-align: center; color: {PALETTE['text']}; margin-bottom: 8px;'>Sube tu documento para comenzar.</h3>", unsafe_allow_html=True)
            st.markdown(
                f"<p style='text-align: center; color: {PALETTE['text']}; opacity: 0.7; font-size: 14px;'>"
                "Sube tus lecturas, apuntes o materiales de estudio. "
                "NuevaMente lo transforma en tarjetas de estudio y cuestionarios personalizados para que estudies de forma más inteligente."
                "</p>",
                unsafe_allow_html=True
            )
            # Espaciador vertical
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            # Cargador de archivos
            archivo = st.file_uploader(
                label="",
                type=["pdf", "docx", "txt", "pptx", "md"]
            )

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            # Botón
            boton_continuar = st.button("Continue", use_container_width=True, disabled=(archivo is None))

            # Pie interno
            st.markdown(f"<p style='text-align: center; font-size: 12px; color: {PALETTE['text']}; opacity: 0.5; margin-top: 6px;'>Sube un documento para continuar.</p>", unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

    # Pie de página externo
    st.markdown(f"<br><p style='text-align: center; font-size: 12px; color: {PALETTE['text']}; opacity: 0.5;'><b>NuevaMente</b> · Convierte cualquier documento en una sesión de estudio eficiente.</p>", unsafe_allow_html=True)


if __name__ == "__main__":
    render()
