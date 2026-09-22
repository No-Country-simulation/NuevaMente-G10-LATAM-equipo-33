import os
import oci
from dotenv import load_dotenv

# Cargar las variables definidas en el archivo .env
load_dotenv()

# Obtener configuraciones del .env
config_file = os.getenv("OCI_CONFIG_FILE")
profile = os.getenv("OCI_PROFILE", "DEFAULT")
namespace = os.getenv("OCI_NAMESPACE")
bucket_name = os.getenv("OCI_BUCKET_NAME")

# Cargar la configuración de autenticación de OCI
config = oci.config.from_file(config_file, profile)

# Inicializar el cliente para Object Storage
object_storage_client = oci.object_storage.ObjectStorageClient(config)


def upload_file(local_file_path, object_name=None):
    if object_name is None:
        object_name = os.path.basename(local_file_path)

    with open(local_file_path, "rb") as file_data:
        response = object_storage_client.put_object(
            namespace_name=namespace,
            bucket_name=bucket_name,
            object_name=object_name,
            put_object_body=file_data
        )
    print(f"Archivo '{object_name}' subido exitosamente al bucket.")
    return response


def download_file(object_name, destination_path):
    response = object_storage_client.get_object(
        namespace_name=namespace,
        bucket_name=bucket_name,
        object_name=object_name
    )

    with open(destination_path, "wb") as file_out:
        for chunk in response.data.raw.stream(1024 * 1024, decode_content=False):
            file_out.write(chunk)

    print(f"Archivo '{object_name}' descargado correctamente en '{destination_path}'.")



if __name__ == "__main__":
    # 1. Crear un archivo de texto local de prueba
    test_filename = "prueba.txt"
    with open(test_filename, "w", encoding="utf-8") as f:
        f.write("Hola OCI, prueba de subida y lectura desde Python!")

    # 2. Subir el archivo al bucket
    print("--- Subiendo archivo ---")
    upload_file(test_filename, "prueba_oci.txt")

    # 3. Leer/Descargar el archivo desde el bucket
    print("\n--- Descargando archivo ---")
    download_file("prueba_oci.txt", "descargado_prueba.txt")