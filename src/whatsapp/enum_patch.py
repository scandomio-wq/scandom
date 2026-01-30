"""
Patch pour les énumérations WhatsApp.

Ce module fournit des fonctions pour patcher les énumérations WhatsApp
afin de les rendre plus robustes et compatibles avec différentes utilisations.
"""

from enum import Enum
from src.whatsapp.models import ConversationStep, MessageDirection, MessageStatus


def patch_enums():
    """
    Patche les classes d'énumération pour les rendre plus robustes.
    """
    # Ajouter une méthode __eq__ personnalisée à ConversationStep
    def conversation_step_eq(self, other):
        if isinstance(other, str):
            return self.value == other
        return super(ConversationStep, self).__eq__(other)
    
    # Ajouter une méthode __eq__ personnalisée à MessageDirection
    def message_direction_eq(self, other):
        if isinstance(other, str):
            return self.value == other
        return super(MessageDirection, self).__eq__(other)
    
    # Ajouter une méthode __eq__ personnalisée à MessageStatus
    def message_status_eq(self, other):
        if isinstance(other, str):
            return self.value == other
        return super(MessageStatus, self).__eq__(other)
    
    # Appliquer les patches
    ConversationStep.__eq__ = conversation_step_eq
    MessageDirection.__eq__ = message_direction_eq
    MessageStatus.__eq__ = message_status_eq
    
    # Ajouter des méthodes pour faciliter la conversion
    def from_string(cls, value):
        """Convertit une chaîne en énumération."""
        if value is None:
            return None
        if isinstance(value, cls):
            return value
        try:
            return cls(value)
        except (ValueError, TypeError):
            return None
    
    # Appliquer la méthode from_string
    ConversationStep.from_string = classmethod(from_string)
    MessageDirection.from_string = classmethod(from_string)
    MessageStatus.from_string = classmethod(from_string)


# Appliquer les patches automatiquement à l'importation
patch_enums()
