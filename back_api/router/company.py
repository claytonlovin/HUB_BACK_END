from config.configdb import *
# IMPORT INTERAL
from fastapi.responses import JSONResponse
from fastapi import  HTTPException
from models.models import User, Organizacao
from sqlalchemy.orm import Session
from fastapi import Depends, Header, HTTPException
# SECURITY
from authentication.securityDefinition import get_auth_user, user_permition
from dotenv import load_dotenv
import jwt
import os
import datetime
import stripe
# CONFIG 
now = datetime.datetime.now()
iso_date = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
load_dotenv()



#
#essa função está em desenvolvimento
#


# CONNECT STRIPE
stripe.api_key = os.getenv('STRIPE_API_KEY')
PREMIUM_VALUE = os.getenv('PREMIUM_VALUE')

@router.get('/listaClientEmp', tags=['Company_payment'])
async def list_enterprise(user: User = Depends(get_auth_user), db: Session = Depends(get_db)):
    try: 
        if user_permition(user.ID_USUARIO, db) == True:
            enterprise = db.query(Organizacao).filter(Organizacao.ID_ORGANIZACAO == user.ID_ORGANIZACAO).all()
        list_grupo_usuario = [{
            "Company_name": g.NOME_ORGANIZACAO,     
            "DS_CNPJ": g.DS_CNPJ,     
            "Data_creation": g.DATA_CRIACAO.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "Fl_active" : g.FL_ATIVO,
            "Premium": g.PREMIUM 
            } 
            for g in enterprise]
        return JSONResponse(content=list_grupo_usuario)
    except Exception as e:
        return {"erro": str(e)}
    
stripe.api_key = "SUA_CHAVE_PRIVADA_DO_STRIPE"
PREMIUM_VALUE = 35880

@router.post("ClientEmp/Getpremium", tags=['Company_payment'])
async def pay_premium(token: str, user: User = Depends(get_auth_user), db: Session = Depends(get_db)):
    
    organizacao = db.query(Organizacao).get(user.ID_ORGANIZACAO)
    if organizacao.PREMIUM:
        raise HTTPException(status_code=400, detail="Organização já é premium")
    
    try:
        charge = stripe.Charge.create(
            amount=PREMIUM_VALUE/100,
            currency="brl",
            source= token,
            description="Pagamento de assinatura da organização {}.".format(organizacao.NOME_ORGANIZACAO),
        )

        organizacao.PREMIUM = True
        db.commit()

        return {"mensagem": "Pagamento efetuado com sucesso"}
    except stripe.error.CardError as e:
        return {"erro": e.error.message}