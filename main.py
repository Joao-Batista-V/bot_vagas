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
        print("ℹ️ Nenhuma vaga nova qualificada para envio hoje.")
        return
    
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    msg = MIMEMultipart()
    msg['Subject'] = f"🚀 {len(vagas)} Novas Vagas (Busca Geral) - João Batista"
    msg['From'] = user
    msg['To'] = user
    
    html = f"<h2>Foram analisadas as melhores vagas de hoje:</h2>"
    for v in vagas:
        html += f"""
        <div style='border-bottom: 1px solid #ddd; padding: 15px; margin-bottom: 10px; font-family: sans-serif;'>
            <h3 style='color: #2c3e50; margin-bottom: 5px;'>{v['titulo']}</h3>
            <p style='margin: 0;'><b>Empresa:</b> {v['empresa']} | <b>Nota IA:</b> <span style='color: green;'>{v['nota']}/10</span></p>
            <p style='background: #f9f9f9; padding: 10px; border-left: 4px solid #3498db;'><i>{v['motivo']}</i></p>
            <a href='{v['link']}' style='display: inline-block; padding: 10px 15px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; margin-top: 10px;'>Ver Detalhes da Vaga</a>
        </div>
        """
    msg.attach(MIMEText(html, 'html'))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(user, password)
            server.send_message(msg)
        print(f"✅ E-mail com {len(vagas)} vagas enviado!")
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")

# 2. EXECUÇÃO
print("--- INICIANDO BUSCA EM MÚLTIPLOS SITES ---")
historico = carregar_historico()
vagas_para_enviar = []

try:
    with open(ARQUIVO_CURRICULO, "r", encoding="utf-8") as f:
        perfil = f.read()
    print("✅ Perfil profissional carregado.")
except:
    perfil = "Técnico de Suporte em TI e desenvolvedor iniciante."

# Lista de sites para varrer
sites_alvo = ["indeed", "linkedin", "glassdoor", "zip_recruiter"]
print(f"🔍 Vasculhando: {', '.join(sites_alvo)}...")

try:
    jobs = scrape_jobs(
        site_name=sites_alvo,
        search_term="Suporte TI, Help Desk, Analista de Suporte, Python Junior",
        location="Florianopolis, SC",
        results_wanted=30, # Aumentamos para pegar mais opções de todos os sites
        country_hint="brazil",
        hours_old=48 # Vagas bem recentes
    )
    print(f"📊 Total bruto de vagas encontradas: {len(jobs)}")
except Exception as e:
    print(f"⚠️ Aviso: Ocorreu um problema em um dos sites, mas continuaremos com o que foi coletado. Erro: {e}")
    jobs = pd.DataFrame()

if not jobs.empty:
    for _, row in jobs.iterrows():
        link = row['job_url']
        
        # 1. Ignorar se já enviamos antes
        if link in historico:
            continue
        
        # 2. IA analisa a compatibilidade
        prompt = f"""
        Avalie a compatibilidade (0 a 10) entre o perfil e a vaga abaixo.
        PERFIL: {perfil}
        VAGA: {row['title']} na empresa {row['company']} - {row['description'][:1000]}
        
        Responda APENAS um JSON:
        {{"nota": int, "motivo": "uma frase curta explicando a nota"}}
        """
        
        try:
            response = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            res_text = response.text.strip().replace("```json", "").replace("```", "")
            res_json = json.loads(res_text)
            
            # Filtro: Só envia se a nota for alta (ajustado para 7)
            if res_json.get("nota", 0) >= 7:
                vagas_para_enviar.append({
                    'titulo': row['title'],
                    'empresa': row['company'],
                    'nota': res_json['nota'],
                    'motivo': res_json['motivo'],
                    'link': link
                })
                salvar_no_historico(link)
                print(f"🌟 Vaga Qualificada: {row['title']}")
            
            time.sleep(1.5) # Pausa para respeitar limites da API
        except:
            continue

enviar_email(vagas_para_enviar)
print("--- FIM DO PROCESSO ---")
