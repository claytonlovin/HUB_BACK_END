from config.configdb import *
from schemas.schemasDatabase import DatabaseCreate, DatabaseUpdate
# IMPORT INTERAL
from fastapi.responses import JSONResponse
from fastapi import  HTTPException
from models.models import User, GroupUser, Database, Grupo
from sqlalchemy.orm import Session
from fastapi import Depends, Header, HTTPException

# SECURITY
from authentication.securityDefinition import get_auth_user, user_permition
import datetime
import hashlib

@router.get('/ListDatabase/{id_grupo}', tags=['Database'])
async def list_database( id_grupo: int,user: User = Depends(get_auth_user), db: Session = Depends(get_db)):
    try:
        if user_permition(user.ID_USUARIO, db):
            databases = db.query(Database).\
                join(GroupUser, GroupUser.ID_GRUPO == id_grupo).\
                join(User, GroupUser.ID_USUARIO == User.ID_USUARIO).\
                filter(
                    User.FL_ADMINISTRADOR == True
                ).all()
        else:
            return HTTPException(status_code=401, detail="Unauthorized")
        
        return JSONResponse(status_code=200, content=[db_instance.to_dict() for db_instance in databases])

    except Exception as e:
        return {"erro": str(e)}
    

@router.post('/CreateDatabase', tags=['Database'])
async def create_database(database: DatabaseCreate, user: User = Depends(get_auth_user), db: Session = Depends(get_db)):
    try:
        # Verifica se o usuário tem permissão
        if user_permition(user.ID_USUARIO, db):
            # Junções explícitas com as condições definidas
            db_database = Database(
                ID_GRUPO = database.ID_GRUPO,
                IP_CONNECTION = database.IP_CONNECTION,
                PORT_CONNECTION = database.PORT_CONNECTION,
                USER_CONNECTION = database.USER_CONNECTION,
                PASSWORD_CONNECTION = database.PASSWORD_CONNECTION,
                DB_CONNECTION = database.DB_CONNECTION
            )
            db.add(db_database)
            db.commit()
            db.refresh(db_database)
            return JSONResponse(status_code=200, content=db_database.to_dict())

        else:
            return HTTPException(status_code=401, detail="Unauthorized")

    except Exception as e:
        return {"erro": str(e)}
    

@router.put('/UpdateDatabase', tags=['Database'])
async def update_database(database: DatabaseUpdate, user: User = Depends(get_auth_user), db: Session = Depends(get_db)):
    try:
        if user_permition(user.ID_USUARIO, db):
            db_database = db.query(Database).filter(Database.ID_DATABASE == database.ID_DATABASE).first()
            db_database.ID_DATABASE = database.ID_DATABASE
            db_database.ID_GRUPO = database.ID_GRUPO
            db_database.IP_CONNECTION = database.IP_CONNECTION
            db_database.PORT_CONNECTION = database.PORT_CONNECTION
            db_database.USER_CONNECTION = database.USER_CONNECTION
            db_database.PASSWORD_CONNECTION = database.PASSWORD_CONNECTION
            db_database.DB_CONNECTION = database.DB_CONNECTION
            db.commit()
            db.refresh(db_database)
            return JSONResponse(status_code=200, content=db_database.to_dict()) 

        else: 
            return HTTPException(status_code=401, detail="Unauthorized")

    except Exception as e:
        return {"erro": str(e)}


@router.delete('/DeleteDatabase', tags=['Database'])
async def delete_database(database_id: int, user: User = Depends(get_auth_user), db: Session = Depends(get_db)):
    try:
        # Verifica se o usuário tem permissão
        if user_permition(user.ID_USUARIO, db):
            # Junções explícitas com as condições definidas
            db_database = db.query(Database).filter(Database.ID_DATABASE == database_id).first()
            db.delete(db_database)
            db.commit()
            return JSONResponse(status_code=200, content=db_database.to_dict())

        else:
            return HTTPException(status_code=401, detail="Unauthorized")

    except Exception as e:
        return {"erro": str(e)}
    