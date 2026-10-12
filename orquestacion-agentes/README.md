# orquestacion-agentes

Recibe el contexto recuperado por `ingesta-rag` y usa Gemini (IA de Google) para generar contenido educativo adaptado al perfil, formato y nicho pedidos.

## Cómo instalarlo y correrlo

1. Conseguí tus API Keys de Gemini gratis en: https://aistudio.google.com/apikey

2. Entrá a la carpeta `orquestacion-agentes` y creá el entorno:

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

3. Copiá `.env.example`, renombralo a `.env` y pegá tus keys:

```
GEMINI_API_KEYS="tu_key_1,tu_key_2,tu_key_3"
```

4. Corré el ejemplo:

```
python main.py
```

Muestra en pantalla un quiz de ejemplo.

## Variables de entorno

- `GEMINI_API_KEYS`: una o varias keys separadas por coma. Si una agota su cupo (error 429), usa la siguiente. También se acepta `GOOGLE_API_KEY` o `GEMINI_API_KEY` con una sola key.
- `GEMINI_MODEL`: opcional. Modelo principal. Por defecto `gemini-3.6-flash`.
- `GEMINI_MODEL_RESPALDO`: opcional. Si el modelo principal está saturado (error 503), usa este. Por defecto `gemini-3.8-flash`.

El archivo `.env` nunca se sube a git.

## Cómo se usa

```python
from main import generar_contenido_adaptado

contenido = generar_contenido_adaptado(
    documento_titulo="Introduccion a la Arquitectura de Redes VCN en OCI",
    contexto=chunks,               # lo que devuelve buscar_contexto de ingesta-rag
    perfil_destinatario="Principiante",
    formato_salida="Quiz",
    nicho_sector="General",
    nivel_detalle="Didactico",
)
```

Devuelve un `ContenidoGenerado` (definido en `shared/contratos.py`).

## Parámetros

- `documento_titulo`: obligatorio.
- `contexto`: obligatorio. Lista de chunks con `texto`, `score` y `fuente`. No puede estar vacía.
- `perfil_destinatario`: obligatorio. Texto libre (por ejemplo "Principiante" o "Líder Técnico").
- `formato_salida`: obligatorio. `Flashcards` o `Quiz`. No importa cómo esté escrito: `quiz`, `QUIZ`, `Flash cards` o `flash-cards` se aceptan igual.
- `nicho_sector`: opcional. Si viene vacío usa "General".
- `nivel_detalle`: opcional. Si viene vacío usa "Didactico".

## Qué devuelve en `items`

- Flashcards: `frente`, `dorso`, `pista_didactica`.
- Quiz: `pregunta`, `opciones`, `respuesta_correcta`, `justificacion`.

## Errores

Todos heredan de `ErrorOrquestacion` y se importan desde `main`:

- `EntradaInvalida`: falta un campo obligatorio o el contexto está vacío. Es un `ValueError`.
- `FormatoNoSoportado`: el formato pedido no existe. Es una `EntradaInvalida`.
- `ErrorGeneracion`: falló la generación (falta la API key, se agotó el cupo de todas las keys, los modelos están saturados o Gemini devolvió algo vacío). El mensaje es apto para mostrar al usuario.

Si `buscar_contexto` no encuentra nada y el contexto queda vacío, el módulo lanza `EntradaInvalida` en vez de inventar contenido.

## Pruebas

```
python -m pytest -q
```

No llaman a Gemini.

## Si algo falla

- Si dice que no encuentra "shared": asegurate de estar parado dentro de la carpeta `orquestacion-agentes` y hacé `git pull origin main`.
- Si dice que el modelo no existe: puede que Google haya cambiado el nombre. Cambialo con `GEMINI_MODEL` en el `.env`.
- Si da error 503: el modelo está saturado, el módulo pasa solo al modelo de respaldo.