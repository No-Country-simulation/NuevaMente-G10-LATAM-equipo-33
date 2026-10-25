"""Persistencia de originales y respuestas, independiente del índice Chroma."""
import json
from pathlib import Path
import re
from uuid import uuid4

from backend.core.config import settings
from backend.core.exceptions import StorageError
from shared.config import ENV_FILE
from shared.contratos import AlmacenamientoLocal, AlmacenamientoOCI, RespuestaFinal


class StorageService:
    def __init__(self, config=None, object_storage=None):
        self.config = config if config is not None else settings
        self.remote = object_storage
        if self.config.storage_backend == "oci" and self.remote is None:
            from oci_storage.client import ObjectStorage
            self.remote = ObjectStorage(
                namespace=self.config.oci_namespace, bucket=self.config.oci_bucket_name,
                region=self.config.oci_region, auth_mode=self.config.oci_auth_mode,
                config_file=str(self._path(self.config.oci_config_file)), profile=self.config.oci_profile,
            )

    @staticmethod
    def _path(value):
        path = Path(value).expanduser()
        return path if path.is_absolute() else ENV_FILE.parent / path

    @staticmethod
    def _validate(key, original):
        pattern = r"[0-9a-f]{32}_original\.(pdf|docx|pptx|txt|md)" if original else r"[0-9a-f]{32}\.json"
        if not isinstance(key, str) or re.fullmatch(pattern, key) is None:
            raise StorageError("Referencia de almacenamiento no válida.")

    @staticmethod
    def _remote_key(key):
        return f"adaptaciones/{key[:32]}/{key}"

    def _write(self, key, data, original):
        self._validate(key, original)
        if self.config.storage_backend == "oci":
            try:
                self.remote.upload(self._remote_key(key), data,
                                   "application/octet-stream" if original else "application/json")
            except Exception:
                raise StorageError("No se pudo confirmar el guardado en OCI.", 502) from None
            return
        path = self._path(self.config.documents_path if original else self.config.generated_path) / key
        created = False
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as output:
                created = True
                output.write(data)
        except Exception:
            if created:
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise StorageError("No se pudo confirmar el guardado local.") from None

    def _read(self, key, original):
        if self.config.storage_backend == "oci" and isinstance(key, str) and key.startswith("adaptaciones/"):
            short_key = key.rsplit("/", 1)[-1]
            self._validate(short_key, original)
            if key != self._remote_key(short_key):
                raise StorageError("Referencia de almacenamiento no válida.")
            key = short_key
        self._validate(key, original)
        if self.config.storage_backend == "oci":
            try:
                return self.remote.download(self._remote_key(key))
            except Exception:
                raise StorageError("No se pudo recuperar el objeto de OCI.", 502) from None
        try:
            return (self._path(self.config.documents_path if original else self.config.generated_path) / key).read_bytes()
        except Exception:
            raise StorageError("No se pudo recuperar el archivo local.") from None

    def guardar_original(self, nombre: str, datos: bytes) -> str:
        extension = Path(nombre).suffix.lower()
        if extension not in {".pdf", ".docx", ".pptx", ".txt", ".md"}:
            raise StorageError("Extensión de almacenamiento no válida.")
        key = f"{uuid4().hex}_original{extension}"
        self._write(key, datos, True)
        return key

    def referencias(self, original):
        self._validate(original, True)
        result = original[:32] + ".json"
        metadata = {"storage_backend": self.config.storage_backend, "documento_original": original,
                    "resultado_generado": result}
        if self.config.storage_backend == "oci":
            metadata["documento_original"] = self._remote_key(original)
            metadata["resultado_generado"] = self._remote_key(result)
            storage = {"almacenamiento_oci": AlmacenamientoOCI(
                bucket=self.config.oci_bucket_name, objeto_id=self._remote_key(result), status_upload="completado")}
        else:
            storage = {"almacenamiento_local": AlmacenamientoLocal(
                documento_original=str(self._path(self.config.documents_path) / original),
                resultado_generado=str(self._path(self.config.generated_path) / result), status_guardado="guardado")}
        return result, metadata, storage

    def guardar_resultado(self, key, respuesta):
        try:
            data = json.dumps(respuesta.model_dump(mode="json"), ensure_ascii=False, indent=2).encode("utf-8")
        except Exception:
            raise StorageError("No se pudo serializar el resultado.") from None
        self._write(key, data, False)

    def recuperar_original(self, key):
        return self._read(key, True)

    def recuperar_resultado(self, key):
        try:
            return RespuestaFinal.model_validate_json(self._read(key, False))
        except StorageError:
            raise
        except Exception:
            raise StorageError("El resultado almacenado no cumple el contrato.") from None
