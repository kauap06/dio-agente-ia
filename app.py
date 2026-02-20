import json
import pandas as pd
import streamlit as st
from groq import Groq
import os

# ======== CONFIGURAÇÃO ========

GROQ_API_KEY = "SUA_API_KEY" #gsk_IJ8bSI6tIAAu875j7Q0OWGdyb3FYrS1xprqEgtHjuyzLMPFGJ***
MODELO = "llama-3.3-70b-versatile"

client = Groq(api_key=GROQ_API_KEY)

# ======== CARREGAR DADOS ========
try:
    perfil = json.load(open('data/perfil_investidor.json'))
    produtos = json.load(open('data/produtos_financeiros.json'))
    transacoes = pd.read_csv('data/transacoes.csv', sep=';', encoding='latin1')
    historico = pd.read_csv('data/historico_atendimento.csv', sep=';', encoding='latin1')

    contexto = f"""
CLIENTE: {perfil['perfil']['nome']}, {perfil['perfil']['idade']} anos, perfil {perfil['perfil']['perfil_investidor']}
OBJETIVO: {perfil['situacao_atual']['objetivo_principal']}
PATRIMÔNIO: R$ {perfil['situacao_atual']['patrimonio_total']} | RESERVA: R$ {perfil['situacao_atual']['reserva_emergencia_atual']}

TRANSAÇÕES RECENTES:
{transacoes.to_string(index=False)}

ATENDIMENTOS ANTERIORES:
{historico.to_string(index=False)}

PRODUTOS DISPONÍVEIS:
{json.dumps(produtos, indent=2, ensure_ascii=False)}
"""
except (FileNotFoundError, KeyError):
    contexto = "Nenhum dado de cliente carregado."

# ======== SYSTEM PROMPT ========

SYSTEM_PROMPT = """ Atlas, Assistente Financeiro

1. Quem é você:
Você é o Atlas, um consultor financeiro virtual. Sua função é ajudar o usuário a ler, organizar e interpretar seus dados financeiros pessoais de forma clara e acessível.

2. Qual o seu objetivo:
Seu objetivo é auxiliar na compreensão e otimização da vida financeira do usuário. Você deve entregar análises estruturadas e precisas a partir das informações fornecidas, perfeitas para controle pessoal, mas sempre mantendo um tom de conversa agradável, prestativo e humano.

3. Regras e Diretrizes de Comportamento:

Comunicação Natural e Equilibrada: Comunique-se de forma fluida e conversacional, como um bom consultor orientando seu cliente. Seja objetivo e conciso para não tomar o tempo do usuário, mas evite respostas robóticas, secas ou telegráficas. Explique os números de forma clara e contextualizada.

Base Factual e Zero Alucinação: Baseie suas respostas, cálculos e análises estritamente nos dados fornecidos pelo usuário no contexto da conversa. Nunca invente, presuma, estime ou preveja valores, taxas de juros, inflação ou tendências de mercado.

Tom e Personalidade: Mantenha uma postura profissional, educada, empática e direta. Evite jargões complexos desnecessários, gírias ou excesso de empolgação. O foco é transmitir confiança e clareza.

Protocolo de Desconhecimento e Faltas: Caso não saiba a resposta, falte algum dado para um cálculo ou a solicitação exija prever o futuro do mercado, seja honesto e educado. Diga naturalmente que não possui essa informação ou capacidade e oriente o usuário de forma prática e amigável sobre quais dados ele precisa fornecer para que você possa ajudá-lo corretamente. """

# ======== CHAMAR GROQ ========

def perguntar(msg):
    historico_groq = [
        {
            "role": "system",
            "content": f"{SYSTEM_PROMPT}\n\nCONTEXTO DO CLIENTE:\n{contexto}"
        }
    ]

    for m in st.session_state.mensagens:
        historico_groq.append({"role": m["role"], "content": m["content"]})

    resposta = client.chat.completions.create(
        model=MODELO,
        messages=historico_groq
    )
    return resposta.choices[0].message.content

# ======== INTERFACE ========

st.title("Atlas, Seu Educador Financeiro")

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

for msg in st.session_state.mensagens:
    st.chat_message(msg["role"]).write(msg["content"])

entrada = st.chat_input(
    "Sua dúvida sobre finanças...",
    accept_file=True,
    file_type=["csv", "txt", "json", "pdf"]
)

if entrada:
    pergunta = entrada.text or ""
    arquivo = entrada.files[0] if entrada.files else None

    conteudo_arquivo = None
    nome_arquivo = None

    if arquivo:
        nome_arquivo = arquivo.name
        try:
            conteudo_arquivo = arquivo.read().decode("utf-8", errors="ignore")

            # Salva o arquivo na pasta data
            os.makedirs("data", exist_ok=True)
            with open(f"data/{nome_arquivo}", "w", encoding="utf-8") as f:
                f.write(conteudo_arquivo)
        except Exception as e:
            conteudo_arquivo = f"[Erro ao ler arquivo: {e}]"

    # Monta exibição
    exibicao = pergunta if pergunta else f"Arquivo enviado: {nome_arquivo}"
    if pergunta and nome_arquivo:
        exibicao = f"{pergunta}\n\n📎 {nome_arquivo}"

    conteudo_completo = pergunta or "Analise o arquivo enviado."
    if conteudo_arquivo:
        conteudo_completo += f"\n\nARQUIVO ENVIADO PELO USUÁRIO ({nome_arquivo}):\n{conteudo_arquivo}"

    # Salva mensagem do usuário com o conteúdo do arquivo incluso
    st.session_state.mensagens.append({"role": "user", "content": conteudo_completo})
    st.chat_message("user").write(exibicao)

    with st.spinner("Pensando..."):
        resposta = perguntar(conteudo_completo)
        st.session_state.mensagens.append({"role": "assistant", "content": resposta})
        st.chat_message("assistant").write(resposta)