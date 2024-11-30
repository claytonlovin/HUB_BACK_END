
# IMPORT EXTERNOS
from config.configdb import *
from schemas.loginSchemas import UserLoginRequest, UserLoginResponse
from schemas.createUserSchemas import UserCreate
#JWT TOKEN
from authentication.auths import create_access_token
# IMPORT INTERAL
from fastapi.responses import JSONResponse
from models.models import User, Organizacao
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi.params import Body
from sqlalchemy import text
import stripe 
import datetime
import jwt
import re
import hashlib

# IMPORT GOOGLE
from google.oauth2 import id_token
from google.auth.transport import requests

router = APIRouter()

@router.post('/google-login', response_model=UserLoginResponse, tags=['Authentication'])
def google_login(google_token: str = Body(...)):
    """
    Autenticação de usuário via Google. Recebe um token JWT do Google e verifica se o e-mail está cadastrado no banco.
    """
    try:
        id_info = id_token.verify_oauth2_token(google_token, requests.Request(), "369932515787-k5i0lh9apkctn310494flhciubjn2asi.apps.googleusercontent.com")
        
        email = id_info.get("email")
        name = id_info.get("name")
        picture = id_info.get("picture")

        if not email:
            raise HTTPException(status_code=400, detail="Token inválido ou e-mail ausente.")

        with SessionLocal() as session:
            user = session.query(User).filter(User.DS_EMAIL == email).first()
            if not user:
                raise HTTPException(status_code=404, detail="Usuário não encontrado. Por favor, cadastre-se.")

            org = session.query(Organizacao).filter(Organizacao.ID_ORGANIZACAO == user.ID_ORGANIZACAO).first()
            if not org or not org.FL_ATIVO:
                raise HTTPException(status_code=403, detail="Organização inativa. Entre em contato com o suporte.")

            user_info = {
                'id_user': user.ID_USUARIO,
                'nome_user': user.NOME_USUARIO,
                'email_user': user.DS_EMAIL,
                'id_company': user.ID_ORGANIZACAO,
                'administrator': user.FL_ADMINISTRADOR,
                'fl_proprietario_conta': user.FL_PROPRIETARIO_CONTA,
                'premium': org.PREMIUM
            }

            token = create_access_token(user_info)
            response = UserLoginResponse(success=True, message="Autenticado com sucesso via Google", token=token, user_info=user_info)
            return response

    except ValueError:
        raise HTTPException(status_code=400, detail="Token do Google inválido.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.post('/login', response_model=UserLoginResponse, tags=['Authentication'])
def login(user_login_request: UserLoginRequest = Body(...) ):
    """ Será gerado um toke JWT, esse token será obrigatório para consumos dos demais endpoints. A expiração é de 1440 Minutos.
    * O token é individual para cada usuário
    * Possui informações específicas de usuários, permissões e organizaçãoo. 
    """
    with SessionLocal() as session:
        email = user_login_request.email
        password = user_login_request.password
        user = session.query(User).filter(User.DS_EMAIL == email).first()
        org = session.query(Organizacao).filter(Organizacao.ID_ORGANIZACAO == user.ID_ORGANIZACAO).first()
        if user:
            password_criptografada = hashlib.sha256(password.encode()).hexdigest()

            if password_criptografada == user.DS_SENHA and org.FL_ATIVO == True:
                user_info = {
                    'id_user': user.ID_USUARIO,
                    'nome_user': user.NOME_USUARIO,
                    'email_user': user.DS_EMAIL,
                    'id_company': user.ID_ORGANIZACAO,
                    'administrator': user.FL_ADMINISTRADOR,
                    'fl_proprietario_conta': user.FL_PROPRIETARIO_CONTA,
                    'premium': org.PREMIUM
                }
                token = create_access_token(user_info)
                response = UserLoginResponse(success=True, message='Autenticado com sucesso', token=token, user_info=user_info)
                return response
    raise HTTPException(status_code=401, detail='Senha incorreta ou Usuário não encontrado!')



@router.post("/registerFullCompanies", tags=['Authentication'])
async def register(user: UserCreate):

    #Endpoint para registrar uma organização e realizar pagamento em um único fluxo.
  
    # Coletar os dados enviados
    
    organization_name = user.organization_name
    cnpj = user.cnpj
    email = user.email
    phone_number = user.phone_number
    name = user.name
    password = user.password

    # Validação de dados
    senha_criptografada = hashlib.sha256(password.encode()).hexdigest()
    if not all([organization_name, cnpj, email, phone_number, name, password]):
        raise HTTPException(status_code=400, detail="Por favor, preencha todos os campos obrigatórios")

    if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
        raise HTTPException(status_code=400, detail="E-mail inválido")

    if not re.match(r'[0-9]{2}[0-9]{5}[0-9]{4}', phone_number):
        raise HTTPException(status_code=400, detail="Telefone inválido")

    # Passo 1: Criar sessão de pagamento no Stripe
    try:
        import stripe
        stripe.api_key = "rk_test_51MGD2ECiScSQxo4glNmBiBx20FxMgVN23bux7jOiinhvyInEteTwkNHLyePgV7MvnoMkYlpDxWCyGpcbMIlVzBbO00WBeTTkOd"

        # Criar sessão de pagamento
        stripe_session  = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "brl",
                        "product_data": {
                            "name": f"Registro de Organização: {organization_name}",
                        },
                        "unit_amount": 5000,  # Preço em centavos (R$50,00)
                    },
                    "quantity": 1,
                },
            ],
            mode="payment",
            success_url="http://seusite.com/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="http://seusite.com/cancel",
        )
        payment_url = stripe_session.url

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Erro no Stripe: {e.user_message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar sessão de pagamento: {str(e)}")

    # Passo 2: Confirmar pagamento (placeholder, substitua pelo webhook em produção)
    payment_confirmed = True  # Simulado por enquanto
    if not payment_confirmed:
        raise HTTPException(status_code=402, detail="Pagamento não confirmado")

    # Passo 3: Criar organização após confirmação de pagamento
    try:
        # executar procedure
        SQL = text('CALL sp_create_organizacao_and_user(:param1, :param2, :param3, :param4, :param5, :param6, :param7, :param8, :param9, :param10, :param11, :param12, :param13, :param14, :param15, :param16, :param17, :param18, :param19, :param20, :param21, :param22, :param23, :param24)')

        params = {
        'param1': 0, 'param2': organization_name, 'param3':cnpj, 'param4': datetime.datetime.now(), 'param5': 1,  'param6': 1,
        'param7': 0, 'param8': 'PW Grupo', 'param9': datetime.datetime.now(),'param10': 1, 'param11': 0,
        'param12': 0, 'param13': name, 'param14': phone_number, 'param15': email, 'param16': email, 'param17': senha_criptografada, 'param18': 1, 'param19': 0, 'param20': 1,
        'param21': 0, 'param22': 0, 'param23': 0, 'param24': 0
        } 

        session = Session(bind=engine)
        session.execute(SQL, params)
        session.commit()

    except SQLAlchemyError as e:
        error_info = str(e.args[0])
        if 'UNIQUE' in error_info and 'email' in error_info:
            raise HTTPException(status_code=400, detail='Alguém está utilizando esse mesmo login ou senha')
        elif 'UNIQUE' in error_info and 'cnpj' in error_info:
            raise HTTPException(status_code=400, detail='CNPJ Já cadastrado!')
        elif 'UNIQUE' in error_info and 'phone_number' in error_info:
            raise HTTPException(status_code=400, detail='Número de telefone já cadastrado!')
        else:
            raise HTTPException(status_code=400, detail='Erro ao inserir no banco de dados')

    # Resposta final
    response = {
        'success': True,
        'message': 'Organização criada com sucesso após pagamento confirmado',
        'payment_url': payment_url  # URL para redirecionar para o Stripe
    }
    return JSONResponse(content=response, status_code=201)

