"""
Modelos de dados Pydantic para validação
"""
from typing import Optional
from pydantic import BaseModel


class BotCreateResponse(BaseModel):
    """Resposta para criação de bot"""
    id: str
    token: Optional[str] = None
    mensagem: str


class BotResponse(BaseModel):
    """Resposta para operações com bots"""
    id: str
    token: str
    reivindicado: bool


class BotClaimResponse(BaseModel):
    """Resposta para reivindicação/liberação de bot"""
    id: str
    reivindicado: bool


class MessageResponse(BaseModel):
    """Resposta simples com mensagem"""
    message: str
    status: Optional[str] = "ok"


class BotCreateRequest(BaseModel):
    """Requisição para criar bot"""
    armazenar: bool = False
    nome: Optional[str] = "Meu Bot Discord"


class BotStoreRequest(BaseModel):
    """Requisição para armazenar bot"""
    bot_id: str
    bot_token: str
    reivindicado: bool = False
