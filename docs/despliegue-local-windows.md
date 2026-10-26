# NuevaMente: instalación y ejecución local en Windows 10/11

Esta guía corresponde a `fix/integracion-final-oci`, con Python 3.12 y un único
entorno `.venv-integracion`. Todos los comandos son para PowerShell, desde la
raíz `NuevaMente-Final-Git`, salvo cuando se indique otra cosa.

Hay dos recorridos:

| Recorrido | Configuración | Requiere |
|---|---|---|
| Local básico | `STORAGE_BACKEND=local` | Gemini y disco local. No configurar Oracle. |
| Local con Oracle | `STORAGE_BACKEND=oci` | Gemini, bucket, perfil OCI y clave privada de API. |

Ambos instalan las mismas dependencias centralizadas. En modo local el SDK OCI
puede estar instalado sin usar credenciales ni realizar operaciones Oracle.

## 1. Requisitos previos

- Windows 10 u 11 y PowerShell.
- Python **3.12** con el lanzador `py` instalado.
- Git si se obtiene el proyecto mediante repositorio; Visual Studio Code es opcional.
- API Keys de Gemini con acceso a los modelos configurados y cuota disponible.
- Para el recorrido Oracle: acceso a OCI, un bucket y permisos de creación y lectura
  de objetos para el usuario autenticado. Tener una API Key no concede permisos IAM.

Comprobar las herramientas instaladas:

```powershell
py -3.12 --version
git --version
```

Si falta Python, instalar Python 3.12 y su lanzador. Si falta Git, instalarlo antes
de utilizar el recorrido de clonación. Abrir una terminal nueva después de instalar.

## 2. Obtener la versión del proyecto y situarse en la raíz

Si ya se tiene la copia que se probó, utilizar esa carpeta:

```powershell
Set-Location -LiteralPath (Read-Host "Ruta de la carpeta NuevaMente-Final-Git")
git branch --show-current
Test-Path .\requirements-integracion.txt
Test-Path .\backend\app.py
```

La rama debe ser `fix/integracion-final-oci` y ambas comprobaciones deben devolver
`True`. Si se necesita cambiar de rama, revisar primero `git status`; no descartar
cambios ni forzar el cambio. Cuando corresponda, usar `git switch fix/integracion-final-oci`.

Para una copia nueva, **solo si el equipo ya publicó esa rama con la versión completa**,
desde la carpeta donde se alojará el proyecto:

```powershell
$repositorioNuevaMente = Read-Host "URL del repositorio entregado por el equipo"
git clone --branch fix/integracion-final-oci $repositorioNuevaMente NuevaMente-Final-Git
Set-Location .\NuevaMente-Final-Git
```

Los cambios sin commit de la copia probada no se obtienen con `git clone`.
Si aún no están publicados, solicitar al equipo la entrega completa del árbol de
trabajo probado. La rama por sí sola no garantiza disponer de esos archivos.
No copiar `.env`, `.oci/` ni entornos virtuales de otra persona.

## 3. Crear y activar el entorno virtual único

Desde la raíz, crear el entorno **si no existe**:

```powershell
if (-not (Test-Path .\.venv-integracion)) {
    py -3.12 -m venv .venv-integracion
}
.\.venv-integracion\Scripts\Activate.ps1
python --version
python -c "import sys; print(sys.executable)"
python -m pip --version
python -m pip install --upgrade pip
```

Python debe indicar 3.12 y el ejecutable debe pertenecer a `.venv-integracion`.
No reutilizar automáticamente un entorno creado con otra versión de Python.

