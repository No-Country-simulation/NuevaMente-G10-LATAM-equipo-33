"""Errores estructurados, reloj/esperas falsos y SDK interceptado sin red."""
from datetime import datetime, timezone
from email.utils import format_datetime
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from ingesta_rag.utils.key_manager import KeyManager
from shared.gemini_policy import GeminiPolicyError, RotationOperation, classify_failure


def error(code=429, *, details=None, headers=None, status=None):
    result = RuntimeError("NO-REGISTRAR-ESTE-MENSAJE-503-ni-clave-ficticia")
    result.code = code
    result.status = status
    result.details = details or {}
    result.response = SimpleNamespace(headers=headers or {})
    return result


def retry_info(delay):
    return {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": delay}


def daily_info(quota="EmbedContentRequestsPerDayPerProjectPerModel"):
    return {"@type": "type.googleapis.com/google.rpc.QuotaFailure",
            "violations": [{"quotaId": quota}]}


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr("socket.socket.connect", Mock(side_effect=AssertionError("Red prohibida")))
    monkeypatch.setattr("socket.create_connection", Mock(side_effect=AssertionError("Red prohibida")))


@pytest.mark.parametrize("code,category", [(401, "autenticacion"), (403, "permisos"),
    (429, "cuota"), (503, "indisponibilidad"), (400, "no_recuperable")])
def test_http_estructurado_prevalece_sobre_mensaje_y_estado(code, category):
    failure = classify_failure(error(code, status="UNAVAILABLE"))
    assert failure.category == category and failure.http_status == code


@pytest.mark.parametrize("status,category", [("UNAUTHENTICATED", "autenticacion"),
    ("PERMISSION_DENIED", "permisos"), ("RESOURCE_EXHAUSTED", "cuota"), ("UNAVAILABLE", "indisponibilidad")])
def test_estado_sin_codigo(status, category):
    assert classify_failure(error(None, status=status)).category == category


def test_causas_validacion_y_no_interpretar_texto():
    inner = error(429)
    outer = RuntimeError("wrapper")
    outer.__cause__ = inner
    assert classify_failure(outer).category == "cuota"
    assert classify_failure(RuntimeError("429 RESOURCE_EXHAUSTED 503")).category == "desconocido"
    parse = json.JSONDecodeError("503", "", 0)
    parse.__cause__ = inner
    assert classify_failure(parse).category == "validacion"
    inner.__cause__ = outer
    assert classify_failure(outer).category == "cuota"  # Ciclo finito.
    invalid = error(400, details={"error": {"details": [{"reason": "API_KEY_EXPIRED"}]}})
    assert classify_failure(invalid).category == "autenticacion"


@pytest.mark.parametrize("value,expected", [("7", 7), ("0", 0), ("2.5", 2.5), ("no", None), ("NaN", None), ("-1", None)])
def test_retry_after(value, expected):
    assert classify_failure(error(headers={"Retry-After": value})).retry_after == expected


def test_retry_after_fecha_retryinfo_y_maximo():
    date = format_datetime(datetime.fromtimestamp(1010, tz=timezone.utc), usegmt=True)
    assert classify_failure(error(headers={"retry-after": date}), now=1000).retry_after == 10
    failure = classify_failure(error(headers={"Retry-After": "2"}, details={"error": {"details": [
        retry_info({"seconds": "3", "nanos": 500000000}), retry_info("6.5s")
    ]}}))
    assert failure.retry_after == 6.5


def test_rotacion_inmediata_y_enfriamiento_antes_de_tercera_clave():
    pool = KeyManager(["a", "b", "c"])
    events = []
    def invoke(key):
        events.append(key)
        if key != "c": raise error()
        return "ok"
    operation = RotationOperation(pool, sleep=lambda seconds: events.append(seconds))
    assert operation.run(invoke) == "ok"
    assert events == ["a", "b", 5.0, "c"]


def test_hint_de_cualquiera_de_las_dos_claves():
    pool = KeyManager(["a", "b", "c"])
    sleep = Mock()
    def invoke(key):
        if key == "a": raise error(headers={"Retry-After": "9"})
        if key == "b": raise error(details={"details": [retry_info("2s")]})
        return "ok"
    assert RotationOperation(pool, sleep=sleep).run(invoke) == "ok"
    sleep.assert_called_once_with(9)


def test_cuatro_intentos_sin_reinicio_y_un_solo_enfriamiento():
    call, sleep = Mock(side_effect=error()), Mock()
    operation = RotationOperation(KeyManager(["a", "b", "c", "d", "e"]), max_attempts=100, sleep=sleep)
    with pytest.raises(GeminiPolicyError): operation.run(call)
    assert call.call_count == 4
    sleep.assert_called_once_with(5)
    with pytest.raises(GeminiPolicyError): operation.run(call)
    assert call.call_count == 4


def test_sin_espera_si_no_habra_otro_intento():
    sleep = Mock()
    with pytest.raises(GeminiPolicyError):
        RotationOperation(KeyManager(["a", "b"]), max_attempts=2, sleep=sleep).run(Mock(side_effect=error()))
    sleep.assert_not_called()


def test_operacion_multilote_solo_enfria_una_vez_y_presupuesto_por_lote():
    pool = KeyManager(["a", "b", "c", "d", "e", "f"])
    sleep = Mock()
    operation = RotationOperation(pool, sleep=sleep)
    calls = []
    for _ in range(2):
        invoke = Mock(side_effect=[error(), error(), "ok"])
        assert operation.run(invoke) == "ok"
        calls.append(invoke.call_count)
    assert calls == [3, 3]
    sleep.assert_called_once_with(5)


def test_claves_distintas_y_cuarentena_expira_sin_borrarlas():
    now = [0]
    pool = KeyManager([" a ", "a", "b"], clock=lambda: now[0])
    assert pool.keys_pool == ["a", "b"]
    for _ in range(3):
        with pytest.raises(GeminiPolicyError):
            RotationOperation(pool, max_attempts=2, sleep=Mock()).run(Mock(side_effect=error()))
    with pytest.raises(RuntimeError): pool.obtener_key_activa()
    assert pool._429_streak == {"a": 3, "b": 3}
    now[0] = 61
    assert pool.obtener_key_activa() in {"a", "b"}
    assert pool.keys_pool == ["a", "b"]


def test_una_clave_no_activa_enfriamiento_y_no_espera_cuarentena():
    pool = KeyManager(["same", "same"], clock=lambda: 0)
    sleep = Mock()
    call = Mock(side_effect=error())
    with pytest.raises(GeminiPolicyError): RotationOperation(pool, sleep=sleep).run(call)
    assert call.call_count == 3  # Tres rondas completas de una clave: cuarentena.
    sleep.assert_not_called()


def test_exito_restablece_contador_y_rompe_429_consecutivos():
    pool = KeyManager(["a", "b"])
    with pytest.raises(GeminiPolicyError):
        RotationOperation(pool, max_attempts=2, sleep=Mock()).run(Mock(side_effect=error()))
    assert pool._429_streak["a"] == 1
    operation = RotationOperation(pool, sleep=Mock())
    assert operation.run(lambda key: "ok") == "ok"
    assert "a" not in pool._429_streak
    assert operation.last_429 is None


@pytest.mark.parametrize("code,attempts", [(401, 2), (403, 1), (503, 1), (400, 1)])
def test_autenticacion_rota_permisos_e_indisponibilidad_no(code, attempts):
    pool = KeyManager(["a", "b"])
    call, sleep = Mock(side_effect=error(code)), Mock()
    with pytest.raises(GeminiPolicyError): RotationOperation(pool, sleep=sleep).run(call)
    assert call.call_count == attempts
    sleep.assert_not_called()
    assert not pool._quarantine_until


def test_401_solo_excluye_durante_operacion():
    pool = KeyManager(["a", "b"])
    operation = RotationOperation(pool, sleep=Mock())
    assert operation.run(Mock(side_effect=[error(401), "ok"])) == "ok"
    assert operation.excluded == {"a"}
    pool._rotar_siguiente()
    assert RotationOperation(pool, sleep=Mock()).run(lambda key: key) == "a"


def test_cuota_diaria_confirmada_detiene_operacion_sin_dormir():
    pool = KeyManager(["a", "b", "c"])
    sleep = Mock()
    call = Mock(side_effect=error(details={"error": {"details": [daily_info(), retry_info("20s")]}}))
    with pytest.raises(GeminiPolicyError, match="diaria"):
        RotationOperation(pool, sleep=sleep).run(call)
    assert call.call_count == 1
    sleep.assert_not_called()
    assert not classify_failure(error(details={"details": [daily_info("RequestsPerMinute")]})).daily_quota
    assert not classify_failure(error(details={"message": "daily limit exceeded"})).daily_quota


def test_no_filtra_claves_mensajes_ni_causas(caplog):
    pool = KeyManager(["credential-SECRET-END1", "credential-SECRET-END2"])
    with pytest.raises(GeminiPolicyError) as caught:
        RotationOperation(pool, sleep=Mock()).run(Mock(side_effect=error()))
    pool.marcar_key_invalida(pool.keys_pool[0], razon="SECRET-RAZON")
    output = caplog.text + str(caught.value)
    assert all(token not in output for token in ("SECRET", "END1", "END2", "NO-REGISTRAR"))
    assert caught.value.__suppress_context__


@pytest.fixture
def embeddings(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEYS", "solo-ficticia")
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "false")
    from ingesta_rag.services import embedding_service
    monkeypatch.setattr(embedding_service, "MAX_EMBEDDING_ATTEMPTS", 4)
    monkeypatch.setattr("shared.gemini_policy.time.sleep", Mock())
    return embedding_service


@pytest.mark.parametrize("query", [False, True])
def test_wrappers_embeddings_aplican_politica(embeddings, monkeypatch, query):
    pool = KeyManager(["a", "b", "c", "d", "e"])
    wrapper = embeddings.GeminiEmbeddingsResiliente(pool)
    call = Mock(side_effect=error())
    monkeypatch.setattr(wrapper, "_obtener_instancia_embeddings", lambda key: SimpleNamespace(embed_query=call, embed_documents=call))
    with pytest.raises(GeminiPolicyError):
        wrapper.embed_query("texto") if query else wrapper.embed_documents(["texto"])
    assert call.call_count == 4


def test_multilote_no_repite_lotes_completados(embeddings, monkeypatch):
    wrapper = embeddings.GeminiEmbeddingsResiliente(KeyManager(["a", "b", "c"]))
    batches = []
    def embed(batch, **kwargs):
        batches.append(list(batch))
        if len(batches) in (2, 3): raise error()
        return [[1.0] for _ in batch]
    monkeypatch.setattr(wrapper, "_obtener_instancia_embeddings", lambda key: SimpleNamespace(embed_documents=embed))
    texts = [str(i) for i in range(101)]
    assert len(wrapper.embed_documents(texts)) == 101
    assert batches == [texts[:50], texts[50:100], texts[50:100], texts[50:100], texts[100:]]


def test_particion_por_tokens_evitar_peticiones_ocultas(embeddings, monkeypatch):
    wrapper = embeddings.GeminiEmbeddingsResiliente(KeyManager(["a", "b"]))
    batches = []
    def embed(batch, **kwargs):
        assert len(embeddings._SingleAttemptEmbeddings._prepare_batches(batch, 50)) == 1
        batches.append(batch)
        return [[1.0] for _ in batch]
    monkeypatch.setattr(wrapper, "_obtener_instancia_embeddings", lambda key: SimpleNamespace(embed_documents=embed))
    assert len(wrapper.embed_documents(["palabra " * 6000] * 5)) == 5
    assert len(batches) > 1


def test_metadatos_incompletos_y_malformados_no_inventan_codigo():
    assert classify_failure(error(None, details={"error": "no estructurado"})).category == "desconocido"
    assert classify_failure(error(details={"details": [{"@type": "type.googleapis.com/google.rpc.QuotaFailure", "violations": None}]})).daily_quota is False


def test_sdk_real_un_solo_intento_http_sin_red(embeddings, monkeypatch):
    from google.genai import errors
    from google.genai._api_client import BaseApiClient
    sdk_error = errors.ClientError(429, {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED"}})
    request = Mock(side_effect=sdk_error)
    monkeypatch.setattr(BaseApiClient, "_request_once", request)
    instance = embeddings._SingleAttemptEmbeddings(model="gemini-embedding-001", google_api_key="ficticia", vertexai=False)
    try:
        assert instance._build_config().http_options.retry_options.attempts == 1
        with pytest.raises(Exception): instance.embed_query("texto")
        assert request.call_count == 1
        wrapper = embeddings.GeminiEmbeddingsResiliente(KeyManager(["a", "b", "c", "d"]))
        monkeypatch.setattr(wrapper, "_obtener_instancia_embeddings", lambda key: instance)
        request.reset_mock()
        with pytest.raises(GeminiPolicyError): wrapper.embed_documents(["texto"])
        assert request.call_count == 4  # Cuatro intentos de política = cuatro peticiones SDK.
    finally:
        instance.client.close()
