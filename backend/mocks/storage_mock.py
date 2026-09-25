from shared.contratos import AlmacenamientoOCI


def almacenar_contenido(
    contenido: dict,
) -> AlmacenamientoOCI:

    return AlmacenamientoOCI(
        bucket="mock-nuevamente",
        objeto_id="mock/contenido-001.json",
        status_upload="simulado",
    )