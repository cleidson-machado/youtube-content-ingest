# GitHub Copilot - Instruções do Projeto YouTube Content Ingest

## 🎯 Contexto do Projeto

Este é um pipeline automatizado de ingestão de conteúdo do YouTube que:
- Busca vídeos no YouTube via API oficial
- Enriquece metadados (categoria, duração, estatísticas)
- Deduplica contra uma API REST personalizada
- Envia novos vídeos para o banco de dados via API

**Arquitetura:** Modular com 7 componentes separados  
**Stack:** Python 3.13, YouTube Data API v3, REST API customizada  
**Ambiente:** macOS com venv, pyenv

---

## 📐 Arquitetura e Estrutura

### Módulos Principais
```
youtube_ingest/
├── config.py           # Configurações e variáveis de ambiente
├── models.py           # Modelos de dados (Video, SearchQuery)
├── youtube_search.py   # Busca no YouTube com paginação
├── api_client.py       # Cliente REST com paginação de 50 itens
├── deduplicator.py     # Deduplicação baseada em URLs
├── metadata_enricher.py # Enriquecimento (desabilitado por padrão)
└── pipeline.py         # Orquestrador principal
```

### Padrões de Código
- **Type hints obrigatórios** em todas as funções
- **Docstrings** em classes e métodos públicos
- **Logging detalhado** com emojis para UX
- **Environment variables** via `python-dotenv` (nunca hardcode)
- **Paginação dinâmica** de 50 itens/página na API REST

---

### 📂 Organização de Arquivos e Diretórios

- **Arquivos de Produção e Estrutura:** O agente tem permissão total para criar e editar arquivos essenciais na raiz do projeto, como `Dockerfile`, `Jenkinsfile`, `requirements.txt`, `.gitignore`, e arquivos de configuração.
- **Código Fonte:** A pasta `youtube_ingest/` é o core do projeto. O agente deve manipular, criar ou refatorar módulos dentro desta pasta conforme as solicitações de desenvolvimento.
- **Arquivos Temporários e de Rascunho (REGRA CRÍTICA):** 
  - **Local Obrigatório:** `x_temp_files/`
  - Qualquer arquivo de teste (`test_*.py`), rascunhos de documentação (`*.md`), arquivos de texto para manipulação de dados ou logs de debug gerados pelo agente **DEVEM** ser criados exclusivamente dentro de `x_temp_files/`.
  - **Proibição:** Nunca criar arquivos de "suporte ao raciocínio" ou "testes rápidos" na raiz do projeto. Se não for um arquivo de configuração oficial ou código de produção, ele pertence à `x_temp_files/`.

  ## 🤖 Comportamento do Agente na Criação de Arquivos

