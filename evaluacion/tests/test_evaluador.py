"""Pruebas del evaluador. No llaman a la API."""

import pytest

from evaluacion.schemas.juez import ResultadoJuez, VeredictoItem
from evaluacion.services import evaluador
from shared.contratos import ChunkResultado, ContenidoGenerado

# Se guardan las funciones reales antes de que la fixture las reemplace por falsas.
_obtener_api_keys_real = evaluador._obtener_api_keys
_obtener_modelos_real = evaluador._obtener_modelos

CONTEXTO = [ChunkResultado(texto="Una VCN es una red virtual privada.", score=0.9, fuente="vcn.pdf")]

ERROR_CUOTA = RuntimeError("429 RESOURCE_EXHAUSTED. Excediste tu cuota actual")
ERROR_SATURADO = RuntimeError("503 UNAVAILABLE. Este modelo está experimentando alta demanda")


def v(indice: int, veredicto: str) -> VeredictoItem:
    return VeredictoItem(indice=indice, veredicto=veredicto, justificacion="x")


# --- Cálculo del score ---


def test_todos_respaldados_da_1():
    assert evaluador.calcular_anclaje([v(0, "respaldado"), v(1, "respaldado")], 2) == 1.0


def test_mezcla_de_veredictos():
    vs = [v(0, "respaldado"), v(1, "parcial"), v(2, "no_respaldado")]
    assert evaluador.calcular_anclaje(vs, 3) == 0.5  # (1 + 0.5 + 0) / 3


def test_el_score_se_redondea_a_dos_decimales():
    vs = [v(0, "respaldado"), v(1, "no_respaldado"), v(2, "no_respaldado")]
    assert evaluador.calcular_anclaje(vs, 3) == 0.33  # 1 / 3


def test_items_omitidos_cuentan_como_no_respaldados():
    assert evaluador.calcular_anclaje([v(0, "respaldado")], 2) == 0.5


def test_indices_repetidos_y_fuera_de_rango_se_ignoran():
    vs = [v(0, "respaldado"), v(0, "respaldado"), v(5, "respaldado")]
    assert evaluador.calcular_anclaje(vs, 2) == 0.5


def test_sin_items_da_0():
    assert evaluador.calcular_anclaje([], 0) == 0.0


# --- Juez simulado (sin llamar a Gemini) ---


class JuezFalso:
    """Imita al LLM: devuelve (o lanza) lo que se le indica y cuenta las llamadas."""

    def __init__(self, resultado=None, error=None):
        self.resultado = resultado
        self.error = error
        self.llamadas = 0

    def with_structured_output(self, _esquema):
        return self

    def invoke(self, _prompt):
        self.llamadas += 1
        if self.error:
            raise self.error
        return self.resultado


def _contenido(items):
    return ContenidoGenerado(
        titulo="VCN",
        introduccion_contextualizada="Intro",
        items=items,
        conceptos_clave=["VCN"],
        tiempo_estimado_estudio_minutos=5,
    )


def _resultado_juez(veredictos, claridad="Alta", observaciones="Resumen."):
    return ResultadoJuez(
        veredictos_items=veredictos,
        claridad_pedagogica=claridad,
        observaciones=observaciones,
    )


def _un_item_respaldado():
    return _resultado_juez([v(0, "respaldado")])


def _evaluar(items=None):
    contenido = _contenido(items if items is not None else [{"a": 1}])
    return evaluador.evaluar_contenido(contenido, CONTEXTO, "principiante", "flashcards")


def _usar_jueces(monkeypatch, jueces_por_clave):
    """Configura las keys disponibles y el juez falso de cada una (un solo modelo)."""
    monkeypatch.setattr(evaluador, "_obtener_modelos", lambda: ["modelo-1"])
    monkeypatch.setattr(evaluador, "_obtener_api_keys", lambda: list(jueces_por_clave))
    monkeypatch.setattr(evaluador, "_get_llm", lambda _modelo, clave: jueces_por_clave[clave])


def _usar_modelos(monkeypatch, jueces):
    """jueces: {(modelo, clave): JuezFalso}. Se prueban en el orden en que aparecen."""
    modelos = list(dict.fromkeys(m for m, _ in jueces))
    claves = list(dict.fromkeys(c for _, c in jueces))
    monkeypatch.setattr(evaluador, "_obtener_modelos", lambda: modelos)
    monkeypatch.setattr(evaluador, "_obtener_api_keys", lambda: claves)
    monkeypatch.setattr(evaluador, "_get_llm", lambda modelo, clave: jueces[(modelo, clave)])


@pytest.fixture(autouse=True)
def juez_falso_por_defecto(monkeypatch):
    """Ninguna prueba llama a Gemini de verdad."""
    monkeypatch.setattr(evaluador, "_clave_actual", 0)
    juez = JuezFalso(resultado=_un_item_respaldado())
    _usar_jueces(monkeypatch, {"clave-1": juez})
    return juez


# --- evaluar_contenido ---


def test_evaluar_contenido_marca_items_no_respaldados(monkeypatch):
    resultado = _resultado_juez(
        [v(0, "respaldado"), v(1, "no_respaldado")], claridad="Alta", observaciones="Resumen."
    )
    _usar_jueces(monkeypatch, {"clave-1": JuezFalso(resultado=resultado)})

    r = _evaluar([{"a": 1}, {"b": 2}])

    assert r.anclaje_fuente_score == 0.5
    assert r.claridad_pedagogica == "Alta"
    assert "[1]" in r.observaciones


