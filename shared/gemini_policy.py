"""Clasificación estructurada y rotación acotada, sin instrumentación ni SDK.

Una operación comparte exclusiones y un único enfriamiento entre sus lotes.
El presupuesto de intentos se aplica a cada lote, no se reinicia al dormir.
"""
from dataclasses import dataclass
from datetime import timezone
from email.utils import parsedate_to_datetime
from enum import Enum
import json
import logging
import math
import re
import time

from pydantic import ValidationError

logger = logging.getLogger(__name__)
MAX_ATTEMPTS = 4
DEFAULT_COOLDOWN_SECONDS = 5.0


class GeminiPolicyError(RuntimeError):
    """Error público seguro; nunca incorpora mensajes externos o claves."""


@dataclass(frozen=True)
class Failure:
    category: str
    http_status: int | None = None
    retry_after: float | None = None
    daily_quota: bool = False


def _chain(error):
    seen = set()
    for _ in range(5):
        if error is None or id(error) in seen:
            break
        seen.add(id(error))
        yield error
        error = error.__cause__ if error.__cause__ is not None else (
            None if error.__suppress_context__ else error.__context__)


def _seconds(value):
    try:
        if isinstance(value, bool):
            return None
        result = float(value)
        return result if math.isfinite(result) and result >= 0 else None
    except (TypeError, ValueError, OverflowError):
        return None


def _duration(value):
    if isinstance(value, str) and re.fullmatch(r"\d+(?:\.\d+)?s", value):
        return _seconds(value[:-1])
    if isinstance(value, dict):
        seconds, nanos = _seconds(value.get("seconds", 0)), _seconds(value.get("nanos", 0))
        return seconds + nanos / 1e9 if seconds is not None and nanos is not None else None
    if hasattr(value, "seconds") and hasattr(value, "nanos"):
        return _duration({"seconds": value.seconds, "nanos": value.nanos})
    return None


def _details(error):
    details = getattr(error, "details", None)
    envelope = details.get("error", details) if isinstance(details, dict) else {}
    if isinstance(envelope, dict):
        details = envelope.get("details", [])
    else:
        envelope = {}
    return envelope, details[:10] if isinstance(details, (list, tuple)) else []


def _retry_and_daily(error, now):
    delays = []
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", None)
    if headers is None:
        headers = getattr(error, "headers", {})
    if hasattr(headers, "items"):
        value = next((v for k, v in headers.items() if isinstance(k, str) and k.lower() == "retry-after"), None)
        delay = _seconds(value)
        if delay is None and isinstance(value, str):
            try:
                date = parsedate_to_datetime(value)
                if date.tzinfo is None:
                    date = date.replace(tzinfo=timezone.utc)
                delay = max(0.0, date.timestamp() - now)
            except (ValueError, TypeError, OverflowError):
                pass
        if delay is not None:
            delays.append(delay)
    daily = False
    _, details = _details(error)
    for detail in details:
        if isinstance(detail, dict):
            kind = detail.get("@type", "")
            if kind == "type.googleapis.com/google.rpc.RetryInfo":
                delay = _duration(detail.get("retryDelay", detail.get("retry_delay")))
                if delay is not None:
                    delays.append(delay)
            if kind == "type.googleapis.com/google.rpc.QuotaFailure":
                violations = detail.get("violations", [])
                for violation in (violations[:20] if isinstance(violations, list) else []):
                    if not isinstance(violation, dict):
                        continue
                    # Solo identificadores estructurados; nunca description/message.
                    quota = violation.get("quotaId", violation.get("quota_id", ""))
                    metric = violation.get("quotaMetric", violation.get("quota_metric", ""))
                    daily |= any(isinstance(v, str) and re.search(r"perday|daily", v, re.I) is not None
                                 for v in (quota, metric))
        elif getattr(getattr(detail, "DESCRIPTOR", None), "full_name", None) == "google.rpc.RetryInfo":
            delay = _duration(detail.retry_delay)
            if delay is not None:
                delays.append(delay)
    return max(delays) if delays else None, daily


