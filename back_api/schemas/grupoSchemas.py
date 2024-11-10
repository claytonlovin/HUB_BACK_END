from pydantic import BaseModel


class GrupoUpdate(BaseModel):
    NOME_DO_GRUPO: str


class Usuario(BaseModel):
    id_usuario: int
    nome_usuario: str
