import os
import json
import time
import requests
import smtplib
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

# CONFIGURAÇÕES
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
ADZUNA_ID = os.getenv("ADZUNA_ID")
ADZUNA_KEY = os.getenv("ADZUNA_KEY")
ARQUIVO_HISTORICO = "vagas_enviadas.txt"

def carregar_historico():
    if not os.path.exists(ARQUIVO_HISTORICO): return set()
    with open(ARQUIVO_HISTORICO, "r") as f:
        return set(line.strip() for line in f)

def salvar_no_historico(link):
    with open(ARQUIVO_HISTORICO, "a") as f:
        f.write(link + "\n")

def perguntar_ao_gemini(prompt):
    """Fala direto com a API do Google via HTTP, sem usar bibliotecas extras"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        res_data = response.json()
        texto = res_data['candidates'][0]['content']['parts'][0]['text']
        # Limpa o markdown do JSON se a IA enviar
        return texto.replace('```json', '').replace('```', '').strip()
    except Exception as e:
        print(f"      ⚠️ Erro na API do Gemini: {e}")
        return None

def enviar_email(vagas):
    if not vagas: 
        print("ℹ️ Nenhuma vaga nova qualificada hoje.")
        return
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    msg = MIMEMultipart()
    msg['Subject'] = f"🚀 {len(vagas)} Vagas para João Batista ({time.strftime('%d/%m')})"
    msg['From'] = user
    msg['To'] = user
    html = "<h2>Vagas Selecionadas por IA</h2>"
    for v in vagas:
        html += f"<div style='border-bottom:1px solid #ccc;padding:15px;'><h3>{v['titulo']}</h3><p><b>{v['empresa']}</b> | Nota: {v['nota']}</p><p>{v['motivo']}</p><a href='{v['link']}'>Ver Vaga</a></div>"
    msg.attach(MIMEText(html, 'html'))
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(user, password)
            server.send_message(msg)
        print("✅ E-MAIL ENVIADO COM SUCESSO!")
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")

# EXECUÇÃO
print(f"--- INICIANDO BUSCA DIRETA ({time.strftime('%H:%M:%S')}) ---")
historico = carregar_historico()
vagas_para_enviar = []

termos = ["Suporte TI", "QA", "Python", "Analista de Dados"]

for termo in termos:
    print(f"🔍 Buscando: {termo} em Floripa...")
    url_adzuna = f"https://api.adzuna.com/v1/api/jobs/br/search/1?app_id={ADZUNA_ID}&app_key={ADZUNA_KEY}&results_per_page=10&what={termo}&where=florianopolis"
    
    try:
        res_adzuna = requests.get(url_adzuna).json()
        results = res_adzuna.get('results', [])
        
        for job in results:
            link = job.get('redirect_url')
            if link in historico: continue
            
            titulo = job.get('title')
            empresa = job.get('company', {}).get('display_name', 'Confidencial')
            desc = job.get('description', 'Sem descrição.')

            prompt = f"Analise esta vaga para um Técnico TI/ADS. Vaga: {titulo} - {desc[:500]}. Retorne APENAS um JSON: {{\"nota\": 0-10, \"motivo\": \"...\"}}"
            
            resultado_ia = perguntar_ao_gemini(prompt)
            if resultado_ia:
                try:
                    res_json = json.loads(resultado_ia)
                    nota = res_json.get("nota", 0)
                    print(f"      🔎 {titulo[:30]}... | Nota: {nota}")

                    if nota >= 2: # Nota baixa para garantir o envio
                        vagas_para_enviar.append({
                            'titulo': titulo, 'empresa': empresa,
                            'nota': nota, 'motivo': res_json.get('motivo'), 'link': link
                        })
                        salvar_no_historico(link)
                        print(f"        ✅ SELECIONADA!")
                except: continue
            time.sleep(1)
    except Exception as e:
        print(f"  ⚠️ Erro na Adzuna: {e}")

enviar_email(vagas_para_enviar)
print("--- PROCESSO FINALIZADO ---")