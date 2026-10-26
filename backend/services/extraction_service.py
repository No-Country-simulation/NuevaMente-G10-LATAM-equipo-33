"""Extrae texto del archivo recibido, sin persistirlo ni consultar servicios externos."""
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from fastapi import HTTPException


def _tabla_texto(tabla):
    return [" | ".join(celda.text for celda in fila.cells) for fila in tabla.rows]


def _formas_texto(formas):
    partes = []
    for forma in formas:
        if forma.has_text_frame:
            partes.append(forma.text_frame.text)
        if forma.has_table:
            partes.extend(_tabla_texto(forma.table))
        if hasattr(forma, "shapes"):
            partes.extend(_formas_texto(forma.shapes))
    return partes


def extraer_texto(nombre: str, datos: bytes) -> str:
    extension = Path(nombre).suffix.lower()
    if extension not in {".pdf", ".docx", ".pptx", ".txt", ".md"}:
        raise HTTPException(415, "Formato admitido: PDF, DOCX, PPTX, TXT o MD.")
    if not datos:
        raise HTTPException(413, "El archivo está vacío.")
    try:
        if extension in {".docx", ".pptx"}:
            with ZipFile(BytesIO(datos)) as archivo:
                if sum(item.file_size for item in archivo.infolist()) > 50 * 1024 * 1024:
                    raise ValueError("Documento demasiado grande al descomprimir.")
        if extension == ".pdf":
            from pypdf import PdfReader
            texto = "\n\n".join(pagina.extract_text() or "" for pagina in PdfReader(BytesIO(datos)).pages)
        elif extension == ".docx":
            from docx import Document
            documento = Document(BytesIO(datos))
            texto = "\n".join(
                [parrafo.text for parrafo in documento.paragraphs]
                + [linea for tabla in documento.tables for linea in _tabla_texto(tabla)]
            )
        elif extension == ".pptx":
            from pptx import Presentation
            texto = "\n\n".join(
                "\n".join(_formas_texto(diapositiva.shapes))
                for diapositiva in Presentation(BytesIO(datos)).slides
            )
        else:
            texto = datos.decode("utf-8-sig")
    except ImportError as error:
        raise HTTPException(503, "Faltan dependencias de extracción en el Backend.") from error
    except Exception as error:
        raise HTTPException(422, "No se pudo extraer el texto. Comprueba la integridad y el formato del archivo.") from error
    if not texto.strip():
        raise HTTPException(422, "El documento no contiene texto utilizable. Los documentos escaneados requieren OCR.")
    return texto.strip()
