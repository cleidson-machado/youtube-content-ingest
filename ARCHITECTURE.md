# 🏗️ Documentação de Arquitetura - YouTube Content Ingest Pipeline

**Data:** 25 de Janeiro de 2026  
**Versão:** 2.0 (Refatorada)  
**Base:** Refatoração de `main_orig_bkp.py`

---

## 📋 Visão Geral

Este projeto implementa um pipeline automatizado para descobrir vídeos no YouTube, extrair metadados completos, verificar duplicatas contra um banco de dados remoto, e postar vídeos novos em uma API REST de gerenciamento de conteúdo.

**Princípio de Design:** Arquitetura modular com separação clara de responsabilidades, seguindo princípios SOLID.

---

## 🎯 Módulos e Responsabilidades

### 1. `config.py` - Gerenciamento de Configuração

**Responsabilidade:** Centralizar todas as configurações do sistema e carregá-las de variáveis de ambiente.

**Classe Principal:**
```python
@dataclass
class Config:
    youtube_api_key: str
    content_api_url: str
    content_api_token: str
    search_query: str
    target_new_videos: int
    max_pages_to_search: int
    max_results_per_page: int
    enable_deduplication: bool
    enable_enrichment: bool
    log_level: str
```

**Métodos Principais:**
- `from_env()`: Carrega configuração de variáveis de ambiente
- `validate()`: Valida se todas as configurações obrigatórias estão presentes

**Uso:**
```python
config = Config.from_env()
config.validate()
```

**Variáveis de Ambiente:**
- Carregadas do arquivo `.env` usando `python-dotenv`
- Valores padrão definidos para configurações opcionais
- Parsing automático de tipos (int, bool)

---

### 2. `models.py` - Modelos de Dados

**Responsabilidade:** Definir estruturas de dados tipadas para Query e Video.

**Classes:**

#### `SearchQuery`
```python
@dataclass
class SearchQuery:
    query: str
    max_results: int = 10
    order: str = "relevance"
    published_after: Optional[datetime] = None
    published_before: Optional[datetime] = None
    region_code: Optional[str] = None
    relevance_language: Optional[str] = None
```

#### `Video`
```python
@dataclass
class Video:
    # Identificação
    video_id: str
    title: str
    description: str
    channel_id: str
    channel_title: str
    published_at: datetime
    
    # Estatísticas
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    
    # Metadados
    tags: List[str]
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    duration_seconds: int = 0
    duration_iso: Optional[str] = None
    thumbnail_url: Optional[str] = None
    
    # Qualidade
    definition: Optional[str] = None  # 'hd' or 'sd'
    caption: bool = False
    default_language: Optional[str] = None
    default_audio_language: Optional[str] = None
```

**Método Especial:**
- `to_dict()`: Converte Video para o formato JSON esperado pela API de destino
  - Transforma `video_id` em URL completa
  - Converte lista de tags para string separada por vírgulas
  - Remove campos `None` ou `N/A` conforme necessário

---

### 3. `youtube_search.py` - Integração com YouTube API

**Responsabilidade:** Buscar vídeos no YouTube e extrair todos os metadados necessários.

**Classe Principal:**
```python
class YouTubeSearcher:
    def __init__(self, config: Config)
    def search(self, query: SearchQuery) -> List[Video]
    def search_page(self, query: str, page_token: Optional[str]) -> Tuple[List[Video], Optional[str]]
    
    # Métodos privados
    def _load_categories(self, region_code: str = 'BR') -> None
    def _get_category_name(self, category_id: Optional[str]) -> Optional[str]
    def _get_video_details(self, video_ids: List[str]) -> List[Video]
    def _parse_video_item(self, item: dict) -> Video
```

**Fluxo de Busca:**
1. `search_page()` executa busca no YouTube API
2. Extrai IDs dos vídeos encontrados
3. `_get_video_details()` busca metadados completos via `videos().list()`
4. `_parse_video_item()` converte resposta da API em objeto `Video`
   - Parse de duração ISO 8601 → segundos (usando `isodate`)
   - Tradução de category_id → category_name (cache interno)
   - Truncamento de título (limite 1000 caracteres)
   - Conversão de caption string → boolean

**Cache de Categorias:**
- Carregado uma vez no `__init__`
- Armazenado em `self._category_cache`
- Evita chamadas repetidas à API
- Usa região 'BR' por padrão

---

### 4. `deduplicator.py` - Detecção de Duplicatas

**Responsabilidade:** Filtrar vídeos que já existem no banco de dados.

**Classe Principal:**
```python
class Deduplicator:
    def __init__(self, config: Config, existing_urls: Set[str])
    def deduplicate(self, videos: List[Video]) -> List[Video]
    def add_existing_urls(self, urls: Set[str]) -> None
```

