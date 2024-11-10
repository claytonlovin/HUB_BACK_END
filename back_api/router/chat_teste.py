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
from transformers import LlamaTokenizer,AutoTokenizer, LlamaForCausalLM, pipeline

router = APIRouter()

load_dotenv()



model_dir = "/home/clayton/.llama/checkpoints/Prompt-Guard-86M/"

# Carregar o tokenizador e o modelo com trust_remote_code
tokenizer = AutoTokenizer.from_pretrained(model_dir, use_fast=False, trust_remote_code=True)
llama_model = LlamaForCausalLM.from_pretrained(model_dir, use_safetensors=True)

llm_pipeline = pipeline('text-generation', model=llama_model, tokenizer=tokenizer)

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

@router.websocket("/ws/chat/2/{id_grupo}")
async def websocket_endpoint(websocket: WebSocket, id_grupo: int, db: Session = Depends(get_db)):
    await websocket.accept()
    try:
        db_connection = get_database_connection(id_grupo, db)

        toolkit = SQLDatabaseToolkit(db=db_connection, llm=llm_pipeline)
        agent_executor = create_sql_agent(
            llm=llm_pipeline,
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
