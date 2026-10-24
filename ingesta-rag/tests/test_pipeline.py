"""
Script de prueba temporal end-to-end para el flujo de Ingesta-RAG.
Llama a pypdf para extraer texto e invoca a indexar_documento().
"""

import sys
from pathlib import Path

# Añadir la raíz de ingesta-rag al sys.path para poder importar los módulos libremente
RAIZ_MODULO = Path(__file__).resolve().parent.parent
sys.path.append(str(RAIZ_MODULO))

from pypdf import PdfReader
from services.indexing_service import indexar_documento
from models.vector_db import buscar_en_chroma
from services.embedding_service import GeminiEmbeddingsResiliente
from utils.key_manager import KeyManager
from utils.config import GEMINI_API_KEYS


def extraer_texto_pdf(ruta_pdf: Path) -> str:
    """Extrae el contenido de texto de un archivo PDF usando PyPDF."""
    reader = PdfReader(ruta_pdf)
    texto_completo = ""
    for page in reader.pages:
        texto = page.extract_text()
        if texto:
            texto_completo += texto + "\n"
    return texto_completo.strip()


def ejecutar_prueba():
    print("=== INICIANDO PRUEBA LOCAL DE INGESTA RAG ===")

    # 1. Buscar PDF de prueba
    carpeta_pdfs = RAIZ_MODULO / "tests" / "pdfs"
    archivos_pdf = list(carpeta_pdfs.glob("*.pdf"))

    if not archivos_pdf:
        print(f"⚠️  No se encontraron archivos PDF en {carpeta_pdfs}. Agrega al menos uno para probar.")
        return

    pdf_prueba = archivos_pdf[0]
    print(f"📄 Procesando PDF de prueba: {pdf_prueba.name}")

    # 2. Extraer Texto
    contenido = extraer_texto_pdf(pdf_prueba)
    print(f"✅ Texto extraído correctamente ({len(contenido)} caracteres).")

    # 3. Probar Indexación (Cumplimiento de Contrato)
    print("🚀 Ejecutando indexar_documento()...")
    doc_id = indexar_documento(
        documento_titulo=pdf_prueba.stem,
        documento_contenido=contenido
    )
    print(f"🎯 Documento indexado exitosamente con doc_id: {doc_id}")

    # 4. Probar Recuperación (Retrieving Opcional para Verificación)
    print("🔍 Realizando búsqueda de prueba en ChromaDB...")
    key_mgr = KeyManager(keys=GEMINI_API_KEYS)
    emb_service = GeminiEmbeddingsResiliente(key_manager=key_mgr)

    resultados = buscar_en_chroma(
        doc_id=doc_id,
        query="resumen general",
        embedding_function=emb_service,
        top_k=2
    )

    print(f"\nSe recuperaron {len(resultados)} fragmentos:")
    for i, res in enumerate(resultados, 1):
        print(f"\n--- Resultado {i} (Score: {res.score:.4f}) ---")
        print(f"Fuente: {res.fuente}")
        print(f"Texto: {res.texto[:150]}...")

    print("\n=== PRUEBA COMPLETADA CON ÉXITO ===")


if __name__ == "__main__":
    ejecutar_prueba()