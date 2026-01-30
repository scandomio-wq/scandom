"""
Point d'entrée de l'application Flask pour l'intégration WhatsApp.

Ce script lance l'application Flask qui expose les endpoints du webhook Twilio.
"""

from src.whatsapp import create_app

app = create_app()


def start_new_conversation_on_launch():
    """
    Démarre une nouvelle conversation au lancement de l'application.
    L'ancienne conversation est conservée mais marquée comme obsolète.
    """
    from src.whatsapp import redis_client
    from src.db.connection import DatabaseConnection
    from src.whatsapp.state_manager import StateManager
    from src.whatsapp.conversation_manager import ConversationManager
    
    # Numéro de téléphone pour la conversation de test
    phone_number = "+33622831670"
    building_qr_code = "QR5050332870"
    
    db_connection = DatabaseConnection()
    state_manager = StateManager(redis_client)
    conversation_manager = ConversationManager(state_manager, db_connection)
    
    conversation_id = conversation_manager.start_new_conversation(phone_number, building_qr_code)
    
    if conversation_id:
        print(f"✅ Nouvelle conversation préparée: {conversation_id}")
        print(f"   Le message de bienvenue sera envoyé quand l'utilisateur enverra un message.")
    else:
        print("❌ Échec de la préparation de la nouvelle conversation")


if __name__ == '__main__':
    # Démarrer une nouvelle conversation au lancement
    start_new_conversation_on_launch()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