Si PowerShell bloquea `Activate.ps1`, y la política de la organización lo permite,
habilitar scripts únicamente para la terminal actual y volver a activar:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv-integracion\Scripts\Activate.ps1
```

Como alternativa, invocar directamente `.\.venv-integracion\Scripts\python.exe`
en lugar de `python`, sin cambiar la política. Para salir del entorno activado:

```powershell
deactivate
```

## 4. Instalar las dependencias centralizadas

Con el entorno activado, utilizar exclusivamente:

```powershell
python -m pip install -r requirements-integracion.txt
python -m pip check
```

`requirements-integracion.txt` incluye mediante `-r` los manifiestos de Backend y
Frontend de la raíz, y agrega herramientas de pruebas. Cubre FastAPI, Uvicorn,
Streamlit, HTTP, extracción PDF/DOCX/PPTX, RAG/ChromaDB, generación/evaluación Gemini
y `oci==2.189.0`. No sustituirlo por los `requirements.txt` individuales de módulos.

No continuar si la instalación o `pip check` reportan errores. Estos manifiestos
seleccionan dependencias principales; no constituyen un lock de todas las transitivas.

## 5. Configurar `.env`: recorrido local básico

Crear la copia de la plantilla sin sobrescribir una configuración existente:

```powershell
if (-not (Test-Path .\.env)) {
    Copy-Item -LiteralPath .\.env.template -Destination .\.env
}
notepad .\.env
```

Completar `GEMINI_API_KEYS` con claves reales separadas por comas. Ejemplo ficticio
de formato, **no utilizable como credencial**:

```ini
GEMINI_API_KEYS="CLAVE_1_DE_EJEMPLO,CLAVE_2_DE_EJEMPLO"
BACKEND_URL=http://localhost:8000
API_PREFIX=/api/v1
API_TIMEOUT_SECONDS=300
STORAGE_BACKEND=local
DOCUMENTS_PATH=./data/documents
GENERATED_PATH=./data/generated
CHROMA_PERSIST_DIR=./chroma_db
NOMBRE_COLECCION=nuevamente_documentos
```

Guardar `.env` como UTF-8. Las claves vacías impiden arrancar el Backend: RAG exige
`GEMINI_API_KEYS` incluso con almacenamiento local. La interfaz puede abrir aunque
el Backend falle, por lo que eso no valida la configuración.

Configuración de modelos:

- `GEMINI_MODEL` y `GEMINI_MODEL_RESPALDO`: principal y respaldo de generación.
- `GEMINI_EVALUATION_MODEL` y `GEMINI_EVALUATION_MODEL_RESPALDO`: opcionales para
  el juez. Dejarlas comentadas conserva la selección general; un respaldo específico
  vacío desactiva el respaldo del juez.
- Los modelos de la plantilla son referencias del proyecto. Deben estar disponibles
  para la cuenta utilizada; no se garantiza acceso solo por escribir su nombre.
- `MODELO_EMBEDDINGS` define los embeddings del índice. No cambiarlo sobre una
  colección existente sin planificar compatibilidad de modelo y dimensiones.

`CHUNK_SIZE`, `CHUNK_OVERLAP` y `TOP_K` controlan segmentación y recuperación.
`MAX_EMBEDDING_ATTEMPTS=4` limita los intentos por lote; valores mayores no elevan
el máximo efectivo. El enfriamiento y la cuarentena tienen reglas fijas en código,
no variables adicionales del `.env`. El máximo de 10 elementos también es fijo.

El cliente reconoce opcionalmente `GOOGLE_API_KEY` y `GEMINI_API_KEY` en generación
y evaluación, con prioridad sobre el pool. RAG necesita el pool `GEMINI_API_KEYS`.
Para una instalación sencilla, usar únicamente este último y evitar variables
alternativas heredadas del sistema.

Frontend y Backend cargan el `.env` de la raíz. Las variables ya exportadas en el
proceso tienen prioridad; reiniciar ambas terminales/procesos al cambiar configuración.
`APP_DEBUG=false` evita activar debug. `API_HOST`/`API_PORT` no configuran por sí
solos Uvicorn: prevalecen los argumentos del comando de arranque.

Los originales y resultados relativos se resuelven contra la raíz del proyecto.
La ruta relativa de Chroma depende del directorio de trabajo: **arrancar siempre
desde la raíz**. Chroma es independiente de `STORAGE_BACKEND`; permanece en disco
también cuando originales y JSON se guardan en Oracle.

Para el recorrido básico, saltar el paso 6 y continuar en el 7.

## 6. Configurar Oracle: solo para `STORAGE_BACKEND=oci`

Usar [oci_storage/README.md](../oci_storage/README.md) como referencia de creación
del bucket y de la API Key. Es una demostración independiente: no sustituye esta guía,
no requiere ejecutar `oci_storage/main.py` y no define toda la configuración de NuevaMente.

### 6.1. Usuario, bucket y par de claves de API

1. En la consola OCI, seleccionar el compartimento y crear o identificar el bucket
   en Object Storage. Anotar su nombre, namespace y región.
2. Abrir la configuración del usuario que realizará las operaciones. En la sección
   de API Keys (Tokens and keys / API Keys, según la consola), agregar una clave.
3. Generar un par de claves y descargar la privada, o registrar la pública de un par
   de API ya creado. La clave pública debe quedar asociada a ese mismo usuario.
4. Copiar los datos del perfil que ofrece OCI: usuario, tenancy, fingerprint y región.
   Verificar con el administrador los permisos de creación y lectura sobre el bucket.

**La clave privada de API de OCI no es la clave SSH de una instancia.** La primera
firma solicitudes al servicio; la segunda inicia sesiones SSH. No intercambiarlas.

Crear la carpeta desde la raíz:

```powershell
New-Item -ItemType Directory -Path .\.oci -Force | Out-Null
```

Guardar la clave privada de API en `.oci/`. Puede llamarse `oci_api_key.pem`, pero
debe usarse el nombre real del archivo descargado, sin añadir una extensión duplicada.
Crear también `.oci/config`, **sin extensión `.txt`**. Ejemplo de estructura:

```text
NuevaMente-Final-Git/
  .oci/
    config
    oci_api_key.pem
