import pytest
from pydantic import BaseModel

import main as orq
from shared.contratos import ChunkResultado, ContenidoQuiz, ItemQuiz

# Se guarda la función real antes de que la fixture la reemplace por una falsa.
_obtener_api_keys_real = orq._obtener_api_keys

CONTEXTO = [
    ChunkResultado(texto="Una VCN es una red virtual privada.", score=0.9, fuente="vcn.pdf")
]

ERROR_CUOTA = RuntimeError("429 RESOURCE_EXHAUSTED. You exceeded your current quota")


class LlmFalso:
    """Imita al LLM: guarda el prompt que recibe y devuelve (o lanza) lo que se le indica."""

    def __init__(self, resultado=None, error=None):
        self.resultado = resultado
        self.error = error
        self.prompt = None
        self.llamadas = 0

    def with_structured_output(self, _modelo):
        return self

    def invoke(self, prompt):
        self.prompt = prompt
        self.llamadas += 1
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


def _usar_llms(monkeypatch, llms_por_clave):
    """Configura las keys disponibles y el LLM falso de cada una."""
    monkeypatch.setattr(orq, "_obtener_api_keys", lambda: list(llms_por_clave))
    monkeypatch.setattr(orq, "_get_llm", lambda clave: llms_por_clave[clave])


@pytest.fixture(autouse=True)
def llm_falso_por_defecto(monkeypatch):
    """Ninguna prueba llama a Gemini de verdad."""
    monkeypatch.setattr(orq, "_clave_actual", 0)
    llm = LlmFalso(resultado=_quiz())
    _usar_llms(monkeypatch, {"clave-1": llm})
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
    _usar_llms(monkeypatch, {"clave-1": LlmFalso(error=RuntimeError("falló la red"))})
    with pytest.raises(orq.ErrorGeneracion) as error:
        _generar()
    assert "RuntimeError" in str(error.value)


@pytest.mark.parametrize("vacio", [None, "sin_items"])
def test_contenido_vacio_de_gemini_lanza_error_generacion(monkeypatch, vacio):
    resultado = None if vacio is None else _quiz(n_items=0)
    _usar_llms(monkeypatch, {"clave-1": LlmFalso(resultado=resultado)})
    with pytest.raises(orq.ErrorGeneracion):
        _generar()


def test_sin_api_key_lanza_error_generacion(monkeypatch):
    monkeypatch.setattr(orq, "_obtener_api_keys", lambda: [])
    with pytest.raises(orq.ErrorGeneracion) as error:
        _generar()
    assert "API key" in str(error.value)


# --- Rotación de API keys ---


def test_si_una_key_no_tiene_cupo_usa_la_siguiente(monkeypatch):
    sin_cupo = LlmFalso(error=ERROR_CUOTA)
    con_cupo = LlmFalso(resultado=_quiz())
    _usar_llms(monkeypatch, {"clave-1": sin_cupo, "clave-2": con_cupo})

    resultado = _generar()

    assert resultado.titulo == "Titulo"
    assert sin_cupo.llamadas == 1
    assert con_cupo.llamadas == 1


def test_recuerda_la_ultima_key_que_funciono(monkeypatch):
    sin_cupo = LlmFalso(error=ERROR_CUOTA)
    con_cupo = LlmFalso(resultado=_quiz())
    _usar_llms(monkeypatch, {"clave-1": sin_cupo, "clave-2": con_cupo})

    _generar()
    _generar()

    assert sin_cupo.llamadas == 1  # la segunda vez ni la prueba
    assert con_cupo.llamadas == 2


def test_si_todas_las_keys_estan_agotadas_lanza_error_generacion(monkeypatch):
    _usar_llms(
        monkeypatch,
        {"clave-1": LlmFalso(error=ERROR_CUOTA), "clave-2": LlmFalso(error=ERROR_CUOTA)},
    )
    with pytest.raises(orq.ErrorGeneracion) as error:
        _generar()
    assert "todas las API keys" in str(error.value)


def test_un_error_que_no_es_de_cuota_no_rota_de_key(monkeypatch):
    con_error = LlmFalso(error=RuntimeError("falló la red"))
    otra = LlmFalso(resultado=_quiz())
    _usar_llms(monkeypatch, {"clave-1": con_error, "clave-2": otra})

    with pytest.raises(orq.ErrorGeneracion):
        _generar()

    assert otra.llamadas == 0


def test_obtener_api_keys_junta_las_variables_sin_repetir(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEYS", " a , b ,a,, c ")
    monkeypatch.setattr(orq, "_obtener_api_keys", _obtener_api_keys_real)

    assert orq._obtener_api_keys() == ["a", "b", "c"]