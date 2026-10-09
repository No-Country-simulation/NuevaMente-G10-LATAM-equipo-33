Backend - Servicio de Adaptación

Este módulo contiene la API backend construida con FastAPI, encargada de gestionar los servicios de adaptación, RAG, orquestación, evaluación y almacenamiento.

📁 Estructura del Proyecto

backend/
│
├── app.py                      # Punto de entrada de la aplicación FastAPI
│
├── api/                        # Rutas y endpoints de la API
│   └── adaptation.py
│
├── schemas/                    # Modelos de datos Pydantic para peticiones/respuestas
│   └── request.py
│
├── services/                   # Lógica de negocio principal
│   ├── adaptation_service.py
│   ├── rag_service.py
│   ├── orchestration_service.py
│   ├── evaluation_service.py
│   └── storage_service.py
│
├── mocks/                      # Mocks para pruebas e integración
│   ├── rag_mock.py
│   ├── orchestration_mock.py
│   ├── evaluation_mock.py
│   └── storage_mock.py
│
├── core/                       # Configuración global y manejo de excepciones
│   ├── config.py
│   └── exceptions.py
│
├── tests/                      # Pruebas unitarias y de integración
│   └── test_adaptation.py
│
├── requirements.txt            # Dependencias del proyecto
├── .env                        # Variables de entorno (No subir a VCS)
└── .env.example                # Plantilla de variables de entorno


🚀 Requisitos Previos

Python 3.9 o superior.

pip e virtualenv instalados.

🛠️ Instalación y Configuración Local

Para configurar y ejecutar el proyecto en tu entorno local:

1. Entrar al directorio del backend

cd backend


2. Crear y activar un entorno virtual

En Linux / macOS:

python -m venv venv
source venv/bin/activate


En Windows (CMD):

python -m venv venv
venv\Scripts\activate


En Windows (PowerShell):

python -m venv venv
.\venv\Scripts\Activate.ps1


3. Instalar las dependencias

pip install -r requirements.txt


4. Configurar variables de entorno

Copia la plantilla .env.example para crear tu archivo .env local


Edita el archivo .env agregando las credenciales y configuraciones correspondientes (API Keys, URLs de servicios, etc.).

▶️ Ejecución en Local

Para iniciar el servidor de desarrollo local con recarga automática:

uvicorn app:app --reload --host 0.0.0.0 --port 8000


Una vez levantado el servidor, estará disponible en:

API Principal: http://localhost:8000

Documentación Interactiva (Swagger UI): http://localhost:8000/docs

Documentación Alternativa (ReDoc): http://localhost:8000/redoc

💡 Ejemplo de Uso Mínimo

A continuación se muestra un ejemplo de cómo consumir el endpoint de adaptación usando curl:

Ejemplo Request (cURL)

curl -X 'POST' \
  'http://localhost:8000/api/adaptation' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "prompt": "Texto o requerimiento a adaptar",
  "context": "Contexto adicional opcional"
}'


Respuesta Esperada (200 OK)

{
  "status": "success",
  "data": {
    "adapted_content": "Resultado de la adaptación generada...",
    "evaluation_score": 0.95
  }
}


🔒 Notas de Seguridad

⚠️ IMPORTANTE: Nunca subas el archivo .env real ni ninguna clave/API Key privada a repositorios de control de versiones públicos o compartidos.

Asegúrate de añadir .env al archivo .gitignore de la raíz de tu proyecto.