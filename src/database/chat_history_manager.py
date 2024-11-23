from datetime import datetime
from typing import List, Dict
from .mongodb_client import MongoDBClient

class ChatHistoryManager:
    def __init__(self):
        self.mongo_client = MongoDBClient()
        self.mongo_client.connect('n4vxzOsiGwqmko4I')
        
    def save_message(self, role: str, content: str, symbol: str, conversation_id: str = None, metadata: Dict = None) -> bool:
        """
        Guarda un mensaje en MongoDB
        
        Args:
            role: 'user' o 'assistant'
            content: contenido del mensaje
            symbol: símbolo del trading pair (ej: 'BTCUSDT')
            conversation_id: ID único de la conversación para agrupar mensajes
            metadata: datos adicionales opcionales
        """
        try:
            message_metadata = {
                'symbol': symbol,
                'timestamp': datetime.utcnow(),
                'conversation_id': conversation_id,
                **(metadata or {})
            }
            
            # Remove None values from metadata
            message_metadata = {k: v for k, v in message_metadata.items() if v is not None}
            
            return self.mongo_client.save_message(
                role=role,
                content=content,
                metadata=message_metadata
            )
        except Exception as e:
            print(f"Error guardando mensaje: {e}")
            return False
            
    def get_chat_history(self, symbol: str = None, conversation_id: str = None, limit: int = 100) -> List[Dict]:
        """
        Recupera el historial del chat
        
        Args:
            symbol: opcional, filtrar por símbolo
            conversation_id: opcional, filtrar por ID de conversación
            limit: número máximo de mensajes a recuperar
        """
        try:
            filter_query = {}
            if symbol:
                filter_query['metadata.symbol'] = symbol
            if conversation_id:
                filter_query['metadata.conversation_id'] = conversation_id
                
            return self.mongo_client.get_chat_history(
                limit=limit,
                filter_query=filter_query
            )
        except Exception as e:
            print(f"Error recuperando historial: {e}")
            return []
    
    def close(self):
        """Cierra la conexión con MongoDB"""
        self.mongo_client.close()
