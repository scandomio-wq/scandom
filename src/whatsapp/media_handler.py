"""
Gestionnaire de médias WhatsApp.

Ce module gère le téléchargement et le stockage local des médias (photos)
envoyés via WhatsApp.
"""

import os
import logging
import requests
import uuid
from datetime import datetime
from typing import Optional, List, Tuple
from urllib.parse import urlparse

from src.whatsapp import whatsapp_config

logger = logging.getLogger('whatsapp.media')

# Répertoire de stockage des médias
MEDIA_STORAGE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'storage', 'whatsapp_media'
)


def ensure_storage_directory() -> str:
    """
    S'assure que le répertoire de stockage existe.
    
    Returns:
        str: Chemin du répertoire de stockage
    """
    if not os.path.exists(MEDIA_STORAGE_DIR):
        os.makedirs(MEDIA_STORAGE_DIR, exist_ok=True)
        logger.info(f"Répertoire de stockage créé: {MEDIA_STORAGE_DIR}")
    return MEDIA_STORAGE_DIR


def get_conversation_media_dir(conversation_id: str) -> str:
    """
    Retourne le répertoire de stockage pour une conversation spécifique.
    
    Args:
        conversation_id: ID de la conversation
        
    Returns:
        str: Chemin du répertoire de stockage pour la conversation
    """
    base_dir = ensure_storage_directory()
    
    # Organiser par date (année/mois)
    now = datetime.now()
    date_path = os.path.join(str(now.year), f"{now.month:02d}")
    
    # Créer le chemin complet
    conversation_dir = os.path.join(base_dir, date_path, conversation_id)
    
    if not os.path.exists(conversation_dir):
        os.makedirs(conversation_dir, exist_ok=True)
        logger.debug(f"Répertoire de conversation créé: {conversation_dir}")
    
    return conversation_dir


def download_media_from_twilio(media_url: str, conversation_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Télécharge un média depuis Twilio et le stocke localement.
    
    Args:
        media_url: URL du média sur Twilio
        conversation_id: ID de la conversation
        
    Returns:
        Tuple[bool, Optional[str], Optional[str]]: (Succès, Chemin local, Message d'erreur)
    """
    try:
        # Récupérer les credentials Twilio
        account_sid = whatsapp_config.get('twilio', 'account_sid')
        auth_token = whatsapp_config.get('twilio', 'auth_token')
        
        # Télécharger le média avec authentification
        response = requests.get(
            media_url,
            auth=(account_sid, auth_token),
            timeout=30
        )
        
        if response.status_code != 200:
            error_msg = f"Échec du téléchargement du média: HTTP {response.status_code}"
            logger.error(error_msg)
            return False, None, error_msg
        
        # Déterminer l'extension du fichier
        content_type = response.headers.get('Content-Type', 'image/jpeg')
        extension = _get_extension_from_content_type(content_type)
        
        # Générer un nom de fichier unique
        filename = f"{uuid.uuid4().hex}{extension}"
        
        # Obtenir le répertoire de stockage
        storage_dir = get_conversation_media_dir(conversation_id)
        local_path = os.path.join(storage_dir, filename)
        
        # Sauvegarder le fichier
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Média téléchargé et stocké: {local_path}")
        return True, local_path, None
        
    except requests.exceptions.Timeout:
        error_msg = "Timeout lors du téléchargement du média"
        logger.error(error_msg)
        return False, None, error_msg
    except requests.exceptions.RequestException as e:
        error_msg = f"Erreur réseau lors du téléchargement du média: {e}"
        logger.error(error_msg)
        return False, None, error_msg
    except Exception as e:
        error_msg = f"Erreur lors du téléchargement du média: {e}"
        logger.error(error_msg)
        return False, None, error_msg


def download_multiple_media(media_urls: List[str], conversation_id: str) -> Tuple[List[str], List[str]]:
    """
    Télécharge plusieurs médias depuis Twilio.
    
    Args:
        media_urls: Liste des URLs des médias
        conversation_id: ID de la conversation
        
    Returns:
        Tuple[List[str], List[str]]: (Liste des chemins locaux, Liste des erreurs)
    """
    local_paths = []
    errors = []
    
    for media_url in media_urls:
        success, local_path, error = download_media_from_twilio(media_url, conversation_id)
        if success and local_path:
            local_paths.append(local_path)
        elif error:
            errors.append(error)
    
    return local_paths, errors


def _get_extension_from_content_type(content_type: str) -> str:
    """
    Retourne l'extension de fichier correspondant au type MIME.
    
    Args:
        content_type: Type MIME du fichier
        
    Returns:
        str: Extension du fichier (avec le point)
    """
    mime_to_ext = {
        'image/jpeg': '.jpg',
        'image/jpg': '.jpg',
        'image/png': '.png',
        'image/gif': '.gif',
        'image/webp': '.webp',
        'image/heic': '.heic',
        'image/heif': '.heif',
        'video/mp4': '.mp4',
        'video/3gpp': '.3gp',
        'audio/ogg': '.ogg',
        'audio/mpeg': '.mp3',
        'application/pdf': '.pdf',
    }
    
    # Extraire le type MIME de base (sans paramètres)
    base_type = content_type.split(';')[0].strip().lower()
    
    return mime_to_ext.get(base_type, '.bin')


def get_media_paths_for_conversation(conversation_id: str) -> List[str]:
    """
    Retourne la liste des chemins de médias pour une conversation.
    
    Args:
        conversation_id: ID de la conversation
        
    Returns:
        List[str]: Liste des chemins de fichiers médias
    """
    try:
        storage_dir = get_conversation_media_dir(conversation_id)
        
        if not os.path.exists(storage_dir):
            return []
        
        media_files = []
        for filename in os.listdir(storage_dir):
            filepath = os.path.join(storage_dir, filename)
            if os.path.isfile(filepath):
                media_files.append(filepath)
        
        return sorted(media_files)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des médias pour {conversation_id}: {e}")
        return []
