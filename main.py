import os
import json
import time
import smtplib
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai
from jobspy import scrape_jobs

# 1. CONFIGURAÇÕES
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
ARQUIVO_HISTORICO = "vagas_enviadas.txt"
ARQUIVO_CURRICULO = "curriculo.txt"

def carregar_historico():
    if not os.path.exists(ARQUIVO_HISTORICO): return set()
    with open(ARQUIVO_HISTORICO, "r") as f:
        return set(line.strip() for line in f)

def salvar_no_historico(link):
    with open(ARQUIVO_HISTORICO, "a") as f:
        f.write(link + "\n")

def enviar_email(vagas):
    if not vagas: 
        print("ℹ️ Nenhuma vaga nova qualificada hoje.")
        return
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    msg = MIMEMultipart()
    msg['Subject'] = f"🚀 {len(vagas)} Vagas Encontradas - João Batista"
    msg['From'] = user
    msg['To'] = user
    html = "<h2>Radar de Vagas Otimizado</h2>"
    for v in vagas:
        html += f"<div style='border-bottom:1px solid #ccc;padding:15px;'><h3>{v['titulo']}</h3><p>{v['empresa']} | Nota: {v['nota']}</p><p>{v['motivo']}</p><a href='{v['link']}'>Ver Vaga</a></div>"
    msg.attach(MIMEText(html, 'html'))
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(user, password)
        server.send_message(msg)

# 2. EXECUÇÃO
print("--- INICIANDO BUSCA PENTE FINO ---")
historico = carregar_historico()
vagas_para_enviar = []

try:
    with open(ARQUIVO_CURRICULO, "r", encoding="utf-8") as f:
        perfil = f.read()
except:
    perfil = "Técnico de TI, cursando ADS, focado em Python, Suporte e QA."

# Termos simplificados e diretos (um por vez para garantir retorno)
buscas = [
    {"termo": "Suporte TI", "local": "Florianopolis"},
    {"termo": "Analista Suporte", "local": "Florianopolis"},
    {"termo": "Python Junior", "local": "Brasil"}, # Brasil para pegar remoto
    {"termo": "QA Junior", "local": "Brasil"},
    {"termo": "Analista Dados", "local": "Brasil"}
]

for item in buscas:
    print(f"🔍 Buscando: {item['termo']} em {item['local']}...")
    try:
        jobs = scrape_jobs(
            site_name=["indeed", "linkedin"],
            search_term=item['termo'],
            location=item['local'],
            results_wanted=20, # Aumentado para ter mais gordura
            country_hint="brazil",
            hours_old=72
        )
        
        if jobs.empty:
            print("  - Vazio.")
            continue

        print(f"  - Analisando {len(jobs)} vagas...")
        for _, row in jobs.iterrows():
            link = row['job_url']
            if link in historico: continue
            
            prompt = f"Candidato: {perfil}. Vaga: {row['title']} - {row['description'][:600]}. Retorne JSON: {{\"nota\": 0-10, \"motivo\": \"...\"}}"
            try:
                response = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
                res_json = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
                
                if res_json.get("nota", 0) >= 6:
                    vagas_para_enviar.append({
                        'titulo': row['title'], 'empresa': row['company'],
                        'nota': res_json['nota'], 'motivo': res_json['motivo'], 'link': link
                    })
                    salvar_no_historico(link)
                    print(f"    ✅ Selecionada: {row['title']}")
                time.sleep(1)
            except: continue
    except Exception as e:
        print(f"  ⚠️ Erro: {e}")

enviar_email(vagas_para_enviar)
print(f"--- FIM: {len(vagas_para_enviar)} vagas ---")
