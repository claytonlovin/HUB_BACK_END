from pydantic import BaseModel
from models.models import Database

class DatabaseCreate(BaseModel):
    ID_GRUPO: int
    IP_CONNECTION: str
    PORT_CONNECTION: str
    USER_CONNECTION: str
    PASSWORD_CONNECTION: str
    DB_CONNECTION: str
   

class DatabaseUpdate(BaseModel):
    ID_GRUPO: int
    IP_CONNECTION: str
    PORT_CONNECTION: str
    USER_CONNECTION: str
    PASSWORD_CONNECTION: str
    DB_CONNECTION: int

    