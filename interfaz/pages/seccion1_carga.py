import sys
from pathlib import Path
import streamlit as st

# Permite encontrar el archivo theme.py que está en la carpeta raíz (interfaz/)
RAIZ_DIR = Path(__file__).resolve().parent.parent
if str(RAIZ_DIR) not in sys.path:
    sys.path.append(str(RAIZ_DIR))

from theme import PALETTE, inject_custom_css


# ---- FUNCIÓN CALLBACK ("Continue") ----
def procesar_y_continuar():
    if 'archivo_temporal' in st.session_state and st.session_state['archivo_temporal'] is not None:
        archivo = st.session_state['archivo_temporal']
        contenido_bytes = archivo.getvalue()

        #Extracción del contenido previamente subido
        try:
            texto_extraido = contenido_bytes.decode("utf-8")
        except Exception:
            texto_extraido = f"Archivo binario ({archivo.type}) subido correctamente."

        # Guardamos datos en session_state para Backend
        st.session_state['documento_titulo'] = archivo.name
        st.session_state['documento_contenido'] = texto_extraido
        st.session_state['archivo_bytes'] = contenido_bytes
        
        # Avanza a la pantalla 2
        st.session_state['paso_actual'] = 2

def render():
    inject_custom_css()

    st.markdown(f"""
        <style>
        /* 1. Limita el ancho centrado */
        div[data-testid="stColumn"]:nth-of-type(2) {{
            max-width: 540px !important;
            margin: 0 auto;
        }}

        /* 2. RECUADRO CONTENEDOR GENERAL DE STREAMLIT */
        div[data-testid="stColumn"]:nth-of-type(2) [data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: #F0F0F0 !important;
            border: 2px solid #F59F0A !important;
            border-radius: 16px !important;
            padding: 24px !important;
        }}

        /* Evita que sub-contenedores o columnas hereden algun borde */
        div[data-testid="stColumn"]:nth-of-type(2) [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlockBorderWrapper"] {{
            border: none !important;
            background-color: transparent !important;
            padding: 0 !important;
        }}

        /* 3. CAJA INTERNA DE SUBIDA DE ARCHIVOS (Dropzone) */
        [data-testid="stFileUploaderDropzone"] {{
            padding: 30px 20px !important;
            min-height: 200px !important;
            background-color: #0094F0 !important;
            border: 2px dashed #0094F0 !important;
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
        
        /* Oculta la etiqueta redundante que aparece */
        [data-testid="stFileUploader"] label {{
            display: none !important;
        }}

        /* Centrado del Badge */
        .badge-wrapper {{
            display: flex;
            justify-content: center;
            margin: 12px 0;
        }}

        /* 4. ESTILOS DEL BOTÓN "CONTINUE" */
        div[data-testid="stButton"] > button:disabled {{
            background-color: #10B77F !important;
            color: #070B22 !important;
            border: 1px solid #10B77F !important;
        }}

        div[data-testid="stButton"] > button {{
            background-color: #10B77F!important;
            color: #FFFFFF !important;
            border-radius: 8px !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    # Centrado de pantalla mediante columnas
    col_izq, col_centro, col_der = st.columns([0.8, 3.4, 0.8])

    with col_centro:
        with st.container(border=True):

            # Header superior (Paso / Upload) alineado con más espacio abajo
            st.markdown(
                f"""
                <div style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 32px;">
                    <span style="color: #0094F0; font-weight: bold; font-size: 13px;">STEP 1 / 3</span>
                    <span style="color: {PALETTE['text']}; opacity: 0.6; font-size: 12px;">Upload</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            # Etiqueta / Badge centrada
            st.markdown(
                "<div class='badge-wrapper' style='margin-bottom: 20px;'>"
                "<span class='nm-pill-accent'>Paso 1 · Añade tu material</span>"
                "</div>", 
                unsafe_allow_html=True
            )

            # Título y Descripción centrados
            st.markdown(
                "<h3 style='text-align: center; color: #F59F0A; margin-bottom: 2px; max-width: 240px; margin-left: auto; margin-right: auto; display: block;'>"
                "Sube un documento para comenzar"
                "</h3>", 
                unsafe_allow_html=True
            )
            
            st.markdown(
                f"<p style='text-align: center; color: {PALETTE['text']}; opacity: 0.7; font-size: 14px; margin-top: 0px; margin-bottom: 24px; max-width: 300px; margin-left: auto; margin-right: auto;'>"
                "Sube tus lecturas, apuntes o materiales de estudio. "
                "NuevaMente lo transforma en tarjetas de estudio y cuestionarios personalizados para que estudies de forma más inteligente."
                "</p>",
                unsafe_allow_html=True
            )
            
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            # Cargador de archivos con "key" conectada al Callback
            archivo = st.file_uploader(
                label="Cargador de archivos",
                label_visibility="collapsed",
                type=["pdf", "docx", "txt", "pptx", "md"],
                key="archivo_temporal"
            )
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            # Botón Continuar activado con el Callback
            boton_continuar = st.button(
                "Continue", 
                use_container_width=True, 
                disabled=(archivo is None),
                on_click=procesar_y_continuar
            )

            # Pie interno
            st.markdown(f"<p style='text-align: center; font-size: 12px; color: {PALETTE['text']}; opacity: 0.5; margin-top: 6px;'>Sube un documento para continuar.</p>", unsafe_allow_html=True)

    # Pie de página externo
    st.markdown(f"<br><p style='text-align: center; font-size: 12px; color: {PALETTE['text']}; opacity: 0.5;'><b>NuevaMente</b> · Convierte cualquier documento en una sesión de estudio eficiente.</p>", unsafe_allow_html=True)

#Para asegurar la renderización local
if __name__ == "__main__":
    render()