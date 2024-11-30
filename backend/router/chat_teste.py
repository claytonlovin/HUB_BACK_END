import os
import json
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, HTTPException, Depends
from decimal import Decimal
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain.callbacks.base import BaseCallbackHandler
from langchain_community.utilities import SQLDatabase
from models.models import Database, Relatorio
from config.configdb import get_db
from langchain_openai import ChatOpenAI
import re

router = APIRouter()

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
openai_organization = os.getenv("OPENAI_ORGANIZATION")

def get_database_connection(id_relatorio: int, db: Session):
    try:
        get_group = db.query(Relatorio).filter(Relatorio.ID_RELATORIO == id_relatorio).first()
        if not get_group:
            raise HTTPException(status_code=404, detail="Grupo nao encontrado") 
        database_config = db.query(Database).filter(Database.ID_GRUPO == get_group.ID_GRUPO).first()

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


@router.websocket("/ws/chat/{id_relatorio}")
async def websocket_endpoint(websocket: WebSocket, id_relatorio: int, db: Session = Depends(get_db)):
    await websocket.accept()
    try:
        # Configuração do banco e agente
        db_connection = get_database_connection(id_relatorio, db)
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
            handle_parsing_errors=True,
        )

        while True:
            try:
                data = await websocket.receive_text()

                if data.lower() == "sair":
                    break

                query = (
                    f"Você está conectado a um banco de dados do grupo {id_relatorio}. "
                    f"Responda usando apenas informações diretamente relacionadas às tabelas. "
                    f"Gere a consulta SQL para a pergunta: '{data}', execute-a e retorne a resposta."
                )

                sql_query = None
                result_raw = None
                resposta_bruta = None

                for step in agent_executor.iter({"input": query}):
                    inter_output = step.get("intermediate_step")
                    if inter_output:
                        action, value = inter_output[0]
                        if action.tool == "sql_db_query":
                            sql_query = action.tool_input 
                            result_raw = value  
                    elif output := step.get("output"):
                        resposta_bruta = output  

                print("Consulta SQL Capturada:", sql_query)
                print("Resultado Bruto Capturado:", result_raw)
                print("Resposta Final Capturada:", resposta_bruta)

                # contextalizar a resposta
                prompt_contextualizado = (
                    f"Pergunta do usuário: {data}\n"
                    f"Resposta do banco de dados: {resposta_bruta}\n\n"
                    "Por favor, gere uma resposta natural e contextualizada para o usuário com base nos dados e na pergunta."
                )

                resposta_obj = llm.invoke(prompt_contextualizado)
                resposta_final = resposta_obj.content

                """result_json = []
                if result_raw and isinstance(result_raw, list):
                    try:
                        columns = db_connection.execute(sql_query).keys()
                        result_json = [
                            {col: (float(val) if isinstance(val, Decimal) else val) for col, val in zip(columns, row)}
                            for row in result_raw
                        ]
                    except Exception as e:
                        print(f"Erro ao formatar resultado bruto em JSON: {e}")"""

                resposta_completa = {
                    "query": sql_query or "Consulta SQL não gerada.",
                    "result": result_raw,
                    "response_text": resposta_final if resposta_final else "Resposta não gerada.",
                }

                await websocket.send_json(resposta_completa)

            except WebSocketDisconnect:
                print("Cliente desconectado.")
                break
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

