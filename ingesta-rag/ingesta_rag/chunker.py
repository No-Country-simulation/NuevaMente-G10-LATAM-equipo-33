import re


def dividir_texto(texto, tamano=1000, solapamiento=200):
    """
    Divide un texto en fragmentos intentando respetar
    párrafos y frases.

    Parámetros:
    - texto: contenido completo del documento.
    - tamano: tamaño aproximado de cada fragmento.
    - solapamiento: cantidad aproximada de caracteres
      compartidos entre fragmentos.

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

    # Separar primero por párrafos
    parrafos = re.split(r"\n\s*\n", texto)

    fragmentos = []
    actual = ""

    for parrafo in parrafos:
        parrafo = parrafo.strip()

        if not parrafo:
            continue

        # Si el párrafo cabe en el chunk actual
        if len(actual) + len(parrafo) + 1 <= tamano:
            actual = f"{actual}\n\n{parrafo}".strip()
            continue

        # Guardar el chunk actual
        if actual:
            fragmentos.append(actual)

        # Si el párrafo por sí solo es demasiado grande,
        # dividirlo por frases.
        if len(parrafo) > tamano:
            frases = re.split(r"(?<=[.!?])\s+", parrafo)

            actual = ""

            for frase in frases:
                if len(actual) + len(frase) + 1 <= tamano:
                    actual = f"{actual} {frase}".strip()
                else:
                    if actual:
                        fragmentos.append(actual)

                    actual = frase.strip()
        else:
            actual = parrafo

    if actual:
        fragmentos.append(actual)

    # Añadir solapamiento entre chunks
    resultado = []

    for i, fragmento in enumerate(fragmentos):
        if i == 0:
            resultado.append(fragmento)
            continue

        anterior = resultado[-1]

        palabras = anterior.split()
        solapamiento_texto = ""

        caracteres = 0

        for palabra in reversed(palabras):
            if caracteres + len(palabra) + 1 > solapamiento:
                break

            solapamiento_texto = f"{palabra} {solapamiento_texto}".strip()
            caracteres += len(palabra) + 1

        nuevo_fragmento = f"{solapamiento_texto} {fragmento}".strip()
        resultado.append(nuevo_fragmento)

    return resultado