def classify_failure(error, *, now=None):
    """Lee atributos y hasta cinco causas; no interpreta str(error) ni cuerpos HTTP."""
    chain = list(_chain(error))
    if any(isinstance(cause, (ValidationError, json.JSONDecodeError)) for cause in chain):
        return Failure("validacion")
    now = time.time() if now is None else now
    delays, daily = [], False
    result = None
    for cause in chain:
        delay, is_daily = _retry_and_daily(cause, now)
        if delay is not None:
            delays.append(delay)
        daily |= is_daily
        envelope, details = _details(cause)
        code = next((int(v) for v in (
            getattr(cause, "status_code", None), getattr(cause, "code", None),
            getattr(getattr(cause, "response", None), "status_code", None), envelope.get("code"),
        ) if isinstance(v, int) and not isinstance(v, bool) and 100 <= v <= 599), None)
        status = getattr(cause, "status", None) or envelope.get("status")
        if isinstance(status, Enum):
            status = status.name
        reason = getattr(cause, "reason", None)
        invalid = reason in {"API_KEY_INVALID", "API_KEY_EXPIRED"} if isinstance(reason, str) else False
        invalid |= any(isinstance(d, dict) and d.get("reason") in ("API_KEY_INVALID", "API_KEY_EXPIRED") for d in details)
        category = {401: "autenticacion", 403: "permisos", 429: "cuota", 503: "indisponibilidad"}.get(code)
        if category is None and code is not None:
            category = "autenticacion" if code == 400 and invalid else "no_recuperable"
        if category is None:
            category = {"UNAUTHENTICATED": "autenticacion", "PERMISSION_DENIED": "permisos",
                        "RESOURCE_EXHAUSTED": "cuota", "UNAVAILABLE": "indisponibilidad"}.get(status) if isinstance(status, str) else None
            if category is None and invalid:
                category = "autenticacion"
        if result is None and category is not None:
            result = (category, code)
    category, code = result or ("desconocido", None)
    return Failure(category, code, max(delays) if delays else None, daily and category == "cuota")


class RotationOperation:
    """Reutilizable por otros módulos sin conectarlos todavía a esta política."""
    def __init__(self, pool, *, max_attempts=4, sleep=None):
        self.pool = pool
        self.max_attempts = max(1, min(MAX_ATTEMPTS, max_attempts))
        self.sleep = time.sleep if sleep is None else sleep
        self.excluded = set()
        self.cooldown_used = False
        self.pending_delay = None
        self.last_429 = None
        self.finished = False

    def run(self, invoke):
        if self.finished:
            raise GeminiPolicyError("La operación de Gemini ya ha finalizado.")
        for attempt in range(1, self.max_attempts + 1):
            try:
                key = self.pool.obtener_key_activa(self.excluded)
            except RuntimeError:
                self.finished = True
                raise GeminiPolicyError("No hay claves disponibles fuera de exclusión o cuarentena.") from None
            if self.pending_delay is not None:
                self.cooldown_used = True
                self.sleep(self.pending_delay)
                self.pending_delay = None
            self.pool.registrar_intento(key)
            try:
                result = invoke(key)
            except Exception as error:
                failure = classify_failure(error)
                logger.warning("Gemini intento=%d clasificacion=%s http_status=%s",
                               attempt, failure.category, failure.http_status)
                if failure.category == "cuota":
                    self.pool.registrar_429(key)
                    self.pool._rotar_siguiente()
                    if failure.daily_quota:
                        self.finished = True
                        raise GeminiPolicyError("Cuota diaria confirmada: operación detenida sin reintentos adicionales.") from None
                    if self.last_429 is not None and self.last_429[0] != key and not self.cooldown_used:
                        hints = [v for v in (self.last_429[1], failure.retry_after) if v is not None]
                        self.pending_delay = max(hints) if hints else DEFAULT_COOLDOWN_SECONDS
                    self.last_429 = (key, failure.retry_after)
                elif failure.category == "autenticacion":
                    self.pool.registrar_otro_error(key)
                    self.excluded.add(key)
                    self.pool._rotar_siguiente()
                    self.last_429 = None
                else:
                    self.pool.registrar_otro_error(key)
                    self.finished = True
                    raise GeminiPolicyError("Gemini no pudo completar la operación: " + failure.category + ".") from None
            else:
                self.pool.registrar_exito(key)
                self.last_429 = None
                return result
        self.finished = True
        raise GeminiPolicyError("Se agotó el máximo de intentos del lote de embeddings.") from None


