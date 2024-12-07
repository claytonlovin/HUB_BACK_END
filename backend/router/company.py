from config.configdb import *
# IMPORT INTERAL
from fastapi.responses import JSONResponse
from fastapi import  HTTPException
from models.models import User, Organizacao
from controller.validatePaymentPlan import totalUserReport
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from fastapi import Depends, Header, HTTPException
# SECURITY
from authentication.securityDefinition import get_auth_user, user_permition
from dotenv import load_dotenv
import mercadopago
import datetime

# CONFIG 
now = datetime.datetime.now()
iso_date = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
load_dotenv()


# CONNECT STRIPE
mp = mercadopago.SDK("TEST-3525020338471494-112418-4bfff38fd8239b50228744b53e9234e1-2062619323")

PREMIUM_VALUE = 9900  # Valor do plano premium R$99.00

@router.post("/ClientEmp/Getpremium", tags=["Company_payment"])
async def pay_premium(user: User = Depends(get_auth_user), db: Session = Depends(get_db)):
    organizacao = db.query(Organizacao).get(user.ID_ORGANIZACAO)
    if organizacao.PREMIUM:
        raise HTTPException(status_code=400, detail="Organização já é premium")
    try:
        preference_data = {
            "items": [
                {
                    "title": f"Assinatura Premium - {organizacao.NOME_ORGANIZACAO}",
                    "quantity": 1,
                    "currency_id": "BRL",
                    "unit_price": PREMIUM_VALUE / 100, 
                }
            ],
            "payer": {
                "email": user.DS_EMAIL 
            },
            "back_urls": {
                "success": "https://seusite.com/pagamento/sucesso",
                "failure": "https://seusite.com/pagamento/falha",
                "pending": "https://seusite.com/pagamento/pendente",
            },
            "auto_return": "approved",
        }

        preference_response = mp.preference().create(preference_data)
        preference_id = preference_response["response"]["id"]

        return {"preference_id": preference_id, "init_point": preference_response["response"]["init_point"]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar preferência: {str(e)}")

# VERIFICA SE PODE PROSSGUIR COMA CRIAÇÕD  GRUPOS E USUARIOS:
@router.get("/payment/status/", tags=["Company_payment"])
async def get_payment_status( user: User = Depends(get_auth_user), db: Session = Depends(get_db)):
    try:
        organizacao = db.query(Organizacao).filter(Organizacao.ID_ORGANIZACAO == user.ID_ORGANIZACAO and user.FL_PROPRIETARIO_CONTA == True).first()
        if not organizacao:
            raise HTTPException(status_code=404, detail="Organização não encontrada")
        return {"status": "success", "status_code": 200, "premium": organizacao.PREMIUM}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter status de pagamento: {str(e)}")


@router.get("/payment/verify_payment", tags=["Company_payment"])
async def verify_payment(user: User = Depends(get_auth_user), db: Session = Depends(get_db)):
    try:
        organizacao = db.query(Organizacao).filter(Organizacao.ID_ORGANIZACAO == user.ID_ORGANIZACAO).first()
        if not organizacao:
            raise HTTPException(status_code=404, detail="Organização não encontrada")

        if organizacao.PREMIUM:
            return {"status": "success", "status_code": 200, "premium": True}
        
        else:
            isValid = totalUserReport(user.ID_ORGANIZACAO, db)
        return isValid
    except SQLAlchemyError as e:
         raise HTTPException(status_code=500, detail=f"Erro no banco de dados: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar status de pagamento: {str(e)}")

@router.post("/payment/update_premium", tags=["Company_payment"])
async def update_premium(user: User = Depends(get_auth_user), db: Session = Depends(get_db)):
    try:
        organizacao = db.query(Organizacao).filter(Organizacao.ID_ORGANIZACAO == user.ID_ORGANIZACAO).first()
        organizacao.PREMIUM = True
        db.commit()
        db.refresh(organizacao) 
        return {"status": "success", "statsus_code": 200, "premium": organizacao.PREMIUM}
    except Exception as e:  
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar status de pagamento: {str(e)}")
    


@router.post("/payment/create_preference", tags=["Payment"])
async def create_preference(user: User = Depends(get_auth_user), db=Depends(get_db)):
    """
    Cria uma preferência de pagamento para o Checkout Pro.
    """
    try:
        organizacao = db.query(Organizacao).get(user.ID_ORGANIZACAO)
        if organizacao.PREMIUM:
            raise HTTPException(status_code=400, detail="Organização já é premium.")

        preference_data = {
            "items": [
                {
                    "title": "Assinatura Premium",
                    "quantity": 1,
                    "unit_price": 100.0,  # Valor em reais
                    "currency_id": "BRL",
                }
            ],
            "payer": {
                "email": user.DS_EMAIL,
            },
            "back_urls": {
                "success": "https://seusite.com/pagamento/sucesso",
                "failure": "https://seusite.com/pagamento/falha",
                "pending": "https://seusite.com/pagamento/pendente",
            },
            "auto_return": "approved",
        }

        # Cria a preferência
        preference = mp.preference().create(preference_data)

        return {"init_point": preference["response"]["init_point"]}  # Link do Checkout Pro
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar preferência: {str(e)}")