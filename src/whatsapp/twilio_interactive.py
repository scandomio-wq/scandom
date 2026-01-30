"""
Module pour envoyer des messages interactifs WhatsApp via l'API Twilio.

Ce module permet d'envoyer des messages avec des boutons (PILLS) et des listes
interactives via l'API REST de Twilio pour WhatsApp Business.
"""

import json
import logging
from typing import List, Dict, Any, Optional

from twilio.rest import Client

logger = logging.getLogger('whatsapp.interactive')


def send_interactive_list_message(
    client: Client,
    from_number: str,
    to_number: str,
    body_text: str,
    button_text: str,
    sections: List[Dict[str, Any]]
) -> Optional[str]:
    """
    Envoie un message interactif avec une liste de choix.
    
    Args:
        client: Client Twilio
        from_number: Numéro WhatsApp de l'expéditeur (format: whatsapp:+1234567890)
        to_number: Numéro WhatsApp du destinataire (format: whatsapp:+1234567890)
        body_text: Texte principal du message
        button_text: Texte du bouton pour afficher la liste
        sections: Liste des sections avec leurs options
        
    Returns:
        Optional[str]: SID du message envoyé ou None en cas d'erreur
    """
    try:
        # Construire le contenu interactif
        content_variables = json.dumps({
            "1": body_text
        })
        
        # Créer le message avec le content SID
        message = client.messages.create(
            from_=from_number,
            to=to_number,
            body=body_text,
            persistent_action=[f"list:{button_text}"]
        )
        
        logger.info(f"Message interactif envoyé: {message.sid}")
        return message.sid
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du message interactif: {e}")
        return None


def send_interactive_buttons_message(
    client: Client,
    from_number: str,
    to_number: str,
    body_text: str,
    buttons: List[str]
) -> Optional[str]:
    """
    Envoie un message interactif avec des boutons (PILLS).
    
    Note: WhatsApp limite à 3 boutons maximum par message.
    
    Args:
        client: Client Twilio
        from_number: Numéro WhatsApp de l'expéditeur (format: whatsapp:+1234567890)
        to_number: Numéro WhatsApp du destinataire (format: whatsapp:+1234567890)
        body_text: Texte principal du message
        buttons: Liste des textes des boutons (max 3)
        
    Returns:
        Optional[str]: SID du message envoyé ou None en cas d'erreur
    """
    try:
        # Limiter à 3 boutons
        buttons = buttons[:3]
        
        # Construire le JSON pour les boutons interactifs
        interactive_content = {
            "type": "button",
            "body": {
                "text": body_text
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": f"btn_{i}",
                            "title": btn_text[:20]  # WhatsApp limite à 20 caractères
                        }
                    }
                    for i, btn_text in enumerate(buttons)
                ]
            }
        }
        
        # Envoyer via l'API Content
        message = client.messages.create(
            from_=from_number,
            to=to_number,
            content_sid=None,  # Utiliser le contenu inline
            body=body_text,
            persistent_action=[json.dumps(interactive_content)]
        )
        
        logger.info(f"Message avec boutons envoyé: {message.sid}")
        return message.sid
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du message avec boutons: {e}")
        return None


def send_text_message(
    client: Client,
    from_number: str,
    to_number: str,
    body_text: str
) -> Optional[str]:
    """
    Envoie un message texte simple.
    
    Args:
        client: Client Twilio
        from_number: Numéro WhatsApp de l'expéditeur (format: whatsapp:+1234567890)
        to_number: Numéro WhatsApp du destinataire (format: whatsapp:+1234567890)
        body_text: Texte du message
        
    Returns:
        Optional[str]: SID du message envoyé ou None en cas d'erreur
    """
    try:
        message = client.messages.create(
            from_=from_number,
            to=to_number,
            body=body_text
        )
        
        logger.info(f"Message texte envoyé: {message.sid}")
        return message.sid
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du message texte: {e}")
        return None


def send_template_message(
    client: Client,
    from_number: str,
    to_number: str,
    content_sid: str,
    content_variables: Optional[Dict[str, str]] = None
) -> Optional[str]:
    """
    Envoie un message utilisant un template approuvé par Meta.
    
    Args:
        client: Client Twilio
        from_number: Numéro WhatsApp de l'expéditeur (format: whatsapp:+1234567890)
        to_number: Numéro WhatsApp du destinataire (format: whatsapp:+1234567890)
        content_sid: SID du template (format: HXxxxxxxxxxx)
        content_variables: Variables à injecter dans le template (optionnel)
        
    Returns:
        Optional[str]: SID du message envoyé ou None en cas d'erreur
    """
    try:
        params = {
            "from_": from_number,
            "to": to_number,
            "content_sid": content_sid
        }
        
        if content_variables:
            params["content_variables"] = json.dumps(content_variables)
        
        message = client.messages.create(**params)
        
        logger.info(f"Message template envoyé: {message.sid} (template: {content_sid})")
        return message.sid
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du message template: {e}")
        return None
