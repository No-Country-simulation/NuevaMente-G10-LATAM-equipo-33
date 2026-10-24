# 📖 Resumen del README — Módulo RAG

### 🎯 Funcionalidad y Alcances

1. **Contratos Unificados (** **contratos.py** **)**: Fuente única de verdad para el ecosistema (`ingesta-rag`, `orquestacion-agentes`, `backend`).
2. **Chunking Inteligente (** **services/chunker.py** **)**: Segmentación limpia de texto respetando oraciones/párrafos con solapamiento (*overlap*).
3. **Embeddings Resilientes (** **services/embedding\_service.py** **)**: Generación vectorial con Google Gemini y rotación automática de API Keys (`KeyManager`) ante límites de tasa (`429`).
4. **Indexación y Almacenamiento Vectorial (** **services/indexing\_service.py** **/** **vector\_db.py** **)**: Persistencia vectorial en **ChromaDB** vinculada a un `doc_id`.
5. **Recuperación Semántica de Contexto (** **services/retrieving\_service.py** **)**: Búsqueda por similitud que devuelve objetos validados `ChunkResultado`.
6. **Consola Interactiva de Pruebas (** **tests/test\_pipelineunificado.py** **)**: Script CLI para indexar y consultar interactivamente desde la terminal.

---

### 📊 Diagrama de Flujo del Proceso

```
flowchart TD
    subgraph INGESTA ["1. Proceso de Ingesta e Indexación"]
        A["indexar_documento(titulo, contenido)"]
        A --> B["Chunking Inteligente (chunker.py)"]
        B --> C["Generación de Embeddings Resiliente (Gemini)"]
        C --> D["Almacenamiento Vectorial (ChromaDB)"]
        D --> E["Retorna doc_id (UUID)"]
    end

    subgraph RETRIEVING ["2. Proceso de Búsqueda de Contexto"]
        H["Consulta de Usuario (Query) + doc_id"] --> I["buscar_contexto(doc_id, query, top_k)"]
        I --> J["Embedding de la Query (Gemini)"]
        J --> K["Búsqueda por Similitud en ChromaDB"]
        K --> L["Mapeo a objetos ChunkResultado"]
        L --> M["Lista de ChunkResultado (texto, score, fuente)"]
    end

```

---

### 🛠️ Guía de Métodos y Firma de Interfaces

#### 1. Modelo de Salida (`contratos.py`)

```
from pydantic import BaseModel

class ChunkResultado(BaseModel):
    texto: str     # Contenido del fragmento
    score: float   # Puntaje de similitud (0.0 a 1.0)
    fuente: str    # Sección o documento de origen

```

#### 2. Método de Indexación (`indexar_documento`)

* **Módulo:** `services.ingestion`
* **Firma:** `indexar_documento(documento_titulo: str, documento_contenido: str) -&gt; str`
* **Entrada:** Título y contenido plano del documento.
* **Salida:** `doc_id` (identificador único para referenciarlo posteriormente).

#### 3. Método de Búsqueda de Contexto (`buscar_contexto`)

* **Módulo:** `services.retrieving_service`
* **Firma:** `buscar_contexto(doc_id: str, query: str, top_k: int = 5) -&gt; list[ChunkResultado]`
* **Entrada:** `doc_id`, consulta en texto plano (`query`) y cantidad de fragmentos (`top_k`).
* **Salida:** Lista de instancias de `ChunkResultado`.

---

### 📦 Librerías a Importar y Requisitos

* **pydantic**: Validación de modelos y esquemas de contratos.
* **chromadb**: Base de datos vectorial.
* **google-generativeai**: Cliente de la API de Google Gemini para embeddings.
* **typing**: Tipado estático nativo (`List`, `Any`).