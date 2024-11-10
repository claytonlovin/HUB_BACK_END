from config.configdb import *
from schemas.createRelatorio import RelatorioBase, RelatorioCreate, RelatorioUpdate
# IMPORT INTERAL
from fastapi.responses import JSONResponse
from fastapi import  HTTPException
from models.models import User, Relatorio
import jwt
from sqlalchemy.orm import Session
from fastapi import Depends, Header, HTTPException

# SECURITY
from authentication.securityDefinition import get_auth_user, get_auth_user, user_permition, user_group
import jwt
import os
import datetime
# CONFIG 
now = datetime.datetime.now()
iso_date = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


@router.get('/ListReport/{group_id}', tags=['Reports'])
async def list_report(group_id: int, user: User = Depends(get_auth_user), db: Session = Depends(get_db)):
    try: 
        grupos_relatorio = db.query(Relatorio).filter(Relatorio.ID_GRUPO == group_id).all()
        
        if not user.FL_ADMINISTRADOR and not user_group(group_id, user.ID_USUARIO, db):
            raise HTTPException(status_code=403, detail='Sem permissão para acessar este grupo')
        
        list_grupo_usuario = [{
            "ID_GRUPO": g.ID_GRUPO,   
            "ID_RELATORIO": g.ID_RELATORIO,  
            "DS_NOME_RELATORIO": g.DS_NOME_RELATORIO,     
            "DS_LINK": g.DS_LINK_RELATORIO
            } 
            for g in grupos_relatorio]

        return JSONResponse(content=list_grupo_usuario)
    except Exception as e:
        return {"erro": str(e)}

@router.get('/ListReportLink/{id_report}', tags=['Reports'])
async def list_report(id_report: int, user: User = Depends(get_auth_user), db: Session = Depends(get_db)):
    try: 
        relatorio = db.query(Relatorio).filter(Relatorio.ID_RELATORIO == id_report).first()
        
        if not relatorio:
            raise HTTPException(status_code=404, detail='Relatório não encontrado')
        
        if not user.FL_ADMINISTRADOR and not user_group(relatorio.ID_GRUPO, user.ID_USUARIO, db):
            raise HTTPException(status_code=403, detail='Sem permissão para acessar este relatório')
        
        list_report = {
            "ID_GRUPO": relatorio.ID_GRUPO,
            "ID_RELATORIO": relatorio.ID_RELATORIO,
            "DS_NOME_RELATORIO": relatorio.DS_NOME_RELATORIO,
            "DS_LINK": relatorio.DS_LINK_RELATORIO
        }

        return JSONResponse(content=list_report)
    except Exception as e:
        return {"erro": str(e)}


@router.delete('/deleteReport/{group_id}/{report_id}', tags=['Reports'])
async def delete_report(group_id: int, report_id: int, user: User = Depends(get_auth_user), db: Session = Depends(get_db)):
    try:
        if not user.FL_ADMINISTRADOR and not user_group(group_id, user.ID_USUARIO, db):
            raise HTTPException(status_code=403, detail='Sem permissão para deletar relatório deste grupo')
        
        relatorio = db.query(Relatorio).filter(Relatorio.ID_GRUPO == group_id, Relatorio.ID_RELATORIO == report_id).first()
        if not relatorio:
            raise HTTPException(status_code=404, detail='Relatório não encontrado')
        
        if user_permition(user.ID_USUARIO, db) != True:
            raise HTTPException(status_code=403, detail='Sem permissão para deletar grupo')
        db.delete(relatorio)
        db.commit()
        
        return {"mensagem": "Relatório deletado com sucesso"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/createReport', tags=['Reports'])
async def create_report(relatorio: RelatorioCreate, user: User = Depends(get_auth_user), db: Session = Depends(get_db)):
    try:
        if not user_permition(user.ID_USUARIO, db):
            raise HTTPException(status_code=403, detail='Sem permissão para criar relatório')
        
        novo_relatorio = Relatorio(ID_GRUPO=relatorio.ID_GRUPO, DS_NOME_RELATORIO=relatorio.DS_NOME_RELATORIO, DS_LINK_RELATORIO=relatorio.DS_LINK_RELATORIO)
        db.add(novo_relatorio)
        db.commit()
        db.refresh(novo_relatorio)
        
        return {"mensagem": "Relatório criado com sucesso", "id_relatorio": novo_relatorio.ID_RELATORIO}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put('/editReport/{report_id}', tags=['Reports'])
async def update_report(report_id: int, relatorio: RelatorioUpdate, user: User = Depends(get_auth_user), db: Session = Depends(get_db)):
    try:
        if not user_permition(user.ID_USUARIO, db):
            raise HTTPException(status_code=403, detail='Sem permissão para editar relatório')
        
        relatorio_db = db.query(Relatorio).filter(Relatorio.ID_RELATORIO == report_id).first()
        if not relatorio_db:
            raise HTTPException(status_code=404, detail='Relatório não encontrado')
        
        relatorio_db.DS_NOME_RELATORIO = relatorio.DS_NOME_RELATORIO or relatorio_db.DS_NOME_RELATORIO
        relatorio_db.DS_LINK_RELATORIO = relatorio.DS_LINK_RELATORIO or relatorio_db.DS_LINK_RELATORIO
        
        db.commit()
        
        return {"mensagem": "Relatório editado com sucesso"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

