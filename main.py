import os
import sys

print("--- TESTE DE INICIALIZACAO ---")

try:
    import pandas as pd
    from jobspy import scrape_jobs
    print("✅ Bibliotecas importadas!")
except Exception as e:
    print(f"❌ Erro nas bibliotecas: {e}")

user = os.getenv("EMAIL_USER")
print(f"✅ Usuario carregado: {user}")

print("🔍 Iniciando busca teste...")
try:
    jobs = scrape_jobs(
        site_name=["indeed"],
        search_term="TI",
        location="Florianopolis",
        results_wanted=1
    )
    print(f"✅ Vagas encontradas: {len(jobs)}")
except Exception as e:
    print(f"❌ Erro no Scraper: {e}")

print("--- FIM DO TESTE ---")
