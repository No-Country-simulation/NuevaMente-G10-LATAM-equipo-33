# Política de claves para embeddings

La política compartida está en `shared/gemini_policy.py`, sin dependencias de
instrumentación. Generación y evaluación todavía no la utilizan.

- Operación: una llamada completa a `embed_documents` o `embed_query`.
- Lote: partición de LangChain por cantidad (hasta 50 textos) y estimación de tokens.
  Cada lote tiene hasta cuatro intentos totales. `MAX_EMBEDDING_ATTEMPTS` puede
  reducir ese límite, pero nunca elevarlo. El enfriamiento no reinicia intentos.
- Ronda: una pasada por claves disponibles del mismo `KeyManager`. Al repetir
  una clave empieza otra ronda; el historial continúa entre operaciones.
- Un 429 rota inmediatamente. Dos 429 consecutivos de claves distintas provocan
  un enfriamiento antes del siguiente intento, si quedan intentos y claves elegibles.
  Se toma el mayor `Retry-After`/`RetryInfo` de ese par; sin indicación se usan 5 s.
  Hay como máximo un enfriamiento por operación, compartido entre todos sus lotes.
- Tres rondas consecutivas con 429 de una clave la ponen en cuarentena 60 s.
  Se omite sin borrarla; si no hay claves disponibles, se finaliza sin esperar.
  Al expirar la cuarentena empieza una nueva ventana de prueba. Un éxito reinicia
  los fallos consecutivos de esa clave. Un error distinto de 429 rompe esa secuencia.
- 401 y razones estructuradas de clave inválida/expirada excluyen la clave solo
  durante la operación. 403, 503, validación y errores desconocidos finalizan.
  No se cambia el modelo de embeddings para evitar incompatibilidades del índice.
- Un 429 con `QuotaFailure` y un identificador de cuota diaria (`PerDay`/`Daily`)
  detiene conservadoramente toda la operación. No se deduce cuota diaria de un
  mensaje, un 429 genérico o la duración de `RetryInfo`.
- Los errores se clasifican por atributos HTTP/estado y hasta cinco causas.
  No se interpretan mensajes ni se registran claves, sufijos, documentos o excepciones.
- Se mantiene la rotación preventiva tras dos lotes exitosos. No hay pausas
  adicionales entre lotes. El SDK recibe `HttpRetryOptions(attempts=1)` por petición.

El estado es temporal y propio de cada instancia/proceso. Indexación y búsqueda
tienen gestores distintos; no comparten cuarentena ni enfriamientos entre sí o
con otros workers. Reiniciar el proceso pierde el historial. La pausa sugerida
por el proveedor puede superar 5 s; no existe plazo global por documento.

La adaptación de LangChain utiliza `_build_config` y `_prepare_batches`, verificados
contra la versión instalada. Al actualizar LangChain/GenAI se debe repetir la prueba
offline que cuenta peticiones SDK y comprueba la partición de lotes.

Pruebas sin servicios externos:

```powershell
.\.venv-integracion\Scripts\python.exe -B -m pytest backend/tests/test_embedding_policy.py -q -p no:cacheprovider
```
