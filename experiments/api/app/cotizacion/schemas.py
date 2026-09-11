from pydantic import BaseModel, ConfigDict, Field


class SolicitudCotizacion(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    cliente_id: str = Field(alias="clienteId")
    monto: float
    edad: int


class RespuestaCotizacion(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: str
    origen_perfil: str = Field(alias="origenPerfil")
    circuito: str
    replica: str
    prima: float
    nivel_riesgo: str = Field(alias="nivelRiesgo")
