"""Persistencia real temporal y OCI falso: sin SDK instalado ni credenciales."""
import ast
from io import BytesIO
import json
from pathlib import Path
import runpy
import socket
import subprocess
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.core.config import Settings
from backend.core.exceptions import StorageError
from backend.services.storage_service import StorageService
from oci_storage.client import ObjectStorage, ObjectStorageError
from shared.contratos import ContenidoGenerado, EvaluacionCalidad, RespuestaFinal

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ContenidoGenerado(titulo="Repaso", introduccion_contextualizada="Texto",
    items=[{"frente": "Pregunta", "dorso": "Respuesta", "pista_didactica": "Pista"}],
    conceptos_clave=["VCN"], tiempo_estimado_estudio_minutos=1)
QUALITY = EvaluacionCalidad(anclaje_fuente_score=1, claridad_pedagogica="Alta", observaciones="OK")
PARAMS = dict(perfil_destinatario="Principiante", formato_salida="Flashcards",
              nicho_sector="General", nivel_detalle="Intermedio")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    original = socket.socket.connect
    def connect(sock, address):
        if isinstance(address, tuple) and address[0] in {"127.0.0.1", "::1"}:
            return original(sock, address)
        raise AssertionError("Red externa prohibida")
    monkeypatch.setattr(socket.socket, "connect", connect)


def config(tmp_path, backend="local"):
    return Settings(_env_file=None, storage_backend=backend,
        documents_path=str(tmp_path / "documents"), generated_path=str(tmp_path / "generated"),
        oci_namespace="test-namespace", oci_bucket_name="test-bucket")


class FakeClient:
    def __init__(self):
        self.objects = {}
        self.closed = Mock()

    def put_object(self, **kwargs):
        assert kwargs["if_none_match"] == "*"
        key = kwargs["object_name"]
        if key in self.objects:
            raise RuntimeError("precondition failed")
        self.objects[key] = kwargs["put_object_body"]
        return SimpleNamespace(status=200)

    def get_object(self, **kwargs):
        data = self.objects[kwargs["object_name"]]
        return SimpleNamespace(status=200, data=SimpleNamespace(
            raw=SimpleNamespace(stream=lambda *args, **kwargs: iter([data[:3], data[3:]])), close=self.closed))


def service(tmp_path, backend):
    client = FakeClient()
    remote = ObjectStorage(namespace="test-namespace", bucket="test-bucket", client=client)
    return StorageService(config(tmp_path, backend), remote if backend == "oci" else None), client


def response(storage, original):
    key, metadata, fields = storage.referencias(original)
    return key, RespuestaFinal(status="exito", metadatos=metadata,
        contenido_adaptado=CONTENT, evaluacion_calidad=QUALITY, **fields)


@pytest.mark.parametrize("backend", ["local", "oci"])
def test_persistencia_recuperacion_y_no_sobrescritura(tmp_path, backend):
    storage, client = service(tmp_path, backend)
    data = b"original intacto\x00\xff\r\n"
    first = storage.guardar_original("../CON.docx", data)
    second = storage.guardar_original("../CON.docx", data)
    assert first != second and first.endswith(".docx")
    assert storage.recuperar_original(first) == data
    key, result = response(storage, first)
    storage.guardar_resultado(key, result)
    assert storage.recuperar_resultado(key) == result
    assert storage.recuperar_original(result.metadatos["documento_original"]) == data
    assert storage.recuperar_resultado(result.metadatos["resultado_generado"]) == result
    if backend == "local":
        assert json.loads((tmp_path / "generated" / key).read_text(encoding="utf-8")) == result.model_dump(mode="json")
        assert result.almacenamiento_oci is None
        assert result.almacenamiento_local.status_guardado == "guardado"
    else:
        assert result.almacenamiento_local is None
        assert result.almacenamiento_oci.status_upload == "completado"
        assert client.closed.called
    with pytest.raises(StorageError):
        storage.guardar_resultado(key, result)
    assert storage.recuperar_resultado(key) == result


