"""
Gerenciamento do banco de dados PostgreSQL
Versão assíncrona com pool de conexões
"""
import logging
from typing import Optional, List, Tuple, Dict, Any

import asyncpg

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gerenciador do banco de dados com pool de conexões"""
    
    def __init__(self, host: str, database: str, user: str, password: str):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Estabelece conexão com o banco de dados"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            await self._init_tables()
            logger.info("Conexão com o banco de dados estabelecida")
        except Exception as e:
            logger.error(f"Erro ao conectar ao banco de dados: {e}")
            raise
    
    async def disconnect(self):
        """Fecha a conexão com o banco de dados"""
        if self.pool:
            await self.pool.close()
            logger.info("Conexão com o banco de dados fechada")
    
    async def _init_tables(self):
        """Inicializa as tabelas necessárias se não existirem"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS bots (
                    client_id VARCHAR(32) PRIMARY KEY,
                    token TEXT NOT NULL,
                    claimed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_bots_claimed ON bots(claimed);
                CREATE INDEX IF NOT EXISTS idx_bots_created ON bots(created_at);
            """)
            logger.info("Tabelas do banco de dados verificadas/criadas")
    
    async def store_bot(self, bot_id: str, bot_token: str, claimed: bool = False) -> Optional[str]:
        """Armazena um bot no banco de dados"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                """
                INSERT INTO bots(client_id, token, claimed)
                VALUES($1, $2, $3)
                ON CONFLICT (client_id) 
                DO UPDATE SET token = $2, updated_at = CURRENT_TIMESTAMP
                RETURNING client_id
                """,
                bot_id, bot_token, claimed
            )
            
            if result:
                logger.info(f"Bot armazenado/atualizado: {result}")
            return result
    
    async def get_bot(self, claimed: bool = False) -> Optional[Tuple[str, str, bool]]:
        """Obtém um bot do banco de dados"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                SELECT client_id, token, claimed 
                FROM bots 
                WHERE claimed = $1 
                ORDER BY created_at 
                LIMIT 1
                """,
                claimed
            )
            
            if result:
                logger.debug(f"Bot obtido: {result['client_id']}")
                return (result['client_id'], result['token'], result['claimed'])
            return None
    
    async def get_bot_by_id(self, bot_id: str) -> Optional[Tuple[str, str, bool]]:
        """Obtém um bot específico pelo ID"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT client_id, token, claimed FROM bots WHERE client_id = $1",
                bot_id
            )
            
            if result:
                return (result['client_id'], result['token'], result['claimed'])
            return None
    
    async def claim_bot(self, bot_id: str) -> Optional[str]:
        """Marca um bot como reivindicado"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                """
                UPDATE bots 
                SET claimed = TRUE, updated_at = CURRENT_TIMESTAMP 
                WHERE client_id = $1 
                RETURNING client_id
                """,
                bot_id
            )
            
            if result:
                logger.info(f"Bot reivindicado: {result}")
            return result
    
    async def unclaim_bot(self, bot_id: str) -> Optional[str]:
        """Marca um bot como não reivindicado"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                """
                UPDATE bots 
                SET claimed = FALSE, updated_at = CURRENT_TIMESTAMP 
                WHERE client_id = $1 
                RETURNING client_id
                """,
                bot_id
            )
            
            if result:
                logger.info(f"Bot liberado: {result}")
            return result
    
    async def sync_token(self, bot_id: str, new_token: str) -> Optional[str]:
        """Sincroniza o token de um bot"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                """
                UPDATE bots 
                SET token = $1, updated_at = CURRENT_TIMESTAMP 
                WHERE client_id = $2 
                RETURNING client_id
                """,
                new_token, bot_id
            )
            
            if result:
                logger.info(f"Token sincronizado: {result}")
            return result
    
    async def sync_tokens(self, bots: List[Dict[str, Any]]) -> bool:
        """Sincroniza tokens de múltiplos bots"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for bot in bots:
                    result = await conn.execute(
                        """
                        UPDATE bots 
                        SET token = $1, updated_at = CURRENT_TIMESTAMP 
                        WHERE client_id = $2
                        """,
                        bot["bot"]["token"], bot["id"]
                    )
                    
                    if result == "UPDATE 0":
                        return False
                
            logger.info(f"{len(bots)} tokens sincronizados")
            return True
    
    async def unclaimed_bots(self) -> int:
        """Retorna o número de bots não reivindicados"""
        async with self.pool.acquire() as conn:
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM bots WHERE NOT claimed"
            )
            logger.debug(f"Bots não reivindicados: {count}")
            return count or 0
    
    async def all_bots(self) -> int:
        """Retorna o número total de bots"""
        async with self.pool.acquire() as conn:
            count = await conn.fetchval("SELECT COUNT(*) FROM bots")
            logger.debug(f"Total de bots: {count}")
            return count or 0
    
    async def bot_exists(self, bot_id: str) -> bool:
        """Verifica se um bot existe no banco"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM bots WHERE client_id = $1)",
                bot_id
            )
            return result
