from config.configdb import *
from models.models import User, Organizacao, GroupUser, Grupo, Relatorio
from authentication.securityDefinition import get_auth_user, user_permition
# IMPORT INTERAL
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import func
from sqlalchemy import text

from typing import Dict
from fastapi import Depends, Header, HTTPException
# SECURITY
import datetime
# CONFIG 
now = datetime.datetime.now()
iso_date = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class CustomException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def totalUserReport(ID_ORGANIZACAO: int, db: Session = Depends(get_db)) -> Dict[str, any]:
    try:
        organizacao = db.query(Organizacao).filter(Organizacao.ID_ORGANIZACAO == ID_ORGANIZACAO).first()
        if organizacao and not organizacao.PREMIUM:
            SQL = text("call sp_status_premium(:ID_ORGANIZACAO)")
            result = db.execute(SQL, {"ID_ORGANIZACAO": ID_ORGANIZACAO}).fetchall()
            if result:
                row = result[0]  
                column_names = ["total_grupos", "total_relatorios", "total_usuarios"]  
                result_content = dict(zip(column_names, row)) 

                return {"status": "success", "status_code": 200, "premium": False,  "content": result_content}     
    except SQLAlchemyError as e:
        raise CustomException(f"Erro no banco de dados: {str(e)}")
