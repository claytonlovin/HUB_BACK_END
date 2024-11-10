from config.configdb import *
from schemas.createUserSchemas import UsuarioSystem
# IMPORT INTERAL
from fastapi.responses import JSONResponse
from fastapi import  HTTPException
from models.models import User, GroupUser
from sqlalchemy.orm import Session
from fastapi import Depends, Header, HTTPException

# SECURITY
from authentication.securityDefinition import get_auth_user, user_permition
import datetime
import hashlib
# CONFIG 
now = datetime.datetime.now()
iso_date = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")




@router.get('/ListUser', tags=['Users'])
async def list_user(user: User = Depends(get_auth_user), db: Session = Depends(get_db)):
    """
    Retorna a lista de usuários da organização.
    Observação: o ID da organização já está incluído no token de autenticação e não precisa ser passado como parâmetro.
    """
    try: 
        usuarios = db.query(User).filter(User.ID_ORGANIZACAO == user.ID_ORGANIZACAO).all()
        if user_permition(user.ID_USUARIO, db) != True:
            raise HTTPException(status_code=403, detail='Sem permissão para visualizar usuarios')
        
        usuarios = [{
            "id_user": g.ID_USUARIO,   
            "DS_EMAIL": g.DS_EMAIL,
            "DS_TELEFONE": g.DS_TELEFONE,
            "NOME_USUARIO": g.NOME_USUARIO,
            "FL_ADMINISTRADOR": g.FL_ADMINISTRADOR
            } 
            for g in usuarios]

        return JSONResponse(content=usuarios)

    except Exception as e:
        return {"erro": str(e)}

@router.delete('/deleteUser/{user_id}', tags=['Users'])
async def delete_user(user_id: int, user: User = Depends(get_auth_user), db: Session = Depends(get_db)):
    try:
        usuario = db.query(User).filter(User.ID_USUARIO == user_id).first()
        grupo_usuario = db.query(GroupUser).filter(GroupUser.ID_USUARIO == usuario.ID_USUARIO).first()

        if user_permition(user.ID_USUARIO, db) != True:
            raise HTTPException(status_code=403, detail='Sem permissão para deletar usuario consulte o administrador do sistema')
        
        if grupo_usuario:
            raise HTTPException(status_code=403, detail='O usuário está vinculado a um grupo')

        db.delete(usuario)
        db.commit()
        
        return {"mensagem": "Usuario deletado com sucesso"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put('/editUser/{user_id}', tags=['Users'])
async def update_user(user_id: int, usuario: UsuarioSystem, user: User = Depends(get_auth_user), db: Session = Depends(get_db)):
    try:
        if not user_permition(user.ID_USUARIO, db):
            raise HTTPException(status_code=403, detail='Sem permissão para criar usuario')        
        usuarioEdit = db.query(User).filter(User.ID_USUARIO == user_id).first()
        email = db.query(User).filter_by(DS_EMAIL=usuario.DS_EMAIL).first()
        telefone = db.query(User).filter_by(DS_TELEFONE=usuario.DS_TELEFONE).first()

        # VERIFICA DADOS
        if not usuarioEdit:
            raise HTTPException(status_code=404, detail='Usuário não encontrado')
        if email and email.ID_USUARIO != user_id:
            raise HTTPException(status_code=400, detail="E-mail já existente")
        if telefone and telefone.ID_USUARIO != user_id:
            raise HTTPException(status_code=400, detail="Telefone já existente")

        DS_SENHA_CR = hashlib.sha256(usuario.DS_SENHA.encode()).hexdigest()

        usuarioEdit.NOME_USUARIO = usuario.NOME_USUARIO or usuarioEdit.NOME_USUARIO
        usuarioEdit.DS_TELEFONE = usuario.DS_TELEFONE or usuarioEdit.DS_TELEFONE
        usuarioEdit.DS_EMAIL = usuario.DS_EMAIL or usuarioEdit.DS_EMAIL
        usuarioEdit.DS_LOGIN = usuario.DS_EMAIL or usuarioEdit.DS_EMAIL
        usuarioEdit.DS_SENHA = DS_SENHA_CR or usuarioEdit.DS_SENHA
        usuarioEdit.FL_ADMINISTRADOR = usuario.FL_ADMINISTRADOR  # Atualiza diretamente
        usuarioEdit.ID_ORGANIZACAO = user.ID_ORGANIZACAO
        usuarioEdit.FL_PROPRIETARIO_CONTA = 0
        db.commit()
        
        return {"mensagem": "Usuário editado com sucesso"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post('/createUser', tags=['Users'])
async def create_user(usuario: UsuarioSystem, user: User = Depends(get_auth_user), db: Session = Depends(get_db)):
    try:
        if not user_permition(user.ID_USUARIO, db):
            raise HTTPException(status_code=403, detail='Sem permissão para criar usuario')
        
        email_existente = db.query(User).filter(User.DS_EMAIL == usuario.DS_EMAIL).first()
        telefone_existente = db.query(User).filter(User.DS_TELEFONE == usuario.DS_TELEFONE).first()

        if email_existente:
            raise HTTPException(status_code=400, detail="Email já existente")
        if telefone_existente:
            raise HTTPException(status_code=400, detail="Telefone já existente")

        DS_SENHA_CR = hashlib.sha256(usuario.DS_SENHA.encode()).hexdigest()

        novo_usuario = User(
            NOME_USUARIO=usuario.NOME_USUARIO,
            DS_TELEFONE=usuario.DS_TELEFONE,
            DS_EMAIL=usuario.DS_EMAIL,
            DS_LOGIN=usuario.DS_LOGIN or usuario.DS_EMAIL,
            DS_SENHA=DS_SENHA_CR,
            FL_ADMINISTRADOR=bool(usuario.FL_ADMINISTRADOR),
            ID_ORGANIZACAO=user.ID_ORGANIZACAO,
            FL_PROPRIETARIO_CONTA=0
        )

        db.add(novo_usuario)
        db.commit()

        return {"mensagem": "Usuário criado com sucesso"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

