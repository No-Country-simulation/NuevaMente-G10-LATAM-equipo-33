"""Adaptador reutilizable: importar no carga el SDK ni accede a OCI."""
from pathlib import Path


class ObjectStorageError(Exception):
    """Fallo seguro, sin mensajes del proveedor."""


class ObjectStorage:
    def __init__(self, *, namespace, bucket, region=None, auth_mode="api_key",
                 config_file="~/.oci/config", profile="DEFAULT", client=None):
        self.namespace, self.bucket = namespace, bucket
        self.region, self.auth_mode = region, auth_mode
        self.config_file, self.profile = config_file, profile
        self._client = client

    def _get_client(self):
        if not self.namespace or not self.bucket:
            raise ObjectStorageError("Falta configurar el namespace o el bucket OCI.")
        if self._client is None:
            import oci
            if self.auth_mode == "api_key":
                config = oci.config.from_file(str(Path(self.config_file).expanduser()), self.profile)
                if self.region:
                    config["region"] = self.region
                args = {"config": config}
            elif self.auth_mode == "instance_principal":
                signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
                args = {"config": {"region": self.region} if self.region else {}, "signer": signer}
            else:
                raise ObjectStorageError("Modalidad de autenticación OCI no válida.")
            self._client = oci.object_storage.ObjectStorageClient(
                **args, timeout=(10, 60), retry_strategy=oci.retry.NoneRetryStrategy()
            )
        return self._client

    def upload(self, object_name: str, data: bytes, content_type="application/octet-stream"):
        try:
            response = self._get_client().put_object(
                namespace_name=self.namespace, bucket_name=self.bucket,
                object_name=object_name, put_object_body=data,
                content_type=content_type, if_none_match="*",
            )
            if response.status != 200:
                raise ObjectStorageError("OCI no confirmó la subida.")
        except Exception:
            raise ObjectStorageError("No se pudo confirmar la subida a OCI.") from None

    def download(self, object_name: str) -> bytes:
        try:
            response = self._get_client().get_object(
                namespace_name=self.namespace, bucket_name=self.bucket, object_name=object_name,
            )
            try:
                if response.status != 200:
                    raise ObjectStorageError("OCI no confirmó la descarga.")
                return b"".join(response.data.raw.stream(1024 * 1024, decode_content=False))
            finally:
                response.data.close()
        except Exception:
            raise ObjectStorageError("No se pudo recuperar el objeto de OCI.") from None
