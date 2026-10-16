import sys
from pathlib import Path
import streamlit as st
import json

RAIZ_DIR = Path(__file__).resolve().parent.parent
if str(RAIZ_DIR) not in sys.path:
    sys.path.append(str(RAIZ_DIR))

from theme import PALETTE
from constants import PERFILES, FORMATOS, NIVELES

# Fallback si constants no tiene alguna lista
if not PERFILES:
    PERFILES = [
        "Principiante / Transición de Carrera",
        "Desarrollador Junior / Semi Senior",
        "Líder Técnico / Arquitecto",
        "Gestor / Ejecutivo (No Técnico)",
    ]

FORMATOS_SELECCION = [
    "Flashcards de Memorización",
    "Quiz Interactivo con Justificaciones",
]

NIVELES_DETALLE = ["Básico", "Intermedio", "Avanzado"]


def volver_al_paso_1():
    st.session_state["paso_actual"] = 1


def _crear_resultado_simulado(solicitud: dict) -> dict:
    """Genera datos de prueba acordes a lo que espera la Pantalla 3."""
    titulo_doc = solicitud.get("documento_titulo") or "Documento Técnico"
    formato = solicitud.get("formato_salida")
    perfil = solicitud.get("perfil_destinatario")
    nicho = solicitud.get("nicho_sector") or "General"

    if formato == "Flashcards de Memorización":
        items = [
            {
                "frente": "¿Cuál es el concepto central abordado en el material?",
                "dorso": f"El procesamiento estructurado y adaptación de contenidos en el sector {nicho}.",
                "pista_didactica": "Revisa los objetivos principales del documento."
            },
            {
                "frente": "¿Cómo influye el perfil del destinatario en la adaptación?",
                "dorso": f"Permite modular la complejidad técnica hacia un enfoque para {perfil}.",
                "pista_didactica": "Piensa en el nivel de abstracción necesario."
            },
            {
                "frente": "¿Qué ventaja ofrece el formato Flashcards?",
                "dorso": "Facilita la retención espaciada y el repaso ágil de conceptos clave.",
                "pista_didactica": "Técnica de memorización activa."
            }
        ]
    else:  # Quiz Interactivo con Justificaciones
        items = [
            {
                "pregunta": f"Respecto a {titulo_doc}, ¿cuál es el objetivo primordial?",
                "opciones": [
                    "Adaptar material educativo a las necesidades del estudiante",
                    "Eliminar la necesidad de lectura técnica",
                    "Traducir código fuente sin análisis previo",
                    "Almacenar documentos sin procesar"
                ],
                "respuesta_correcta": "Adaptar material educativo a las necesidades del estudiante",
                "justificacion": f"El sistema busca optimizar la comprensión para {perfil}."
            },
            {
                "pregunta": "¿Por qué es importante medir el anclaje a la fuente?",
                "opciones": [
                    "Para asegurar que no existan alucinaciones y el contenido sea fiel",
                    "Para aumentar la longitud del texto resultante",
                    "Para formatear únicamente en HTML",
                    "Para omitir la etapa de evaluación"
                ],
                "respuesta_correcta": "Para asegurar que no existan alucinaciones y el contenido sea fiel",
                "justificacion": "El anclaje garantiza que la adaptación se base estrictamente en el documento original."
            }
        ]

    return {
        "status": "exito",
        "metadatos": {
            "perfil_aplicado": perfil,
            "formato_generado": formato,
            "tiempo_estimado_estudio_minutos": 8,
            "conceptos_clave": ["Adaptación Didáctica", nicho, "Evaluación RAG"],
        },
        "contenido_adaptado": {
            "titulo": f"Sesión de Estudio: {titulo_doc}",
            "introduccion_contextualizada": (
                f"Material adaptado para el perfil '{perfil}' con enfoque en '{nicho}'."
            ),
            "items": items,
        },
        "evaluacion_calidad": {
            "anclaje_fuente_score": 0.95,
            "claridad_pedagogica": "Alta",
            "observaciones": "Generación adaptada correctamente al formato solicitado."
        },
        "almacenamiento_oci": {
            "bucket": "nuevamente-storage",
            "objeto_id": f"adaptaciones/{titulo_doc}.json",
            "status_upload": "completado"
        }
    }


def generar():
    solicitud = {
        "documento_titulo": st.session_state.get("documento_titulo", "Documento"),
        "documento_contenido": st.session_state.get("documento_contenido", ""),
        "perfil_destinatario": st.session_state.get("param_perfil", "General"),
        "formato_salida": st.session_state.get("param_formato", FORMATOS_SELECCION[0]),
        "nicho_sector": st.session_state.get("param_nicho", "").strip() or "General",
        "nivel_detalle": st.session_state.get("param_nivel", "Intermedio"),
    }
    st.session_state["solicitud"] = solicitud

    # 1. Intento de llamada al backend si requests está disponible y el servidor activo
    resultado = None
    try:
        import requests
        resp = requests.post(
            "http://localhost:8000/api/v1/adapt",
            json=solicitud,
            timeout=5
        )
        if resp.status_code == 200:
            resultado = resp.json()
    except Exception:
        resultado = None

    # 2. Si no hay backend levantado, usa el generador local de prueba
    if not resultado or resultado.get("status") != "exito":
        resultado = _crear_resultado_simulado(solicitud)

    st.session_state["resultado"] = resultado
    st.session_state["paso_actual"] = 3


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
            st.selectbox("Formato de salida", FORMATOS_SELECCION, key="param_formato")
            st.text_input(
                "Nicho o sector",
                key="param_nicho",
                placeholder="Ej.: salud, educación, finanzas",
            )
            st.selectbox("Nivel de detalle", NIVELES_DETALLE, key="param_nivel")

            col_a, col_b = st.columns(2)
            with col_a:
                st.button("← Volver", on_click=volver_al_paso_1, use_container_width=True)
            with col_b:
                st.button("Generar", type="primary", on_click=generar, use_container_width=True)


if __name__ == "__main__":
    render()
