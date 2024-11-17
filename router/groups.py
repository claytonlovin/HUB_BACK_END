from config.configdb import *
from schemas.grupoSchemas import GrupoUpdate, Usuario
from schemas.createGrupo import GrupoCreate
# IMPORT INTERAL
from fastapi.responses import JSONResponse
from fastapi import  HTTPException
from models.models import User, Organizacao, GroupUser, Grupo
import jwt
from sqlalchemy.orm import Session
from sqlalchemy import exists, and_
from fastapi import Depends, Header, HTTPException
# SECURITY
from authentication.securityDefinition import get_auth_user, user_permition
import jwt
import datetime
# CONFIG 
now = datetime.datetime.now()
iso_date = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

@router.get('/listGroup', tags=['Group_companies'])
async def list_group(user: User = Depends(get_auth_user), db: Session = Depends(get_db)):
    try: 
        if user_permition(user.ID_USUARIO, db) == True:
            grupos_usuario = db.query(Grupo).filter(Grupo.ID_ORGANIZACAO == user.ID_ORGANIZACAO).all()
        else:
            grupos_usuario = db.query(Grupo).join(GroupUser).join(Organizacao).join(User). \
                filter(GroupUser.ID_USUARIO == user.ID_USUARIO).all()
        list_grupo_usuario = [{
            "Id_group": g.ID_GRUPO,     
            "Name_group": g.NOME_DO_GRUPO,     
            "Data_create": g.DATA_CRIACAO.strftime("%Y-%m-%dT%H:%M:%S.%fZ")    
            } 
            for g in grupos_usuario]

        return JSONResponse(content=list_grupo_usuario)
    except Exception as e:
        return {"erro": str(e)}

@router.put('/editGroup/{group_id}', tags=['Group_companies'])
async def edit_group(group_id: int, group: GrupoUpdate, current_user: Usuario = Depends(get_auth_user), db: Session = Depends(get_db)):
    try:   
        grupo_db = db.query(Grupo).filter(Grupo.ID_GRUPO == group_id).first()
        usuario = db.query(User).filter(User.ID_USUARIO == current_user.ID_USUARIO).first()
        if grupo_db is None:
            raise HTTPException(status_code=404, detail='Grupo não encontrado')

        # Sim eu sei que é a mesma coisa da função user_permition!!! bjs!
        if usuario.FL_ADMINISTRADOR == False:
            raise HTTPException(status_code=403, detail='Sem permissão para editar este grupo')

        grupo_db.NOME_DO_GRUPO = group.NOME_DO_GRUPO
        #grupo_db.DATA_ATUALIZACAO = datetime.utcnow()
        db.commit()
        db.refresh(grupo_db)
        return grupo_db
    except Exception as e:
        return {"erro": str(e)}

@router.delete('/deleteGroup/{grupo_id}', tags=['Group_companies'])
async def delete_group(grupo_id: int, current_user: Usuario = Depends(get_auth_user),db: Session = Depends(get_db),):
    try:
        grupo_db = db.query(Grupo).filter(Grupo.ID_GRUPO == grupo_id).first()
        grupo_db_user = db.query(GroupUser).filter(GroupUser.ID_GRUPO == grupo_id).first() 
        if grupo_db is None:
            raise HTTPException(status_code=404, detail='Grupo não encontrado')

        if user_permition(current_user.ID_USUARIO, db) != True:
            raise HTTPException(status_code=403, detail='Sem permissão para deletar grupos')
        if grupo_db_user:
            db.delete(grupo_db_user)
    
        if grupo_db:
            db.delete(grupo_db)
        db.commit()
        return {"mensagem": "Grupo deletado com sucesso"}
    except Exception as e:
        return {"erro": str(e)}


@router.post('/createGroup', tags=['Group_companies'])
async def create_group(grupo: GrupoCreate, current_user: Usuario = Depends(get_auth_user), db: Session = Depends(get_db)):
    try:
        usuario = db.query(User).filter(User.ID_USUARIO == current_user.ID_USUARIO).first()
        if usuario is None:
            raise HTTPException(status_code=401, detail='Usuário não autenticado')
        
        if user_permition(current_user.ID_USUARIO, db) != True:
            raise HTTPException(status_code=403, detail='Sem permissão para criar grupo')
        
        novo_grupo = Grupo(
            NOME_DO_GRUPO=grupo.NOME_DO_GRUPO,
            DATA_CRIACAO=datetime.datetime.now(),
            FL_ATIVO=True,
            ID_ORGANIZACAO=usuario.ID_ORGANIZACAO
        )
        db.add(novo_grupo)
        db.commit()
        db.refresh(novo_grupo)

        return {
            "success": True,
            "newGroup": {
                "ID_GRUPO": novo_grupo.ID_GRUPO,
                "Name_group": novo_grupo.NOME_DO_GRUPO,
                "Data_create": novo_grupo.DATA_CRIACAO.isoformat()
            }
        }
    except Exception as e:
        return {"erro": str(e)}



