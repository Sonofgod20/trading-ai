from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import os
from typing import List, Dict, Optional

class MongoDBClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.uri = "mongodb+srv://growhubsa:<db_password>@tradingai.jdz47.mongodb.net/?retryWrites=true&w=majority&appName=tradingAI"
            self.client = None
            self.db = None
            self.chat_collection = None
            self.initialized = True
            
    def connect(self, db_password: str) -> bool:
        """
        Conecta a MongoDB Atlas usando las credenciales proporcionadas
        
        Args:
            db_password: Contraseña de la base de datos
        """
        try:
            uri = self.uri.replace("<db_password>", db_password)
            
            # Detectar si estamos en Streamlit Cloud
            is_streamlit_cloud = os.environ.get('STREAMLIT_SHARING') == 'true'
            
            if is_streamlit_cloud:
                # Configuración específica para Streamlit Cloud
                self.client = MongoClient(
                    uri,
                    server_api=ServerApi('1'),
                    tls=True,
                    tlsAllowInvalidCertificates=True,
                    connectTimeoutMS=30000,
                    socketTimeoutMS=30000
                )
            else:
                # Configuración para entorno local
                self.client = MongoClient(uri, server_api=ServerApi('1'))
            
            # Verificar conexión
            self.client.admin.command('ping')
            
            # Configurar base de datos y colección
            self.db = self.client.trading_ai_db
            self.chat_collection = self.db.chat_history
            
            print("Conexión exitosa a MongoDB Atlas!")
            return True
            
        except Exception as e:
            print(f"Error conectando a MongoDB: {e}")
            return False
            
    def save_message(self, role: str, content: str, metadata: Dict = None) -> bool:
        """
        Guarda un mensaje del chat
        
        Args:
            role: 'user' o 'assistant'
            content: contenido del mensaje
            metadata: datos adicionales opcionales (ej: timestamps, ids, etc)
        """
        try:
            message = {
                'role': role,
                'content': content,
                'timestamp': datetime.utcnow(),
                'metadata': metadata or {}
            }
            
            result = self.chat_collection.insert_one(message)
            return result.acknowledged
            
        except Exception as e:
            print(f"Error guardando mensaje: {e}")
            return False
            
    def get_chat_history(self, limit: int = 100, filter_query: Dict = None) -> List[Dict]:
        """
        Recupera el historial del chat
        
        Args:
            limit: número máximo de mensajes a recuperar
            filter_query: filtro opcional para la búsqueda (ej: {'metadata.symbol': 'BTCUSDT', 'metadata.conversation_id': '123'})
        """
        try:
            query = filter_query or {}
            
            # Sort by timestamp to ensure messages are in chronological order
            messages = list(
                self.chat_collection
                .find(query, {'_id': 0})  # Excluimos el _id de MongoDB
                .sort('timestamp', 1)  # 1 for ascending order (oldest first)
                .limit(limit)
            )
            
            return messages
            
        except Exception as e:
            print(f"Error recuperando historial: {e}")
            return []
    
    def delete_messages(self, filter_query: Dict) -> bool:
        """
        Elimina mensajes que coincidan con el filtro
        
        Args:
            filter_query: criterios para eliminar mensajes
        """
        try:
            result = self.chat_collection.delete_many(filter_query)
            return result.acknowledged
            
        except Exception as e:
            print(f"Error eliminando mensajes: {e}")
            return False
            
    def close(self):
        """Cierra la conexión con MongoDB"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            self.chat_collection = None
