import streamlit as st

st.set_page_config(layout="wide")

# CSS para la estructura, márgenes y proporciones
st.markdown("""
    <style>
    /* 1. Limita el ancho de la tarjeta */
    div[data-testid="stColumn"]:nth-of-type(2) {
        max-width: 540px !important;
        margin: 0 auto;
    }

    /* 2. Contenedor principal: le da padding interno */
    [data-testid="stVerticalBlock"] > div:has(div.tarjeta-contenedor) {
        padding: 10px;
    }

    .tarjeta-contenedor {
        padding: 40px 30px !important;
    }

    /* 3. Área de subida de archivos: altura y centrado en columna */
    [data-testid="stFileUploaderDropzone"] {
        padding: 40px 20px !important; /* Más alto verticalmente */
        min-height: 220px !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }

    [data-testid="stFileUploaderDropzone"] > div {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        gap: 8px !important;
    }

    /* Oculta la etiqueta redundante sobre el cargador */
    [data-testid="stFileUploader"] label {
        display: none !important;
    }

    /* Centrado de la etiqueta Badge */
    .badge-wrapper {
        display: flex;
        justify-content: center;
        margin: 12px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Centrado de pantalla mediante columnas
col_izq, col_centro, col_der = st.columns([0.8, 3.4, 0.8])

with col_centro:
    # Contenedor de la tarjeta
    with st.container(border=True):
        st.markdown('<div class="tarjeta-contenedor">', unsafe_allow_html=True)

        # Header superior (Paso / Upload)
        col_paso, col_tipo = st.columns([1, 1])
        with col_paso:
            st.caption("STEP **1** / 3")
        with col_tipo:
            st.markdown("<div style='text-align: right; color: gray; font-size: 12px;'>Upload</div>", unsafe_allow_html=True)

        # Etiqueta / Badge centrada
        st.markdown(
            "<div class='badge-wrapper'>"
            "<span style='background-color: #E2F163; padding: 4px 12px; border-radius: 12px; font-weight: bold; font-size: 12px; color: black;'>"
            "Paso 1 · Añade tu material"
            "</span></div>", 
            unsafe_allow_html=True
        )

        # Título y Descripción centrados
        st.markdown("<h3 style='text-align: center; margin-bottom: 8px;'>Sube tu documento para comenzar.</h3>", unsafe_allow_html=True)
        st.markdown(
            "<p style='text-align: center; color: gray; font-size: 14px;'>"
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
        st.markdown("<p style='text-align: center; font-size: 12px; color: gray; margin-top: 6px;'>Sube un documento para continuar.</p>", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

# Pie de página externo
st.markdown("<br><p style='text-align: center; font-size: 12px; color: gray;'><b>NuevaMente</b> · Convierte cualquier documento en una sesión de estudio eficiente.</p>", unsafe_allow_html=True)