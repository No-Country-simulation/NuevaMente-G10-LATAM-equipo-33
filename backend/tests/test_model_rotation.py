"""Wrappers reales, runnables falsos y SDK interceptado. Ninguna llamada remota."""
import json
import socket
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest
from langchain_core.exceptions import OutputParserException
from pydantic import ValidationError

from orquestacion_agentes import main as generation
from evaluacion.services import evaluador as evaluation
from evaluacion.schemas.juez import ResultadoJuez, VeredictoItem
from shared.contratos import ChunkResultado, ContenidoQuiz, ItemQuiz, ContenidoGenerado
from shared.gemini_policy import classify_model_failure, invoke_models

KEYS = ["key-a-SECRET", "key-b-SECRET"]
MODELS = ["primary", "backup"]
REAL_GET = {generation: generation._get_llm, evaluation: evaluation._get_llm}


def error(code=None, **attrs):
    result = RuntimeError("SECRET provider message 429 503")
    if code is not None:
        result.status_code = code
    for key, value in attrs.items():
        setattr(result, key, value)
    return result


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", Mock(side_effect=AssertionError("Red prohibida")))
    monkeypatch.setattr(socket, "create_connection", Mock(side_effect=AssertionError("Red prohibida")))
    for key in ("GOOGLE_API_KEY", "GEMINI_API_KEY", "GEMINI_API_KEYS"):
        monkeypatch.setenv(key, "offline-only")
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "false")
    for module in (generation, evaluation):
        monkeypatch.setattr(module, "_clave_actual", 0)
        REAL_GET[module].cache_clear()


@pytest.fixture(params=[generation, evaluation], ids=["generacion", "evaluacion"])
def wrapper(request, monkeypatch):
    module = request.param
    monkeypatch.setattr(module, "_obtener_api_keys", lambda: list(KEYS))
    monkeypatch.setattr(module, "_obtener_modelos", lambda: list(MODELS))
    if module is generation:
        result = ContenidoQuiz(titulo="VCN", introduccion_contextualizada="Repaso",
            items=[ItemQuiz(pregunta="Que es?", opciones=["Red", "Disco"], respuesta_correcta="Red", justificacion="Fuente")],
            conceptos_clave=["VCN"], tiempo_estimado_estudio_minutos=1)
        invoke = lambda: module._invocar_con_rotacion(ContenidoQuiz, "SECRET prompt")
        public_error = module.ErrorGeneracion
    else:
        result = ResultadoJuez(veredictos_items=[VeredictoItem(indice=0, veredicto="respaldado", justificacion="Fuente")],
                               claridad_pedagogica="Alta", observaciones="OK")
        invoke = lambda: module._invocar_con_rotacion("SECRET prompt")
        public_error = module.ErrorEvaluacion
    calls = []
    def configure(outcomes=None, preparation_error=None):
        outcomes = {} if outcomes is None else outcomes
        def get(model, key):
            if preparation_error is not None:
                calls.append((model, key))
                raise preparation_error
            def run(prompt):
                assert prompt == "SECRET prompt"
                calls.append((model, key))
                value = outcomes.get((model, key), result)
                if isinstance(value, list):
                    value = value.pop(0)
                if isinstance(value, Exception):
                    raise value
                return value
            runnable = Mock(invoke=Mock(side_effect=run))
            runnable.with_structured_output.return_value = runnable
            return runnable
        monkeypatch.setattr(module, "_get_llm", get)
    configure()
    return SimpleNamespace(module=module, result=result, invoke=invoke, error=public_error, calls=calls, configure=configure)


def test_429_rota_y_recuerda_ultima_clave(wrapper):
    wrapper.configure({("primary", KEYS[0]): error(429)})
    assert wrapper.invoke() == wrapper.result
    assert wrapper.calls == [("primary", KEYS[0]), ("primary", KEYS[1])]
    assert wrapper.module._clave_actual == 1
    wrapper.invoke()
    assert wrapper.calls[-1] == ("primary", KEYS[1])


def test_agotamiento_modelo_principal_pasa_a_respaldo(wrapper):
    wrapper.configure({("primary", key): error(429) for key in KEYS})
    assert wrapper.invoke() == wrapper.result
    assert wrapper.calls == [("primary", key) for key in KEYS] + [("backup", KEYS[0])]


def test_503_pasa_a_respaldo_sin_probar_otra_clave(wrapper):
    wrapper.configure({("primary", KEYS[0]): error(503)})
    assert wrapper.invoke() == wrapper.result
    assert wrapper.calls == [("primary", KEYS[0]), ("backup", KEYS[0])]


@pytest.mark.parametrize("failure", [error(401), error(400, reason="API_KEY_INVALID"),
    error(400, details={"error": {"details": [{"reason": "API_KEY_EXPIRED"}]}})])