@router.post('/bindUser/{user_id}/{group_id}', tags=['Permission'])
async def bind_group(user_id: int, group_id : int, current_user: Usuario = Depends(get_auth_user), db: Session = Depends(get_db)):
    try:
        usuario = db.query(User).filter(User.ID_USUARIO == user_id).first()
        if usuario is None:
            raise HTTPException(status_code=401, detail='Usuário não encontrado')
        
        if user_permition(current_user.ID_USUARIO, db) != True:
            raise HTTPException(status_code=403, detail='Sem permissão para criar grupo')
        
        if db.query(exists().where(and_(GroupUser.ID_USUARIO == user_id, GroupUser.ID_GRUPO == group_id))).scalar():
            raise HTTPException(status_code=400, detail="Usuário já vinculado a este grupo")

        user_group = GroupUser(
            ID_USUARIO=user_id,
            ID_GRUPO=group_id,
            ID_ORGANIZACAO=current_user.ID_ORGANIZACAO
        )

        db.add(user_group)
        db.commit()
        db.refresh(user_group)

        return {"mensagem": "Usuário vinculado com sucesso", "id_usuario": user_group.ID_USUARIO, "id_grupo": user_group.ID_GRUPO}
    except Exception as e:
        return {"erro": str(e)}
@router.delete('/unbindUser/{usuario_id}/{group_id}', tags=['Permission'])
async def unlink_group(usuario_id: int, group_id: int, current_user: Usuario = Depends(get_auth_user), db: Session = Depends(get_db)):
    try:
        usuario = db.query(User).filter(User.ID_USUARIO == usuario_id).first()
        if usuario is None:
            raise HTTPException(status_code=401, detail='Usuário não encontrado')
        
        if user_permition(current_user.ID_USUARIO, db) != True:
            raise HTTPException(status_code=403, detail='Sem permissão para criar grupo')
    
        if not db.query(exists().where(and_(GroupUser.ID_USUARIO == usuario_id, GroupUser.ID_GRUPO == group_id))).scalar():
            raise HTTPException(status_code=400, detail="Usuário não está vinculado a este grupo")

        db.query(GroupUser).filter(and_(GroupUser.ID_USUARIO == usuario_id, GroupUser.ID_GRUPO == group_id)).delete()

        db.commit()

        return {"mensagem": "Usuário desvinculado do grupo com sucesso", "id_usuario": usuario_id, "id_grupo": group_id}
    except Exception as e:
        return {"erro": str(e)}



# Lista grupos por usuarios
@router.get('/listGroupUser/{id_group}', tags=['Group_companies'])
async def list_group_user(id_group: int, current_user: Usuario = Depends(get_auth_user), db: Session = Depends(get_db)):
    try:
        grupos = db.query(GroupUser, User).filter(GroupUser.ID_GRUPO == id_group, GroupUser.ID_ORGANIZACAO == current_user.ID_ORGANIZACAO).join(User, GroupUser.ID_USUARIO == User.ID_USUARIO).all()
        
        listGrupUser = [{
            "Id_group": g.ID_GRUPO,     
            'Id_user': g.ID_USUARIO,  
            "Name_user": u.NOME_USUARIO,     
        } for g, u in grupos]

        return JSONResponse(content=listGrupUser)    
    except Exception as e:
        return {"erro": str(e)}

@router.get('/listUsersNotInGroup/{id_group}', tags=['Group_companies'])
async def list_users_not_in_group(id_group: int, current_user: Usuario = Depends(get_auth_user), db: Session = Depends(get_db)):
    try:
        subquery = db.query(GroupUser.ID_USUARIO).filter(GroupUser.ID_GRUPO == id_group).subquery()
        usuarios = db.query(User).filter(User.ID_USUARIO.notin_(subquery), User.ID_ORGANIZACAO == current_user.ID_ORGANIZACAO).all()
        
        listUsersNotInGroup = [{
            "Id_user": u.ID_USUARIO,
            "Name_user": u.NOME_USUARIO,
        } for u in usuarios]
        if not listUsersNotInGroup:
            raise HTTPException(status_code=404, detail='Nenhum usuário encontrado')
        else:
            return JSONResponse(content=listUsersNotInGroup)
    except Exception as e:
        return {"erro": str(e)}
