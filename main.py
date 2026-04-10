import os
import time
import smtplib
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jobspy import scrape_jobs

# CONFIGURAÇÕES
ARQUIVO_HISTORICO = "vagas_enviadas.txt"
ARQUIVO_CURRICULO = "curriculo.txt"

def enviar_email(vagas):
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    
    if not user or not password:
        print("❌ Erro: EMAIL_USER ou EMAIL_PASS não configurados nos Secrets.")
        return

    msg = MIMEMultipart()
    msg['Subject'] = f"🚀 Teste de Conexão: {len(vagas)} Vagas"
    msg['From'] = user
    msg['To'] = user
    
    corpo = "<ul>"
    for v in vagas:
        corpo += f"<li>{v['titulo']} - {v['empresa']}</li>"
    corpo += "</ul>"
    
    msg.attach(MIMEText(corpo, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(user, password)
            server.send_message(msg)
        print("✅ E-mail enviado com sucesso!")
    except Exception as e:
        print(f"❌ Erro no envio de e-mail: {e}")

print("--- INICIANDO DIAGNÓSTICO ---")

# Passo 1: Testar leitura do currículo
try:
    with open(ARQUIVO_CURRICULO, "r", encoding="utf-8") as f:
        conteudo = f.read()
    print(f"✅ Arquivo de currículo lido ({len(conteudo)} caracteres).")
except Exception as e:
    print(f"❌ Erro ao ler currículo: {e}")

# Passo 2: Testar o Scraper (Apenas 1 site para evitar bloqueio)
print("🔍 Tentando buscar vagas no Indeed...")
try:
    jobs = scrape_jobs(
        site_name=["indeed"],
        search_term="Suporte TI",
        location="Florianopolis, SC",
        results_wanted=3,
        country_hint="brazil"
    )
    print(f"✅ Scraper finalizado. Vagas encontradas: {len(jobs)}")
except Exception as e:
    print(f"❌ Erro no Scraper: {e}")
    jobs = pd.DataFrame()

# Passo 3: Tentar enviar e-mail se houver algo
if not jobs.empty:
    lista_teste = []
    for _, row in jobs.iterrows():
        lista_teste.append({'titulo': row['title'], 'empresa': row['company']})
    
    enviar_email(lista_teste)
    
    # Passo 4: Testar escrita no histórico
    try:
        with open(ARQUIVO_HISTORICO, "a") as f:
            f.write("teste_conexao\n")
        print("✅ Escrita no histórico funcionando.")
    except Exception as e:
        print(f"❌ Erro ao escrever no histórico: {e}")
else:
    print("⚠️ Nenhuma vaga encontrada para enviar e-mail.")

print("--- FIM DO DIAGNÓSTICO ---")