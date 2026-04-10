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
ARQUIVO_CURRICULO = "curriculo.txt" # Ajustado para o nome com acento conforme seu VS Code

def carregar_historico():
    if not os.path.exists(ARQUIVO_HISTORICO):
        return set()
    with open(ARQUIVO_HISTORICO, "r") as f:
        return set(line.strip() for line in f)

def salvar_no_historico(link):
    with open(ARQUIVO_HISTORICO, "a") as f:
        f.write(link + "\n")

def enviar_email(vagas):
    if not vagas: 
        print("ℹ️ Nenhuma vaga nova qualificada para envio.")
        return
    
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

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(user, password)
            server.send_message(msg)
        print("✅ E-mail enviado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")

# 3. EXECUÇÃO PRINCIPAL
print("🚀 Iniciando busca de vagas...")
historico = carregar_historico()
vagas_para_enviar = []

# Carregar Currículo
try:
    with open(ARQUIVO_CURRICULO, "r", encoding="utf-8") as f:
        perfil_candidato = f.read()
except FileNotFoundError:
    print(f"❌ Erro: Arquivo {ARQUIVO_CURRICULO} não encontrado.")
    perfil_candidato = "Perfil técnico em TI e Física." # Fallback simples

# Realizar Busca
try:
    jobs = scrape_jobs(
        site_name=["indeed", "linkedin"],
        search_term="Suporte TI, Analista de Suporte, Help Desk, Python Junior",
        location="Florianopolis, SC",
        results_wanted=20,
        country_hint="brazil",
        hours_old=168 # Busca vagas da última semana
    )
except Exception as e:
    print(f"⚠️ Erro no Scraper: {e}")
    jobs = pd.DataFrame()

if not jobs.empty:
    print(f"📊 {len(jobs)} vagas encontradas. Analisando compatibilidade...")
    
    for _, row in jobs.iterrows():
        link = row['job_url']
        
        # Pula se já foi enviada antes
        if link in historico:
            continue
            
        # IA analisa a vaga
        prompt = f"""
        Aja como um recrutador. Avalie a vaga abaixo para este candidato:
        CANDIDATO: {perfil_candidato}
        VAGA: {row['title']} - {row['description']}
        
        Responda APENAS um JSON:
        {{"nota": 0 a 10, "motivo": "uma frase curta"}}
        """
        
        try:
            response = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            # Limpeza simples do texto da resposta
            res_text = response.text.strip().replace("```json", "").replace("```", "")
            res_json = json.loads(res_text)
            
            nota = res_json.get("nota", 0)
            
            # FILTRO: Nota mínima 6 para enviar por e-mail
            if nota >= 6:
                vagas_para_enviar.append({
                    'titulo': row['title'],
                    'empresa': row['company'],
                    'nota': nota,
                    'motivo': res_json.get("motivo", ""),
                    'link': link
                })
                salvar_no_historico(link)
                print(f"✅ Vaga aprovada (Nota {nota}): {row['title']}")
            
            time.sleep(2) # Evitar limite de cota da API
            
        except Exception as e:
            print(f"⚠️ Erro ao analisar vaga {row['title']}: {e}")
            continue

# Finalização
enviar_email(vagas_para_enviar)