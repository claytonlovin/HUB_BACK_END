from config.configdb import *
from schemas.integracaoSchema import IntegracaoResponse, IntegracaoCreate, IntegracaoUpdate
from schemas.createGrupo import GrupoCreate
# IMPORT INTERAL
from fastapi.responses import JSONResponse
from fastapi import  HTTPException
from models.models import User, Organizacao, GroupUser, Grupo, Integracao
import jwt
from sqlalchemy.orm import Session
from sqlalchemy import exists, and_
from fastapi import Depends, Header, HTTPException
# SECURITY
from authentication.securityDefinition import get_auth_user, user_permition
import jwt
import datetime
from typing import List

# CONFIG 

@router.post("/integracao/", tags=["Integracoes"], response_model=IntegracaoResponse)
async def create_integracao(IntegracaoCreate: IntegracaoCreate, db: Session = Depends(get_db), user: User = Depends(get_auth_user)):
    try:
        if user_permition(user.ID_USUARIO, db):
            DS_NOME_INTEGRACAO = IntegracaoCreate.DS_NOME_INTEGRACAO,
            CHAVE_INTEGRACAO_ONE = IntegracaoCreate.CHAVE_INTEGRACAO_ONE,
            CHAVE_INTEGRACAO_TWO = IntegracaoCreate.CHAVE_INTEGRACAO_TWO,
            ID_ORGANIZACAO = user.ID_ORGANIZACAO
            new_integracao = Integracao(DS_NOME_INTEGRACAO=DS_NOME_INTEGRACAO, CHAVE_INTEGRACAO_ONE=CHAVE_INTEGRACAO_ONE, CHAVE_INTEGRACAO_TWO=CHAVE_INTEGRACAO_TWO, ID_ORGANIZACAO=ID_ORGANIZACAO)
            db.add(new_integracao)
            db.commit()
            db.refresh(new_integracao)
            return new_integracao
            
        else:
            raise HTTPException(status_code=403, detail='Sem permissão para criar integracao')
    except Exception as e:
        return {"erro": str(e)}
    
    
@router.get("/integracao/", tags=["Integracoes"])
async def get_integracao(user: User = Depends(get_auth_user), db: Session = Depends(get_db)):
    try:
        if user_permition(user.ID_USUARIO, db):
            integracoes = db.query(Integracao).all()
            return integracoes
        else:   
            raise HTTPException(status_code=403, detail='Sem permissão para criar integracao')
    except Exception as e:
        return {"erro": str(e)}
    
@router.delete("/integracao/{id_integracao}",  tags=["Integracoes"])
async def delete_integracao(id_integracao: int, user: User = Depends(get_auth_user), db: Session = Depends(get_db)):
    try:
        if user_permition(user.ID_USUARIO, db):
            integracao = db.query(Integracao).filter(Integracao.ID_INTEGRACAO == id_integracao).first()
            if integracao is None:
                raise HTTPException(status_code=404, detail='Integração nao encontrada')
            db.delete(integracao)
            db.commit()
            return {"mensagem": "Integração deletada com sucesso"}
        else:
            raise HTTPException(status_code=403, detail='Sem permissão para criar integracao')
    except Exception as e:
        return {"erro": str(e)}
    
@router.put("/integracao/{id_integracao}", tags=["Integracoes"], response_model=IntegracaoResponse)
async def update_integracao(id_integracao: int, integracao: IntegracaoUpdate, user: User = Depends(get_auth_user), db: Session = Depends(get_db)):
    try:
        if user_permition(user, "integracoes"):
            integracao_db = db.query(Integracao).filter(Integracao.ID_INTEGRACAO == id_integracao).first()
            if integracao_db is None:
                raise HTTPException(status_code=404, detail='Integração não encontrada')

            # Atualizar os campos individualmente
            update_data = integracao.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(integracao_db, key, value)

            db.commit()
            db.refresh(integracao_db)  # Atualiza `integracao_db` com os dados do banco

            return integracao_db  # Retorna o objeto atualizado como `IntegracaoResponse`
        else:
            raise HTTPException(status_code=403, detail='Sem permissão para atualizar integração')
    except Exception as e:
        return JSONResponse(content={"erro": str(e)}, status_code=500)