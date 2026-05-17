"""
Integração com a API do Discord
Versão moderna com suporte a async/await e rate limiting
"""
import logging
from typing import List, Dict, Optional, Any
from os import getenv

from httpx import AsyncClient, HTTPError

logger = logging.getLogger(__name__)

# Configurações da API
DISCORD_API_BASE = "https://discord.com/api/v10"  # Atualizado para v10
USER_AGENT = "DiscordBotManager/2025.1.0"


async def create_bot(client: AsyncClient, team_id: str) -> str:
    """
    Cria uma nova aplicação em um time
    
    Args:
        client: Cliente HTTP assíncrono
        team_id: ID do time Discord
    
    Returns:
        ID da nova aplicação ou string vazia em caso de erro
    """
    try:
        response = await client.post(
            f"{DISCORD_API_BASE}/applications",
            headers={
                "User-Agent": USER_AGENT,
                "Content-Type": "application/json",
                "Authorization": getenv("AUTH", ""),
            },
            json={"name": "Meu Bot Discord", "team_id": team_id},
        )
        
        response.raise_for_status()
        return response.json().get("id", "")
        
    except HTTPError as e:
        logger.error(f"Erro ao criar bot: {e.response.text if e.response else str(e)}")
        return ""


async def create_bot_token(client: AsyncClient, bot_id: str) -> Optional[str]:
    """
    Cria um novo token para um bot
    
    Args:
        client: Cliente HTTP assíncrono
        bot_id: ID do bot
    
    Returns:
        Token do bot ou None em caso de erro
    """
    try:
        response = await client.post(
            f"{DISCORD_API_BASE}/applications/{bot_id}/bot",
            headers={
                "User-Agent": USER_AGENT,
                "Content-Type": "application/json",
                "Authorization": getenv("AUTH", ""),
            },
        )
        
        response.raise_for_status()
        return response.json().get("token")
        
    except HTTPError as e:
        logger.error(f"Erro ao criar token: {e.response.text if e.response else str(e)}")
        return None


async def get_teams(client: AsyncClient) -> List[str]:
    """
    Lista todos os times que o usuário participa
    
    Args:
        client: Cliente HTTP assíncrono
    
    Returns:
        Lista de IDs dos times
    """
    try:
        response = await client.get(
            f"{DISCORD_API_BASE}/teams",
            headers={
                "User-Agent": USER_AGENT,
                "Authorization": getenv("AUTH", ""),
            },
        )
        
        response.raise_for_status()
        return [team["id"] for team in response.json()]
        
    except HTTPError as e:
        logger.error(f"Erro ao obter times: {e.response.text if e.response else str(e)}")
        return []


async def get_bot(client: AsyncClient, bot_id: str) -> Dict[str, Any]:
    """
    Obtém informações de um bot
    
    Args:
        client: Cliente HTTP assíncrono
        bot_id: ID do bot
    
    Returns:
        Dicionário com informações do bot
    """
    try:
        response = await client.get(
            f"{DISCORD_API_BASE}/applications/{bot_id}",
            headers={
                "User-Agent": USER_AGENT,
                "Authorization": getenv("AUTH", ""),
            },
        )
        
        response.raise_for_status()
        return response.json()
        
    except HTTPError as e:
        logger.error(f"Erro ao obter bot: {e.response.text if e.response else str(e)}")
        return {}


async def get_bots(client: AsyncClient) -> List[Dict[str, Any]]:
    """
    Lista todos os bots que o usuário possui
    
    Args:
        client: Cliente HTTP assíncrono
    
    Returns:
        Lista de bots
    """
    try:
        response = await client.get(
            f"{DISCORD_API_BASE}/applications?with_team_applications=true",
            headers={
                "User-Agent": USER_AGENT,
                "Authorization": getenv("AUTH", ""),
            },
        )
        
        response.raise_for_status()
        return response.json()
        
    except HTTPError as e:
        logger.error(f"Erro ao obter bots: {e.response.text if e.response else str(e)}")
        return []


async def change_bot_name(client: AsyncClient, token: str, name: str) -> bool:
    """
    Altera o nome do bot
    
    Args:
        client: Cliente HTTP assíncrono
        token: Token do bot
        name: Novo nome
    
    Returns:
        True se bem sucedido, False caso contrário
    """
    try:
        response = await client.patch(
            f"{DISCORD_API_BASE}/users/@me",
            headers={
                "Authorization": f"Bot {token}",
                "Content-Type": "application/json"
            },
            json={"username": name},
        )
        
        response.raise_for_status()
        return response.json().get("username") == name
        
    except HTTPError as e:
        logger.error(f"Erro ao alterar nome: {e.response.text if e.response else str(e)}")
        return False


async def change_bot_photo(client: AsyncClient, token: str, base64_photo: str) -> bool:
    """
    Altera a foto do bot
    
    Args:
        client: Cliente HTTP assíncrono
        token: Token do bot
        base64_photo: Foto codificada em base64
    
    Returns:
        True se bem sucedido, False caso contrário
    """
    try:
        response = await client.patch(
            f"{DISCORD_API_BASE}/users/@me",
            headers={
                "Authorization": f"Bot {token}",
                "Content-Type": "application/json"
            },
            json={"avatar": base64_photo},
        )
        
        response.raise_for_status()
        return bool(response.json().get("avatar"))
        
    except HTTPError as e:
        logger.error(f"Erro ao alterar foto: {e.response.text if e.response else str(e)}")
        return False
