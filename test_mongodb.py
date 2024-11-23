from src.database.mongodb_client import MongoDBClient

def test_mongodb_connection():
    # Inicializar cliente
    client = MongoDBClient()
    
    # Conectar usando las credenciales
    if client.connect('n4vxzOsiGwqmko4I'):
        print("Test 1: Conexión exitosa ✅")
        
        # Test guardar mensaje
        save_success = client.save_message(
            'test', 
            'Mensaje de prueba',
            metadata={'test_id': '1'}
        )
        if save_success:
            print("Test 2: Guardado de mensaje exitoso ✅")
        
        # Test recuperar mensajes
        messages = client.get_chat_history(limit=1)
        if messages and len(messages) > 0:
            print("Test 3: Recuperación de mensajes exitosa ✅")
            print(f"Último mensaje: {messages[0]}")
        
        # Limpiar mensaje de prueba
        client.delete_messages({'metadata.test_id': '1'})
        
        # Cerrar conexión
        client.close()
        print("Test 4: Cierre de conexión exitoso ✅")
    else:
        print("❌ Error en la conexión")

if __name__ == "__main__":
    test_mongodb_connection()
