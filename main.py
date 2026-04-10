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
        print("ℹ️ Nenhuma vaga nova qualificada hoje para os novos termos.")
        return
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    msg = MIMEMultipart()
    msg['Subject'] = f"🚀 {len(vagas)} Oportunidades Selecionadas - João Batista"
    msg['From'] = user
    msg['To'] = user
    html = "<h2>Radar de Vagas IA (TI, QA, Dados e Suporte)</h2>"
    for v in vagas:
        html += f"""
        <div style='border-bottom:1px solid #ccc;padding:15px;'>
            <h3 style='color:#2c3e50;'>{v['titulo']}</h3>
            <p><b>Empresa:</b> {v['empresa']} | <b>Nota:</b> {v['nota']}/10</p>
            <p style='color:#555;'>{v['motivo']}</p>
            <a href='{v['link']}' style='color:#3498db;'>Candidatar-se agora</a>
        </div>
        """
    msg.attach(MIMEText(html, 'html'))
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(user, password)
        server.send_message(msg)

# 2. EXECUÇÃO
print("--- INICIANDO BUSCA MULTIDISCIPLINAR (FLORIPA + REMOTO) ---")
historico = carregar_historico()
vagas_para_enviar = []

try:
    with open(ARQUIVO_CURRICULO, "r", encoding="utf-8") as f:
        perfil = f.read()
except:
    perfil = "Técnico de TI, cursando ADS, com foco em Python, Dados e QA."

# Lista de cargos para pesquisa (buscas otimizadas)
termos_pesquisa = [
    "Implementation Engineer", "Analista de Integracoes", "QA Quality Assurance",
    "Analista de Dados", "BI Business Intelligence", "Python Junior", 
    "Suporte Tecnico", "Suporte de Aplicacoes"
]

# Configurações de Localização para teste amplo
locais = ["Florianopolis", "Remoto"]

for local in locais:
    print(f"📍 Pesquisando em: {local}")
    for termo in termos_pesquisa:
        print(f"  🔍 Cargo: {termo}...")
        try:
            # APENAS LinkedIn e Indeed (os outros bloqueiam o bot)
            jobs = scrape_jobs(
                site_name=["linkedin", "indeed"],
                search_term=termo,
                location=local,
                results_wanted=10,
                country_hint="brazil",
                hours_old=168 # 7 dias
            )
            
            if jobs.empty: continue

            for _, row in jobs.iterrows():
                link = row['job_url']
                if link in historico: continue
                
                # IA analisa a vaga
                prompt = f"Avalie a vaga para este candidato: {perfil}. Vaga: {row['title']} - {row['description'][:800]}. Responda APENAS um JSON: {{"nota": 0 a 10, "motivo": "frase"}}"
                try:
                    response = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
                    res_json = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
                    
                    if res_json.get("nota", 0) >= 6:
                        vagas_para_enviar.append({
                            'titulo': row['title'], 'empresa': row['company'],
                            'nota': res_json['nota'], 'motivo': res_json['motivo'], 'link': link
                        })
                        salvar_no_historico(link)
                        print(f"    ✅ Vaga aprovada: {row['title']}")
                    time.sleep(1) # Respeitar API Gemini
                except: continue
        except Exception as e:
            print(f"    ⚠️ Erro no scraper para {termo}: {e}")
            continue

enviar_email(vagas_para_enviar)
print(f"--- PROCESSO FINALIZADO: {len(vagas_para_enviar)} vagas novas enviadas ---")