```

### 6.2. Perfil `.oci/config`

El contenido siguiente es ficticio; reemplazar todos sus valores antes de usarlo:

```ini
[DEFAULT]
user=ocid1.user.oc1..EJEMPLO
fingerprint=FINGERPRINT_DE_EJEMPLO
tenancy=ocid1.tenancy.oc1..EJEMPLO
region=REGION_DE_EJEMPLO
key_file=RUTA_A_LA_CLAVE_PRIVADA
```

| Propiedad | Significado y procedencia |
|---|---|
| `user` | OCID del usuario al que se registró la clave pública; aparece en sus detalles/perfil. |
| `fingerprint` | Huella de esa API Key pública, mostrada en OCI. No es el contenido del `.pem`. |
| `tenancy` | OCID de la tenancy; disponible en los detalles de tenancy y en el perfil sugerido por OCI. |
| `region` | Identificador de región del bucket, obtenido de su ubicación en OCI. |
| `key_file` | Ruta al archivo privado correspondiente a la pública registrada. |

Usar una ruta absoluta para `key_file`, sin depender del directorio de arranque.
Para obtenerla sin mostrar el contenido de la clave, adaptando el nombre real:

```powershell
(Resolve-Path -LiteralPath .\.oci\oci_api_key.pem).Path
```

Copiar esa ruta a `key_file`; puede escribirse con `/` como separador en Windows.
Mantener estos archivos accesibles únicamente para las personas autorizadas.

### 6.3. Activar OCI en `.env`

```ini
STORAGE_BACKEND=oci
OCI_CONFIG_FILE=./.oci/config
OCI_PROFILE=DEFAULT
OCI_NAMESPACE=TU_NAMESPACE
OCI_BUCKET_NAME=TU_BUCKET
OCI_AUTH_MODE=api_key
OCI_REGION=""
```

Sustituir `TU_NAMESPACE` y `TU_BUCKET` por los valores del bucket. `OCI_REGION` vacía
conserva la región de `[DEFAULT]`; si se define, reemplaza la región de ese perfil.
El Backend resuelve `OCI_CONFIG_FILE` relativo a la raíz y entrega `OCI_PROFILE` al SDK.

`OCI_TENANCY_OCID` aparece en el ejemplo histórico, pero el adaptador actual no lee
esa variable del `.env`: utiliza `tenancy` de `.oci/config`. No hace falta duplicarla.
`instance_principal` está soportado para una instancia OCI, pero queda fuera de este
recorrido local: aquí se conserva `OCI_AUTH_MODE=api_key`.

### 6.4. Comprobar exclusiones de Git

En esta versión `.gitignore` debe excluir `.env`, `.oci/` y `.venv-integracion/`:

```powershell
git check-ignore -- .env .oci/config .oci/oci_api_key.pem .venv-integracion/Scripts/python.exe
```

Adaptar el nombre del `.pem` si corresponde. Deben mostrarse las cuatro rutas.
La plantilla `.env.template` sí se puede versionar. Nunca compartir ni subir API Keys,
claves privadas, perfiles reales o tokens; no pegar su contenido en capturas o reportes.
Si un secreto ya estaba rastreado, `.gitignore` no lo retira del historial: solicitar
su revisión y rotación antes de publicar. No realizar limpiezas automáticas.

## 7. Arrancar el Backend: primera terminal

Desde la raíz, con `.env` ya configurado:

```powershell
.\.venv-integracion\Scripts\Activate.ps1
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Esperar el mensaje de inicio completo y la dirección `http://127.0.0.1:8000`.
No debe aparecer un traceback de importación o configuración. Dejar esta terminal
abierta. La escucha en `127.0.0.1` es para uso local, no exposición a otras máquinas.

