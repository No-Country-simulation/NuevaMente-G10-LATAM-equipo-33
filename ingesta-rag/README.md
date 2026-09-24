# Módulo ingesta-rag

Módulo encargado de la ingesta y preparación de documentos para el sistema RAG de NuevaMente.

## Componentes

### Chunking

El componente `chunker.py` divide el contenido de un documento en fragmentos (`chunks`) para su posterior procesamiento mediante embeddings e indexación en un vector store o base de datos vectorial.

Actualmente utiliza una estrategia que:

* Normaliza espacios excesivos.
* Separa inicialmente el contenido por párrafos.
* Divide párrafos demasiado extensos por frases.
* Genera fragmentos de aproximadamente 1000 caracteres.
* Mantiene un solapamiento configurable entre fragmentos.

### Uso

```python
from ingesta_rag.chunker import dividir_texto

chunks = dividir_texto(texto)

for chunk in chunks:
    print(chunk)
```

### Parámetros

`dividir_texto()` acepta los siguientes parámetros:

* `texto`: contenido completo del documento.
* `tamano`: tamaño aproximado de cada fragmento. Por defecto: `1000` caracteres.
* `solapamiento`: cantidad aproximada de caracteres compartidos entre fragmentos. Por defecto: `200` caracteres.

El solapamiento debe ser menor que el tamaño del fragmento.

## Dependencias

El componente de chunking utiliza únicamente la biblioteca estándar de Python (`re`), por lo que no requiere dependencias externas adicionales.