**Lógica:**
- Mantém set de URLs existentes (`self.existing_urls`)
- Para cada vídeo, constrói URL: `https://www.youtube.com/watch?v={video_id}`
- Compara URL contra set de URLs existentes
- Retorna apenas vídeos únicos (não duplicados)

**Importante:** Usa URLs completas (não apenas IDs) para compatibilidade com a API original.

---

### 5. `api_client.py` - Cliente da API de Conteúdo

**Responsabilidade:** Comunicação com a API REST de gerenciamento de conteúdo.

**Classe Principal:**
```python
class APIClient:
    def __init__(self, config: Config)
    def get_existing_urls(self) -> Set[str]
    def post_videos(self, videos: List[Video]) -> Dict[str, Any]
    
    # Métodos privados
    def _post_single_video(self, video: Video) -> Dict[str, Any]
    def _log_video_details(self, video: Video) -> None
```

**Recursos:**
- Sessão HTTP persistente com autenticação configurada
- Bearer token authentication no header
- Timeout de 10 segundos (mesmo do original)
- Verifica status 201 para sucesso (compatível com original)

**Formato de Resposta da API GET:**
```python
# Aceita ambos os formatos:
# Formato 1: Array direto
[{"url": "...", ...}, ...]

# Formato 2: Objeto com items
{"items": [{"url": "...", ...}, ...]}
```

**Logging Detalhado:**
- Exibe todos os metadados antes de enviar
- Formato idêntico ao script original (emojis, indentação)
- Feedback visual de sucesso/falha por vídeo

---

### 6. `metadata_enricher.py` - Enriquecimento de Metadados

**Responsabilidade:** Adicionar metadados calculados ou externos aos vídeos.

**Classe Principal:**
```python
class MetadataEnricher:
    def __init__(self, config: Config)
    def enrich(self, videos: List[Video]) -> List[Video]
```

**Status Atual:**
- Implementação básica (placeholder)
- Pode ser desabilitado via `ENABLE_ENRICHMENT=false`
- Calcula: word_count, has_tags, engagement_ratio

**Extensões Futuras:**
- Análise de sentimento
- Extração de keywords
- Transcrição de vídeo
- Classificação de tópicos

---

### 7. `pipeline.py` - Orquestração do Pipeline

**Responsabilidade:** Coordenar todos os componentes e gerenciar o fluxo de execução.

**Classe Principal:**
```python
class Pipeline:
    def __init__(self, config: Config)
    def run(self, queries: List[SearchQuery]) -> dict
    def run_incremental_search(self, search_query: str, target_count: int, max_pages: int) -> dict
```

**Método Principal: `run_incremental_search()`**

Este método implementa a lógica incremental do script original:

```python
Fluxo:
1. Carregar URLs existentes da API
2. Inicializar deduplicador com URLs existentes
3. Loop:
   a. Buscar página de resultados no YouTube
   b. Para cada vídeo:
      - Verificar se URL não existe no banco
      - Verificar se URL não está no batch atual
      - Se novo: adicionar à lista
   c. Se atingiu target OU max_pages: parar
   d. Se não há mais páginas: parar
4. Enriquecer metadados (se habilitado)
5. Postar vídeos novos na API
6. Retornar resultados
```

**Retorno:**
```python
{
    "queries_processed": 1,
    "pages_searched": 5,
    "videos_found": 10,
    "videos_unique": 10,
    "videos_posted": 10,
    "videos_failed": 0,
    "errors": []
}
```

---

## 🔄 Fluxo de Dados Completo

```
[.env] → Config.from_env() → Config object
                                    ↓
                        Pipeline.__init__(config)
                                    ↓
                    ┌───────────────┴───────────────┐
                    ↓                               ↓
            YouTubeSearcher                    APIClient
                    ↓                               ↓
        1. get_existing_urls() ←────────────────────┘
                    ↓
        2. search_page(query, token=None)
                    ↓
            [Video, Video, ...]
                    ↓
        3. Deduplicator.deduplicate(videos)
                    ↓
            [Unique Videos]
                    ↓
        4. MetadataEnricher.enrich(videos) (opcional)
                    ↓
            [Enriched Videos]
                    ↓
        5. APIClient.post_videos(videos)
                    ↓
            Results Dictionary
```

---

## 🔌 Dependências Externas

### APIs Utilizadas

#### YouTube Data API v3
- **Endpoints:**
  - `search().list()` - Busca de vídeos
  - `videos().list()` - Detalhes completos dos vídeos
  - `videoCategories().list()` - Lista de categorias por região

- **Quota:**
  - Search: ~100 unidades por chamada
  - Videos: ~1 unidade por chamada
  - VideoCategories: ~1 unidade (cache)
  - **Estimativa por execução:** ~1,100 unidades (10 buscas + 100 vídeos)

