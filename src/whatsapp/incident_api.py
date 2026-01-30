"""
API d'intégration pour les incidents WhatsApp.

Ce module fournit des fonctions pour créer des incidents à partir des conversations WhatsApp
et gérer les erreurs d'API avec un mécanisme de retry via Celery.
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Tuple, Any, Optional, List, Union

from src.db.connection import DatabaseConnection
from src.db.incident_dao import IncidentDAO
from src.models.incident import Incident
from src.whatsapp import whatsapp_config
from src.whatsapp.models import ConversationState, PendingIncident

# Configuration du logger
logger = logging.getLogger('whatsapp.incident_api')


def create_incident_from_conversation(conversation: ConversationState, 
                                     db_connection: DatabaseConnection) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Crée un incident à partir d'une conversation WhatsApp.
    
    Args:
        conversation: L'état de la conversation
        db_connection: Connexion à la base de données
        
    Returns:
        Tuple[bool, Optional[str], Optional[str]]: (Succès, ID de l'incident ou None, Message d'erreur ou None)
    """
    try:
        # Construire les données de l'incident
        incident_data = build_incident_data(conversation)
        
        # Tenter d'importer l'incident
        success, incident_id, error_message = import_incident(incident_data, db_connection)
        
        if success:
            logger.info(f"Incident créé avec succès: {incident_id}")
            return True, incident_id, None
        else:
            logger.warning(f"Échec de création d'incident: {error_message}")
            
            # Classifier l'erreur
            if is_technical_error(error_message):
                # Erreur technique, créer un incident en attente pour retry
                pending_id = create_pending_incident(conversation.conversation_id, incident_data, 
                                                   error_message, db_connection)
                
                logger.info(f"Incident en attente créé: {pending_id}")
                
                # Informer l'utilisateur que l'incident sera traité plus tard
                return False, None, "Erreur technique temporaire. Votre incident a été enregistré et sera traité dès que possible."
            else:
                # Erreur fonctionnelle, informer l'utilisateur
                return False, None, f"Erreur: {error_message}"
    
    except Exception as e:
        logger.error(f"Erreur lors de la création d'incident: {e}")
        return False, None, f"Erreur système: {str(e)}"


def build_incident_data(conversation: ConversationState) -> Dict[str, Any]:
    """
    Construit les données d'incident à partir d'une conversation.
    
    Args:
        conversation: L'état de la conversation
        
    Returns:
        Dict[str, Any]: Les données de l'incident au format attendu par l'API
    """
    data = conversation.collected_data
    
    # Mapper la priorité WhatsApp vers la priorité d'incident
    priority_mapping = {
        'haute': 'HIGH',
        'moyenne': 'MEDIUM',
        'basse': 'LOW'
    }
    
    # Construire les données d'incident selon le schéma attendu
    # Le schéma requiert: zone, etage, categorie, type (en minuscules)
    incident_data = {
        "BUILDING_QR_CODE": conversation.building_qr_code,
        "INCIDENT_INFORMATION": {
            "zone": data.get('zone', ''),
            "etage": str(data.get('etage', '')),
            "categorie": data.get('categorie', ''),
            "type": data.get('categorie', ''),  # Utiliser la catégorie comme type par défaut
            "informations_supplementaires": data.get('informations', '')
        }
    }
    
    # Ajouter le téléphone du reporter si disponible
    if conversation.user_phone:
        incident_data["REPORTER_PHONE"] = conversation.user_phone
    
    return incident_data