@pytest.mark.parametrize("backend", ["local", "oci"])
def test_referencias_invalidas_ausentes_y_json_corrupto(tmp_path, backend):
    storage, client = service(tmp_path, backend)
    with pytest.raises(StorageError):
        storage.recuperar_original("../../secreto")
    with pytest.raises(StorageError):
        storage.recuperar_original("0" * 32 + "_original.pdf")
    key = "0" * 32 + ".json"
    if backend == "local":
        path = tmp_path / "generated" / key
        path.parent.mkdir()
        path.write_bytes(b"no-json")
    else:
        client.objects[storage._remote_key(key)] = b"no-json"
    with pytest.raises(StorageError, match="contrato"):
        storage.recuperar_resultado(key)


def test_rutas_relativas_y_fallo_local(tmp_path, monkeypatch):
    from backend.services import storage_service
    monkeypatch.setattr(storage_service, "ENV_FILE", tmp_path / ".env")
    cfg = config(tmp_path)
    cfg.documents_path = "relative/documents"
    storage = StorageService(cfg)
    original = storage.guardar_original("a.pdf", b"bytes")
    assert (tmp_path / "relative/documents" / original).read_bytes() == b"bytes"
    cfg.documents_path = str(tmp_path / "blocked")
    (tmp_path / "blocked").write_bytes(b"file")
    with pytest.raises(StorageError) as error:
        storage.guardar_original("a.pdf", b"bytes")
    assert error.value.status_code == 500


@pytest.mark.parametrize("operation", ["upload", "download"])
@pytest.mark.parametrize("failure", [401, 403, 404, 500, "timeout"])
def test_errores_oci_seguros(operation, failure):
    client = Mock()
    error = TimeoutError("secret") if failure == "timeout" else RuntimeError("secret")
    error.status = failure
    getattr(client, "put_object" if operation == "upload" else "get_object").side_effect = error
    remote = ObjectStorage(namespace="n", bucket="b", client=client)
    with pytest.raises(ObjectStorageError) as caught:
        remote.upload("a", b"bytes") if operation == "upload" else remote.download("a")
    assert "secret" not in str(caught.value)


def test_respuesta_oci_no_confirmada_y_cierre():
    client = Mock()
    remote = ObjectStorage(namespace="n", bucket="b", client=client)
    client.put_object.return_value.status = 500
    with pytest.raises(ObjectStorageError): remote.upload("a", b"bytes")
    client.get_object.return_value.status = 404
    with pytest.raises(ObjectStorageError): remote.download("a")
    client.get_object.return_value.data.close.assert_called_once()


@pytest.mark.parametrize("mode", ["api_key", "instance_principal"])
def test_cliente_bajo_demanda_autenticacion_y_cache(monkeypatch, mode):
    sdk = ModuleType("oci")
    sdk.config = SimpleNamespace(from_file=Mock(return_value={"region": "profile-region"}))
    signer = Mock()
    sdk.auth = SimpleNamespace(signers=SimpleNamespace(InstancePrincipalsSecurityTokenSigner=signer))
    client = Mock()
    client.put_object.return_value.status = 200
    sdk.object_storage = SimpleNamespace(ObjectStorageClient=Mock(return_value=client))
    sdk.retry = SimpleNamespace(NoneRetryStrategy=Mock())
    monkeypatch.setitem(sys.modules, "oci", sdk)
    remote = ObjectStorage(namespace="n", bucket="b", region="test-region", auth_mode=mode,
                           config_file="~/test-config", profile="TEST")
    sdk.object_storage.ObjectStorageClient.assert_not_called()
    signer.assert_not_called()
    remote.upload("a", b"bytes")
    remote.upload("b", b"bytes")
    sdk.object_storage.ObjectStorageClient.assert_called_once()
    args = sdk.object_storage.ObjectStorageClient.call_args.kwargs
    assert args["config"]["region"] == "test-region"
    if mode == "api_key":
        sdk.config.from_file.assert_called_once_with(str(Path("~/test-config").expanduser()), "TEST")
        signer.assert_not_called()
    else:
        signer.assert_called_once()
        sdk.config.from_file.assert_not_called()


