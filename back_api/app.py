from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

#  CONFIG
from config.configdb import engine, Base, SessionLocal

# IMPORTAS 
from router import  authentication, company, groups, report, user, database, chat

# START
app = FastAPI()

# Definindo portas
origins = [    "http://localhost:3000", "http://127.0.0.1:3000",   "http://localhost:8000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="PowerHUB API",
        version="1.0.0",
        description="Report Management API",
        routes=app.routes,
    )
    """openapi_schema["info"]["x-logo"] = {
        "url": "https://cdn-icons-png.flaticon.com/512/4140/4140047.png"
    }"""
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# IMPORTAR ROTAS
app.include_router(authentication.router)
app.include_router(groups.router)
app.include_router(report.router)
app.include_router(user.router)
app.include_router(company.router)
app.include_router(database.router)
app.include_router(chat.router)
#app.include_router(chat_teste.router)


# EXECUÇÃO DO SERVIDOR
app.openapi = custom_openapi