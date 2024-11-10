from typing import Optional
from pydantic import BaseModel


class RelatorioBase(BaseModel):
    DS_NOME_RELATORIO: str
    DS_LINK_RELATORIO: str


class RelatorioCreate(RelatorioBase):
    DS_NOME_RELATORIO: str
    DS_LINK_RELATORIO: Optional[str] = None
    ID_GRUPO: int
    


class RelatorioUpdate(RelatorioBase):
    pass
