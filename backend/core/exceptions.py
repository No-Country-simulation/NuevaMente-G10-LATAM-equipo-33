class NuevamenteException(Exception):
    pass


class DocumentError(NuevamenteException):
    pass


class RagError(NuevamenteException):
    pass


class OrchestrationError(NuevamenteException):
    pass


class EvaluationError(NuevamenteException):
    pass


class StorageError(NuevamenteException):
    def __init__(self, message="No se pudo completar el almacenamiento.", status_code=500):
        super().__init__(message)
        self.status_code = status_code
