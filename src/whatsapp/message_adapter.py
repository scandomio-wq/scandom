"""
Adaptateur pour les messages WhatsApp et les états de conversation.

Ce module fournit des adaptateurs pour les messages WhatsApp et les états de conversation
afin de garantir la compatibilité entre les différentes versions du code.
"""

from src.whatsapp.models import WhatsAppMessage, ConversationState, ConversationStep, MessageDirection, MessageStatus


class WhatsAppMessageAdapter:
    """
    Adaptateur pour les messages WhatsApp.
    
    Cette classe ajoute des propriétés compatibles avec le code existant
    pour faciliter la transition entre les différentes versions de l'API.
    """
    
    @staticmethod
    def add_compatibility(message: WhatsAppMessage) -> WhatsAppMessage:
        """
        Ajoute des propriétés de compatibilité à un message WhatsApp.
        
        Args:
            message: Message WhatsApp à adapter
            
        Returns:
            WhatsAppMessage: Message adapté
        """
        # Ajouter la propriété from_phone
        if not hasattr(message, 'from_phone'):
            setattr(message, 'from_phone', message.user_phone if hasattr(message, 'user_phone') else None)
        
        # Ajouter la propriété message_sid si elle n'existe pas
        if not hasattr(message, 'message_sid'):
            setattr(message, 'message_sid', message.message_id)
        
        return message


# Monkey patch la classe WhatsAppMessage pour ajouter les propriétés de compatibilité
original_init = WhatsAppMessage.__init__

def patched_init(self, *args, **kwargs):
    """Initialisation patchée pour ajouter les propriétés de compatibilité."""
    # Extraire user_phone pour from_phone avant de passer à l'init original
    from_phone = kwargs.pop('user_phone', None)
    
    # Gérer la conversion de direction string en MessageDirection enum
    if 'direction' in kwargs and isinstance(kwargs['direction'], str):
        try:
            kwargs['direction'] = MessageDirection(kwargs['direction'])
        except (ValueError, TypeError):
            # Si la conversion échoue, garder la valeur string
            pass
            
    # Gérer la conversion de status string en MessageStatus enum
    if 'status' in kwargs and isinstance(kwargs['status'], str):
        try:
            kwargs['status'] = MessageStatus(kwargs['status'])
        except (ValueError, TypeError):
            # Si la conversion échoue, garder la valeur string
            pass
    
    original_init(self, *args, **kwargs)
    
    # Ajouter la propriété from_phone
    if not hasattr(self, 'from_phone'):
        setattr(self, 'from_phone', from_phone)
    
    # Ajouter la propriété message_sid
    if not hasattr(self, 'message_sid'):
        setattr(self, 'message_sid', self.message_id)
        
    # Ajouter la propriété to_phone si nécessaire
    if not hasattr(self, 'to_phone'):
        setattr(self, 'to_phone', '+14155238886')  # Numéro Twilio par défaut
        
    # Ajouter la propriété body comme alias de content
    if not hasattr(self, 'body') and hasattr(self, 'content'):
        setattr(self, 'body', self.content)

WhatsAppMessage.__init__ = patched_init

# Monkey patch la classe ConversationState pour ajouter les propriétés de compatibilité
original_conversation_init = ConversationState.__init__

def patched_conversation_init(self, *args, **kwargs):
    """Initialisation patchée pour ajouter les propriétés de compatibilité."""
    # Gérer la conversion de from_phone en user_phone
    if 'from_phone' in kwargs and 'user_phone' not in kwargs:
        kwargs['user_phone'] = kwargs.pop('from_phone')
    
    # Gérer la conversion de message_sid en conversation_id
    if 'message_sid' in kwargs and 'conversation_id' not in kwargs:
        kwargs['conversation_id'] = kwargs.pop('message_sid')
        
    # Gérer la conversion de current_step string en ConversationStep enum
    if 'current_step' in kwargs and isinstance(kwargs['current_step'], str):
        try:
            kwargs['current_step'] = ConversationStep(kwargs['current_step'])
        except (ValueError, TypeError):
            # Si la conversion échoue, garder la valeur string
            pass
    
    original_conversation_init(self, *args, **kwargs)
    
    # Ajouter la propriété from_phone comme alias de user_phone
    if not hasattr(self, 'from_phone') and hasattr(self, 'user_phone'):
        setattr(self, 'from_phone', self.user_phone)
    
    # Ajouter la propriété message_sid comme alias de conversation_id
    if not hasattr(self, 'message_sid') and hasattr(self, 'conversation_id'):
        setattr(self, 'message_sid', self.conversation_id)

ConversationState.__init__ = patched_conversation_init
