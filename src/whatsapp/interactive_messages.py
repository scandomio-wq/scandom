"""
Module pour la gestion des messages interactifs WhatsApp.

Ce module fournit des fonctions pour créer des messages interactifs
avec des boutons (PILLS) pour WhatsApp via l'API Twilio.
"""

from typing import List, Dict, Any, Optional, Union
import json


def create_interactive_buttons_message(body_text: str, buttons: List[str]) -> Dict[str, Any]:
    """
    Crée un message interactif avec des boutons (PILLS).
    
    Args:
        body_text: Texte principal du message
        buttons: Liste des textes à afficher sur les boutons
        
    Returns:
        Dict[str, Any]: Structure de message interactif pour l'API Twilio
    """
    # Limiter à 3 boutons maximum (limitation de WhatsApp)
    buttons = buttons[:3]
    
    # Créer la structure de boutons
    button_objects = []
    for i, button_text in enumerate(buttons):
        button_objects.append({
            "type": "reply",
            "reply": {
                "id": f"button_{i}",
                "title": button_text
            }
        })
    
    # Créer le message interactif
    interactive_message = {
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": body_text
            },
            "action": {
                "buttons": button_objects
            }
        }
    }
    
    return interactive_message


def create_list_message(body_text: str, button_text: str, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Crée un message interactif avec une liste de choix.
    
    Args:
        body_text: Texte principal du message
        button_text: Texte du bouton pour afficher la liste
        sections: Liste des sections avec leurs options
        
    Returns:
        Dict[str, Any]: Structure de message interactif pour l'API Twilio
    """
    interactive_message = {
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {
                "text": body_text
            },
            "action": {
                "button": button_text,
                "sections": sections
            }
        }
    }
    
    return interactive_message


def create_zone_options() -> List[Dict[str, Any]]:
    """
    Crée les options pour la sélection de zone.
    
    Returns:
        List[Dict[str, Any]]: Liste des sections avec les options de zone
    """
    zones = [
        "Hall",
        "Couloir",
        "Ascenseur",
        "Escalier",
        "Façade",
        "Boîte aux lettres",
        "Local Velo",
        "Local technique",
        "Cour / Jardin",
        "Autre"
    ]
    
    # Créer les options
    rows = []
    for i, zone in enumerate(zones):
        rows.append({
            "id": f"zone_{i}",
            "title": zone
        })
    
    # Créer la section
    sections = [{
        "title": "Zones disponibles",
        "rows": rows
    }]
    
    return sections


def create_categorie_options() -> List[Dict[str, Any]]:
    """
    Crée les options pour la sélection de catégorie.
    
    Returns:
        List[Dict[str, Any]]: Liste des sections avec les options de catégorie
    """
    categories = [
        "Electricité",
        "Propreté",
        "Plomberie",
        "Poste / Fenêtre",
        "Consommable",
        "Autre"
    ]
    
    # Créer les options
    rows = []
    for i, categorie in enumerate(categories):
        rows.append({
            "id": f"categorie_{i}",
            "title": categorie
        })
    
    # Créer la section
    sections = [{
        "title": "Catégories disponibles",
        "rows": rows
    }]
    
    return sections


def create_confirmation_buttons() -> Dict[str, Any]:
    """
    Crée un message interactif avec des boutons pour la confirmation.
    
    Returns:
        Dict[str, Any]: Structure de message interactif pour l'API Twilio
    """
    buttons = [
        "Je confirme ce signalement",
        "Annuler et recommencer"
    ]
    
    return create_interactive_buttons_message("", buttons)


def get_interactive_message_for_step(step: str, body_text: str, summary: str = None) -> Optional[Dict[str, Any]]:
    """
    Retourne un message interactif pour une étape donnée.
    
    Args:
        step: Étape de la conversation
        body_text: Texte principal du message
        summary: Résumé de l'incident (pour l'étape de confirmation)
        
    Returns:
        Optional[Dict[str, Any]]: Structure de message interactif ou None
    """
    if step == "zone":
        return create_list_message(
            body_text=body_text,
            button_text="Choisir une zone",
            sections=create_zone_options()
        )
    elif step == "categorie":
        return create_list_message(
            body_text=body_text,
            button_text="Choisir une catégorie",
            sections=create_categorie_options()
        )
    elif step == "confirmation":
        message_text = f"{body_text}\n\n{summary}" if summary else body_text
        return create_interactive_buttons_message(
            body_text=message_text,
            buttons=["Je confirme ce signalement", "Annuler et recommencer"]
        )
    elif step == "photos":
        return create_interactive_buttons_message(
            body_text=body_text,
            buttons=["Non", "J'envoie une photo"]
        )
    
    return None
