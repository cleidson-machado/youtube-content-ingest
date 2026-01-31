# 🤖 Configuração do GitHub Copilot

Este projeto está configurado para usar **instruções customizadas** do GitHub Copilot automaticamente.

## ✅ O que foi configurado

### 1. Arquivo de Instruções
📁 [`.github/copilot-instructions.md`](.github/copilot-instructions.md)

Este arquivo contém:
- 🎯 Contexto do projeto
- 📐 Arquitetura e padrões de código
- 🔧 Boas práticas técnicas (Python, APIs, YouTube)
- 🚨 Restrições e limitações
- 💡 Exemplos de código (✅ fazer / ❌ evitar)
- 📊 Padrões de logs e emojis
- 🔐 Segurança e credenciais
- 🚀 Fluxo de execução do pipeline

### 2. Configuração do VS Code
📁 [`.vscode/settings.json`](.vscode/settings.json)

```json
"github.copilot.chat.codeGeneration.instructions": [
    {
        "file": ".github/copilot-instructions.md"
    }
]
```

## 🚀 Como Usar

### Automático (já funciona!)
O Copilot **automaticamente** usa as instruções quando você:
- ✨ Pede sugestões de código (autocomplete)
- 💬 Conversa no Copilot Chat (`Cmd + Shift + I`)
- 🤖 Usa o Copilot Edits
- 🔍 Faz perguntas sobre o código

**Não precisa fazer nada!** O contexto é carregado automaticamente.

### Testando

1. **Abra o Copilot Chat:**
   - `Cmd + Shift + I` (macOS)
   - Ou clique no ícone do Copilot na sidebar

2. **Faça perguntas como:**
   ```
   "Como devo fazer logging neste projeto?"
   "Qual o tamanho de página correto para a API?"
   "Como tratar erros de duplicação?"
   ```

3. **Peça código:**
   ```
   "Crie uma função para buscar vídeos do YouTube"
   "Adicione validação de configuração"
   ```

O Copilot responderá seguindo os padrões do arquivo de instruções!

## 📋 Benefícios

### ✅ Antes (sem instruções)
```python
# Copilot gera código genérico
def get_data(url):
    response = requests.get(url)
    return response.json()
```

### ✅ Agora (com instruções)
```python
# Copilot gera código seguindo os padrões do projeto
def get_existing_urls(self) -> Set[str]:
    """Fetch existing video URLs from the content API using pagination.
    
    Returns:
        Set of existing video URLs.
    """
    all_urls = set()
    page = 0
    page_size = 50  # Padrão da API REST
    
    try:
        logger.info("🔍 Fetching existing URLs...")
        # ... código com type hints, logs, emojis, paginação
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Failed: {e}")
        return all_urls
```

## 🔧 Personalização

### Editar Instruções
Simplesmente edite o arquivo:
```bash
.github/copilot-instructions.md
```

O Copilot detecta mudanças automaticamente (pode demorar alguns segundos).

### Adicionar Seções
Você pode adicionar mais seções como:
- 🧪 Padrões de teste
- 📦 Estrutura de pacotes
- 🌐 Configurações de API
- 📝 Documentação de código

### Desabilitar (se necessário)
Remova estas linhas de `.vscode/settings.json`:
```json
"github.copilot.chat.codeGeneration.instructions": [
    {
        "file": ".github/copilot-instructions.md"
    }
]
```

## 🆚 CLI do Copilot (não necessária)

### Com Instruções Customizadas (este projeto)
- ✅ Funciona automaticamente no VS Code
- ✅ Sem instalação adicional
- ✅ Contexto sempre atualizado
- ✅ Compartilhado com toda a equipe (via Git)

### CLI do Copilot
- ❌ Requer instalação separada (`npm install -g @githubnext/github-copilot-cli`)
- ❌ Funciona apenas no terminal
- ❌ Não usa arquivo de instruções do projeto
- ✅ Útil para: comandos shell, git, etc.

**Conclusão:** Para desenvolvimento Python no VS Code, **não precisa da CLI**! Este setup é suficiente e superior.

## 📊 Verificando se Está Funcionando

### 1. Verifique os Arquivos
```bash
# Deve existir
ls -la .github/copilot-instructions.md

# Deve conter a configuração
grep "copilot.chat.codeGeneration" .vscode/settings.json
```

### 2. Teste no Copilot Chat
1. Abra Copilot Chat (`Cmd + Shift + I`)
2. Pergunte: **"Quais são os emojis que devo usar nos logs?"**
3. Deve responder com: 🔍, ✓, ✅, ⚠️, ✗, etc. (da instrução)

### 3. Teste Sugestão de Código
1. Crie um novo arquivo Python
2. Comece a digitar: `def get_videos`
3. O Copilot deve sugerir código com type hints e logging

## 🎯 Próximos Passos

### Para Melhorar Ainda Mais

1. **Adicione exemplos específicos** ao arquivo de instruções:
   ```markdown
   ## Exemplos de Uso
   
   ### Buscar Vídeos
   \`\`\`python
   # Exemplo real do projeto
   \`\`\`
   ```

2. **Documente APIs específicas**:
   ```markdown
   ## API Endpoints
   
   ### POST /contents
   Body: {...}
   Response: {...}
   ```

3. **Adicione troubleshooting**:
   ```markdown
   ## Problemas Comuns
   
   ### Erro 500 ao enviar vídeo
   Causa: URL duplicada...
   ```

## 📚 Referências

- [GitHub Copilot Customization](https://docs.github.com/en/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot)
- [VS Code Copilot Settings](https://code.visualstudio.com/docs/copilot/copilot-settings)

---

**Status:** ✅ Configurado e funcionando  
**Última atualização:** 31/01/2026

## ⚠️ Importante

- Este arquivo **não deve** conter credenciais ou tokens
- As instruções são **compartilhadas** via Git (todos veem)
- Mudanças nas instruções afetam **todos** que usam o projeto
- O arquivo pode ter no máximo **~4000 tokens** (cerca de 3000 palavras)
