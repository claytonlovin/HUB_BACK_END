from pydantic import BaseModel


class IntegracaoUpdate(BaseModel):
    DS_NOME_INTEGRACAO: str
    CHAVE_INTEGRACAO_ONE: str
    CHAVE_INTEGRACAO_TWO: str

    class Config:
        orm_mode = True


class IntegracaoCreate(BaseModel):
    DS_NOME_INTEGRACAO: str
    CHAVE_INTEGRACAO_ONE: str
    CHAVE_INTEGRACAO_TWO: str


class IntegracaoResponse(BaseModel): 
    ID_INTEGRACAO: int 
    DS_NOME_INTEGRACAO: str 
    CHAVE_INTEGRACAO_ONE: str
    CHAVE_INTEGRACAO_TWO: str   
    ID_ORGANIZACAO: int