def test_evaluar_contenido_todo_respaldado():
    r = _evaluar()

    assert r.anclaje_fuente_score == 1.0
    assert "Ítems a revisar" not in r.observaciones


def test_evaluar_contenido_sin_items_no_llama_al_llm(juez_falso_por_defecto):
    r = _evaluar(items=[])

    assert r.anclaje_fuente_score == 0.0
    assert r.claridad_pedagogica == "Baja"
    assert juez_falso_por_defecto.llamadas == 0


def test_evaluar_contenido_devuelve_evaluacion_por_defecto_si_falla_el_llm(monkeypatch):
    _usar_jueces(monkeypatch, {"clave-1": JuezFalso(error=RuntimeError("falló la red"))})

    r = _evaluar()

    assert r.anclaje_fuente_score == 0.0
    assert r.claridad_pedagogica == "No evaluada"
    assert "RuntimeError" in r.observaciones


def test_sin_api_key_devuelve_evaluacion_por_defecto(monkeypatch):
    monkeypatch.setattr(evaluador, "_obtener_api_keys", lambda: [])

    r = _evaluar()

    assert r.claridad_pedagogica == "No evaluada"
    assert "API key" in r.observaciones


# --- Rotación de API keys ---


def test_si_una_key_no_tiene_cupo_usa_la_siguiente(monkeypatch):
    sin_cupo = JuezFalso(error=ERROR_CUOTA)
    con_cupo = JuezFalso(resultado=_un_item_respaldado())
    _usar_jueces(monkeypatch, {"clave-1": sin_cupo, "clave-2": con_cupo})

    r = _evaluar()

    assert r.anclaje_fuente_score == 1.0
    assert sin_cupo.llamadas == 1
    assert con_cupo.llamadas == 1


def test_recuerda_la_ultima_key_que_funciono(monkeypatch):
    sin_cupo = JuezFalso(error=ERROR_CUOTA)
    con_cupo = JuezFalso(resultado=_un_item_respaldado())
    _usar_jueces(monkeypatch, {"clave-1": sin_cupo, "clave-2": con_cupo})

    _evaluar()
    _evaluar()

    assert sin_cupo.llamadas == 1  # la segunda vez ni la prueba
    assert con_cupo.llamadas == 2


def test_si_todas_las_keys_estan_agotadas_devuelve_evaluacion_por_defecto(monkeypatch):
    _usar_jueces(
        monkeypatch,
        {"clave-1": JuezFalso(error=ERROR_CUOTA), "clave-2": JuezFalso(error=ERROR_CUOTA)},
    )

    r = _evaluar()

    assert r.claridad_pedagogica == "No evaluada"
    assert "todas las API keys" in r.observaciones


def test_un_error_que_no_es_de_cuota_no_rota_de_key(monkeypatch):
    con_error = JuezFalso(error=RuntimeError("falló la red"))
    otro = JuezFalso(resultado=_un_item_respaldado())
    _usar_jueces(monkeypatch, {"clave-1": con_error, "clave-2": otro})

    r = _evaluar()

    assert r.claridad_pedagogica == "No evaluada"
    assert otro.llamadas == 0


def test_obtener_api_keys_junta_las_variables_sin_repetir(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEYS", " a , b ,a,, c ")
    monkeypatch.setattr(evaluador, "_obtener_api_keys", _obtener_api_keys_real)

    assert evaluador._obtener_api_keys() == ["a", "b", "c"]


# --- Modelo de respaldo ---


def test_si_el_modelo_esta_saturado_usa_el_modelo_de_respaldo(monkeypatch):
    principal_k1 = JuezFalso(error=ERROR_SATURADO)
    principal_k2 = JuezFalso(error=ERROR_SATURADO)
    respaldo_k1 = JuezFalso(resultado=_un_item_respaldado())
    _usar_modelos(
        monkeypatch,
        {
            ("modelo-1", "clave-1"): principal_k1,
            ("modelo-1", "clave-2"): principal_k2,
            ("modelo-2", "clave-1"): respaldo_k1,
            ("modelo-2", "clave-2"): JuezFalso(resultado=_un_item_respaldado()),
        },
    )

    r = _evaluar()

    assert r.anclaje_fuente_score == 1.0
    assert principal_k1.llamadas == 1
    assert principal_k2.llamadas == 0  # con el modelo saturado, otra key no ayuda
    assert respaldo_k1.llamadas == 1


def test_si_todos_los_modelos_estan_saturados_devuelve_evaluacion_por_defecto(monkeypatch):
    _usar_modelos(
        monkeypatch,
        {
            ("modelo-1", "clave-1"): JuezFalso(error=ERROR_SATURADO),
            ("modelo-2", "clave-1"): JuezFalso(error=ERROR_SATURADO),
        },
    )

    r = _evaluar()

    assert r.claridad_pedagogica == "No evaluada"
    assert "saturados" in r.observaciones


def test_obtener_modelos_agrega_el_respaldo_y_no_repite(monkeypatch):
    monkeypatch.setattr(evaluador, "_obtener_modelos", _obtener_modelos_real)
    monkeypatch.setenv("GEMINI_MODEL", "a")
    monkeypatch.setenv("GEMINI_MODEL_RESPALDO", "b")
    assert evaluador._obtener_modelos() == ["a", "b"]

    monkeypatch.setenv("GEMINI_MODEL_RESPALDO", "a")
    assert evaluador._obtener_modelos() == ["a"]