class StructuredResultError(ValueError):
    """El resultado no cumple el contrato esperado de generación o evaluación."""


def classify_model_failure(error):
    """Extiende la clasificación para chat sin cambiar la política de embeddings."""
    import httpx
    from langchain_core import exceptions as lc_errors
    try:
        import httpx2
    except ImportError:
        httpx2 = None

    chain = list(_chain(error))
    if any(isinstance(cause, (StructuredResultError, ValidationError,
                              json.JSONDecodeError, lc_errors.OutputParserException)) for cause in chain):
        return Failure("validacion")
    failure = classify_failure(error)
    if failure.http_status in (408, 504):
        return Failure("timeout", failure.http_status)
    if failure.http_status in (500, 502):
        return Failure("servidor_transitorio", failure.http_status)
    if failure.category != "desconocido":
        return failure
    for cause in chain:
        envelope, _ = _details(cause)
        status = getattr(cause, "status", None) or envelope.get("status")
        if isinstance(status, Enum):
            status = status.name
        if status == "DEADLINE_EXCEEDED":
            return Failure("timeout")
        if status == "INTERNAL":
            return Failure("servidor_transitorio")
    transports = (httpx,) if httpx2 is None else (httpx, httpx2)
    for cause in chain:
        for name, category in (
            ("ModelAuthenticationError", "autenticacion"),
            ("ModelPermissionDeniedError", "permisos"),
            ("ModelRateLimitError", "cuota"), ("ModelTimeoutError", "timeout"),
            ("ModelConnectionError", "transporte_transitorio"),
            ("ModelInvalidRequestError", "no_recuperable"),
            ("ModelNotFoundError", "no_recuperable"), ("ModelAPIError", "servidor_transitorio"),
        ):
            if isinstance(cause, getattr(lc_errors, name, ())):
                return Failure(category)
        if isinstance(cause, TimeoutError) or any(isinstance(cause, module.TimeoutException) for module in transports):
            return Failure("timeout")
        if isinstance(cause, ConnectionError) or any(isinstance(cause, (module.NetworkError, module.RemoteProtocolError)) for module in transports):
            return Failure("transporte_transitorio")
    return failure


def invoke_models(*, models, keys, start_index, prepare, validate, prompt, error_type):
    """Hasta M*(K+1) intentos, sin sleeps ni reintentos de cuota de una pareja.

    Una clave rechazada se excluye solo durante esta invocación, también en el
    respaldo. Un fallo transitorio permite un intento adicional por modelo.
    Los errores públicos no conservan mensajes, cuerpos ni causas del proveedor.
    """
    if not keys or not models:
        raise error_type("Falta configurar modelos o API keys de Gemini.")
    excluded = set()
    order = [(start_index + offset) % len(keys) for offset in range(len(keys))]
    attempt = 0
    for model in models:
        transient_retries = 0
        next_model = False
        for index in order:
            if index in excluded:
                continue
            while True:
                attempt += 1
                try:
                    result = prepare(model, keys[index]).invoke(prompt)
                    validate(result)
                except Exception as error:
                    failure = classify_model_failure(error)
                    category = failure.category
                    logger.warning("Gemini chat intento=%d clasificacion=%s http_status=%s",
                                   attempt, category, failure.http_status)
                    if category == "autenticacion":
                        excluded.add(index)
                        break
                    if category == "cuota":
                        if failure.daily_quota:
                            next_model = True
                        break
                    if category == "indisponibilidad":
                        next_model = True
                        break
                    if category in {"timeout", "transporte_transitorio", "servidor_transitorio"}:
                        if transient_retries < 1:
                            transient_retries += 1
                            continue
                        next_model = True
                        break
                    raise error_type("Gemini no pudo completar la operación: " + category + ".") from None
                return result, index
            if next_model:
                break
    raise error_type("Se agotaron todas las API keys o los modelos disponibles por cuota, autenticación o indisponibilidad.") from None
