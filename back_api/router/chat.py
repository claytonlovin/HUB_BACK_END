import os
import json
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, HTTPException, Depends
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

        llm = ChatOpenAI(
            model="gpt-3.5-turbo-16k",
            temperature=0.0,
            openai_api_key=openai_api_key,
            openai_organization=openai_organization,
            verbose=True,
        )

        toolkit = SQLDatabaseToolkit(db=db_connection, llm=llm)
        agent_executor = create_sql_agent(
            llm=llm,
            toolkit=toolkit,
            verbose=True
        )

        while True:
            try:
                data = await websocket.receive_text()

                if data.lower() == "sair":
                    break

                # Garante que o modelo entenda que a resposta deve ser traduzida para português
                query = f"Por favor, retorne a resposta para a seguinte consulta SQL em português: {data}"
                resposta = agent_executor.run(query)

                if "gráfico" in data.lower():
                    chart_data = format_data_for_chart(resposta)
                    await websocket.send_text(json.dumps(chart_data))
                else:
                    traduzido_para_pt = traduzir_para_portugues(resposta)
                    await websocket.send_text(traduzido_para_pt)

            except WebSocketDisconnect:
                print("Cliente desconectado.")
                break
            except Exception as e:
                # Captura o erro, envia uma mensagem ao cliente e mantém o WebSocket aberto
                print(f"Erro ao processar: {str(e)}")
                await websocket.send_text("Ocorreu um erro ao processar sua solicitação. Tente novamente.")
                continue  # Mantém o loop funcionando após o erro
    except Exception as e:
        print(f"Erro no WebSocket: {str(e)}")
        try:
            await websocket.send_text("Erro na conexão. Por favor, tente novamente mais tarde.")
        except Exception:
            print("Não foi possível enviar a mensagem de erro ao cliente.")
    finally:
        print("Conexão WebSocket encerrada.")

def format_data_for_chart(resposta):
    categories = []
    values = []

    for entry in resposta:
        categories.append(entry['month'])
        values.append(entry['value'])

    return {
        "options": {
            "chart": {
                "id": "dynamic-chart",
            },
            "xaxis": {
                "categories": categories,
            },
            "title": {
                "text": "Gráfico Dinâmico",
                "align": "center",
            },
        },
        "series": [{
            "name": "Valores Dinâmicos",
            "data": values,
        }],
    }

def traduzir_para_portugues(texto):
    return {texto}
