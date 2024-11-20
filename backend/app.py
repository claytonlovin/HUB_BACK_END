from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import gunicorn
#  CONFIG
from config.configdb import engine, Base, SessionLocal

from router import  authentication, company, groups, report, user, database, chat, integracao

app = FastAPI(
         openapi_url="/api/openapi.json",
         docs_url="/api/docs",
        redoc_url="/api/redoc"

)

origins = [
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "petalflow.com.br",
    "http://127.0.0.1:8000/login",
    "http://127.0.0.1:8000",
    "https://petalflow.com.br",
    "https://145.223.94.206",
    "145.223.94.206"
    ]

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
    openapi_schema["openapi"] = "3.1.0"  
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# IMPORTAR ROTAS
app.include_router(authentication.router, prefix="/api")
app.include_router(groups.router, prefix="/api")
app.include_router(report.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(company.router, prefix="/api")
app.include_router(database.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(integracao.router, prefix="/api")

# EXECUÇÃO DO SERVIDOR
app.openapi = custom_openapi
