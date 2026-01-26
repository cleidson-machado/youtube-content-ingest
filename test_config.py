#!/usr/bin/env python
"""Script de teste para validar a configuração do projeto."""

from dotenv import load_dotenv
from youtube_ingest.config import Config

# Carregar variáveis de ambiente
load_dotenv()

# Criar e validar configuração
try:
    config = Config.from_env()
    config.validate()
    
    print("✅ Configuração validada com sucesso!\n")
    print("📋 Configurações Carregadas:")
    print(f"  - YouTube API Key: {'*' * 20}{config.youtube_api_key[-10:]}")
    print(f"  - Content API URL: {config.content_api_url}")
    print(f"  - Content API Token: {'*' * 20}{config.content_api_token[-10:]}")
    print(f"  - Search Query: {config.search_query}")
    print(f"  - Target Videos: {config.target_new_videos}")
    print(f"  - Max Pages: {config.max_pages_to_search}")
    print(f"  - Results Per Page: {config.max_results_per_page}")
    print(f"  - Deduplication: {config.enable_deduplication}")
    print(f"  - Enrichment: {config.enable_enrichment}")
    print(f"  - Log Level: {config.log_level}")
    print("\n✅ Tudo pronto para executar: python main.py")
    
except ValueError as e:
    print(f"❌ Erro de configuração: {e}")
    print("\n💡 Solução:")
    print("  1. Verifique se o arquivo .env existe na raiz do projeto")
    print("  2. Edite .env e configure as variáveis necessárias")
    print("  3. Execute: nano .env")
    exit(1)
    
except Exception as e:
    print(f"❌ Erro inesperado: {e}")
    exit(1)