1. **Identificação de Escopo:** Antes de criar um arquivo, o agente deve classificar:
   - *É essencial para o funcionamento do pipeline ou deploy?* (Ex: `requirements.txt`, `Dockerfile`) -> **Raiz**.
   - *É um módulo do sistema?* -> **youtube_ingest/**.
   - *É um teste, rascunho, dump de dados ou arquivo auxiliar?* -> **x_temp_files/**.
2. **Limpeza Automática:** Ao sugerir novos scripts de teste, o agente deve nomeá-los como `x_temp_files/test_nome_do_recurso.py` por padrão.

---

## 🔧 Boas Práticas Técnicas

### Python
- Usar **f-strings** em logs (configurado no Pylint para aceitar)
- Máximo de **120 caracteres/linha**
- Nomes de variáveis descritivos (exceto `i`, `e`, `df` permitidos)
- Preferir **sets** para deduplicação (performance)
- **Try/except** robusto com mensagens de erro claras

### API REST
- **Timeout de 10s** em todas as requests
- **Paginação obrigatória** com `page_size=50`
- **Bearer token** via header `Authorization`
- **Validar status codes** (201=sucesso, 500=duplicata)
- Endpoint paginado: `/contents/paged?page=X&size=50`
- Formato de resposta: `{content: [], totalPages, currentPage, totalItems}`

### YouTube API
- **Quota-aware**: cada busca consome 100 unidades
- **Campos otimizados**: snippet, contentDetails, statistics, localizations
- **Categoria BR**: carregar do arquivo JSON `categories_BR.json`
- **Duração ISO 8601**: converter com `isodate.parse_duration()`

### Deduplicação
- Sempre buscar **TODAS** as URLs existentes antes de enviar
- Comparar por **URL completa** (não apenas video_id)
- Usar **Set** para lookup O(1)
- Logs claros: "✓ New video found" ou "⊘ Already exists"

---

## 🚨 Restrições e Limitações

### API REST Personalizada
- **NÃO aceita URLs duplicadas** → retorna erro 500
- **Paginação customizada** (não usa Spring Data padrão)
- **Campos obrigatórios**: url, title, channel_title, published_at, category_id
- **Token de autenticação** obrigatório em TODAS as requests

### YouTube API
- **Quota limitada**: 10.000 unidades/dia
- **Rate limit**: não exceder 100 requests/segundo
- **Região BR**: sempre usar `regionCode=BR`
- **Idioma PT**: priorizar vídeos em português

### Ambiente
- **macOS**: usar `venv/` (não conda)
- **Python 3.13+**: via pyenv
- **Pylint configurado**: aceita f-strings, linhas 120 chars
- **.env obrigatório**: nunca commitar credenciais

---

## 💡 Sugestões de Código

### ✅ Fazer Assim
```python
# Logging com f-strings e emojis
logger.info(f"✓ Page {page + 1}/{total}: {len(items)} items")

# Type hints completos
def get_videos(self, query: str) -> List[Video]:
    """Busca vídeos no YouTube."""
    ...

# Paginação automática
while current_page + 1 < total_pages:
    page += 1
    # buscar próxima página

# Deduplicação eficiente
existing_urls = set(api_client.get_existing_urls())
if video.url not in existing_urls:
    # enviar vídeo
```

### ❌ Evitar
```python
# Sem type hints
def get_videos(query):
    ...

# Hardcoded credentials
api_token = "my-secret-token-123"

# Paginação manual/fixa
for page in range(10):  # ❌ não sabe quantas páginas existem

# Logs sem contexto
print("Video posted")  # ❌ sem emoji, sem detalhes

# Exceções genéricas
except Exception:  # ❌ capturar exceção específica
    pass
```

---

## 🧪 Testes e Validação

### Antes de Enviar Código
1. **Validar sintaxe**: Pylint deve estar limpo
2. **Testar paginação**: verificar se busca TODAS as páginas
3. **Testar deduplicação**: não enviar URLs existentes
4. **Logs legíveis**: usuário deve entender o que acontece
5. **Tratamento de erro**: nunca deixar exceção sem catch

### Scripts de Teste Disponíveis
- `test_config.py` - Valida variáveis de ambiente
- `test_pagination.py` - Testa paginação básica
- `test_pagination_debug.py` - Debug detalhado da API
- `demo_pagination.py` - Demonstração visual

---

## 📝 Convenções de Commit

### Formato
```
<tipo>: <descrição curta>

<descrição detalhada se necessário>
```

### Tipos
- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `refactor:` Refatoração (sem mudança de comportamento)
- `docs:` Documentação
- `test:` Testes
- `chore:` Manutenção (dependências, config)
- `perf:` Melhoria de performance

### Exemplos
```
feat: add pagination to API client

- Implement dynamic pagination with 50 items/page
- Auto-detect total pages from API response
- Add detailed logging for each page

fix: handle missing 'last' field in API response

The API returns custom pagination format with
totalPages/currentPage instead of Spring Data format.
```

---

## 🔐 Segurança

### Credenciais
- **NUNCA** commitar `.env`
- **SEMPRE** usar `python-dotenv`
- **Token de API** via `CONTENT_API_TOKEN`
- **YouTube API key** via `YOUTUBE_API_KEY`
- `.gitignore` deve incluir: `.env`, `venv/`, `*.log`, `Temp_*.txt`

### Validação
```python
# Sempre validar configuração no início
config = Config(...)
config.validate()  # ← Lança exceção se faltarem variáveis
```

---

## 📊 Logs e Monitoramento

### Padrão de Logs
```python
# Início de operação
logger.info("🔍 Fetching existing URLs...")

# Progresso
logger.info(f"  ✓ Page 1/3: 50 URLs fetched")

# Sucesso
logger.info("✅ Total: 150 URLs in database")

# Aviso (não fatal)
logger.warning("⚠️  No videos found on this page")

# Erro (fatal)
logger.error("✗ Failed to connect to API")
```

### Emojis Padrão
- 🔍 Busca/pesquisa
- ✓ Sucesso parcial
- ✅ Sucesso completo
- ⚠️ Aviso
- ✗ Erro
- 📊 Estatísticas
- 📹 Vídeo
- 🚀 Início
- ⊘ Item ignorado/duplicado

---

## 🎓 Conhecimento do Domínio

### YouTube API v3
- **Video ID**: 11 caracteres alfanuméricos (ex: `dQw4w9WgXcQ`)
- **URL formato**: `https://www.youtube.com/watch?v={video_id}`
- **Categorias**: 44 categorias globais, carregar lista BR
- **Duração ISO**: `PT5M30S` = 5 minutos e 30 segundos
- **Definition**: `hd` (720p+) ou `sd` (480p-)

### REST API Personalizada
- **Base URL**: `https://api.aguide-ptbr.com.br/contents`
- **Endpoints**:
  - `GET /paged?page=X&size=Y` - Buscar com paginação
  - `POST /` - Criar novo conteúdo
- **Status esperados**:
  - `201 Created` - Sucesso
  - `500 Internal Server Error` - URL duplicada (não é erro real)
  - `401/403` - Problema de autenticação

---

## 🚀 Fluxo de Execução

### Pipeline Principal
1. **Carregar configuração** (`.env` → Config)
2. **Validar credenciais** (API tokens)
3. **Buscar URLs existentes** (paginação completa)
4. **Buscar no YouTube** (query configurável)
5. **Deduplica**r (comparar com URLs existentes)
6. **Enriquecer** (opcional, desabilitado)
7. **Enviar à API** (POST um por um)
8. **Logs finais** (estatísticas)

### Ordem de Importância
1. **Deduplicação funcional** (evitar erros 500)
2. **Paginação completa** (buscar TODAS as URLs)
3. **Logs claros** (UX do usuário)
4. **Type safety** (type hints)
5. **Performance** (usar sets, cache)

---

## 🤝 Interação com Copilot

### Quando Sugerir Código
- **Sempre incluir type hints**
- **Sempre adicionar docstrings**
- **Sempre tratar exceções**
- **Sempre adicionar logs com emojis**
- **Seguir estrutura modular existente**

### Ao Fazer Refatoração
- **Manter compatibilidade** com código existente
- **Não quebrar a API pública** dos módulos
- **Adicionar testes** se possível
- **Atualizar documentação** (README, ARCHITECTURE)

### Linguagem
- **Comentários em português** quando já existem
- **Docstrings em inglês** (padrão Python)
- **Mensagens de log em inglês** (profissional)
- **Documentação em português** (README, guias)

---

## ⚡ Performance

### Otimizações Aplicadas
- **Sets para deduplicação**: O(1) lookup vs O(n) em listas
- **Paginação de 50 itens**: balanceamento entre velocidade e memória
- **Requests com timeout**: evitar travamento
- **Cache de categorias**: carregar 1x do arquivo JSON

### Não Otimizar Prematuramente
- Pipeline processa ~10-50 vídeos por execução
- Performance não é gargalo atual
- Clareza > velocidade neste projeto

---

## 📚 Referências

### Documentação Oficial
- [YouTube Data API v3](https://developers.google.com/youtube/v3/docs)
- [Python Requests](https://requests.readthedocs.io/)
- [Python Dotenv](https://pypi.org/project/python-dotenv/)
- [isodate](https://pypi.org/project/isodate/)

### Arquivos de Documentação do Projeto
- [README.md](../README.md) - Visão geral
- [QUICKSTART.md](../QUICKSTART.md) - Como começar
- [ARCHITECTURE.md](../ARCHITECTURE.md) - Arquitetura detalhada
- [PAGINATION.md](../PAGINATION.md) - Sistema de paginação
- [MIGRATION_GUIDE.md](../MIGRATION_GUIDE.md) - Migração do código antigo

---

**Última atualização:** 31/01/2026  
**Versão do projeto:** 0.1.0  
**Python requerido:** 3.13+
