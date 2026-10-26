# NuevaMente — Sistema Inteligente de Adaptación de Contenido Educativo

Proyecto desarrollado para el **Hackathon ONE — Grupo 10 (Oracle Next Education & Alura)**
Equipo: G10-LATAM Equipo 33

## Descripción
Sistema que ingiere documentación técnica (PDF, Markdown, texto) y genera contenido educativo adaptado según perfil del destinatario, formato pedagógico y nicho, usando RAG (Retrieval-Augmented Generation) y orquestación de agentes/LLM.

## Estructura del repositorio
- `ingesta_rag/` — extracción, chunking, embeddings, vector store
- `orquestacion_agentes/` — orquestación de prompts/agentes con LLM
- `backend/` — API/endpoint, validación de esquemas
- `interfaz/` — Streamlit/Gradio
- `oci_storage/` — integración con OCI Object Storage
- `evaluacion/` — métricas de fidelidad al documento fuente
- `docs/` — arquitectura, diagramas, guía de instalación

## Estado
En desarrollo — MVP para Hackathon ONE G10

## Equipo
- Rocio Valentina Pereyra
- Milagros Luciana Altamirano
- Zharyt Gisell sepulveda montañez
- Jesús Eduardo Estupiñan Hernández
- Abraham Yendes
- Kevin Góngora
- David Urbina Figueroa
- Beatriz Delgadillo
- Miguel Ángel Molinero