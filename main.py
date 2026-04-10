import os
import sys

# Força o erro a aparecer no log do GitHub se o script travar
def exception_handler(exception_type, exception, traceback):
    print(f"❌ ERRO CRÍTICO: {exception}")

sys.excepthook = exception_handler

try:
    import smtplib
    import pandas as pd
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from jobspy import scrape_jobs
    print("✅ Bibliotecas importadas com sucesso.")
except Exception as e:
    print(f"❌ Erro ao importar bibliotecas: {e}")
    sys.exit(1)

# CONFIGURAÇÕES
ARQUIVO_CURRICULO = "curriculo.txt"

def enviar_email_teste(vagas):
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    
    if not user or not password:
        print("❌ Secrets de e-mail não encontrados.")
        return

    msg = MIMEMultipart()
    msg['Subject'] = "🚀 Teste Final do Bot"
    msg['From'] = user
    msg['To'] = user
    msg.attach(MIMEText(f"O bot encontrou {len(vagas)} vagas.", 'plain'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(user, password)
            server.send_message(msg)
        print("✅ E-mail enviado!")
    except Exception as e:
        print(f"❌ Falha no e-mail: {e}")

print("--- INICIANDO PROCESSO ---")

# 1. Tentar ler currículo
if os.path.exists(ARQUIVO_CURRICULO):
    print(f"✅ Arquivo {ARQUIVO_CURRICULO} encontrado.")
else:
    print(f"⚠️ Arquivo {ARQUIVO_CURRICULO} não encontrado na raiz.")

# 2. Buscar vagas (simplificado para teste)
print("🔍 Buscando vagas no Indeed...")
try:
    jobs = scrape_jobs(
        site_name=["indeed"],
        search_term="Suporte",
        location="Florianopolis, SC",
        results_wanted=2,
        country_hint="brazil"
    )
    print(f"✅ Busca concluída. Vagas: {len(jobs)}")
    
    if not jobs.empty:
        enviar_email_teste(jobs.to_dict('records'))
    else:
        print("ℹ️ Nenhuma vaga encontrada no momento.")

except Exception as e:
    print(f"❌ Erro no Scraper: {e}")

print("--- FIM DO PROCESSO ---")