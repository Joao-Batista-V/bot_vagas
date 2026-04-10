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
    msg['Subject'] = f"🚀 {len(vagas)} Novas Vagas para João Batista"
    msg['From'] = user
    msg['To'] = user
    html = "<h2>Vagas Selecionadas por IA</h2>"
    for v in vagas:
        html += f"<div style='border-bottom:1px solid #ccc;padding:10px;'><h3>{v['titulo']}</h3><p><b>Nota: {v['nota']}</b> | {v['empresa']}</p><p>{v['motivo']}</p><a href='{v['link']}'>Ver Vaga</a></div>"
    msg.attach(MIMEText(html, 'html'))
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(user, password)
        server.send_message(msg)

# 2. EXECUÇÃO
print("--- INICIANDO BUSCA OTIMIZADA ---")
historico = carregar_historico()
vagas_para_enviar = []

try:
    with open(ARQUIVO_CURRICULO, "r", encoding="utf-8") as f:
        perfil = f.read()
    print("✅ Currículo carregado.")
except:
    perfil = "Técnico de Suporte TI, graduado em Física, cursando ADS."

# BUSCA FOCO EM FLORIPA E REGIÃO
try:
    jobs = scrape_jobs(
        site_name=["indeed", "linkedin"],
        search_term="Suporte TI, Help Desk, Tecnico Informatica, Analista Suporte",
        location="Florianopolis",
        distance=50, # Pega São José, Palhoça, etc.
        results_wanted=50,
        country_hint="brazil",
        hours_old=168 # Últimos 7 dias
    )
    print(f"✅ Vagas encontradas no total: {len(jobs)}")
except Exception as e:
    print(f"❌ Erro no Scraper: {e}")
    jobs = pd.DataFrame()

if not jobs.empty:
    for _, row in jobs.iterrows():
        link = row['job_url']
        if link in historico: continue
        
        # Filtro inicial por palavras-chave no título para poupar API
        titulo = row['title'].lower()
        if not any(x in titulo for x in ['suporte', 'tecnico', 'help', 'analista', 'ti', 'informatica', 'python']):
            continue

        prompt = f"Avalie a vaga para este candidato: {perfil}. Vaga: {row['title']} - {row['description'][:800]}. Responda APENAS um JSON: {{"nota": 0 a 10, "motivo": "frase"}}"
        try:
            response = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            res_text = response.text.strip().replace("```json", "").replace("```", "")
            res_json = json.loads(res_text)
            
            # Nota 6 ou mais para garantir que chegue algo no início
            if res_json.get("nota", 0) >= 6:
                vagas_para_enviar.append({
                    'titulo': row['title'], 'empresa': row['company'],
                    'nota': res_json['nota'], 'motivo': res_json['motivo'], 'link': link
                })
                salvar_no_historico(link)
                print(f"🎯 Aprovada: {row['title']} (Nota {res_json['nota']})")
            time.sleep(2)
        except: continue

enviar_email(vagas_para_enviar)
print("--- FIM DO PROCESSO ---")
