"""Carga la configuración local desde la raíz, conservando el entorno del servicio."""
from pathlib import Path

from dotenv import load_dotenv

ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_FILE, override=False)
