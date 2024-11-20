
from pydantic import BaseModel, EmailStr, EmailStr

class UserCreate(BaseModel):
    organization_name: str
    cnpj: str
    email: str
    phone_number: str
    name: str
    password: str

    class Config:
        orm_mode = True

class UsuarioSystem(BaseModel):
    NOME_USUARIO: str
    DS_TELEFONE: str
    DS_EMAIL: str
    DS_LOGIN: str
    DS_SENHA: str
    FL_ADMINISTRADOR: bool = False
    FL_PROPRIETARIO_CONTA:  bool = False

    class Config:
        orm_mode = True

