import os
import json
import time
import smtplib
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai
from jobspy import scrape_jobs

# 1. CONFIGURAÇÕES INICIAIS
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
ARQUIVO_HISTORICO = "vagas_enviadas.txt"

def carregar_historico():
    if not os.path.exists(ARQUIVO_HISTORICO):
        return set()
    with open(ARQUIVO_HISTORICO, "r") as f:
        return set(line.strip() for line in f)

def salvar_no_historico(link):
    with open(ARQUIVO_HISTORICO, "a") as f:
        f.write(link + "\n")

def enviar_email(vagas):
    if not vagas: return
    
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    
    msg = MIMEMultipart()
    msg['Subject'] = f"🚀 {len(vagas)} Novas Vagas para João Batista"
    msg['From'] = user
    msg['To'] = user

    html = "<h2>Vagas selecionadas pelo seu Bot IA</h2>"
    for v in vagas:
        html += f"""
        <div style='border-bottom: 1px solid #ccc; padding: 10px;'>
            <h3>{v['titulo']}</h3>
            <p><b>Nota:</b> {v['nota']}/10 | <b>Empresa:</b> {v['empresa']}</p>
            <p><i>{v['motivo']}</i></p>
            <a href='{v['link']}'>Ver Vaga</a>
        </div>
        """
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(user, password)
        server.send_message(msg)

# 3. EXECUÇÃO PRINCIPAL
historico = carregar_historico()
vagas_para_enviar = []

# (Aqui entra sua lógica de busca scrape_jobs e o loop da IA que já criamos)
# Ao final do loop da IA, você adiciona esta condição:
# if nota >= 6 and row['job_url'] not in historico:
#     vagas_para_enviar.append({...})
#     salvar_no_historico(row['job_url'])

enviar_email(vagas_para_enviar)