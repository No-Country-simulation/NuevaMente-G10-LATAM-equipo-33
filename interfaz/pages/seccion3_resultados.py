"""Sección 3 — Resultado adaptado interactivo y moderno.

Responsable: Gisell — cubre los 5 formatos completos con tarjetas
estilizadas, botones dinámicos y navegación fluido.
"""

import sys
from pathlib import Path
import streamlit as st

RAIZ_DIR = Path(__file__).resolve().parent.parent
if str(RAIZ_DIR) not in sys.path:
    sys.path.append(str(RAIZ_DIR))

from theme import PALETTE, render_donut

LETRAS = ["A", "B", "C", "D", "E", "F"]


def reiniciar_proceso():
    """Limpia el estado de la sesión para volver al Paso 1."""
    st.session_state["paso_actual"] = 1
    st.session_state["resultado"] = None
    st.session_state["solicitud"] = {}
    st.session_state["quiz_respuestas"] = {}
    st.session_state["flash_idx"] = 0
    st.rerun()


def render() -> None:
    resultado = st.session_state.get("resultado")

    # Centrado de pantalla idéntico al Paso 1 y Paso 2
    col_izq, col_centro, col_der = st.columns([0.6, 3.8, 0.6])

    with col_centro:
        if not resultado:
            with st.container(border=True):
                st.warning("No hay un resultado disponible para mostrar.")
                if st.button("← Cargar un documento (Paso 1)", use_container_width=True):
                    reiniciar_proceso()
            return

        with st.container(border=True):

            # Header superior compacto
            col_h1, col_h2 = st.columns([3, 1])
            with col_h1:
                st.markdown(
                    f"""
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                        <span style="color: {PALETTE.get('primary', '#0094F0')}; font-weight: bold; font-size: 13px;">PASO 3 DE 3</span>
                        <span style="color: {PALETTE.get('text', '#FFFFFF')}; opacity: 0.5; font-size: 12px;">• Resultado Interactivo</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_h2:
                if st.button("↺ Inicio", key="btn_reiniciar_top", use_container_width=True):
                    reiniciar_proceso()

            # Control de error de backend
            if isinstance(resultado, dict) and resultado.get("status") != "exito":
                st.error("No se pudo generar el contenido. Intenta de nuevo.")
                if st.button("← Regresar al Paso 2", use_container_width=True):
                    st.session_state["paso_actual"] = 2
                    st.rerun()
                return

            meta = resultado.get("metadatos", {})
            contenido = resultado.get("contenido_adaptado", {})
            calidad = resultado.get("evaluacion_calidad", {})
            oci = resultado.get("almacenamiento_oci", {})

            titulo = contenido.get("titulo", "Resultado de estudio")
            intro = contenido.get("introduccion_contextualizada", "")

            # Título principal estilizado
            st.markdown(
                f"""
                <div style="text-align: center; margin-top: 10px; margin-bottom: 12px;">
                    <h2 style="color: {PALETTE.get('accent', '#F59F0A')}; font-size: 26px; font-weight: 800; margin-bottom: 6px;">
                        {titulo}
                    </h2>
                    <p style="color: {PALETTE.get('text', '#FFFFFF')}; opacity: 0.8; font-size: 14px; max-width: 600px; margin: 0 auto;">
                        {intro}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Tarjetas de Métricas Resumen
            st.markdown(
                f"""
                <div style="display: flex; gap: 12px; justify-content: center; margin-bottom: 20px; flex-wrap: wrap;">
                    <div style="background: rgba(255, 255, 255, 0.05); padding: 12px 20px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1); text-align: center; min-width: 140px;">
                        <span style="font-size: 11px; opacity: 0.6; display: block; text-transform: uppercase; font-weight: 600;">Tiempo Est.</span>
                        <span style="font-size: 20px; font-weight: 700; color: #38BDF8;">⏱ {meta.get('tiempo_estimado_estudio_minutos', 0)} min</span>
                    </div>
                    <div style="background: rgba(255, 255, 255, 0.05); padding: 12px 20px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1); text-align: center; min-width: 140px;">
                        <span style="font-size: 11px; opacity: 0.6; display: block; text-transform: uppercase; font-weight: 600;">Anclaje</span>
                        <span style="font-size: 20px; font-weight: 700; color: #4ADE80;">🎯 {calidad.get('anclaje_fuente_score', 0):.2f}</span>
                    </div>
                    <div style="background: rgba(255, 255, 255, 0.05); padding: 12px 20px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1); text-align: center; min-width: 140px;">
                        <span style="font-size: 11px; opacity: 0.6; display: block; text-transform: uppercase; font-weight: 600;">Claridad</span>
                        <span style="font-size: 20px; font-weight: 700; color: #FACC15;">✨ {calidad.get('claridad_pedagogica', 'N/A')}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Conceptos clave (Badges)
            conceptos = meta.get("conceptos_clave", [])
            if conceptos:
                html_badges = "".join([
                    f'<span style="background: rgba(245, 159, 10, 0.15); color: #F59F0A; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; border: 1px solid rgba(245, 159, 10, 0.3);">{c}</span>'
                    for c in conceptos
                ])
                st.markdown(
                    f'<div style="display: flex; justify-content: center; gap: 8px; flex-wrap: wrap; margin-bottom: 24px;">{html_badges}</div>',
                    unsafe_allow_html=True,
                )

            st.divider()

            # Renderizado dinámico según el formato seleccionado
            formato = meta.get("formato_generado", "")
            items = contenido.get("items", [])

            if formato == "Flashcards de Memorización":
                _render_flashcards(items)
            elif formato == "Quiz Interactivo con Justificaciones":
                _render_quiz(items)
            elif formato == "Guía Práctica Paso a Paso (Tutorial)":
                _render_tutorial(items)
            elif formato == "Resumen Ejecutivo (TL;DR)":
                _render_resumen(items)
            elif formato == "Guion de Video / Podcast Curado":
                _render_guion(items)
            else:
                for item in items:
                    st.write(item)

            st.divider()

            # Pie técnico OCI
            if oci:
                st.markdown(
                    f"""
                    <div style="background: rgba(0,0,0,0.2); padding: 8px 14px; border-radius: 8px; text-align: center; font-size: 11px; opacity: 0.6; font-family: monospace;">
                        Guardado en OCI · bucket: <b>{oci.get('bucket', 'N/A')}</b> · id: <b>{oci.get('objeto_id', 'N/A')}</b> · estado: <b>{oci.get('status_upload', 'N/A')}</b>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

            if st.button("← Probar otro formato / Cargar nuevo documento", type="primary", use_container_width=True):
                reiniciar_proceso()

    # Footer global
    st.markdown(
        f"<br><p style='text-align: center; font-size: 12px; color: {PALETTE.get('text', '#FFFFFF')}; opacity: 0.5;'>"
        "<b>NuevaMente</b> · Convierte cualquier documento en una sesión de estudio eficiente."
        "</p>",
        unsafe_allow_html=True,
    )


def _render_flashcards(items: list) -> None:
    """Diseño visual mejorado para tarjetas de estudio."""
    if not items:
        st.info("No hay flashcards para mostrar.")
        return

    total = len(items)
    if "flash_idx" not in st.session_state:
        st.session_state.flash_idx = 0
    idx = min(st.session_state.flash_idx, total - 1)

    # Barra de progreso estilizada
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 12px; font-weight: 600; opacity: 0.7;">PROGRESO DEL MAZO</span>
            <span style="font-size: 12px; font-weight: bold; color: #38BDF8;">Tarjeta {idx + 1} de {total}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress((idx + 1) / total)

    item = items[idx]
    key_reveal = f"flash_reveal_{idx}"
    revelada = st.session_state.get(key_reveal, False)

    # Tarjeta Principal Estilizada
    if not revelada:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border: 2px solid #38BDF8; border-radius: 16px; padding: 32px 24px; text-align: center; min-height: 200px; display: flex; flex-direction: column; justify-content: center; align-items: center; box-shadow: 0 10px 25px rgba(0,0,0,0.3); margin-top: 12px; margin-bottom: 16px;">
                <span style="background: #38BDF8; color: #0F172A; font-weight: 800; font-size: 11px; padding: 4px 12px; border-radius: 12px; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 16px;">TÉRMINO / PREGUNTA</span>
                <h3 style="color: #FFFFFF; font-size: 22px; font-weight: 700; margin: 0; line-height: 1.4;">{item.get('frente', '')}</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🔄 Voltear tarjeta para ver respuesta", key=f"flip_{idx}", use_container_width=True, type="primary"):
            st.session_state[key_reveal] = True
            st.rerun()
    else:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #064E3B 0%, #022C22 100%); border: 2px solid #4ADE80; border-radius: 16px; padding: 32px 24px; text-align: center; min-height: 200px; display: flex; flex-direction: column; justify-content: center; align-items: center; box-shadow: 0 10px 25px rgba(0,0,0,0.3); margin-top: 12px; margin-bottom: 16px;">
                <span style="background: #4ADE80; color: #022C22; font-weight: 800; font-size: 11px; padding: 4px 12px; border-radius: 12px; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 16px;">RESPUESTA / CONCEPTO</span>
                <h3 style="color: #FFFFFF; font-size: 20px; font-weight: 600; margin: 0; line-height: 1.4;">{item.get('dorso', '')}</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if item.get("pista_didactica"):
            st.markdown(
                f"""
                <div style="background: rgba(250, 204, 21, 0.1); border-left: 4px solid #FACC15; padding: 12px 16px; border-radius: 0 8px 8px 0; margin-bottom: 16px;">
                    <span style="color: #FACC15; font-weight: bold; font-size: 13px;">💡 Pista pedagógica:</span>
                    <p style="color: #E2E8F0; font-size: 13px; margin: 4px 0 0 0;">{item['pista_didactica']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if st.button("🔄 Volver al término", key=f"flip_back_{idx}", use_container_width=True):
            st.session_state[key_reveal] = False
            st.rerun()

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # Controles de navegación
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Anterior", disabled=idx == 0, key="flash_prev", use_container_width=True):
            st.session_state.flash_idx = idx - 1
            st.rerun()
    with col2:
        if st.button("Siguiente →", disabled=idx == total - 1, key="flash_next", use_container_width=True):
            st.session_state.flash_idx = idx + 1
            st.rerun()

    if idx == total - 1 and revelada:
        st.markdown(
            """
            <div style="background: rgba(74, 222, 128, 0.15); border: 1px solid #4ADE80; padding: 12px; border-radius: 12px; text-align: center; color: #4ADE80; font-weight: bold; margin-top: 16px;">
                🎉 ¡Mazo completado! Has revisado todas las tarjetas de esta sesión.
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_quiz(items: list) -> None:
    """Diseño interactivo de Quiz."""
    if not items:
        st.info("No hay preguntas para mostrar.")
        return

    if "quiz_respuestas" not in st.session_state:
        st.session_state.quiz_respuestas = {}

    total = len(items)
    for i, item in enumerate(items):
        st.markdown(
            f"""
            <div style="background: rgba(255,255,255,0.03); padding: 16px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); margin-bottom: 12px;">
                <span style="color: #38BDF8; font-weight: bold; font-size: 12px; text-transform: uppercase;">Pregunta {i + 1} de {total}</span>
                <h4 style="margin: 6px 0 12px 0; color: #FFFFFF; font-size: 16px;">{item.get('pregunta', '')}</h4>
            </div>
            """,
            unsafe_allow_html=True,
        )

        opciones = item.get("opciones", [])
        opciones_con_letra = [f"{LETRAS[j]}  ·  {op}" for j, op in enumerate(opciones)]

        if opciones_con_letra:
            respuesta = st.radio("Selecciona tu respuesta:", opciones_con_letra, key=f"quiz_{i}", label_visibility="collapsed")
            idx_elegida = opciones_con_letra.index(respuesta)
            texto_elegido = opciones[idx_elegida]

            if st.button(f"Comprobar Pregunta {i + 1}", key=f"check_{i}", use_container_width=True):
                es_correcta = texto_elegido == item.get("respuesta_correcta")
                st.session_state.quiz_respuestas[i] = es_correcta
                if es_correcta:
                    st.success(f"✔ ¡Correcto! — {item.get('justificacion', '')}")
                else:
                    st.error(f"✘ Incorrecto — {item.get('justificacion', '')}")
        st.divider()

    respondidas = st.session_state.quiz_respuestas
    if len(respondidas) == total and total > 0:
        correctas = sum(respondidas.values())
        pct = round(100 * correctas / total)
        st.markdown(f"### Resultado Final: {correctas} de {total} Aciertos ({pct}%)")
        try:
            render_donut(pct, label="Puntaje")
        except Exception:
            st.progress(pct / 100)

        if st.button("🔄 Intentar Quiz de Nuevo", use_container_width=True):
            st.session_state.quiz_respuestas = {}
            st.rerun()


def _render_tutorial(items: list) -> None:
    if not items:
        st.info("No hay pasos tutoriales para mostrar.")
        return
    for item in items:
        st.markdown(
            f"""
            <div style="display: flex; gap: 16px; background: rgba(255,255,255,0.03); padding: 16px; border-radius: 12px; margin-bottom: 12px; border-left: 4px solid #38BDF8;">
                <div style="background: #38BDF8; color: #0F172A; font-weight: bold; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                    {item.get('paso', '#')}
                </div>
                <div>
                    <h4 style="margin: 0 0 6px 0; color: #FFFFFF;">{item.get('titulo', '')}</h4>
                    <p style="margin: 0; color: #CBD5E1; font-size: 14px;">{item.get('contenido', '')}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_resumen(items: list) -> None:
    if not items:
        st.info("No hay puntos clave para mostrar.")
        return
    for item in items:
        st.markdown(
            f"""
            <div style="background: rgba(255,255,255,0.03); padding: 12px 16px; border-radius: 10px; margin-bottom: 8px; border: 1px solid rgba(255,255,255,0.05); display: flex; align-items: center; gap: 12px;">
                <span style="color: #F59F0A; font-size: 18px;">📌</span>
                <span style="color: #E2E8F0; font-size: 14px;">{item.get('punto', '')}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_guion(items: list) -> None:
    if not items:
        st.info("No hay escenas registradas.")
        return
    for item in items:
        st.markdown(
            f"""
            <div style="background: rgba(255,255,255,0.03); padding: 16px; border-radius: 12px; margin-bottom: 12px; border: 1px solid rgba(255,255,255,0.08);">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #FACC15; font-weight: bold; font-size: 13px;">🎬 ESCENA: {item.get('escena', '').upper()}</span>
                    <span style="color: #94A3B8; font-size: 12px;">⏱ {item.get('duracion_estimada_segundos', 0)} seg</span>
                </div>
                <p style="margin: 0; color: #E2E8F0; font-size: 14px; font-style: italic;">"{item.get('texto', '')}"</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    render()