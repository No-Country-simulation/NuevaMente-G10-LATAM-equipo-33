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
    pass