def test_clave_invalida_excluida_tambien_en_respaldo(wrapper, failure):
    wrapper.configure({("primary", KEYS[0]): failure, ("primary", KEYS[1]): error(503)})
    assert wrapper.invoke() == wrapper.result
    assert wrapper.calls == [("primary", KEYS[0]), ("primary", KEYS[1]), ("backup", KEYS[1])]
    wrapper.module._clave_actual = 0
    wrapper.calls.clear()
    wrapper.configure()
    assert wrapper.invoke() == wrapper.result
    assert wrapper.calls == [("primary", KEYS[0])]  # Exclusión no persistente.


@pytest.mark.parametrize("code,count", [(401, 2), (429, 4), (503, 2)])
def test_agotamiento_acotado(wrapper, code, count):
    wrapper.configure({(model, key): error(code) for model in MODELS for key in KEYS})
    with pytest.raises(wrapper.error): wrapper.invoke()
    assert len(wrapper.calls) == count


@pytest.mark.parametrize("failure", [TimeoutError("SECRET"), httpx.ReadTimeout("SECRET"),
    error(408), error(504), error(500), error(502), ConnectionError("SECRET")])
def test_transitorios_un_reintento_por_modelo(wrapper, failure):
    wrapper.configure({("primary", KEYS[0]): failure})
    assert wrapper.invoke() == wrapper.result
    assert wrapper.calls == [("primary", KEYS[0]), ("primary", KEYS[0]), ("backup", KEYS[0])]


def test_presupuesto_transitorio_no_se_reinicia_por_clave(wrapper):
    wrapper.configure({("primary", KEYS[0]): [TimeoutError(), error(429)],
                       ("primary", KEYS[1]): TimeoutError()})
    assert wrapper.invoke() == wrapper.result
    assert wrapper.calls == [("primary", KEYS[0]), ("primary", KEYS[0]),
                             ("primary", KEYS[1]), ("backup", KEYS[0])]


@pytest.mark.parametrize("failure", [error(403, status="UNAVAILABLE"), error(404),
    RuntimeError("429 RESOURCE_EXHAUSTED 503"), OutputParserException("SECRET 503"),
    json.JSONDecodeError("429", "", 0)])
def test_fallos_no_recuperables_no_rotan(wrapper, failure):
    wrapper.configure({("primary", KEYS[0]): failure})
    with pytest.raises(wrapper.error) as caught: wrapper.invoke()
    assert wrapper.calls == [("primary", KEYS[0])]
    assert caught.value.__suppress_context__


@pytest.mark.parametrize("invalid", [None, {}, "SECRET invalid response"])
def test_resultado_sin_contrato_no_rota(wrapper, invalid):
    wrapper.configure({("primary", KEYS[0]): invalid})
    with pytest.raises(wrapper.error, match="validacion"): wrapper.invoke()
    assert len(wrapper.calls) == 1


def test_validacion_pydantic_con_contexto_429_no_rota(wrapper):
    try:
        ContenidoQuiz.model_validate({"titulo": "429 503"})
    except ValidationError as validation:
        failure = validation
    failure.__cause__ = error(429)
    wrapper.configure({("primary", KEYS[0]): failure})
    with pytest.raises(wrapper.error, match="validacion"): wrapper.invoke()
    assert len(wrapper.calls) == 1


def test_preparacion_tambien_clasifica_sin_filtrar(wrapper, caplog):
    wrapper.configure(preparation_error=error(403))
    with pytest.raises(wrapper.error) as caught: wrapper.invoke()
    assert len(wrapper.calls) == 1
    assert "SECRET" not in caplog.text + str(caught.value)


def test_sin_claves_no_prepara_llm(wrapper, monkeypatch):
    monkeypatch.setattr(wrapper.module, "_obtener_api_keys", lambda: [])
    with pytest.raises(wrapper.error): wrapper.invoke()
    assert not wrapper.calls


def test_no_hay_esperas_ni_datos_sensibles(wrapper, monkeypatch, caplog):
    sleep = Mock(side_effect=AssertionError("No debe dormir"))
    monkeypatch.setattr("shared.gemini_policy.time.sleep", sleep)
    wrapper.configure({(model, key): error(429) for model in MODELS for key in KEYS})
    with pytest.raises(wrapper.error) as caught: wrapper.invoke()
    sleep.assert_not_called()
    assert "SECRET" not in caplog.text + str(caught.value)
    assert all(key not in caplog.text for key in KEYS)


