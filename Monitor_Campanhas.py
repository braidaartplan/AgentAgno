import os

from agno.agent import Agent
from agno.tools.tavily import TavilyTools
from agno.tools.sql import SQLTools
from agno.models.openai import OpenAIChat
from dotenv import load_dotenv
from agno.playground import Playground, serve_playground_app
from agno.storage.sqlite import SqliteStorage
from textwrap import dedent
from agno.memory.v2.memory import Memory
from agno.memory.v2.db.sqlite import SqliteMemoryDb


# Carrega as variáveis de ambiene com as chaves de API necessárias bem como as credenciais do banco de dados
load_dotenv('/Users/braida/Dev/Python/Stremlit/GitHub/AgentAgno/.env')

# Credenciais do banco de dados Artplan
db_url = f"mysql+pymysql://{os.getenv('DB_USUARIO')}:{os.getenv('DB_SENHA')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NOME')}"

# Criação de banco de dados para armazenar conversas das sessões
db_file = "tmp/agent.db"
db_conversations = SqliteStorage(table_name="Sessoes_Agentes", db_file="tmp/agent.db")


# Criação de memória para o agente. Esta função cria um agente secundário que gerencia a conversa com o usuário, armazenando as principais informações
memory= Memory(
    model= OpenAIChat(id="gpt-4.1-mini"),
    db = SqliteMemoryDb(table_name="Memoria_usuario", db_file=db_file)
    )

# Criação do agente principal que irá analisar as campanhas dos clientes semnalmente e irá ajudar na estruturação dos relatório nas sprints
sql_agent = Agent(
    tools = [SQLTools(db_url=db_url)],
    model= OpenAIChat(id="gpt-4.1-mini"),
    num_history_runs=5,
    add_history_to_messages=True,  
    storage=db_conversations,
    description=dedent("""
                       Você é um analista de dados de marketing digital com experiência em campanhas pagas. Sua tarefa é realizar o acompanhamento semanal das campanhas de marketing dos clientes, com foco na performance dos criativos.
                            Analise os dados da semana e destaque os criativos com melhor e pior desempenho, considerando o objetivo da campanha.
                            Para cada destaque positivo e negativo, apresente as seguintes métricas:
                            Impressões, CPM (Custo por mil impressões)
                            Visualizações até 100%, CPV (Custo por visualização)
                            A análise deve considerar o contexto do objetivo da campanha: por exemplo, para campanhas de alcance, o foco deve estar em impressões e CPM; para campanhas de visualização, dê mais peso para visualizações 100% e CPV.
                            Evite trazer listas longas: selecione apenas os criativos com performance mais relevante — tanto positiva quanto negativa — com base nos dados. 
                            A resposta deve ser estruturada por cliente e campanha, destacando o criativo e suas métricas associadas.
                            Faça:
                            1. 🧠 Um resumo analítico da performance (bom/ruim e por quê)
                            2. 📊 Interpretação dos KPIs principais
                            3. ✅ Recomendações acionáveis para otimização                       
                       """),  
    instructions=(
                    "Sempre que precisar consultar dados, utilize a VIEW Metricas, que contém as seguintes colunas:\n"
                    "- Cliente: Nome do cliente responsável pela campanha. Exemplos incluem: Eletrobras, BNDES, CNI, SEBRAE e SEBRAE RJ.\n"
                    "- Campanha: Nome da campanha. Nem todas as campanhas estão ativas atualmente.\n"
                    "- Veiculo: Plataforma em que os anúncios foram veiculados, como: Instagram, Facebook, TikTok, Pinterest, LinkedIn, Google Discovery, YouTube, entre outras.\n"
                    "- Data: Data de ocorrência do registro.\n"
                    "- Impressoes: Quantidade de vezes que o anúncio foi exibido (impressões).\n"
                    "- Investimento: Valor investido no anúncio nesse dia específico.\n"
                    "- Visualizacoes_ate_100: Número de visualizações que chegaram até o fim do vídeo (100%).\n"
                    "- Video_Play: Quantidade de vezes que o vídeo foi iniciado.\n"
                    "- Formato: Tipo de formato do criativo, como: Card, Carrossel, Coleção, Discovery, Estático, Reels, Stories, Vídeo.\n"
                    "- Criativo: Nome ou identificador do criativo utilizado no anúncio.\n"
                    "- Objetivo: Objetivo da campanha, como: Alcance, Visualização, Tráfego, Engajamento, Consideração ou Conversão.\n"
                    "- Editoria: Subdivisão editorial dentro da campanha.\n"
                    "- Link_do_Anuncio: URL do anúncio correspondente."
                )
)

#analyst_agent = Agent(    model = OpenAIChat(id='gpt_4.1-mini'),    instructions=())

playground_app = Playground(agents=[sql_agent])
app = playground_app.get_app()
if __name__ == "__main__":
    serve_playground_app("Monitor_Campanhas:app", reload=True) 