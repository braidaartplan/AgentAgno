# agent_agno_streamlit.py
"""
Streamlit App – Estagiário Inteligente

Interface de chat para monitoramento de campanhas de marketing,
alimentada por um Agente Agno que consulta o banco MySQL.
Agora inclui uma **barra lateral** para filtros de data e cliente.
"""

from __future__ import annotations

import os
from datetime import date
from textwrap import dedent

import streamlit as st
from dotenv import load_dotenv

from agno.agent import Agent
from agno.tools.sql import SQLTools
from agno.models.openai import OpenAIChat
from agno.memory.v2.memory import Memory
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.storage.sqlite import SqliteStorage

########################
# 🔧 Configurações
########################

# Carrega variáveis de ambiente (.env deve conter DB_USUARIO, DB_SENHA, DB_HOST, DB_NOME)
load_dotenv()

DB_URL = (
    f"mysql+pymysql://{os.getenv('DB_USUARIO')}:{os.getenv('DB_SENHA')}@"
    f"{os.getenv('DB_HOST')}/{os.getenv('DB_NOME')}"
)
DB_FILE = os.getenv("AGNO_DB_FILE", "tmp/agent.db")

# Lista de Clientes
CLIENTES = [
    "ELETROBRÁS",
    "BNDES",
    "CNI",
    "SEBRAE",
    "SEBRAE RJ"
]

########################
# 🤖 Inicialização do Agente
########################

def init_agent() -> Agent:
    """Cria e retorna o agente Agno configurado."""

    storage = SqliteStorage(table_name="Sessoes_Agentes", db_file=DB_FILE)

    memory = Memory(
        model=OpenAIChat(id="gpt-4.1-mini"),
        db=SqliteMemoryDb(table_name="Memoria_usuario", db_file=DB_FILE),
    )

    description = dedent(
        """
        Você é um analista de dados de marketing digital com experiência em campanhas pagas. 
        Sua tarefa é realizar o acompanhamento semanal das campanhas de marketing dos clientes, 
        com foco na performance dos criativos.
        Analise os dados da semana e destaque os criativos com melhor e pior desempenho.
        Para cada destaque positivo e negativo, apresente as seguintes métricas:
          • Impressões, CPM (Custo por mil impressões)
          • Visualizações até 100 %, CPV (Custo por visualização)
        A análise deve considerar o contexto do objetivo da campanha.
        Evite listas longas: selecione apenas os criativos com performance mais relevante.
        Estruture a resposta por cliente e campanha.
        Inclua:
          1. 🧠 Resumo analítico
          2. 📊 Interpretação dos KPIs
          3. ✅ Recomendações acionáveis
        """
    )

    instructions = (
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
                    "- Link_do_Anuncio: URL do anúncio correspondente.\n"
                    "- Engajamento_Total: Soma de comentários, reações e compartilhamentos.\n"
                    "- Cliques_no_Link: Número de cliques no link do anúncio.\n"
                    "- PageViews: Número de visualizações da página de destino dos anúncios.\n"
                    "- Tempo_Medio_de_Video: Tempo médio que os usuários assistiram ao vídeo do anúncio.\n"
                )

    return Agent(
        tools=[SQLTools(db_url=DB_URL)],
        model=OpenAIChat(id="gpt-4.1-mini"),
        num_history_runs=5,
        add_history_to_messages=True,
        storage=storage,
        memory=memory,
        description=description,
        instructions=instructions,
    )


# Interface Streamlit


def render_sidebar():
    """Renderiza a barra lateral com filtros e ações utilitárias."""
    with st.sidebar:
        st.title("⚙️ Filtros & Configuração")

        # Filtros de data
        today = date.today()
        start = st.date_input("Data inicial", value=today.replace(day=1), max_value=today)
        end = st.date_input("Data final", value=today, min_value=start, max_value=today)

        # Filtro de cliente
        cliente_sel = st.selectbox("Cliente", options=CLIENTES, index=0)
        cliente_val = cliente_sel

        # Botão para limpar histórico
        if st.button("🗑️ Limpar conversa"):
            st.session_state.history.clear()
            st.toast("Histórico limpo ✅", icon="🗑️")
            st.rerun()

    # Salva filtros em session_state
    st.session_state.sidebar_filters = {
        "start_date": start,
        "end_date": end,
        "cliente": cliente_val.strip(),
    }


def render_history():
    """Exibe o histórico salvo em session_state.history."""
    for item in st.session_state.history:
        chat = st.chat_message("human" if item["role"] == "user" else "ai")
        chat.markdown(item["content"], unsafe_allow_html=True)


def pagina_chat():
    st.set_page_config(page_title="🎯 Monitoramento de Campanhas", layout="wide")
    st.header("🤖 Olá, sou seu analista de campanhas", divider=True)

    # Estado inicial
    if "agent" not in st.session_state:
        st.session_state.agent = init_agent()
    if "history" not in st.session_state:
        st.session_state.history = []
    if "sidebar_filters" not in st.session_state:
        # Inicialização padrão (evita AttributeError em execuções iniciais)
        today = date.today()
        st.session_state.sidebar_filters = {
            "start_date": today.replace(day=1),
            "end_date": today,
            "cliente": "None",
        }

    # Barra lateral (pode sobrescrever os valores iniciais)
    render_sidebar()

    # Mostra histórico
    render_history()

    # Entrada do usuário
    prompt = st.chat_input("Pergunte algo sobre a performance das campanhas…")

    if prompt:
        filters = st.session_state.sidebar_filters
        filtro_texto = ""
        if filters.get("cliente"):
            filtro_texto += f" Cliente: {filters['cliente']}."
        if filters.get("start_date") and filters.get("end_date"):
            filtro_texto += (
                f" Intervalo de dados: {filters['start_date'].strftime('%d/%m/%Y')} "
                f"até {filters['end_date'].strftime('%d/%m/%Y')}."
            )

        # Mescla filtros ao prompt sem alterá‑lo caso não haja filtros
        final_prompt = f"{filtro_texto}\n{prompt}" if filtro_texto else prompt

        # Salva pergunta
        st.session_state.history.append({"role": "user", "content": prompt})

        with st.spinner("Analisando…"):
            try:
                raw_resp = st.session_state.agent.run(final_prompt)
                answer = getattr(raw_resp, "content", str(raw_resp))
            except Exception as e:
                answer = f"❌ Erro ao processar: {e}"

        # Salva resposta
        st.session_state.history.append({"role": "assistant", "content": answer})
        st.rerun()


if __name__ == "__main__":
    pagina_chat()
