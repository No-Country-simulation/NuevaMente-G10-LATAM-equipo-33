from pydantic import BaseModel, Field


class AdaptacionRequest(BaseModel):
    documento_titulo: str = Field(min_length=1)
    documento_contenido: str = Field(min_length=1)
    perfil_destinatario: str = Field(min_length=1)
    formato_salida: str = Field(min_length=1)
    nicho_sector: str = Field(min_length=1)
    nivel_detalle: str = Field(min_length=1)