En otra terminal o en el navegador, comprobar la salud:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health" -Method Get
```

Debe devolver `status=ok`. La documentación interactiva está en
`http://127.0.0.1:8000/docs`. Health acredita el proceso API; no comprueba Gemini,
cuota, extracción, Chroma ni acceso al bucket. Si se cambia `API_PREFIX`, ajustar
la URL de health y la configuración del cliente de forma consistente.

## 8. Arrancar el Frontend: segunda terminal

Abrir otra terminal PowerShell y situarse en la misma raíz del proyecto:

```powershell
Set-Location -LiteralPath (Read-Host "Ruta de la carpeta NuevaMente-Final-Git")
.\.venv-integracion\Scripts\Activate.ps1
python -m streamlit run interfaz/app.py
```

Abrir **http://localhost:8501**. Ambas terminales deben permanecer abiertas.
Streamlit envía las peticiones al Backend desde su proceso Python. Conservar
`BACKEND_URL=http://localhost:8000` para este despliegue local.

Para detener cada servicio, usar `Ctrl+C` en su terminal; después, `deactivate`.

## 9. Probar la aplicación y distinguir una simulación

**Estas comprobaciones sí consumen Gemini y, en modo OCI, escriben/leen objetos.**
Realizarlas cuando el operador desee validar la integración, con documentos de prueba.

1. Cargar un PDF con texto seleccionable, DOCX o PPTX válido, no vacío y de hasta
   10 MiB (`MAX_UPLOAD_MB=10`). No se incluye OCR. Office considera texto y tablas;
   algunos elementos gráficos o diseños complejos pueden no extraerse.
2. Elegir perfil, nicho, nivel y Flashcards o Quiz. Generar el contenido.
3. Revisar la terminal del Backend: debe recibir `POST /api/v1/adapt` y responder
   200. Los errores o la ausencia de petición requieren revisar la conexión.
4. Comprobar que el contenido corresponde al documento y contiene entre **1 y 10**
   flashcards/preguntas. El prompt pide un máximo de 10 y Python conserva los primeros
   10 si Gemini devuelve más. Cero elementos produce error.
5. Revisar que la calidad no sea `No evaluada`. Actualmente el Backend puede guardar
   y devolver éxito aunque falle el juez; eso no acredita una evaluación real completa.
