import os
import json
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, HTTPException, Depends
from decimal import Decimal
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from models.models import Database
from config.configdb import get_db
from langchain_openai import ChatOpenAI

router = APIRouter()

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
openai_organization = os.getenv("OPENAI_ORGANIZATION")

def get_database_connection(id_grupo: int, db: Session):
    try:
        database_config = db.query(Database).filter(Database.ID_GRUPO == id_grupo).first()
        if not database_config:
            raise HTTPException(status_code=404, detail="Conexão com o banco de dados não encontrada para o grupo fornecido.")

        db_type = database_config.ID_TYPE_DATABASE

        if db_type == 3:
            connection_string = (
                f"oracle+cx_oracle://{database_config.USER_CONNECTION}:{database_config.PASSWORD_CONNECTION}"
                f"@{database_config.IP_CONNECTION}:{database_config.PORT_CONNECTION}/{database_config.DB_CONNECTION}"
            )
        elif db_type == 4:
            connection_string = (
                f"mssql+pyodbc://{database_config.USER_CONNECTION}:{database_config.PASSWORD_CONNECTION}"
                f"@{database_config.IP_CONNECTION}:{database_config.PORT_CONNECTION}/{database_config.DB_CONNECTION}"
                "?driver=ODBC+Driver+17+for+SQL+Server"
            )
        elif db_type == 5:
            connection_string = (
                f"mysql+pymysql://{database_config.USER_CONNECTION}:{database_config.PASSWORD_CONNECTION}"
                f"@{database_config.IP_CONNECTION}:{database_config.PORT_CONNECTION}/{database_config.DB_CONNECTION}"
            )
        else:
            raise HTTPException(status_code=400, detail="Tipo de banco de dados não suportado.")

        return SQLDatabase.from_uri(connection_string)
    except Exception as e:
        print(f"Erro ao obter conexão com o banco de dados: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao tentar conectar ao banco de dados.")
    
    
@router.websocket("/ws/chat/{id_grupo}")
async def websocket_endpoint(websocket: WebSocket, id_grupo: int, db: Session = Depends(get_db)):
    await websocket.accept()
    try:
        db_connection = get_database_connection(id_grupo, db)
        print("Tabelas disponíveis:", db_connection.get_table_names())

        llm = ChatOpenAI(
            model="gpt-3.5-turbo-16k",
            temperature=0.7,
            openai_api_key=openai_api_key,
            openai_organization=openai_organization,
            verbose=True,
        )

        relevant_tables = db_connection.get_table_names()
        toolkit = SQLDatabaseToolkit(db=db_connection, llm=llm, tables=relevant_tables, schema="ERP")
        agent_executor = create_sql_agent(
            llm=llm,
            toolkit=toolkit,
            verbose=True,
            handle_parsing_errors=True
        )

        while True:
            try:
                data = await websocket.receive_text()

                if data.lower() == "sair":
                    break

                query = (
                    f"Você está conectado a um banco de dados do grupo {id_grupo}. "
                    f"Responda apenas usando informações das tabelas diretamente relacionadas. "
                    f"Por favor, retorne a resposta para a seguinte consulta em português: {data}"
                )

                resposta_bruta = agent_executor.run(query)
                resposta_formatada = formatar_resposta_bruta(resposta_bruta)

                prompt_contextualizado = (
                    f"Pergunta do usuário: {data}\n"
                    f"Resposta do banco de dados: {resposta_formatada}\n\n"
                    "Por favor, gere uma resposta natural e contextualizada para o usuário com base nos dados e na pergunta."
                )

                resposta_obj = llm.invoke(prompt_contextualizado)
                resposta_final = resposta_obj.content

                await websocket.send_text(resposta_final)

            except WebSocketDisconnect:
                print("Cliente desconectado.")
                break
            except ValueError as ve:
                print(f"Erro de formatação: {str(ve)}")
                await websocket.send_text("Erro ao formatar a resposta. Tente novamente.")
            except Exception as e:
                print(f"Erro ao processar: {str(e)}")
                await websocket.send_text("Ocorreu um erro ao processar sua solicitação. Tente novamente.")
                continue  
    except Exception as e:
        print(f"Erro no WebSocket: {str(e)}")
        try:
            await websocket.send_text("Erro na conexão. Por favor, tente novamente mais tarde.")
        except Exception:
            print("Não foi possível enviar a mensagem de erro ao cliente.")
    finally:
        print("Conexão WebSocket encerrada.")

def formatar_resposta_bruta(resposta):
    if isinstance(resposta, list):
        resposta_formatada = []
        for item in resposta:
            chave = item[0]
            valor = float(item[1]) if isinstance(item[1], Decimal) else item[1]
            resposta_formatada.append(f"{chave}: {valor}")
        return "; ".join(resposta_formatada)
    return str(resposta)
