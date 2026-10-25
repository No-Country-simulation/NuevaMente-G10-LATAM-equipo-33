# Generación y evaluación: claves y modelos

Los dos wrappers usan `invoke_models` y `classify_model_failure` de
`shared/gemini_policy.py`. La clasificación y la operación de embeddings
permanecen sin cambios. No se añade instrumentación de rendimiento.

| Evidencia | Acción |
|---|---|
| HTTP 429 / `RESOURCE_EXHAUSTED` | Siguiente clave del modelo; al agotarlas, respaldo. |
| 401 / `UNAUTHENTICATED` / razón estructurada de clave inválida o expirada | Excluir esa clave durante esta invocación, también en el respaldo. |
| 403 / `PERMISSION_DENIED` | Finalizar; no asumir que otra clave resuelve permisos. |
| 503 / `UNAVAILABLE` | Siguiente modelo, sin recorrer más claves del actual. |
| Timeout, 408/504, red, 500/502 | Un reintento adicional por modelo, luego respaldo o finalizar. |
| Parsing, validación Pydantic o resultado estructurado incorrecto/vacío | Finalizar sin rotación. |
| Otros errores o ausencia de evidencia reconocida | Finalizar sin inferir códigos del mensaje. |

Un 429 con cuota diaria confirmada evita recorrer más claves de ese modelo;
todavía puede probarse el respaldo, cuya cuota puede ser distinta.

Para M modelos y K claves únicas hay como máximo M × (K + 1) intentos de
preparación, incluyendo los fallidos antes de llamar al SDK. Cada uno contiene
como máximo un invoke. No hay sleeps ni repetición de la misma pareja por cuota.
`max_retries=1` se conserva y se verifica con el SDK instalado: un intento HTTP
por invoke. Se configura timeout de 60 segundos por petición. Estos límites no
son un plazo global estricto por documento.

Se conserva el orden de las claves y la última exitosa por módulo. Las exclusiones
no modifican `.env`, no se comparten con embeddings y no persisten entre llamadas.
Los logs solo indican intento, categoría y HTTP; no modelos configurados, claves,
mensajes del proveedor, prompts ni contenido. Los errores públicos son controlados.

Generación mantiene `ErrorGeneracion` y los formatos Flashcards/Quiz. Evaluación
mantiene el cálculo de scores y devuelve `No evaluada` cuando falla el juez. No se
cambia la decisión del backend sobre guardar/presentar una evaluación no disponible.

## Modelos del juez

- Principal: `GEMINI_EVALUATION_MODEL`, luego `GEMINI_MODEL`, luego el predeterminado.
- Respaldo: `GEMINI_EVALUATION_MODEL_RESPALDO` si existe; de lo contrario,
  `GEMINI_MODEL_RESPALDO` o el predeterminado.
- Un respaldo específico vacío desactiva el respaldo del juez. No definir las dos
  variables específicas conserva la selección anterior. Modelos repetidos se deduplican.
- Estas variables son opcionales; no se modifica el `.env` en esta intervención.

Validación sin servicios externos:

```powershell
.\.venv-integracion\Scripts\python.exe -B -m pytest backend/tests/test_model_rotation.py evaluacion/tests/test_evaluador.py -q -p no:cacheprovider
```
