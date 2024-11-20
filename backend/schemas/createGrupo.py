from pydantic import BaseModel

class GrupoCreate(BaseModel):
    NOME_DO_GRUPO: str

    class Config:
        orm_mode = True