6. Confirmar persistencia mediante el JSON/archivo local o los objetos del bucket.
   La base `chroma_db/chroma.sqlite3` debe existir tras indexar. Su existencia sola
   no acredita una recuperación correcta para el documento actual.

**El Frontend conserva un simulador ante errores HTTP, timeout o Backend caído.**
No muestra una etiqueta inequívoca de simulación. Puede presentar contenido fijo,
score `0.95` y un mensaje ficticio de OCI con un objeto `adaptaciones/<título>.json`.
Esos indicios no sustituyen una comprobación: ni la pantalla ni “Guardado en OCI”
demuestran éxito real. El flujo productivo usa referencias con UUID, y la modalidad
real aparece en `metadatos.storage_backend`.

En modo local, comprobar originales en `data/documents/` y JSON en `data/generated/`.
La pantalla actual no presenta un detalle específico del almacenamiento local.
En OCI, comprobar objetos bajo `adaptaciones/<uuid>/`; Chroma sigue siendo local.
Un fallo posterior al guardado del original puede dejarlo persistido sin resultado:
no hay transacción conjunta ni limpieza automática.

### Verificación directa para evitar el simulador

Con ambos servicios disponibles, abrir una tercera terminal en la raíz, activar el
entorno y ejecutar el siguiente comando. Solicita un archivo existente y envía una
petición multipart real; recupera el resultado guardado y compara los bytes originales.
No imprime credenciales ni elimina archivos u objetos. Cada ejecución crea nuevos
originales/resultados y consume servicios según la configuración.

```powershell
.\.venv-integracion\Scripts\Activate.ps1
$archivoPrueba = Read-Host "Ruta de un PDF, DOCX o PPTX de prueba"
@'
from pathlib import Path
import sys
import requests
from interfaz.client_config import ADAPT_URL, API_TIMEOUT_SECONDS
from backend.core.config import settings
from backend.services.storage_service import StorageService

path = Path(sys.argv[1])
params = dict(perfil_destinatario="Principiante", formato_salida="Flashcards",
              nicho_sector="General", nivel_detalle="Intermedio")
with path.open("rb") as source:
    response = requests.post(ADAPT_URL, data=params,
        files={"archivo": (path.name, source, "application/octet-stream")},
        timeout=API_TIMEOUT_SECONDS)
print("HTTP:", response.status_code)
response.raise_for_status()
body = response.json()
assert body["status"] == "exito"
assert 1 <= len(body["contenido_adaptado"]["items"]) <= 10
assert body["evaluacion_calidad"]["claridad_pedagogica"] != "No evaluada"
assert body["metadatos"]["storage_backend"] == settings.storage_backend
storage = StorageService()
assert storage.recuperar_original(body["metadatos"]["documento_original"]) == path.read_bytes()
stored = storage.recuperar_resultado(body["metadatos"]["resultado_generado"])
assert stored.model_dump(mode="json") == body
print("OK: respuesta directa, evaluacion disponible y persistencia verificada.")
print("Elementos:", len(body["contenido_adaptado"]["items"]))
'@ | python -B - $archivoPrueba
if ($LASTEXITCODE -ne 0) {
    throw "La validacion real no se completo; revisar la terminal del Backend."
}
```

Para validar Quiz, cambiar únicamente `formato_salida="Flashcards"` por
`formato_salida="Quiz"`. Repetir con los tres formatos de archivo. La generación
rechaza contexto vacío: una respuesta directa válida confirma que hubo contexto
utilizable, aunque no mide por sí sola la relevancia o fidelidad de cada fragmento.

## 10. Pruebas offline opcionales

Estas suites existentes sustituyen los servicios externos. No ejecutar los ejemplos
de `oci_storage/main.py` ni confundir las pruebas offline con validación de credenciales.

```powershell
python -B -m pytest backend/tests/test_generation_limit.py backend/tests/test_model_rotation.py backend/tests/test_embedding_policy.py backend/tests/test_document_upload.py backend/tests/test_storage.py evaluacion/tests/test_evaluador.py -q -p no:cacheprovider
```

