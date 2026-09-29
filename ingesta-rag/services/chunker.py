"""
Módulo de Chunking / Segmentación de Texto
Implementa la lógica pura de segmentación por párrafos y frases respetando solapamientos.
"""

import re
import logging
# Usaremos variables de ambiente para CHUNK_SIZE, CHUNK_OVERLAP
from utils.config import CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)

def dividir_texto(
    texto: str,
    tamano: int = CHUNK_SIZE,           # Variable de ambiente
    solapamiento: int = CHUNK_OVERLAP   # Variable de ambiente
) -> list[str]:
    """
    Divide un texto en fragmentos intentando respetar
    párrafos y frases.

    Parámetros:
    - texto: contenido completo del documento.
    - tamano: tamaño aproximado de cada fragmento.
    - solapamiento: cantidad aproximada de caracteres compartidos entre fragmentos.

    Retorna:
    - lista de fragmentos.
    """

    if not texto:
        return []

    if solapamiento >= tamano:
        raise ValueError(
            "El solapamiento debe ser menor que el tamaño del fragmento."
        )

    # Normalizar espacios excesivos
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto).strip()



    # Separar primero por párrafos - corregido por MAMT
    parrafos = re.split(r"\n\s*\n", texto)

    # Reservamos espacio para el solapamiento.  - corregido por MAMT
    # El chunk final nunca debe superar `tamano`.
    tamano_contenido = tamano - solapamiento

    fragmentos = []
    actual = ""

    for parrafo in parrafos:
        parrafo = parrafo.strip()

        if not parrafo:
            continue

        # Si el párrafo cabe en el chunk actual
        if len(actual) + len(parrafo) + 2 <= tamano_contenido:  # Corregido por MAMT
            actual = f"{actual}\n\n{parrafo}".strip()
            continue

        # Guardar el chunk actual
        if actual:
            fragmentos.append(actual)

        # Si el párrafo por sí solo es demasiado grande,
        # dividirlo por frases.
        if len(parrafo) > tamano_contenido:
            frases = re.split(r"(?<=[.!?])\s+", parrafo)

            actual = ""

            # *****************************************************************
            # Todo este bloque corregido por MAMT
            for frase in frases:
                frase = frase.strip()

                if not frase:
                    continue

                # La frase cabe dentro del espacio disponible.
                if len(frase) <= tamano_contenido:
                    if len(actual) + len(frase) + 1 <= tamano_contenido:
                        actual = f"{actual} {frase}".strip()
                    else:
                        if actual:
                            fragmentos.append(actual)

                        actual = frase

                    continue

                # ---------------------------------------------------------
                # La frase individual es demasiado grande.
                # Debemos dividirla sin perder contenido.
                # ---------------------------------------------------------

                if actual:
                    fragmentos.append(actual)
                    actual = ""

                inicio = 0

                while inicio < len(frase):
                    fin = min(inicio + tamano_contenido, len(frase))

                    # Intentar cortar en un espacio para no partir palabras.
                    if fin < len(frase):
                        corte = frase.rfind(" ", inicio, fin)

                        # Si no encontramos un espacio válido,
                        # hacemos un corte duro para garantizar el límite.
                        if corte <= inicio:
                            corte = fin
                    else:
                        corte = fin

                    trozo = frase[inicio:corte].strip()

                    if trozo:
                        fragmentos.append(trozo)

                    inicio = corte

                    # Saltar espacios que quedaron entre los fragmentos.
                    while inicio < len(frase) and frase[inicio].isspace():
                        inicio += 1


            # *****************************************************************

        else:
            actual = parrafo

    if actual:
        fragmentos.append(actual)

    # Añadir solapamiento entre chunks - Corregido por MAMT
    resultado = []

    for i, fragmento in enumerate(fragmentos):
        if i == 0:
            resultado.append(fragmento)
            continue

        # anterior = resultado[-1]   Antes
        anterior = fragmentos[i - 1]    # Cambio por MAMT

        palabras = anterior.split()
        solapamiento_texto = ""

        caracteres = 0

        for palabra in reversed(palabras):
            if caracteres + len(palabra) + 1 > solapamiento:
                break

            solapamiento_texto = f"{palabra} {solapamiento_texto}".strip()
            caracteres += len(palabra) + 1

        # ************************************************************************************
        # Bloque corregido por MAMT

        # El fragmento ya fue construido con espacio reservado
        # para el solapamiento.
        nuevo_fragmento = f"{solapamiento_texto} {fragmento}".strip()

        resultado.append(nuevo_fragmento)

        # ************************************************************************************


    return resultado
