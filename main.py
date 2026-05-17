"""
API para Gerenciamento de Bots do Discord
Versão 2025 - Totalmente assíncrona e modernizada
"""
from typing import Optional, Dict, Any
from os import getenv
from base64 import b64encode
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from httpx import AsyncClient, HTTPError
import asyncpg
from tenacity import retry, stop_after_attempt, wait_exponential

from prometheus_fastapi_instrumentator import Instrumentator, metrics
from prometheus_client import Gauge

from discord import (
    get_bot,
    get_bots,
    create_bot,
    create_bot_token,
    get_teams,
    change_bot_name,
    change_bot_photo,
)
from db import DatabaseManager
from schemas import BotCreateResponse, BotResponse, BotClaimResponse, MessageResponse

# Configuração de logging moderna
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Variáveis globais
db_manager: Optional[DatabaseManager] = None
http_client: Optional[AsyncClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    global db_manager, http_client
    
    # Inicialização
    logger.info("Iniciando o gerenciador de bots...")
    
    # Conecta ao PostgreSQL
    db_manager = DatabaseManager(
        host=getenv("DB_HOST"),
        database=getenv("DB_DB"),
        user=getenv("DB_USER"),
        password=getenv("DB_PASS")
    )
    await db_manager.connect()
    
    # Cliente HTTP com rate limiting automático
    http_client = AsyncClient(timeout=30.0)
    
    logger.info("Gerenciador de bots iniciado com sucesso!")
    
    yield
    
    # Limpeza
    logger.info("Desligando o gerenciador de bots...")
    await db_manager.disconnect()
    await http_client.aclose()


# Inicialização da aplicação
app = FastAPI(
    title="Gerenciador de Bots do Discord",
    description="API para criar e gerenciar bots do Discord de forma eficiente",
    version="2025.1.0",
    lifespan=lifespan
)

# Configuração CORS para segurança
app.add_middleware(
    CORSMiddleware,
    allow_origins=getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def bots_total() -> callable:
    """Exporta o número total de bots no banco de dados"""
    METRIC = Gauge("bots", "Bots no banco de dados", labelnames=("status",))
    
    async def instrumentation(info: metrics.Info) -> None:
        if db_manager:
            METRIC.labels("nao_reivindicados").set(await db_manager.unclaimed_bots())
            METRIC.labels("total").set(await db_manager.all_bots())
    
    return instrumentation


@app.on_event("startup")
async def setup_metrics():
    """Configura as métricas do Prometheus"""
    Instrumentator().add(bots_total()).instrument(app).expose(app)


@app.get("/", response_model=MessageResponse)
async def read_root():
    """Endpoint de verificação de saúde da API"""
    return {"message": "API de Gerenciamento de Bots do Discord", "status": "online"}


@app.post("/bot/criar", response_model=BotCreateResponse)
async def criar_bot(armazenar: bool = False):
    """
    Cria uma nova aplicação no Discord e gera um token de bot
    
    Args:
        armazenar: Se True, armazena o bot no banco de dados
    
    Returns:
        ID do bot e token (se não armazenado)
    """
    if not http_client:
        raise HTTPException(status_code=503, detail="Cliente HTTP não inicializado")
    
    # Obtém próximo time disponível
    novo_id = ""
    teams = await get_teams(http_client)
    
    if not teams:
        raise HTTPException(status_code=503, detail="Nenhum time disponível")
    
    for team in teams:
        logger.info(f"Tentando criar bot no time: {team}")
        novo_id = await create_bot(http_client, team)
        if novo_id:
            break
    
    if not novo_id:
        raise HTTPException(status_code=500, detail="Não foi possível criar o bot")
    
    logger.info(f"Novo bot criado: {novo_id}")
    
    try:
        novo_token = await create_bot_token(http_client, novo_id)
    except Exception as e:
        logger.error(f"Erro ao gerar token: {e}")
        raise HTTPException(status_code=500, detail="Erro ao gerar token do bot")
    
    if armazenar and db_manager:
        await db_manager.store_bot(novo_id, novo_token)
        return {"id": novo_id, "token": None, "mensagem": "Bot armazenado no banco de dados"}
    
    return {"id": novo_id, "token": novo_token, "mensagem": "Bot criado com sucesso"}


@app.post("/bot/armazenar", response_model=BotResponse)
async def armazenar_bot(bot_id: str, bot_token: str, reivindicado: bool = False):
    """
    Armazena um bot existente no banco de dados
    
    Args:
        bot_id: ID do bot
        bot_token: Token do bot
        reivindicado: Se o bot já está em uso
    """
    if not db_manager:
        raise HTTPException(status_code=503, detail="Banco de dados não conectado")
    
    resultado = await db_manager.store_bot(bot_id, bot_token, reivindicado)
    
    if resultado:
        return {"id": bot_id, "token": bot_token, "reivindicado": reivindicado}
    else:
        raise HTTPException(status_code=500, detail="Erro ao armazenar o bot")


@app.get("/bot/verificar", response_model=BotResponse)
async def verificar_bot(bot_id: str, response: Response):
    """Obtém um bot específico do banco de dados"""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Banco de dados não conectado")
    
    bot = await db_manager.get_bot_by_id(bot_id)
    
    if bot:
        return {"id": bot[0], "token": bot[1], "reivindicado": bot[2]}
    else:
        raise HTTPException(status_code=404, detail="Bot não encontrado")


@app.get("/bot/obter", response_model=BotResponse)
async def obter_bot_db(reivindicado: bool = False):
    """Obtém um bot disponível do banco de dados"""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Banco de dados não conectado")
    
    bot = await db_manager.get_bot(reivindicado)
    
    if bot:
        return {"id": bot[0], "token": bot[1], "reivindicado": reivindicado}
    else:
        raise HTTPException(status_code=404, detail="Nenhum bot disponível")


@app.put("/bot/reivindicar", response_model=BotClaimResponse)
async def reivindicar_bot(bot_id: str):
    """Marca um bot como reivindicado (em uso)"""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Banco de dados não conectado")
    
    resultado = await db_manager.claim_bot(bot_id)
    
    if resultado:
        return {"id": bot_id, "reivindicado": True}
    else:
        raise HTTPException(status_code=404, detail="Bot não encontrado")


@app.put("/bot/liberar", response_model=BotClaimResponse)
async def liberar_bot(bot_id: str):
    """Marca um bot como não reivindicado (livre)"""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Banco de dados não conectado")
    
    resultado = await db_manager.unclaim_bot(bot_id)
    
    if resultado:
        return {"id": bot_id, "reivindicado": False}
    else:
        raise HTTPException(status_code=404, detail="Bot não encontrado")


@app.put("/bot/sincronizar", response_model=Dict[str, Any])
async def sincronizar_bot(bot_id: str = ""):
    """Sincroniza o token do bot no banco de dados com o valor atual"""
    if not db_manager or not http_client:
        raise HTTPException(status_code=503, detail="Serviços não inicializados")
    
    if bot_id:
        bot = await get_bot(http_client, bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot não encontrado")
        
        if "bot" not in bot:
            try:
                novo_token = await create_bot_token(http_client, bot["id"])
                bot["bot"] = {"token": novo_token}
            except Exception as e:
                logger.error(f"Erro ao gerar token: {e}")
                raise HTTPException(status_code=500, detail="Aplicação não é um bot")
        
        resultado = await db_manager.sync_token(bot_id, bot["bot"]["token"])
        if resultado:
            return {"id": resultado, "sincronizado": True}
        else:
            raise HTTPException(status_code=500, detail="Erro na sincronização")
    
    else:
        bots = await get_bots(http_client)
        if not bots:
            raise HTTPException(status_code=404, detail="Nenhum bot encontrado")
        
        bots = [x for x in bots if "bot" in x]
        resultado = await db_manager.sync_tokens(bots)
        
        if resultado:
            return {"sincronizados": len(bots), "status": "sucesso"}
        else:
            raise HTTPException(status_code=500, detail="Erro na sincronização")


@app.get("/bot/nao_reivindicados", response_model=Dict[str, int])
async def contar_bots_nao_reivindicados():
    """Obtém a contagem de bots não reivindicados"""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Banco de dados não conectado")
    
    contagem = await db_manager.unclaimed_bots()
    return {"count": contagem}


@app.put("/bot/nome", response_model=MessageResponse)
async def alterar_nome_bot(bot_id: str, nome: str):
    """Altera o nome do bot"""
    if not db_manager or not http_client:
        raise HTTPException(status_code=503, detail="Serviços não inicializados")
    
    bot = await db_manager.get_bot_by_id(bot_id)
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")
    
    sucesso = await change_bot_name(http_client, bot[1], nome)
    
    if sucesso:
        return {"message": f"Nome do bot alterado para: {nome}"}
    else:
        raise HTTPException(status_code=500, detail="Erro ao alterar o nome do bot")


@app.put("/bot/foto", response_model=MessageResponse)
async def alterar_foto_bot(
    bot_id: str,
    url_foto: str = "https://www.freepnglogos.com/uploads/discord-logo-png/discord-logo-logodownload-download-logotipos-1.png"
):
    """Altera a foto do bot"""
    if not db_manager or not http_client:
        raise HTTPException(status_code=503, detail="Serviços não inicializados")
    
    bot = await db_manager.get_bot_by_id(bot_id)
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")
    
    # Download da imagem
    try:
        response = await http_client.get(url_foto)
        response.raise_for_status()
        photo_data = response.content
    except Exception as e:
        logger.error(f"Erro ao baixar imagem: {e}")
        raise HTTPException(status_code=400, detail="Erro ao baixar a imagem da URL")
    
    # Codifica para base64
    extensao = url_foto.split(".")[-1].split("?")[0]
    photo_encoded = f'data:image/{extensao};base64,' + b64encode(photo_data).decode("ascii")
    
    sucesso = await change_bot_photo(http_client, bot[1], photo_encoded)
    
    if sucesso:
        return {"message": "Foto do bot alterada com sucesso"}
    else:
        raise HTTPException(status_code=500, detail="Erro ao alterar a foto do bot")
