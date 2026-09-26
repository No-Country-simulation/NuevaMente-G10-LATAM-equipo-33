import sys
from pathlib import Path
import streamlit as st

# Permite encontrar el archivo theme.py que está en la carpeta raíz (interfaz/)
RAIZ_DIR = Path(__file__).resolve().parent.parent
if str(RAIZ_DIR) not in sys.path:
    sys.path.append(str(RAIZ_DIR))

from theme import PALETTE


# ---- FUNCIÓN CALLBACK ("Continue") ----
def procesar_y_continuar():
    if 'archivo_temporal' in st.session_state and st.session_state['archivo_temporal'] is not None:
        archivo = st.session_state['archivo_temporal']
        contenido_bytes = archivo.getvalue()

        # Extracción del contenido previamente subido
        try:
            texto_extraido = contenido_bytes.decode("utf-8")
        except Exception:
            texto_extraido = f"Archivo binario ({archivo.type}) subido correctamente."

        # Guarda datos en session_state para Backend
        st.session_state['documento_titulo'] = archivo.name
        st.session_state['documento_contenido'] = texto_extraido
        st.session_state['archivo_bytes'] = contenido_bytes
        
        # Avanza a la pantalla 2
        st.session_state['paso_actual'] = 2

def render():
    # Centrado de pantalla mediante columnas
    col_izq, col_centro, col_der = st.columns([0.8, 3.4, 0.8])

    with col_centro:
        with st.container(border=True):

            # Header superior (Paso / Upload)
            st.markdown(
                f"""
                <div style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 24px;">
                    <span style="color: {PALETTE.get('primary', '#0094F0')}; font-weight: bold; font-size: 13px;">STEP 1 / 3</span>
                    <span style="color: {PALETTE.get('text', '#FFFFFF')}; opacity: 0.6; font-size: 12px;">Upload</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Etiqueta / Badge centrada
            st.markdown(
                "<div style='text-align: center; margin-bottom: 16px;'>"
                "<span class='nm-pill-accent'>Paso 1 · Añade tu material</span>"
                "</div>", 
                unsafe_allow_html=True
            )

            # Título y Descripción centrados y limpios (usando PALETTE de theme.py)
            st.markdown(
                f"<h3 style='text-align: center; color: {PALETTE.get('accent', '#F59F0A')}; margin-bottom: 8px;'>"
                "Sube un documento para comenzar"
                "</h3>", 
                unsafe_allow_html=True
            )
            
            st.markdown(
                f"<p style='text-align: center; color: {PALETTE.get('text', '#FFFFFF')}; opacity: 0.7; font-size: 14px; margin-bottom: 24px;'>"
                "Sube tus lecturas, apuntes o materiales de estudio. "
                "NuevaMente lo transforma en tarjetas de estudio y cuestionarios personalizados para que estudies de forma más inteligente."
                "</p>",
                unsafe_allow_html=True
            )

            # Cargador de archivos con "key" conectada al Callback
            archivo = st.file_uploader(
                label="Cargador de archivos",
                label_visibility="collapsed",
                type=["pdf", "docx", "txt", "pptx", "md"],
                key="archivo_temporal"
            )
            
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

            # Botón Continuar activado con el Callback
            st.button(
                "Continue", 
                use_container_width=True, 
                disabled=(archivo is None),
                on_click=procesar_y_continuar
            )

            # Pie interno
            st.markdown(f"<p style='text-align: center; font-size: 12px; color: {PALETTE.get('text', '#FFFFFF')}; opacity: 0.5; margin-top: 8px;'>Sube un documento para continuar.</p>", unsafe_allow_html=True)

    # Pie de página externo
    st.markdown(f"<br><p style='text-align: center; font-size: 12px; color: {PALETTE.get('text', '#FFFFFF')}; opacity: 0.5;'><b>NuevaMente</b> · Convierte cualquier documento en una sesión de estudio eficiente.</p>", unsafe_allow_html=True)

# Para asegurar la renderización local
if __name__ == "__main__":
    render()