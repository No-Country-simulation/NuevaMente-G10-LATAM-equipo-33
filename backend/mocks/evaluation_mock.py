from shared.contratos import (
    ChunkResultado,
    ContenidoGenerado,
    EvaluacionCalidad,
)


def evaluar_contenido(
    contenido: ContenidoGenerado,
    contexto: list[ChunkResultado],
) -> EvaluacionCalidad:

    return EvaluacionCalidad(
        anclaje_fuente_score=0.95,
        claridad_pedagogica="Alta",
        observaciones="Evaluación simulada para pruebas del backend.",
    )