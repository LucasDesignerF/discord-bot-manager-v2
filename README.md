# 🤖 Discord Bot Manager V2

<div align="center">

![Versão](https://img.shields.io/badge/versão-2025.1.0-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-teal)
![Discord API](https://img.shields.io/badge/Discord%20API-v10-purple)
![Licença](https://img.shields.io/badge/licença-MIT-yellow)

**Gerencie seus bots do Discord com eficiência e estilo**  
*Totalmente assíncrono, moderno e em português*

[Documentação](#documentação-da-api) • [Instalação](#instalação) • [Contribuir](#contribuindo)

</div>

---

## ✨ Destaques

- ⚡ **100% Assíncrono** - Performance máxima com async/await
- 🚀 **FastAPI Moderno** - Documentação automática e validação de dados
- 🐘 **PostgreSQL Otimizado** - Pool de conexões para alta performance
- 📊 **Métricas Prometheus** - Monitoramento completo do seu sistema
- 🔒 **Segurança Robusta** - CORS, validação Pydantic e boas práticas
- 🇧🇷 **Totalmente em PT-BR** - Código, comentários e documentação traduzidos
- 🎨 **API Intuitiva** - Endpoints claros e consistentes

## 📋 Sobre o Projeto

O **Discord Bot Manager V2** é uma API moderna para criar, gerenciar e monitorar bots do Discord. Desenvolvido pensando em escalabilidade e facilidade de uso, ele permite:

- Criar múltiplos bots automaticamente
- Gerenciar tokens de forma segura
- Controlar quais bots estão em uso
- Monitorar métricas em tempo real
- Integrar com seus sistemas existentes

## 🚀 Começando

### Pré-requisitos

- Python 3.11 ou superior
- PostgreSQL 15+
- Conta de desenvolvedor Discord
- Token de autenticação Discord (obtido via DevTools)

### Instalação

1. **Clone o repositório**
```bash
git clone https://github.com/LucasDesignerF/discord-bot-manager-v2.git
cd discord-bot-manager-v2
```

2. **Crie um ambiente virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

3. **Instale as dependências**
```bash
pip install -r requirements.txt
```

4. **Configure as variáveis de ambiente**
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

5. **Inicie o servidor**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

A API estará disponível em `http://localhost:8000`

## 🔧 Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Banco de Dados PostgreSQL
DB_HOST=localhost
DB_DB=bots_db
DB_USER=seu_usuario
DB_PASS=sua_senha

# Autenticação Discord (obter via DevTools)
AUTH=mfa_seu_token_aqui

# Configurações CORS (separar por vírgula)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Ambiente
ENV=development
LOG_LEVEL=INFO
```

### Como obter o token de autenticação Discord

1. Abra o Discord no navegador
2. Pressione `F12` para abrir as DevTools
3. Vá até a aba `Network`
4. Faça qualquer ação no Discord
5. Clique em qualquer requisição e procure pelo header `Authorization`
6. Copie o valor (geralmente começa com `mfa.`)

## 📖 Documentação da API

Após iniciar o servidor, acesse:

| Interface | URL |
|-----------|-----|
| **Swagger UI** | `http://localhost:8000/docs` |
| **ReDoc** | `http://localhost:8000/redoc` |
| **Métricas** | `http://localhost:8000/metrics` |

### Endpoints Principais

#### 🤖 Gerenciamento de Bots

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/bot/criar` | Cria um novo bot no Discord |
| `POST` | `/bot/armazenar` | Armazena um bot existente no DB |
| `GET` | `/bot/obter` | Obtém um bot disponível |
| `GET` | `/bot/verificar` | Verifica um bot específico |
| `PUT` | `/bot/reivindicar` | Marca bot como em uso |
| `PUT` | `/bot/liberar` | Libera um bot para uso |
| `PUT` | `/bot/sincronizar` | Sincroniza tokens do bot |

#### 🎨 Personalização

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `PUT` | `/bot/nome` | Altera o nome do bot |
| `PUT` | `/bot/foto` | Altera a foto do bot |

#### 📊 Monitoramento

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/bot/nao_reivindicados` | Conta bots disponíveis |
| `GET` | `/` | Status da API |

### Exemplos de Uso

#### Criar um novo bot
```bash
curl -X POST "http://localhost:8000/bot/criar?armazenar=true"
```

**Resposta:**
```json
{
  "id": "123456789012345678",
  "mensagem": "Bot armazenado no banco de dados"
}
```

#### Obter um bot disponível
```bash
curl -X GET "http://localhost:8000/bot/obter?reivindicado=false"
```

**Resposta:**
```json
{
  "id": "123456789012345678",
  "token": "seu_token_aqui",
  "reivindicado": false
}
```

#### Alterar nome do bot
```bash
curl -X PUT "http://localhost:8000/bot/nome?bot_id=123456789012345678&nome=MeuBotOficial"
```

## 🗄️ Banco de Dados

### Estrutura da Tabela

```sql
CREATE TABLE bots (
    client_id VARCHAR(32) PRIMARY KEY,
    token TEXT NOT NULL,
    claimed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Índices Otimizados

- `idx_bots_claimed` - Busca rápida por bots disponíveis
- `idx_bots_created` - Ordenação por data de criação

## 📊 Monitoramento com Prometheus

A API exporta métricas prontas para uso com Prometheus:

| Métrica | Descrição |
|---------|-----------|
| `bots_total` | Número total de bots (labels: status) |
| `bots_unclaimed` | Quantidade de bots disponíveis |
| `http_requests_total` | Total de requisições HTTP |
| `http_request_duration_seconds` | Latência das requisições |

### Configuração do Prometheus

```yaml
scrape_configs:
  - job_name: 'discord-bot-manager'
    static_configs:
      - targets: ['localhost:8000']
```

## 🐳 Docker

### Usando Docker Compose

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DB_HOST=postgres
      - DB_DB=bots_db
      - DB_USER=admin
      - DB_PASS=senha123
      - AUTH=${AUTH}
    depends_on:
      - postgres

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=bots_db
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=senha123
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### Build da imagem

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🛠️ Tecnologias Utilizadas

- **[FastAPI](https://fastapi.tiangolo.com/)** - Framework web moderno e rápido
- **[asyncpg](https://github.com/MagicStack/asyncpg)** - Cliente PostgreSQL assíncrono de alta performance
- **[httpx](https://www.python-httpx.org/)** - Cliente HTTP assíncrono
- **[Pydantic](https://docs.pydantic.dev/)** - Validação de dados baseada em tipos
- **[Prometheus](https://prometheus.io/)** - Monitoramento e métricas
- **[Uvicorn](https://www.uvicorn.org/)** - Servidor ASGI de alta performance

## 🤝 Contribuindo

Contribuições são sempre bem-vindas! Siga os passos abaixo:

1. **Fork o projeto**
2. **Crie sua feature branch**
```bash
git checkout -b feature/AmazingFeature
```
3. **Commit suas mudanças**
```bash
git commit -m 'Add some AmazingFeature'
```
4. **Push para a branch**
```bash
git push origin feature/AmazingFeature
```
5. **Abra um Pull Request**

### Diretrizes

- Mantenha o código em português
- Siga as boas práticas de async/await
- Adicione type hints em todas as funções
- Documente novos endpoints no Swagger
- Escreva testes para novas funcionalidades

## 📄 Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

## 📧 Contato

LucasDesignerF - [@LucasDesignerF](https://github.com/LucasDesignerF)

Link do Projeto: [https://github.com/LucasDesignerF/discord-bot-manager-v2](https://github.com/LucasDesignerF/discord-bot-manager-v2)

## 🙏 Agradecimentos

- [Discord Developer Portal](https://discord.com/developers/docs/intro)
- [FastAPI Community](https://github.com/tiangolo/fastapi)
- Todos os contribuidores do projeto

---

<div align="center">
  
**Feito com 💙 por LucasDesignerF**

</div>
