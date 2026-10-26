"""Cantidad de Flashcards/Quiz: generación real con el límite externo simulado."""
import socket
from unittest.mock import Mock

import pytest

from orquestacion_agentes import main as generation
from shared.contratos import (
    ChunkResultado, ContenidoFlashcards, ContenidoQuiz, ContenidoGenerado,
    ItemFlashcard, ItemQuiz, RespuestaFinal, EvaluacionCalidad,
)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", Mock(side_effect=AssertionError("Red prohibida")))
    monkeypatch.setattr(socket, "create_connection", Mock(side_effect=AssertionError("Red prohibida")))
    monkeypatch.setattr(generation, "_obtener_api_keys", lambda: ["offline-key"])
    monkeypatch.setattr(generation, "_obtener_modelos", lambda: ["offline-model"])
    monkeypatch.setattr(generation, "_clave_actual", 0)


@pytest.mark.parametrize("formato,modelo,item_type", [
    ("Flashcards", ContenidoFlashcards, ItemFlashcard),
    ("Quiz", ContenidoQuiz, ItemQuiz),
])
@pytest.mark.parametrize("cantidad", [0, 1, 10, 13])
def test_limite_y_contrato_de_generacion(monkeypatch, formato, modelo, item_type, cantidad):
    if formato == "Flashcards":
        items = [item_type(frente=f"Frente {i}", dorso=f"Dorso {i}", pista_didactica="Pista")
                 for i in range(cantidad)]
    else:
        items = [item_type(pregunta=f"Pregunta {i}", opciones=["A", "B"],
                           respuesta_correcta="A", justificacion="Fuente") for i in range(cantidad)]
    original = modelo(titulo="Repaso", introduccion_contextualizada="Introducción",
                      items=items, conceptos_clave=["Concepto"], tiempo_estimado_estudio_minutos=5)
    llm = Mock()
    llm.with_structured_output.return_value = llm
    llm.invoke.return_value = original
    monkeypatch.setattr(generation, "_get_llm", Mock(return_value=llm))
    argumentos = dict(documento_titulo="material.txt",
        contexto=[ChunkResultado(texto="Contenido de estudio.", score=1, fuente="material.txt")],
        perfil_destinatario="Principiante", formato_salida=formato,
        nicho_sector="Educación", nivel_detalle="Intermedio")

    if cantidad == 0:
        with pytest.raises(generation.ErrorGeneracion):
            generation.generar_contenido_adaptado(**argumentos)
    else:
        result = generation.generar_contenido_adaptado(**argumentos)
        assert isinstance(result, ContenidoGenerado)
        assert generation.MAX_GENERATED_ITEMS == 10
        assert len(result.items) == min(cantidad, 10)
        assert result.items == [item.model_dump() for item in items[:10]]
        assert all(isinstance(item, dict) for item in result.items)
        assert len(original.items) == cantidad  # No modifica la respuesta recibida.
        assert result.titulo == original.titulo
        assert result.conceptos_clave == original.conceptos_clave
        assert result.tiempo_estimado_estudio_minutos == original.tiempo_estimado_estudio_minutos
        # Conserva serialización y estructura de la respuesta Backend.
        response = RespuestaFinal(status="exito", metadatos={"formato_generado": formato},
            contenido_adaptado=result,
            evaluacion_calidad=EvaluacionCalidad(anclaje_fuente_score=0,
                claridad_pedagogica="No evaluada", observaciones="Prueba offline"))
        assert RespuestaFinal.model_validate_json(response.model_dump_json()) == response

    llm.with_structured_output.assert_called_once_with(modelo)
    llm.invoke.assert_called_once()
    prompt = llm.invoke.call_args.args[0]
    assert "como máximo 10 elementos" in prompt
    assert "Podés generar menos" in prompt
