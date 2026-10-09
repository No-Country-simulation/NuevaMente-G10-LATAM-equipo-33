"""Pruebas del evaluador. No llaman a la API."""

from schemas.juez import VeredictoItem
from services import evaluador


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