#### Content API (Sua API REST)
- **GET {base_url}**: Listar conteúdo existente
- **POST {base_url}**: Criar novo conteúdo
- **Auth:** Bearer token no header `Authorization`

### Bibliotecas Python

```
google-api-python-client  → YouTube API client
requests                   → HTTP client para Content API
python-dotenv             → Carregar .env
isodate                   → Parse de duração ISO 8601
```

---

## 🛡️ Segurança e Boas Práticas

### Credenciais
- ✅ **Nunca** hardcoded no código
- ✅ Armazenadas em `.env` (gitignored)
- ✅ Carregadas via variáveis de ambiente
- ✅ Validação antes da execução

### Logging
- ✅ Níveis apropriados (INFO, WARNING, ERROR)
- ✅ Não loga credenciais
- ✅ Formato consistente
- ❌ **Atenção:** Não sanitiza dados sensíveis em exceções (melhoria futura)

### Error Handling
- ✅ Try/catch em todas as operações de I/O
- ✅ Logging de erros com contexto
- ✅ Degradação graceful (continua mesmo com erros parciais)
- ✅ Exit codes apropriados (0 = sucesso, 1 = erro)

---

## 🎯 Casos de Uso

### Uso 1: Busca Padrão (via .env)
```bash
# Configure .env
echo "SEARCH_QUERY=python tutorial" >> .env
echo "TARGET_NEW_VIDEOS=5" >> .env

# Execute
python main.py
```

### Uso 2: Busca Customizada (Programático)
```python
from youtube_ingest.pipeline import Pipeline
from youtube_ingest.config import Config

config = Config.from_env()
pipeline = Pipeline(config)

results = pipeline.run_incremental_search(
    search_query="machine learning",
    target_count=20,
    max_pages=15
)
```

### Uso 3: Apenas Buscar (sem postar)
```python
from youtube_ingest.youtube_search import YouTubeSearcher
from youtube_ingest.config import Config

config = Config.from_env()
searcher = YouTubeSearcher(config)

videos, next_token = searcher.search_page("AI tutorial")
for video in videos:
    print(f"{video.title} - {video.view_count:,} views")
```

---

## 📊 Estrutura de Dados

### Video Model → API JSON

```python
# Objeto Video (Python)
Video(
    video_id="abc123",
    title="Como tirar visto para Portugal",
    description="Tutorial completo...",
    channel_title="Canal Exemplo",
    thumbnail_url="https://...",
    category_id="27",
    category_name="Education",
    tags=["visto", "portugal", "imigração"],
    duration_seconds=600,
    duration_iso="PT10M",
    view_count=1000,
    like_count=50,
    comment_count=10,
    definition="hd",
    caption=True,
    default_language="pt",
    default_audio_language="pt"
)

# ↓ to_dict() ↓

# JSON enviado para API
{
    "title": "Como tirar visto para Portugal",
    "description": "Tutorial completo...",
    "url": "https://www.youtube.com/watch?v=abc123",
    "channelName": "Canal Exemplo",
    "type": "VIDEO",
    "thumbnailUrl": "https://...",
    "categoryId": "27",
    "categoryName": "Education",
    "tags": "visto, portugal, imigração",
    "durationSeconds": 600,
    "durationIso": "PT10M",
    "definition": "hd",
    "caption": true,
    "viewCount": 1000,
    "likeCount": 50,
    "commentCount": 10,
    "defaultLanguage": "pt",
    "defaultAudioLanguage": "pt"
}
```

**Transformações Aplicadas:**
- `video_id` → `url` (URL completa do YouTube)
- `channel_title` → `channelName` (camelCase)
- `tags: List[str]` → `tags: str` (vírgula-separado)
- `caption: str` → `caption: bool` (conversão de tipo)
- Campos com valor `None` são enviados como `null`

---

## 🔍 Componentes Internos Detalhados

### YouTubeSearcher - Cache de Categorias

```python
# Carregado uma vez no __init__
_category_cache = {
    "1": "Film & Animation",
    "2": "Autos & Vehicles",
    "10": "Music",
    "15": "Pets & Animals",
    "17": "Sports",
    "19": "Travel & Events",
    "20": "Gaming",
    "22": "People & Blogs",
    "23": "Comedy",
    "24": "Entertainment",
    "25": "News & Politics",
    "26": "Howto & Style",
    "27": "Education",
    "28": "Science & Technology",
    # ... mais categorias
}
```

**Benefícios:**
- Reduz chamadas à API (economia de quota)
- Traduz IDs em nomes legíveis
- Região configurável (default: BR)

---

### Deduplicator - Estratégia de Detecção

**Input:** Lista de vídeos + Set de URLs existentes  
**Output:** Lista filtrada (apenas vídeos novos)

