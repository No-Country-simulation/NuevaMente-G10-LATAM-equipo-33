
from ingesta_rag.services.ingestion import indexar_documento
from ingesta_rag.services.retrieving_service import buscar_contexto


def main():
    titulo = "Guía de infraestructura en la nube"

    contenido = """
    La infraestructura en la nube permite utilizar recursos informáticos
    bajo demanda. Entre sus ventajas se encuentran la escalabilidad,
    la flexibilidad y el pago por consumo.

    La escalabilidad permite aumentar o reducir los recursos según
    la demanda. La seguridad requiere controles de acceso, cifrado
    y supervisión continua.
    """

    print("1. Indexando documento...")

    doc_id = indexar_documento(
        documento_titulo=titulo,
        documento_contenido=contenido,
    )

    print(f"Documento indexado. ID: {doc_id}")

    print("\n2. Recuperando contexto...")

    resultados = buscar_contexto(
        doc_id=doc_id,
        query="¿Cuáles son las ventajas de la infraestructura en la nube?",
        top_k=3,
    )

    print(f"\nFragmentos recuperados: {len(resultados)}")

    for i, fragmento in enumerate(resultados, start=1):
        print(f"\nFragmento {i}")
        print(f"Texto: {fragmento.texto}")
        print(f"Score: {fragmento.score}")
        print(f"Fuente: {fragmento.fuente}")


if __name__ == "__main__":
    main()