"""
NuevaMente - Frontend (Streamlit) — versión de una sola página

Las 3 secciones (carga, parámetros, resultado) viven en archivos separados
dentro de pages/, pero se muestran todas en la misma página, una debajo de
otra, para que el usuario no tenga que "navegar" entre pantallas.

    - pages/seccion1_carga.py       -> Beatriz
    - pages/seccion2_parametros.py  -> Alessandra
    - pages/seccion3_resultados.py  -> Gisell
    - theme.py / constants.py / backend.py -> compartidos, avisar antes de tocar
"""


import streamlit as st

from pages import seccion1_carga, seccion2_parametros, seccion3_resultados
from theme import PALETTE, inject_custom_css

st.set_page_config(page_title="NuevaMente", page_icon="🎓", layout="centered")
inject_custom_css()

# ---------------------------------------------------------------------------
# Estado de sesión (Manejo de pasos y datos)
# ---------------------------------------------------------------------------

if "paso_actual" not in st.session_state:
    st.session_state["paso_actual"] = 1

if "solicitud" not in st.session_state:
    st.session_state.solicitud = {}

if "resultado" not in st.session_state:
    st.session_state.resultado = None
if "paso_actual" not in st.session_state:
    st.session_state["paso_actual"] = 1

# ---------------------------------------------------------------------------
# Encabezado (con espacio reservado para el logo)
# ---------------------------------------------------------------------------

col_logo, col_titulo = st.columns([1, 5])

with col_logo:
    st.markdown(
        """
        <div style="
            width:64px; height:64px;
            border:2px dashed rgba(240,240,240,0.35);
            border-radius:12px;
            display:flex; align-items:center; justify-content:center;
            text-align:center; font-size:10px; line-height:1.1;
            color:rgba(240,240,240,0.55);
        ">
            LOGO<br>AQUÍ
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_titulo:
    st.title("NuevaMente")
    st.caption("Sistema Inteligente de Adaptación y Generación de Contenido Educativo")

st.divider()

# ---------------------------------------------------------------------------
<<<<<<< Updated upstream
# Control de navegación entre pasos
=======
# Control de navegación por pasos
>>>>>>> Stashed changes
# ---------------------------------------------------------------------------

paso = st.session_state["paso_actual"]

if paso == 1:
    try:
        seccion1_carga.render()
    except (AttributeError, TypeError):
        st.info("La vista 'Carga de Datos' aún está en desarrollo por el equipo.")

elif paso == 2:
    try:
        seccion2_parametros.render()
    except (AttributeError, TypeError):
        st.info("La vista 'Parámetros' aún está en desarrollo por el equipo.")

elif paso == 3:
    try:
        seccion3_resultados.render()
    except (AttributeError, TypeError):
        st.info("La vista 'Resultados' aún está en desarrollo por el equipo.")