def import_incident(incident_data: Dict[str, Any], 
                   db_connection: Optional[DatabaseConnection] = None) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Importe un incident via l'API d'import.
    
    Args:
        incident_data: Les données de l'incident
        db_connection: Connexion à la base de données (optionnel)
        
    Returns:
        Tuple[bool, Optional[str], Optional[str]]: (Succès, ID de l'incident ou None, Message d'erreur ou None)
    """
    try:
        # Créer l'incident via l'API existante
        incident_dao = IncidentDAO()
        
        # Créer un objet Incident à partir des données
        incident = Incident.from_json(incident_data)
        
        # Sauvegarder l'incident
        incident_id = incident_dao.create_incident(incident)
        
        if incident_id:
            return True, incident_id, None
        else:
            return False, None, "Échec de création de l'incident dans la base de données"
    
    except Exception as e:
        logger.error(f"Erreur lors de l'import d'incident: {e}")
        return False, None, str(e)


def is_technical_error(error_message: str) -> bool:
    """
    Détermine si une erreur est technique (temporaire) ou fonctionnelle (permanente).
    
    Args:
        error_message: Le message d'erreur
        
    Returns:
        bool: True si l'erreur est technique, False sinon
    """
    # Liste de mots-clés indiquant une erreur technique
    technical_keywords = [
        'connexion', 'connection', 'timeout', 'délai', 'database', 'base de données',
        'serveur', 'server', 'indisponible', 'unavailable', 'temporaire', 'temporary',
        'retry', 'réessayer', 'réseau', 'network', 'erreur interne', 'internal error'
    ]
    
    # Vérifier si le message d'erreur contient un mot-clé technique
    for keyword in technical_keywords:
        if keyword.lower() in error_message.lower():
            return True
    
    return False


def create_pending_incident(conversation_id: str, incident_data: Dict[str, Any], 
                           error_message: str, db_connection: DatabaseConnection) -> str:
    """
    Crée un incident en attente pour retry ultérieur.
    
    Args:
        conversation_id: ID de la conversation
        incident_data: Données de l'incident
        error_message: Message d'erreur
        db_connection: Connexion à la base de données
        
    Returns:
        str: ID de l'incident en attente
    """
    # Créer un nouvel ID pour l'incident en attente
    pending_id = f"pending_{str(uuid.uuid4())}"
    
    # Calculer la date de la prochaine tentative
    retry_delay = whatsapp_config.getint('conversation', 'retry_delay', fallback=300)  # 5 minutes par défaut
    next_retry = datetime.now() + timedelta(seconds=retry_delay)
    
    # Créer l'incident en attente
    pending_incident = PendingIncident(
        id=pending_id,
        conversation_id=conversation_id,
        incident_data=incident_data,
        error_message=error_message,
        retry_count=0,
        next_retry=next_retry
    )
    
    # Sauvegarder l'incident en attente
    pending_incident.save(db_connection)
    
    # Planifier la tâche de retry
    from src.whatsapp.tasks import retry_import_incident
    retry_import_incident.apply_async(args=[pending_id], eta=next_retry)
    
    return pending_id


def get_pending_incidents_count() -> int:
    """
    Récupère le nombre d'incidents en attente.
    
    Returns:
        int: Nombre d'incidents en attente
    """
    try:
        db_connection = DatabaseConnection()
        
        query = """
            SELECT COUNT(*) FROM pending_incidents
        """
        result = db_connection.execute_query(query, fetch_one=True)
        
        return result[0] if result else 0
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du nombre d'incidents en attente: {e}")
        return 0


def get_incident_creation_success_rate(days: int = 7) -> float:
    """
    Calcule le taux de réussite de création d'incidents sur une période donnée.
    
    Args:
        days: Nombre de jours à considérer
        
    Returns:
        float: Taux de réussite (0-100)
    """
    try:
        db_connection = DatabaseConnection()
        
        # Calculer la date limite
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Compter les conversations complétées
        query_completed = """
            SELECT COUNT(*) FROM whatsapp_conversations
            WHERE is_completed = TRUE AND updated_at >= %s
        """
        completed_count = db_connection.execute_query(query_completed, (cutoff_date,), fetch_one=True)
        
        # Compter les incidents créés avec succès (source = WHATSAPP)
        query_incidents = """
            SELECT COUNT(*) FROM t_incident
            WHERE incident_information->>'SOURCE' = 'WHATSAPP' AND creation_date >= %s
        """
        incidents_count = db_connection.execute_query(query_incidents, (cutoff_date,), fetch_one=True)
        
        # Calculer le taux de réussite
        if completed_count and completed_count[0] > 0:
            success_rate = (incidents_count[0] / completed_count[0]) * 100
            return success_rate
        else:
            return 0.0
    
    except Exception as e:
        logger.error(f"Erreur lors du calcul du taux de réussite de création d'incidents: {e}")
        return 0.0
