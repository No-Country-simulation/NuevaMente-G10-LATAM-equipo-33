"""Pruebas del evaluador. No llaman a la API."""

from schemas.juez import VeredictoItem
from services import evaluador
from evaluacion.schemas.juez import ResultadoJuez, VeredictoItem
from evaluacion.services import evaluador
from shared.contratos import ChunkResultado, ContenidoGenerado

def v(indice: int, veredicto: str) -> VeredictoItem:
    return VeredictoItem(indice=indice, veredicto=veredicto, justificacion="x")


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

    # --- Pruebas de evaluar_contenido con un juez simulado (sin llamar a Gemini) ---


class JuezFalso:
    """Imita al LLM: devuelve siempre el resultado que se le indica."""

    def __init__(self, resultado):
        self.resultado = resultado

    def with_structured_output(self, _esquema):
        return self

    def invoke(self, _prompt):
        return self.resultado


CONTEXTO = [ChunkResultado(texto="Una VCN es una red virtual privada.", score=0.9, fuente="vcn.pdf")]


def _contenido(items):
    return ContenidoGenerado(
        titulo="VCN",
        introduccion_contextualizada="Intro",
        items=items,
        conceptos_clave=["VCN"],
        tiempo_estimado_estudio_minutos=5,
    )


def test_evaluar_contenido_marca_items_no_respaldados(monkeypatch):
    resultado = ResultadoJuez(
        veredictos_items=[
            VeredictoItem(indice=0, veredicto="respaldado", justificacion="ok"),
            VeredictoItem(indice=1, veredicto="no_respaldado", justificacion="inventado"),
        ],
        claridad_pedagogica="Alta",
        observaciones="Resumen.",
    )
    monkeypatch.setattr(evaluador, "_get_llm", lambda: JuezFalso(resultado))

    r = evaluador.evaluar_contenido(_contenido([{"a": 1}, {"b": 2}]), CONTEXTO, "principiante", "flashcards")

    assert r.anclaje_fuente_score == 0.5
    assert r.claridad_pedagogica == "Alta"
    assert "[1]" in r.observaciones


def test_evaluar_contenido_todo_respaldado(monkeypatch):
    resultado = ResultadoJuez(
        veredictos_items=[VeredictoItem(indice=0, veredicto="respaldado", justificacion="ok")],
        claridad_pedagogica="Media",
        observaciones="Todo bien.",
    )
    monkeypatch.setattr(evaluador, "_get_llm", lambda: JuezFalso(resultado))

    r = evaluador.evaluar_contenido(_contenido([{"a": 1}]), CONTEXTO, "principiante", "flashcards")

    assert r.anclaje_fuente_score == 1.0
    assert "Ítems a revisar" not in r.observaciones


def test_evaluar_contenido_sin_items_no_llama_al_llm(monkeypatch):
    def no_deberia_llamarse():
        raise AssertionError("no debe llamar al LLM si no hay ítems")

    monkeypatch.setattr(evaluador, "_get_llm", no_deberia_llamarse)

    r = evaluador.evaluar_contenido(_contenido([]), CONTEXTO, "principiante", "flashcards")

    assert r.anclaje_fuente_score == 0.0
    assert r.claridad_pedagogica == "Baja"

def test_evaluar_contenido_devuelve_evaluacion_por_defecto_si_falla_el_llm(monkeypatch):
    class JuezQueFalla:
        def with_structured_output(self, _esquema):
            return self

        def invoke(self, _prompt):
            raise RuntimeError("cuota agotada")

    monkeypatch.setattr(evaluador, "_get_llm", lambda: JuezQueFalla())

    r = evaluador.evaluar_contenido(_contenido([{"a": 1}]), CONTEXTO, "principiante", "flashcards")

    assert r.anclaje_fuente_score == 0.0
    assert r.claridad_pedagogica == "No evaluada"
    assert "RuntimeError" in r.observaciones