**Algoritmo:**
```python
for video in videos:
    video_url = f"https://www.youtube.com/watch?v={video.video_id}"
    
    if video_url not in existing_urls:
        unique_videos.append(video)
        existing_urls.add(video_url)  # Evita duplicatas no batch
```

**Complexidade:** O(n) onde n = número de vídeos  
**Espaço:** O(m) onde m = URLs existentes no banco

---

### APIClient - Estratégia de Postagem

**Abordagem:** POST individual (não batch)

**Motivo:** 
- Compatibilidade com API original
- Logging detalhado por vídeo
- Controle fino sobre sucesso/falha

**Fluxo por Vídeo:**
```
1. _log_video_details(video)  → Exibe metadados completos
2. _post_single_video(video)  → POST na API
3. Check status == 201        → Sucesso
4. Log resultado              → ✓ ou ✗
```

**Tratamento de Erros:**
- Network timeout: 10 segundos
- HTTP errors: Capturados e logados
- Continua mesmo com falhas parciais
- Retorna contagem de sucessos e falhas

---

## 📈 Performance e Otimização

### Considerações Atuais

**Pontos Fortes:**
- ✅ Cache de categorias (1 chamada vs N chamadas)
- ✅ Batch de vídeos na chamada de detalhes (até 50 IDs por chamada)
- ✅ Early termination (para quando atinge target)

**Oportunidades de Melhoria:**
- ⚠️ POST individual (não batch) - latência multiplicada
- ⚠️ Sem retry logic - falhas não são reprocessadas
- ⚠️ Sem rate limiting - pode exceder quota da API
- ⚠️ Sem cache de resultados - re-busca do zero a cada execução

### Estimativa de Tempo

Para TARGET_NEW_VIDEOS=10:
- Fetch existing URLs: ~500ms
- Load categories: ~200ms
- Search page (x2-3): ~1-2s
- Get video details: ~500ms
- Post videos (x10): ~5-10s
- **Total:** ~7-13 segundos (variável por network)

---

## 🧪 Testes e Validação

### Checklist de Validação

Antes de usar em produção:

- [ ] Verificar credenciais no `.env`
- [ ] Testar busca com query pequena (TARGET_NEW_VIDEOS=1)
- [ ] Confirmar formato de resposta da sua API
- [ ] Verificar quota disponível no YouTube API
- [ ] Testar deduplicação com vídeos já existentes
- [ ] Verificar logs para erros de autenticação

### Testes Manuais

```bash
# 1. Testar configuração
python -c "from youtube_ingest.config import Config; c = Config.from_env(); c.validate(); print('✓ Config OK')"

# 2. Testar busca (sem postar)
# Desabilite deduplicação e set LOG_LEVEL=DEBUG para ver detalhes

# 3. Testar com 1 vídeo apenas
# Set TARGET_NEW_VIDEOS=1 no .env
python main.py
```

---

## 🔧 Troubleshooting

### Erro: "Unable to import 'isodate'"
**Solução:** `pip install isodate`

### Erro: "YOUTUBE_API_KEY is required"
**Solução:** Configure `YOUTUBE_API_KEY` no `.env`

### Erro: "401 Unauthorized" ou "403 Forbidden"
**Solução:** Verifique `CONTENT_API_TOKEN` no `.env`

### Nenhum vídeo novo encontrado
**Causas possíveis:**
- Todos os vídeos já existem no banco
- Query muito específica
- Filtros de data muito restritivos

**Solução:** 
- Aumente `MAX_PAGES_TO_SEARCH`
- Tente query diferente
- Verifique logs em modo DEBUG

### Quota exceeded no YouTube API
**Solução:** 
- Aguarde reset (meia-noite Pacific Time)
- Solicite aumento de quota no Google Cloud Console
- Reduza `MAX_RESULTS_PER_PAGE` e `MAX_PAGES_TO_SEARCH`

---

## 🚀 Roadmap de Melhorias

### Versão 2.1 (Próxima)
- [ ] Retry logic com exponential backoff
- [ ] Batch POST na API (se suportado)
- [ ] Logging para arquivo
- [ ] Métricas de execução

### Versão 2.2
- [ ] CLI com argumentos (`argparse`)
- [ ] Suporte a múltiplas queries em paralelo
- [ ] Cache de resultados (Redis/SQLite)
- [ ] Rate limiting inteligente

### Versão 3.0
- [ ] Scheduler integrado (cron-like)
- [ ] Web dashboard para monitoramento
- [ ] Webhook notifications
- [ ] Database integration (bypass API)

---

## 📚 Referências

- [YouTube Data API v3 Documentation](https://developers.google.com/youtube/v3/docs)
- [Google API Python Client](https://github.com/googleapis/google-api-python-client)
- [isodate Library](https://pypi.org/project/isodate/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)

---

**Documentação mantida por:** GitHub Copilot  
**Última atualização:** 25 de Janeiro de 2026
