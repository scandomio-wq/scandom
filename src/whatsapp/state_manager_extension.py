"""
Extension du gestionnaire d'état Redis pour les conversations WhatsApp.

Ce module ajoute des méthodes supplémentaires au gestionnaire d'état
pour faciliter la gestion des conversations WhatsApp.
"""

from typing import Optional
from src.whatsapp.state_manager import StateManager
from src.whatsapp.models import ConversationState

# Ajouter les méthodes manquantes à la classe StateManager
def get_conversation_by_phone(self, phone: str) -> Optional[ConversationState]:
    """
    Récupère un état de conversation par numéro de téléphone.
    
    Args:
        phone: Numéro de téléphone de l'utilisateur
        
    Returns:
        Optional[ConversationState]: L'état de conversation ou None si non trouvé
    """
    try:
        # Recherche par pattern pour trouver toutes les conversations
        pattern = f"{self.key_prefix}*"
        all_keys = self.redis_client.keys(pattern)
        
        for key in all_keys:
            state_json = self.redis_client.get(key)
            if state_json:
                state = ConversationState.from_json(state_json)
                if state.user_phone == phone and not state.is_completed:
                    # Rafraîchir le TTL
                    self.redis_client.expire(key, self.ttl)
                    return state
        
        return None
    except Exception as e:
        return None

def save_conversation(self, conversation: ConversationState) -> bool:
    """
    Sauvegarde un état de conversation dans Redis.
    
    Args:
        conversation: État de conversation à sauvegarder
        
    Returns:
        bool: True si la sauvegarde a réussi, False sinon
    """
    return self.save_state(conversation)

def update_conversation(self, conversation: ConversationState) -> Optional[ConversationState]:
    """
    Met à jour un état de conversation dans Redis.
    
    Args:
        conversation: État de conversation à mettre à jour
        
    Returns:
        Optional[ConversationState]: L'état de conversation mis à jour ou None si échec
    """
    try:
        # Sauvegarder l'état mis à jour
        success = self.save_state(conversation)
        if success:
            return conversation
        return None
    except Exception as e:
        return None

# Ajouter les méthodes à la classe StateManager
StateManager.get_conversation_by_phone = get_conversation_by_phone
StateManager.save_conversation = save_conversation
StateManager.update_conversation = update_conversation
