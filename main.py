import os
import sys

# Garante que qualquer erro apareça no log do GitHub
print("--- INICIANDO SCRIPT ---")

try:
    import smtplib
    import pandas as pd
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from jobspy import scrape_jobs
    print("✅ Bibliotecas carregadas.")
except Exception as e:
    print(f"❌ Erro nas bibliotecas: {e}")
    sys.exit(1)

# TESTE DE AMBIENTE
user = os.getenv("EMAIL_USER")
print(f"✅ Usuário configurado: {user}")

# BUSCA DE VAGAS
print("🔍 Buscando vagas...")
try:
    jobs = scrape_jobs(
        site_name=["indeed"],
        search_term="TI",
        location="Florianopolis, SC",
        results_wanted=2,
        country_hint="brazil"
    )
    print(f"✅ Vagas encontradas: {len(jobs)}")
except Exception as e:
    print(f"❌ Erro no scraper: {e}")
    jobs = pd.DataFrame()

# TESTE DE ENVIO
if not jobs.empty:
    print("📧 Tentando enviar e-mail de teste...")
    msg = MIMEMultipart()
    msg['Subject'] = "Teste do Bot - João Batista"
    msg['From'] = user
    msg['To'] = user
    msg.attach(MIMEText("O bot rodou com sucesso no GitHub!", 'plain'))
    
    try:
        password = os.getenv("EMAIL_PASS")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(user, password)
            server.send_message(msg)
        print("✅ E-mail enviado!")
    except Exception as e:
        print(f"❌ Falha no e-mail: {e}")
else:
    print("⚠️ Nenhuma vaga encontrada para testar o e-mail.")

print("--- FIM DO SCRIPT ---")