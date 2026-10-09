"""
Demo del módulo evaluacion (llama a la API real de Gemini).

Correr desde la carpeta evaluacion/:
    python demo.py
"""

import sys
from pathlib import Path

# Raíz del repo en el path, para encontrar shared/ y evaluacion/
sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.evaluador import evaluar_contenido
from shared.contratos import ChunkResultado, ContenidoGenerado

if __name__ == "__main__":
    contexto = [
        ChunkResultado(
            texto=(
                "La Virtual Cloud Network (VCN) es una red privada y personalizable "
                "configurada en Oracle Cloud Infrastructure. Ofrece control total sobre "
                "el entorno de red, incluyendo subredes publicas y privadas, tablas de "
                "enrutamiento, Internet Gateways, NAT Gateways y Security Lists."
            ),
            score=0.95,
            fuente="Fragmento 1",
        )
    ]

    contenido = ContenidoGenerado(
        titulo="Dominando Redes en la Nube (VCN) desde Cero",
        introduccion_contextualizada=(
            "Imagina la VCN como tu propio barrio privado y seguro dentro de la nube de Oracle."
        ),
        items=[
            {
                "frente": "¿Que es una VCN en Oracle Cloud?",
                "dorso": "Es tu red virtual privada y personalizable dentro de OCI.",
                "pista_didactica": "Piensa en un terreno cercado para tus servidores.",
            },
            {
                "frente": "¿Cuantas zonas de disponibilidad tiene una VCN por defecto?",
                "dorso": "Tres zonas de disponibilidad.",
                "pista_didactica": "Dato inventado a proposito: no esta en el contexto.",
            },
        ],
        conceptos_clave=["VCN", "Subredes", "Security Lists"],
        tiempo_estimado_estudio_minutos=5,
    )

    evaluacion = evaluar_contenido(contenido, contexto, "Principiante", "Flashcards")
    print(evaluacion.model_dump_json(indent=2))