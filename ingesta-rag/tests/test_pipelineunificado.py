""" Script de prueba temporal end-to-end para el flujo de Ingesta-RAG. Llama a pypdf para extraer
 texto e invoca a indexar_documento() y buscar_contexto() a través de sus servicios correspondientes.
"""

import sys
from pathlib import Path

# Añadir la raíz de ingesta-rag al sys.path para poder importar los módulos libremente
RAIZ_MODULO = Path(__file__).resolve().parent.parent
sys.path.append(str(RAIZ_MODULO))

from pypdf import PdfReader # Importamos las funciones desde los módulos correspondientes
from services.ingestion import indexar_documento
from services.retrieving_service import buscar_contexto

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
        print(f"⚠️ No se encontraron archivos PDF en {carpeta_pdfs}. Agrega al menos uno para probar.")
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
                documento_contenido=contenido )
    print(f"🎯 Documento indexado exitosamente con doc_id: {doc_id}")

    # 4. Consola interactiva para realizar consultas (Retrieving)
    print("\n" + "=" * 50)
    print("🔍 MODO INTERACTIVO DE BÚSQUEDA DE CONTEXTO")
    print("Ingresa tu consulta/pregunta para buscar en el documento indexado.")
    print("Escribe 'salir' o 'exit' para finalizar la sesión.")
    print("=" * 50)
    while True:
        try:
            query_usuario = input("\n❓ Ingresa tu query/pregunta: ").strip()
            # Opción para salir del bucle
            if query_usuario.lower() in ["salir", "exit", "q"]:
                print("👋 Saliendo de la búsqueda interactiva.")
                break
            # Evitar queries vacías
            if not query_usuario:
                print("⚠️️ Por favor escribe una consulta válida.")
                continue
            # Invocación a la función contractual de búsqueda
            resultados = buscar_contexto(
                            doc_id=doc_id,
                            query=query_usuario,
                            top_k=3 )
            print(f"\n✨ Se recuperaron {len(resultados)} fragmentos validados (ChunkResultado):")
            for i, res in enumerate(resultados, 1):
                print(f"\n--- [Resultado {i}] ---")
                print(f"Score: {res.score:.4f} | Fuente: {res.fuente}")
                print(f"Texto: {res.texto[:200]}...\n")
        except KeyboardInterrupt:
            print("\n👋 Sesión interrumpida por el usuario. Saliendo.")
            break
        except Exception as e:
            print(f"❌ Error al procesar la consulta: {e}")
    print("\n=== PRUEBA COMPLETADA CON ÉXITO ===")

if __name__ == "__main__":
    ejecutar_prueba()