"""
Gestion des étapes de conversation WhatsApp.

Ce module contient les fonctions de traitement et de validation pour chaque étape
de la conversation WhatsApp pour le signalement d'incidents.
"""

import logging
import re
from typing import Dict, Tuple, Any, Optional, List, Union

from src.db.building_dao import BuildingDAO
from src.db.connection import DatabaseConnection
from src.utils.validators import validate_qr_code_number, validate_email
from src.whatsapp.models import ConversationState

# Configuration du logger
logger = logging.getLogger('whatsapp.conversation_steps')

# Validation des entrées par étape
def validate_building_qr(input_text: str, db_connection: DatabaseConnection) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Valide un code QR de bâtiment.
    
    Args:
        input_text: Texte d'entrée
        db_connection: Connexion à la base de données
        
    Returns:
        Tuple[bool, Optional[str], Optional[str]]: (Valide, Valeur normalisée ou None, Message d'erreur ou None)
    """
    # Nettoyer l'entrée
    qr_code = input_text.strip().upper()
    
    # Valider le format
    if not validate_qr_code_number(qr_code, prefix="QR"):
        return False, None, "Le code QR doit commencer par 'QR' suivi de chiffres."
    
    # Vérifier que le bâtiment existe
    building_dao = BuildingDAO()
    building = building_dao.get_building_by_qr_code(qr_code)
    
    if not building:
        return False, None, "Bâtiment non trouvé. Veuillez vérifier le code QR et réessayer."
    
    return True, qr_code, None


def validate_description(input_text: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Valide une description d'incident.
    
    Args:
        input_text: Texte d'entrée
        
    Returns:
        Tuple[bool, Optional[str], Optional[str]]: (Valide, Valeur normalisée ou None, Message d'erreur ou None)
    """
    # Nettoyer l'entrée
    description = input_text.strip()
    
    # Vérifier la longueur
    if len(description) < 5:
        return False, None, "La description est trop courte. Veuillez fournir plus de détails."
    
    if len(description) > 200:
        return False, None, "La description est trop longue. Veuillez la limiter à 200 caractères."
    
    return True, description, None


def validate_zone(input_text: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Valide une zone de bâtiment.
    
    Args:
        input_text: Texte d'entrée
        
    Returns:
        Tuple[bool, Optional[str], Optional[str]]: (Valide, Valeur normalisée ou None, Message d'erreur ou None)
    """
    # Nettoyer l'entrée
    zone = input_text.strip()
    
    # Vérifier la longueur
    if len(zone) < 2:
        return False, None, "La zone est trop courte. Veuillez fournir plus de détails."
    
    if len(zone) > 100:
        return False, None, "La zone est trop longue. Veuillez la limiter à 100 caractères."
    
    return True, zone, None


def validate_etage(input_text: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Valide un étage. Accepte n'importe quelle entrée non vide.
    
    Args:
        input_text: Texte d'entrée
        
    Returns:
        Tuple[bool, Optional[str], Optional[str]]: (Valide, Valeur normalisée ou None, Message d'erreur ou None)
    """
    import logging
    logger = logging.getLogger('whatsapp.conversation')
    
    # Nettoyer l'entrée
    etage = input_text.strip()
    logger.info(f"Validation étage: '{etage}'")
    
    # Seule contrainte: l'entrée ne doit pas être vide
    if not etage:
        return False, None, "Veuillez indiquer un étage."
    
    # Limiter la longueur pour éviter les abus
    if len(etage) > 50:
        return False, None, "L'entrée est trop longue. Veuillez la limiter à 50 caractères."
    
    logger.info(f"Étage validé: {etage}")
    return True, etage, None


def validate_priorite(input_text: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Valide une priorité d'incident.
    
    Args:
        input_text: Texte d'entrée
        
    Returns:
        Tuple[bool, Optional[str], Optional[str]]: (Valide, Valeur normalisée ou None, Message d'erreur ou None)
    """
    # Nettoyer l'entrée
    priorite = input_text.strip().lower()
    
    # Valeurs acceptées
    valid_values = ['haute', 'moyenne', 'basse', 'high', 'medium', 'low', '1', '2', '3']
    
    # Normalisation
    if priorite in ['haute', 'high', '1']:
        normalized = 'haute'
    elif priorite in ['moyenne', 'medium', '2']:
        normalized = 'moyenne'
    elif priorite in ['basse', 'low', '3']:
        normalized = 'basse'
    else:
        return False, None, "Priorité invalide. Veuillez répondre par 'haute', 'moyenne' ou 'basse'."
    
    return True, normalized, None


def validate_phone(input_text: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Valide un numéro de téléphone.
    
    Args:
        input_text: Texte d'entrée
        
    Returns:
        Tuple[bool, Optional[str], Optional[str]]: (Valide, Valeur normalisée ou None, Message d'erreur ou None)
    """
    # Nettoyer l'entrée
    phone = input_text.strip()
    
    # Valider le format (format international +XX...)
    pattern = r'^\+\d{10,15}$'
    if not re.match(pattern, phone):
        return False, None, "Format de téléphone invalide. Veuillez utiliser le format international (ex: +33612345678)."
    
    return True, phone, None


def validate_email_address(input_text: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Valide une adresse email.
    
    Args:
        input_text: Texte d'entrée
        
    Returns:
        Tuple[bool, Optional[str], Optional[str]]: (Valide, Valeur normalisée ou None, Message d'erreur ou None)
    """
    # Nettoyer l'entrée
    email = input_text.strip()
    
    # Valider le format
    if not validate_email(email):
        return False, None, "Format d'email invalide. Veuillez fournir une adresse email valide."
    
    return True, email, None


def validate_confirmation(input_text: str) -> Tuple[bool, Optional[bool], Optional[str]]:
    """
    Valide une confirmation.
    
    Args:
        input_text: Texte d'entrée
        
    Returns:
        Tuple[bool, Optional[bool], Optional[str]]: (Valide, Confirmation ou None, Message d'erreur ou None)
    """
    # Nettoyer l'entrée
    confirmation = input_text.strip().lower()
    
    # Valeurs positives
    positive_values = ['oui', 'yes', 'o', 'y', '1', 'ok', 'confirmer', 'confirm']
    
    # Valeurs négatives
    negative_values = ['non', 'no', 'n', '0', 'annuler', 'cancel']
    
    if confirmation in positive_values:
        return True, True, None
    elif confirmation in negative_values:
        return True, False, None
    else:
        return False, None, "Réponse invalide. Veuillez répondre par 'OUI' ou 'NON'."


def validate_zone_choix(input_text: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Valide le choix de zone parmi une liste prédéfinie.
    Supporte les réponses numérotées.
    
    Args:
        input_text: Texte d'entrée
        
    Returns:
        Tuple[bool, Optional[str], Optional[str]]: (Valide, Valeur normalisée ou None, Message d'erreur ou None)
    """
    import logging
    logger = logging.getLogger('whatsapp.conversation')
    
    # Nettoyer l'entrée
    zone = input_text.strip().lower()
    logger.info(f"Validation zone: '{zone}'")
    
    # Liste des zones valides avec leur numéro
    zones_list = [
        'Hall',
        'Couloir',
        'Ascenseur',
        'Escalier',
        'Façade',
        'Boîte aux lettres',
        'Local Velo',
        'Local technique',
        'Cour / Jardin',
        'Autre'
    ]
    
    # Mapping des noms de zones
    valid_zones = {
        'hall': 'Hall',
        'couloir': 'Couloir',
        'ascenseur': 'Ascenseur',
        'escalier': 'Escalier',
        'facade': 'Façade',
        'façade': 'Façade',
        'boite aux lettres': 'Boîte aux lettres',
        'boîte aux lettres': 'Boîte aux lettres',
        'local velo': 'Local Velo',
        'local technique': 'Local technique',
        'cour': 'Cour / Jardin',
        'jardin': 'Cour / Jardin',
        'cour / jardin': 'Cour / Jardin',
        'autre': 'Autre'
    }
    
    # Gestion des réponses numérotées (1-9, 0)
    if zone.isdigit():
        num = int(zone)
        logger.info(f"Réponse numérique détectée: {num}")
        if 1 <= num <= 9 and num-1 < len(zones_list):
            logger.info(f"Zone sélectionnée par numéro: {zones_list[num-1]}")
            return True, zones_list[num-1], None
        elif num == 0:  # 0 pour Autre
            logger.info("Zone 'Autre' sélectionnée par numéro")
            return True, 'Autre', None
    
    # Vérifier si la zone est valide (saisie manuelle)
    for key, value in valid_zones.items():
        # Correspondance exacte
        if zone == key or zone == value.lower():
            logger.info(f"Correspondance exacte trouvée pour la zone: {value}")
            return True, value, None
    
    # Si aucune correspondance exacte, essayer les correspondances partielles
    for key, value in valid_zones.items():
        # Vérification si la clé est dans la zone ou si la zone est dans la clé
        if key in zone or zone in key or value.lower() in zone or zone in value.lower():
            logger.info(f"Correspondance partielle trouvée pour la zone: {value}")
            return True, value, None
    
    logger.warning(f"Aucune zone valide trouvée pour l'entrée: {zone}")
    return False, None, "Zone invalide. Veuillez choisir parmi les options proposées ou répondre avec un numéro (1-9, 0)."


def validate_categorie(input_text: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Valide la catégorie d'incident parmi une liste prédéfinie.
    Supporte les réponses numérotées.
    
    Args:
        input_text: Texte d'entrée
        
    Returns:
        Tuple[bool, Optional[str], Optional[str]]: (Valide, Valeur normalisée ou None, Message d'erreur ou None)
    """
    import logging
    logger = logging.getLogger('whatsapp.conversation')
    
    # Nettoyer l'entrée
    categorie = input_text.strip().lower()
    logger.info(f"Validation catégorie: '{categorie}'")
    
    # Liste des catégories valides avec leur numéro
    categories_list = [
        'Electricité',
        'Propreté',
        'Plomberie',
        'Poste / Fenêtre',
        'Consommable',
        'Autre'
    ]
    
    # Mapping des noms de catégories
    valid_categories = {
        'electricite': 'Electricité',
        'électricité': 'Electricité',
        'electricité': 'Electricité',
        'proprete': 'Propreté',
        'propreté': 'Propreté',
        'plomberie': 'Plomberie',
        'poste': 'Poste / Fenêtre',
        'fenetre': 'Poste / Fenêtre',
        'fenêtre': 'Poste / Fenêtre',
        'poste / fenetre': 'Poste / Fenêtre',
        'poste / fenêtre': 'Poste / Fenêtre',
        'consommable': 'Consommable',
        'autre': 'Autre'
    }
    
    # Gestion des réponses numérotées (1-6)
    if categorie.isdigit():
        num = int(categorie)
        logger.info(f"Réponse numérique détectée: {num}")
        if 1 <= num <= 6 and num-1 < len(categories_list):
            logger.info(f"Catégorie sélectionnée par numéro: {categories_list[num-1]}")
            return True, categories_list[num-1], None
    
    # Vérifier si la catégorie est valide (saisie manuelle)
    for key, value in valid_categories.items():
        # Correspondance exacte
        if categorie == key or categorie == value.lower():
            logger.info(f"Correspondance exacte trouvée pour la catégorie: {value}")
            return True, value, None
    
    # Si aucune correspondance exacte, essayer les correspondances partielles
    for key, value in valid_categories.items():
        # Vérification si la clé est dans la catégorie ou si la catégorie est dans la clé
        if key in categorie or categorie in key or value.lower() in categorie or categorie in value.lower():
            logger.info(f"Correspondance partielle trouvée pour la catégorie: {value}")
            return True, value, None
    
    logger.warning(f"Aucune catégorie valide trouvée pour l'entrée: {categorie}")
    return False, None, "Catégorie invalide. Veuillez choisir parmi les options proposées ou répondre avec un numéro (1-6)."


def validate_informations(input_text: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Valide les informations complémentaires.
    
    Args:
        input_text: Texte d'entrée
        
    Returns:
        Tuple[bool, Optional[str], Optional[str]]: (Valide, Valeur normalisée ou None, Message d'erreur ou None)
    """
    # Nettoyer l'entrée
    informations = input_text.strip()
    
    # Vérifier la longueur
    if len(informations) > 500:
        return False, None, "Les informations sont trop longues. Veuillez les limiter à 500 caractères."
    
    return True, informations, None


def validate_photos(input_text: str, media_url: Optional[str] = None, conversation_id: Optional[str] = None) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """
    Valide les photos ou la réponse "Non".
    Supporte les réponses numérotées.
    Télécharge les photos localement si une URL est fournie.
    
    Args:
        input_text: Texte d'entrée
        media_url: URL du média (si présent)
        conversation_id: ID de la conversation (pour le stockage local)
        
    Returns:
        Tuple[bool, Optional[Dict], Optional[str]]: (Valide, Données de photo ou None, Message d'erreur ou None)
    """
    from src.whatsapp.media_handler import download_media_from_twilio
    
    # Nettoyer l'entrée
    response = input_text.strip().lower()
    
    def process_media(url: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Télécharge le média et retourne le résultat."""
        if conversation_id:
            success, local_path, error = download_media_from_twilio(url, conversation_id)
            if success and local_path:
                return True, {'has_photo': True, 'media_url': url, 'local_path': local_path}, None
            else:
                logger.warning(f"Échec du téléchargement, conservation de l'URL Twilio: {error}")
                return True, {'has_photo': True, 'media_url': url}, None
        else:
            return True, {'has_photo': True, 'media_url': url}, None
    
    # Gestion des réponses numérotées
    if response.isdigit() and len(response) == 1:
        num = int(response)
        if num == 1:  # 1 pour "Non"
            return True, {'has_photo': False}, None
        elif num == 2:  # 2 pour "Oui, j'envoie une photo"
            # Si une photo est déjà jointe au message
            if media_url:
                return process_media(media_url)
            else:
                return False, None, "Veuillez envoyer une photo."
    
    # Si l'utilisateur a répondu "Non"
    if response in ['non', 'no', 'n']:
        return True, {'has_photo': False}, None
    
    # Si l'utilisateur a répondu "Oui"
    if response in ['oui', 'yes', 'y', 'o']:
        # Si une photo est déjà jointe au message
        if media_url:
            return process_media(media_url)
        else:
            return False, None, "Veuillez envoyer une photo."
    
    # Si une photo a été fournie directement
    if media_url:
        return process_media(media_url)
    
    # Si l'utilisateur a envoyé du texte mais pas de photo
    return False, None, "Veuillez envoyer une photo ou répondre 'Non' ou avec le numéro 1."


def validate_confirmation_new(input_text: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Valide la confirmation finale avec les nouvelles options.
    Supporte les réponses numérotées.
    
    Args:
        input_text: Texte d'entrée
        
    Returns:
        Tuple[bool, Optional[str], Optional[str]]: (Valide, Réponse ou None, Message d'erreur ou None)
    """
    # Nettoyer l'entrée
    confirmation = input_text.strip().lower()
    
    # Gestion des réponses numérotées
    if confirmation.isdigit() and len(confirmation) == 1:
        num = int(confirmation)
        if num == 1:  # 1 pour "Je confirme ce signalement"
            return True, 'confirm', None
        elif num == 2:  # 2 pour "Annuler et faire un nouveau signalement"
            return True, 'restart', None
    
    # Options valides pour la saisie manuelle
    confirm_values = ['je confirme', 'je confirme ce signalement', 'confirmer', 'confirme', 'oui', 'ok']
    restart_values = ['annuler', 'annuler et faire un nouveau signalement', 'nouveau', 'recommencer']
    
    if any(value in confirmation for value in confirm_values):
        return True, 'confirm', None
    elif any(value in confirmation for value in restart_values):
        return True, 'restart', None
    else:
        return False, None, "Réponse invalide. Veuillez choisir parmi les options proposées ou répondre avec un numéro (1 ou 2)."


from src.whatsapp.models import ConversationStep

# Dictionnaire des fonctions de validation par étape
VALIDATORS = {
    'building_qr': validate_building_qr,  # Conservé pour compatibilité
    ConversationStep.ETAGE: validate_etage,
    ConversationStep.ZONE: validate_zone_choix,
    ConversationStep.ZONE_AUTRE: validate_zone,
    ConversationStep.CATEGORIE: validate_categorie,
    ConversationStep.CATEGORIE_AUTRE: validate_description,
    ConversationStep.INFORMATIONS: validate_informations,
    ConversationStep.PHOTOS: validate_photos,
    ConversationStep.CONFIRMATION: validate_confirmation_new
}


def generate_summary(conversation: ConversationState) -> str:
    """
    Génère un résumé de la conversation pour confirmation.
    
    Args:
        conversation: État de la conversation
        
    Returns:
        str: Résumé formaté
    """
    data = conversation.collected_data
    
    # Gérer la zone (normale ou personnalisée)
    zone = data.get('zone', 'Non spécifié')
    if zone == 'Autre' and 'zone_autre' in data:
        zone = f"Autre: {data.get('zone_autre')}"
    
    # Gérer la catégorie (normale ou personnalisée)
    categorie = data.get('categorie', 'Non spécifié')
    if categorie == 'Autre' and 'categorie_autre' in data:
        categorie = f"Autre: {data.get('categorie_autre')}"
    
    # Gérer les photos
    photos = "Non"
    if data.get('photos', {}).get('has_photo', False):
        photos = "Oui"
    
    # Gérer les informations complémentaires
    informations = data.get('informations', 'Non spécifié')
    
    summary = f"""
Bâtiment: {conversation.building_qr_code}
Étage: {data.get('etage', 'Non spécifié')}
Zone: {zone}
Catégorie: {categorie}
Informations complémentaires: {informations}
Photos: {photos}
"""
    
    return summary.strip()


def get_next_step(current_step: ConversationStep, collected_data: Dict = None) -> ConversationStep:
    """
    Détermine l'étape suivante de la conversation, avec gestion des étapes conditionnelles.
    
    Args:
        current_step: Étape actuelle
        collected_data: Données collectées jusqu'à présent
        
    Returns:
        ConversationStep: Étape suivante
    """
    from src.whatsapp.conversation_manager import STEPS
    
    # Gérer les étapes conditionnelles
    if collected_data:
        # Après l'étape ZONE, vérifier si on doit aller à ZONE_AUTRE
        if current_step == ConversationStep.ZONE and collected_data.get(ConversationStep.ZONE.value) == 'Autre':
            return ConversationStep.ZONE_AUTRE
        # Sinon, si on est à ZONE ou ZONE_AUTRE, aller à CATEGORIE
        elif current_step in [ConversationStep.ZONE, ConversationStep.ZONE_AUTRE]:
            return ConversationStep.CATEGORIE
        
        # Après l'étape CATEGORIE, vérifier si on doit aller à CATEGORIE_AUTRE
        if current_step == ConversationStep.CATEGORIE and collected_data.get(ConversationStep.CATEGORIE.value) == 'Autre':
            return ConversationStep.CATEGORIE_AUTRE
        # Sinon, si on est à CATEGORIE ou CATEGORIE_AUTRE, aller à INFORMATIONS
        elif current_step in [ConversationStep.CATEGORIE, ConversationStep.CATEGORIE_AUTRE]:
            return ConversationStep.INFORMATIONS
    
    # Comportement par défaut pour les autres étapes
    try:
        current_index = STEPS.index(current_step)
        if current_index < len(STEPS) - 1:
            return STEPS[current_index + 1]
        else:
            return current_step
    except ValueError:
        # Si l'étape actuelle n'est pas dans la liste, revenir à la première étape
        return STEPS[0]
