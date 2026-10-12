import pytest
from pydantic import BaseModel

import main as orq
from shared.contratos import ChunkResultado, ContenidoQuiz, ItemQuiz

CONTEXTO = [
    ChunkResultado(texto="Una VCN es una red virtual privada.", score=0.9, fuente="vcn.pdf")
]


class LlmFalso:
    """Imita al LLM: guarda el prompt que recibe y devuelve (o lanza) lo que se le indica."""

    def __init__(self, resultado=None, error=None):
        self.resultado = resultado
        self.error = error
        self.prompt = None

    def with_structured_output(self, _modelo):
        return self

    def invoke(self, prompt):
        self.prompt = prompt
        if self.error:
            raise self.error
        return self.resultado


def _quiz(n_items=1):
    items = [
        ItemQuiz(
            pregunta="¿Qué es una VCN?",
            opciones=["Una red privada", "Un disco"],
            respuesta_correcta="Una red privada",
            justificacion="Lo dice el contexto.",
        )
        for _ in range(n_items)
    ]
    return ContenidoQuiz(
        titulo="Titulo",
        introduccion_contextualizada="Intro",
        items=items,
        conceptos_clave=["VCN"],
        tiempo_estimado_estudio_minutos=5,
    )


def _generar(**cambios):
    args = dict(
        documento_titulo="Doc",
        contexto=CONTEXTO,
        perfil_destinatario="Principiante",
        formato_salida="Quiz",
        nicho_sector="General",
        nivel_detalle="Didactico",
    )
    args.update(cambios)
    return orq.generar_contenido_adaptado(**args)


@pytest.fixture(autouse=True)
def llm_falso_por_defecto(monkeypatch):
    """Ninguna prueba llama a Gemini de verdad."""
    llm = LlmFalso(resultado=_quiz())
    monkeypatch.setattr(orq, "_get_llm", lambda: llm)
    return llm


# --- Formato tolerante ---


@pytest.mark.parametrize(
    "escrito, oficial",
    [
        ("Quiz", "Quiz"),
        ("quiz", "Quiz"),
        ("  QUIZ ", "Quiz"),
        ("Flashcards", "Flashcards"),
        ("flash cards", "Flashcards"),
        ("Flash-Cards", "Flashcards"),
    ],
)
def test_formato_se_acepta_sin_importar_como_este_escrito(escrito, oficial):
    nombre, _modelo = orq._resolver_formato(escrito)
    assert nombre == oficial


def test_formato_desconocido_lanza_formato_no_soportado():
    with pytest.raises(orq.FormatoNoSoportado) as error:
        _generar(formato_salida="Tutorial")
    assert "Flashcards" in str(error.value)
    assert isinstance(error.value, ValueError)


# --- Campos obligatorios y opcionales ---


@pytest.mark.parametrize(
    "campo", ["documento_titulo", "perfil_destinatario", "formato_salida"]
)
@pytest.mark.parametrize("valor", ["", "   ", None])
def test_campos_obligatorios_vacios_lanzan_entrada_invalida(campo, valor):
    with pytest.raises(orq.EntradaInvalida):
        _generar(**{campo: valor})


def test_nicho_y_nivel_vacios_usan_valores_por_defecto(llm_falso_por_defecto):
    _generar(nicho_sector="  ", nivel_detalle="")
    assert "Sector/nicho: General" in llm_falso_por_defecto.prompt
    assert "Nivel de detalle: Didactico" in llm_falso_por_defecto.prompt


def test_perfil_libre_se_acepta_tal_cual(llm_falso_por_defecto):
    _generar(perfil_destinatario="  Gerente de ventas  ")
    assert "Perfil del destinatario: Gerente de ventas" in llm_falso_por_defecto.prompt


# --- Contexto ---


@pytest.mark.parametrize(
    "contexto",
    [[], [ChunkResultado(texto="   ", score=0.5, fuente="x")], "no es una lista"],
)
def test_contexto_vacio_o_invalido_lanza_entrada_invalida(contexto):
    with pytest.raises(orq.EntradaInvalida):
        _generar(contexto=contexto)


def test_acepta_chunks_de_otra_clase_con_la_misma_estructura():
    """ingesta-rag tiene su propia copia de ChunkResultado: debe aceptarse igual."""

    class ChunkAjeno(BaseModel):
        texto: str
        score: float
        fuente: str

    resultado = _generar(contexto=[ChunkAjeno(texto="Una VCN...", score=0.9, fuente="x")])
    assert resultado.titulo == "Titulo"


# --- Resultado y errores de generación ---


def test_devuelve_items_como_dicts_planos():
    resultado = _generar()
    assert isinstance(resultado.items[0], dict)
    assert resultado.items[0]["pregunta"] == "¿Qué es una VCN?"


def test_error_de_gemini_se_convierte_en_error_generacion(monkeypatch):
    llm = LlmFalso(error=RuntimeError("cuota agotada"))
    monkeypatch.setattr(orq, "_get_llm", lambda: llm)
    with pytest.raises(orq.ErrorGeneracion) as error:
        _generar()
    assert "RuntimeError" in str(error.value)


@pytest.mark.parametrize("vacio", [None, "sin_items"])
def test_contenido_vacio_de_gemini_lanza_error_generacion(monkeypatch, vacio):
    resultado = None if vacio is None else _quiz(n_items=0)
    monkeypatch.setattr(orq, "_get_llm", lambda: LlmFalso(resultado=resultado))
    with pytest.raises(orq.ErrorGeneracion):
        _generar()


def test_sin_api_key_lanza_error_generacion(monkeypatch):
    monkeypatch.undo()  # saca el LLM falso: probamos el _get_llm real
    monkeypatch.setattr(orq, "_obtener_api_key", lambda: None)
    orq._get_llm.cache_clear()
    with pytest.raises(orq.ErrorGeneracion) as error:
        _generar()
    assert "API key" in str(error.value)