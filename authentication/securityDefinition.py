from config.configdb import *
# IMPORT INTERAL
from fastapi import  HTTPException
from models.models import User, Organizacao, GroupUser, Grupo
from sqlalchemy.orm import Session
from fastapi import Depends, Header, HTTPException
# SECURITY
import jwt
import os
import datetime
# CONFIG 
now = datetime.datetime.now()
iso_date = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

# chave secreta do JWT
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

def get_auth_user(db: Session = Depends(get_db), token: str = Header(..., description='Authorization token', example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',), id_usuario: int = None):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("id_user")
        user = db.query(User).get(user_id)
        
        if datetime.datetime.utcnow() > datetime.datetime.fromtimestamp(payload['exp']):
            raise HTTPException(status_code=401, detail="O token fornecido expirou.")
        
        if user.FL_ADMINISTRADOR:
            return user
        if id_usuario is not None and id_usuario != user_id or id_usuario != user_id:
            raise HTTPException(status_code=401, detail="O ID do usuário no token não corresponde ao ID do usuário fornecido.")

        return user
    except:
        raise HTTPException(status_code=401, detail="O token fornecido é inválido ou expirou. Verifique se o token está correto ou gere um novo.")

def user_permition(user_id: int, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.ID_USUARIO == user_id).first()
    if usuario.FL_ADMINISTRADOR == True:
        return True
    
def user_group(group_id: int, user_id: int, db: Session):
    usuario = db.query(GroupUser).filter(GroupUser.ID_GRUPO == group_id, GroupUser.ID_USUARIO == user_id).first()
    if usuario:
        return True
    else:
        return False