@pytest.mark.parametrize("keys_count", [1, 2, 5])
def test_limite_total_m_por_k_mas_uno(keys_count):
    keys = list(range(keys_count))
    calls = []
    counts = {model: 0 for model in MODELS}
    def prepare(model, key):
        def run(prompt):
            calls.append((model, key))
            counts[model] += 1
            if counts[model] == 1: raise TimeoutError()
            raise error(429)
        return SimpleNamespace(invoke=run)
    with pytest.raises(RuntimeError):
        invoke_models(models=MODELS, keys=keys, start_index=0, prepare=prepare,
                      validate=lambda result: None, prompt="", error_type=RuntimeError)
    assert len(calls) == len(MODELS) * (keys_count + 1)


def test_clasificacion_extendida_no_cambia_embeddings():
    from shared.gemini_policy import classify_failure
    assert classify_failure(TimeoutError()).category == "desconocido"
    assert classify_model_failure(TimeoutError()).category == "timeout"
    assert classify_failure(error(500)).category == "no_recuperable"
    assert classify_model_failure(error(500)).category == "servidor_transitorio"


def test_timeout_estructurado_en_causa_prevalece_sobre_wrapper_generico():
    from langchain_core.exceptions import ModelAPIError
    outer = ModelAPIError("SECRET")
    outer.__cause__ = error(status="DEADLINE_EXCEEDED")
    assert classify_model_failure(outer).category == "timeout"


def test_modelos_evaluacion_opcionales_y_respaldo_vacio(monkeypatch):
    monkeypatch.delenv("GEMINI_EVALUATION_MODEL", raising=False)
    monkeypatch.delenv("GEMINI_EVALUATION_MODEL_RESPALDO", raising=False)
    monkeypatch.setenv("GEMINI_MODEL", "general")
    monkeypatch.setenv("GEMINI_MODEL_RESPALDO", "general-backup")
    assert evaluation._obtener_modelos() == ["general", "general-backup"]
    monkeypatch.setenv("GEMINI_EVALUATION_MODEL", "judge")
    assert evaluation._obtener_modelos() == ["judge", "general-backup"]
    monkeypatch.setenv("GEMINI_EVALUATION_MODEL_RESPALDO", "judge-backup")
    assert evaluation._obtener_modelos() == ["judge", "judge-backup"]
    monkeypatch.setenv("GEMINI_EVALUATION_MODEL_RESPALDO", "")
    assert evaluation._obtener_modelos() == ["judge"]
    assert generation._obtener_modelos() == ["general", "general-backup"]


def test_errores_publicos_sin_datos_sensibles(monkeypatch, caplog):
    context = [ChunkResultado(texto="Fuente", score=1, fuente="test.txt")]
    content = ContenidoGenerado(titulo="T", introduccion_contextualizada="I", items=[{"x": 1}],
                                conceptos_clave=[], tiempo_estimado_estudio_minutos=1)
    monkeypatch.setattr(generation, "_invocar_con_rotacion", Mock(side_effect=RuntimeError("SECRET")))
    with pytest.raises(generation.ErrorGeneracion) as caught:
        generation.generar_contenido_adaptado("T", context, "Perfil", "Quiz", "General", "Básico")
    monkeypatch.setattr(evaluation, "_invocar_con_rotacion", Mock(side_effect=RuntimeError("SECRET")))
    result = evaluation.evaluar_contenido(content, context, "Perfil", "Quiz")
    assert result.claridad_pedagogica == "No evaluada"
    assert "SECRET" not in caplog.text + str(caught.value) + result.observaciones


@pytest.mark.parametrize("module", [generation, evaluation], ids=["generacion", "evaluacion"])
def test_sdk_interceptado_un_http_por_invoke(module, monkeypatch):
    from google.genai import errors
    from google.genai._api_client import BaseApiClient
    request = Mock(side_effect=errors.ClientError(429, {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED"}}))
    monkeypatch.setattr(BaseApiClient, "_request_once", request)
    llm = REAL_GET[module]("gemini-3.6-flash", "offline-key")
    created = [llm]
    try:
        assert llm.max_retries == 1 and llm.timeout == 60
        with pytest.raises(Exception): llm.invoke("offline")
        assert request.call_count == 1
        def get(model, key):
            instance = REAL_GET[module](model, key)
            created.append(instance)
            return instance
        monkeypatch.setattr(module, "_get_llm", get)
        monkeypatch.setattr(module, "_obtener_api_keys", lambda: KEYS)
        monkeypatch.setattr(module, "_obtener_modelos", lambda: ["gemini-3.6-flash", "gemini-3.8-flash"])
        request.reset_mock()
        if module is generation:
            with pytest.raises(module.ErrorGeneracion): module._invocar_con_rotacion(ContenidoQuiz, "offline")
        else:
            with pytest.raises(module.ErrorEvaluacion): module._invocar_con_rotacion("offline")
        assert request.call_count == 4  # Dos modelos por dos claves, sin reintentos ocultos.
    finally:
        for instance in created:
            instance.client.close()
        REAL_GET[module].cache_clear()