Ejecutarlas desde una copia Git que conserve las referencias usadas por las pruebas
históricas (`origin/oci-storage` y `HEAD`). La prueba que compara ejemplos y funciones
visuales requiere esas referencias; una entrega sin `.git` no permite esa comprobación.

## 11. Problemas frecuentes

| Problema | Comprobación y solución |
|---|---|
| Entorno no activado | Revisar `python -c "import sys; print(sys.executable)"` y activar `.venv-integracion`, o invocar su Python directamente. |
| `ModuleNotFoundError: backend`, `shared` o `ingesta_rag` | Volver a la raíz y usar `python -m uvicorn backend.app:app`; no arrancar dentro de `backend/` ni renombrar paquetes. |
| Dependencias faltantes | Con el entorno correcto, repetir `python -m pip install -r requirements-integracion.txt` y `python -m pip check`. |
| Puerto 8000/8501 ocupado | Identificar el proceso con los comandos siguientes. Detener únicamente el servicio propio identificado con `Ctrl+C`, o elegir otro puerto. |
| Claves Gemini ausentes | Completar `GEMINI_API_KEYS` en `.env`, no solo una variable individual; reiniciar Backend. No publicar su contenido. |
| Gemini 429 | Revisar cuota/proyecto/modelo. Embeddings rota con hasta cuatro intentos y un enfriamiento por operación; cuota diaria confirmada detiene esa operación. Generación/evaluación recorren claves/modelos con presupuesto finito. Claves del mismo proyecto pueden compartir cuota. |
| Gemini 503 | Generación/evaluación prueban el respaldo configurado; embeddings finaliza sin cambiar el modelo del índice. Verificar disponibilidad/acceso, sin reintentos manuales continuos. |
| `.oci/config` ausente | Verificar `OCI_CONFIG_FILE=./.oci/config`, ubicación en la raíz y extensión real del archivo. |
| Ruta `.pem` incorrecta | Confirmar que `key_file` es la ruta absoluta a la clave privada de API existente y que coincide con la pública registrada. No usar la clave SSH. |
| OCI autenticación/permisos | Revisar perfil, usuario, tenancy, fingerprint, clave y región; después permisos IAM, namespace y bucket. Un 502 de almacenamiento puede ocultar esos detalles por seguridad. No publicar perfiles o mensajes sensibles para diagnosticarlo. |
| `BACKEND_URL` incorrecta | Usar `http://localhost:8000`, confirmar que Uvicorn escucha allí y que `API_PREFIX` coincide. Reiniciar Streamlit después de modificar `.env`. |
| PDF escaneado o extracción fallida | Probar texto seleccionable; usar documentos íntegros. No hay OCR. Archivo sin texto/corrupto: 422; vacío o demasiado grande: 413; extensión no admitida: 415. |
| Pantalla exitosa con Backend fallido | Puede ser el simulador. Revisar HTTP directo, referencias UUID y recuperación del objeto/JSON. |

```powershell
Get-NetTCPConnection -State Listen -LocalPort 8000,8501 -ErrorAction SilentlyContinue |
    Select-Object LocalAddress,LocalPort,OwningProcess
```

Si se elige otro puerto de Backend, cambiar **ambos** `--port` en Uvicorn y
`BACKEND_URL` en `.env`; actualizar `API_PORT` para mantener la configuración coherente.
Para otro puerto de Frontend: `python -m streamlit run interfaz/app.py --server.port 8502`.

## 12. Alcance de esta documentación

La guía y la plantilla se contrastaron con el código y los manifiestos actuales.
Redactarlas no ejecuta instalaciones, pruebas reales ni operaciones de nube.
Una instalación desde cero requiere completar esos pasos y comprobar sus resultados
en la máquina destino. No se incluyen despliegue de VMs, endpoints públicos de
descarga, configuración SSH, cambios IAM automáticos ni modificación del código.
