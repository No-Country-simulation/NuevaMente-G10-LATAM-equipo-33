# NuevaMente — Sistema Inteligente de Adaptación de Contenido Educativo

Proyecto desarrollado para el **Hackathon ONE — Grupo 10 (Oracle Next Education & Alura)**
Equipo: G10-LATAM Equipo 33

## Descripción
Sistema que ingiere documentación técnica (PDF, Markdown, texto) y genera contenido
educativo adaptado según perfil del destinatario, formato pedagógico y nicho, usando
RAG (Retrieval-Augmented Generation) y orquestación de agentes/LLM.

## Estructura del repositorio
- `ingesta-rag/` — extracción, chunking, embeddings, vector store
- `orquestacion-agentes/` — orquestación de prompts/agentes con LLM
- `backend/` — API/endpoint, validación de esquemas
- `interfaz/` — Streamlit/Gradio
- `oci-storage/` — integración con OCI Object Storage
- `evaluacion/` — métricas de fidelidad al documento fuente
- `docs/` — arquitectura, diagramas, guía de instalación

## Estado
En desarrollo — MVP para Hackathon ONE G10

## Equipo