def test_import_no_carga_sdk(monkeypatch):
    monkeypatch.setitem(sys.modules, "oci", None)
    runpy.run_path(str(ROOT / "oci_storage/client.py"))
    ObjectStorage(namespace="n", bucket="b")


@pytest.mark.parametrize("backend", ["local", "oci"])
@pytest.mark.parametrize("failure", [None, "original", "resultado"])
def test_http_pipeline_y_confirmacion(tmp_path, monkeypatch, backend, failure):
    storage, client = service(tmp_path, backend)
    rag = ModuleType("backend.services.rag_service")
    def indexar(**kwargs):
        if backend == "local": assert list((tmp_path / "documents").glob("*_original.txt"))
        else: assert any("_original.txt" in key for key in client.objects)
        return "doc-id"
    rag.indexar = Mock(side_effect=indexar)
    rag.buscar = Mock(return_value=[])
    orchestration = ModuleType("backend.services.orchestration_service")
    orchestration.generar_contenido = Mock(return_value=CONTENT)
    evaluation = ModuleType("evaluacion.services.evaluador")
    evaluation.evaluar_contenido = Mock(return_value=QUALITY)
    errors = ModuleType("orquestacion_agentes.main")
    errors.EntradaInvalida = type("EntradaInvalida", (Exception,), {})
    errors.ErrorGeneracion = type("ErrorGeneracion", (Exception,), {})
    for module in (rag, orchestration, evaluation, errors):
        monkeypatch.setitem(sys.modules, module.__name__, module)
    coordinator = runpy.run_path(str(ROOT / "backend/services/adaptation_service.py"))
    coordinator["adaptar_contenido"].__globals__["StorageService"] = lambda: storage
    service_module = ModuleType("backend.services.adaptation_service")
    service_module.adaptar_contenido = coordinator["adaptar_contenido"]
    monkeypatch.setitem(sys.modules, service_module.__name__, service_module)
    if failure:
        method = "guardar_original" if failure == "original" else "guardar_resultado"
        monkeypatch.setattr(storage, method, Mock(side_effect=StorageError("Guardado no confirmado", 502 if backend == "oci" else 500)))
    endpoint = runpy.run_path(str(ROOT / "backend/api/adaptation.py"))
    app = FastAPI()
    app.include_router(endpoint["router"], prefix="/api/v1")
    with TestClient(app) as http:
        result = http.post("/api/v1/adapt", data=PARAMS, files={"archivo": ("source.txt", b"Texto fuente")})
    if failure:
        assert result.status_code == (502 if backend == "oci" else 500)
        assert "almacenamiento_oci" not in result.json()
        if failure == "original": rag.indexar.assert_not_called()
    else:
        assert result.status_code == 200
        parsed = RespuestaFinal.model_validate(result.json())
        assert storage.recuperar_original(parsed.metadatos["documento_original"]) == b"Texto fuente"
        assert storage.recuperar_resultado(parsed.metadatos["resultado_generado"]).model_dump(mode="json") == result.json()


def test_ejemplos_recuperados_y_simulador_intactos():
    git = ["git", "-c", "safe.directory=" + ROOT.as_posix(), "-C", str(ROOT)]
    entries = subprocess.check_output(git + ["ls-tree", "-rz", "origin/oci-storage", "--", "oci-storage/"]).split(b"\0")
    for entry in filter(None, entries):
        metadata, path = entry.split(b"\t", 1)
        oid = metadata.split()[2].decode()
        local = ROOT / "oci_storage" / Path(path.decode()).relative_to("oci-storage")
        assert local.read_bytes() == subprocess.check_output(git + ["cat-file", "blob", oid])
    for path, names in (("interfaz/pages/seccion1_carga.py", ["render"]),
                        ("interfaz/pages/seccion2_parametros.py", ["render", "_crear_resultado_simulado"])):
        old = subprocess.check_output(git + ["show", "HEAD:" + path], text=True, encoding="utf-8")
        new = (ROOT / path).read_text(encoding="utf-8")
        for name in names:
            extract = lambda text: next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == name)
            assert ast.dump(extract(old)) == ast.dump(extract(new))
