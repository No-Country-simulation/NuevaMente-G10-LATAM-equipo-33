# Módulo evaluacion

Evalúa la calidad del contenido educativo generado por `orquestacion-agentes`. Usa un modelo de Gemini como juez y compara el contenido contra el contexto original que devolvió `ingesta-rag`.

## Qué hace

Para cada ítem del contenido generado, el juez decide si la fuente lo respalda. El score se calcula por código, no lo inventa el modelo:

- respaldado: 1
- parcial: 0.5
- no respaldado: 0

El `anclaje_fuente_score` es el promedio de todos los ítems, entre 0 y 1. Si el juez omite un ítem, cuenta como 0. También evalúa la claridad pedagógica para el perfil del destinatario (Alta, Media o Baja).

En los quizzes se evalúan la pregunta, la respuesta correcta y la justificación. Las opciones incorrectas no se penalizan.

## Instalación

Desde la raíz del repo:

```
pip install -r evaluacion/requirements.txt
```

## Variables de entorno

Se leen del archivo `evaluacion/.env` (ver `.env.example`).

- `GEMINI_API_KEYS`: keys de Gemini separadas por coma. Se usa la primera.
- `GOOGLE_API_KEY` o `GEMINI_API_KEY`: alternativa con una sola key. Tiene prioridad si está definida.
- `GEMINI_MODEL`: opcional. Por defecto `gemini-3.6-flash`.

El archivo `.env` nunca se sube a git.

## Uso

```python
from evaluacion.services.evaluador import evaluar_contenido

evaluacion = evaluar_contenido(
    contenido_generado=contenido,     # ContenidoGenerado (de orquestacion-agentes)
    contexto=chunks,                  # list[ChunkResultado] (de ingesta-rag)
    perfil_destinatario="principiante",
    formato_salida="flashcards",
)
```

Los tipos `ContenidoGenerado`, `ChunkResultado` y `EvaluacionCalidad` están en `shared/contratos.py`.

## Qué devuelve

Un `EvaluacionCalidad`:

- `anclaje_fuente_score`: número entre 0 y 1.
- `claridad_pedagogica`: "Alta", "Media" o "Baja".
- `observaciones`: resumen en texto. Si hay ítems no respaldados, termina con `Ítems a revisar (índice desde 0): [...]`.

## Casos especiales

- Si el contenido no tiene ítems, devuelve score 0.0 y claridad "Baja", sin llamar a Gemini.
- Si Gemini falla (cuota, red, key inválida), no lanza error. Devuelve score 0.0, claridad "No evaluada" y una observación que explica el problema. Así el backend siempre puede armar la `RespuestaFinal`.

## Probar el módulo

Con Gemini real (necesita la key en el `.env`):

```
cd evaluacion
python demo.py
```

Pruebas automáticas (no llaman a Gemini):

```
cd evaluacion
python -m pytest -q
```

## Estructura

```
evaluacion/
  prompts/juez.py        prompt del juez
  schemas/juez.py        formato de respuesta del juez
  services/evaluador.py  función evaluar_contenido
  tests/                 pruebas
  demo.py                ejemplo con Gemini real
```