"""
Configuration Celery pour les tâches asynchrones de l'intégration WhatsApp.

Ce module configure Celery pour gérer les tâches asynchrones, notamment :
- Les retries des appels API d'import d'incident en cas d'erreur technique
- La purge des données selon la politique de rétention
- Les tâches périodiques de maintenance
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

from celery import Celery
from celery.schedules import crontab

from src.db.connection import DatabaseConnection
from src.whatsapp.models import PendingIncident
from src.whatsapp import whatsapp_config
from src.whatsapp.data_retention import run_data_retention_tasks

# Configuration du logger
logger = logging.getLogger('whatsapp.tasks')

# Configuration de Celery
broker_url = whatsapp_config.get('celery', 'broker_url', fallback='redis://localhost:6379/0')
result_backend = whatsapp_config.get('celery', 'result_backend', fallback='redis://localhost:6379/0')

celery_app = Celery('whatsapp_tasks', broker=broker_url, backend=result_backend)
celery_app.conf.include = ['src.email.tasks']

# Configuration des options Celery depuis le fichier de configuration
celery_app.conf.update(
    task_serializer=whatsapp_config.get('celery', 'task_serializer', fallback='json'),
    accept_content=json.loads(whatsapp_config.get('celery', 'accept_content', fallback='["json"]')),
    result_serializer=whatsapp_config.get('celery', 'result_serializer', fallback='json'),
    timezone=whatsapp_config.get('celery', 'timezone', fallback='Europe/Paris'),
    enable_utc=whatsapp_config.getboolean('celery', 'enable_utc', fallback=True),
    worker_concurrency=whatsapp_config.getint('celery', 'worker_concurrency', fallback=4),
    task_acks_late=whatsapp_config.getboolean('celery', 'task_acks_late', fallback=True),
    task_reject_on_worker_lost=whatsapp_config.getboolean('celery', 'task_reject_on_worker_lost', fallback=True)
)

# Configuration des tâches périodiques
celery_app.conf.beat_schedule = {
    'retry-pending-incidents-every-5-minutes': {
        'task': 'src.whatsapp.tasks.retry_pending_incidents',
        'schedule': 300.0,  # 5 minutes
    },
    'cleanup-expired-conversations-daily': {
        'task': 'src.whatsapp.tasks.cleanup_expired_conversations',
        'schedule': crontab(hour=3, minute=0),  # 3h00 du matin
    },
    'purge-old-data-monthly': {
        'task': 'whatsapp.purge_old_data',
        'schedule': crontab(day_of_month=1, hour=2, minute=0),  # 1er du mois à 2h00
    },
}


@celery_app.task(bind=True, max_retries=None)
def retry_pending_incidents(self) -> Dict[str, Any]:
    """
    Tâche périodique pour réessayer les incidents en attente.
    
    Returns:
        Dict[str, Any]: Résultats de l'opération
    """
    logger.info("Démarrage de la tâche de retry des incidents en attente")
    
    try:
        db_connection = DatabaseConnection()
        
        # Récupérer les incidents en attente
        pending_incidents = PendingIncident.get_pending_retries(db_connection)
        
        results = {
            'total': len(pending_incidents),
            'success': 0,
            'failure': 0,
            'max_retries_reached': 0
        }
        
        max_retries = whatsapp_config.getint('conversation', 'max_retries', fallback=5)
        
        for incident in pending_incidents:
            # Vérifier si le nombre maximum de tentatives est atteint
            if incident.retry_count >= max_retries:
                logger.warning(f"Nombre maximum de tentatives atteint pour l'incident {incident.id}, "
                              f"abandon après {incident.retry_count} tentatives")
                incident.delete(db_connection)
                results['max_retries_reached'] += 1
                continue
            
            # Tenter d'envoyer l'incident à l'API
            success = retry_import_incident.delay(incident.id)
            
            if success:
                results['success'] += 1
            else:
                results['failure'] += 1
        
        logger.info(f"Tâche de retry terminée: {results}")
        return results
    
    except Exception as e:
        logger.error(f"Erreur lors de la tâche de retry des incidents en attente: {e}")
        return {'error': str(e)}


@celery_app.task(bind=True, max_retries=None)
def retry_import_incident(self, incident_id: str) -> bool:
    """
    Tâche pour réessayer l'import d'un incident spécifique.
    
    Args:
        incident_id: ID de l'incident en attente
        
    Returns:
        bool: True si l'import a réussi, False sinon
    """
    logger.info(f"Tentative d'import de l'incident en attente {incident_id}")
    
    try:
        db_connection = DatabaseConnection()
        
        # Récupérer l'incident en attente
        incident = PendingIncident.get_by_id(db_connection, incident_id)
        
        if not incident:
            logger.warning(f"Incident en attente {incident_id} non trouvé")
            return False
        
        # Importer l'incident via l'API
        from src.whatsapp.incident_api import import_incident
        
        success, incident, error_message = import_incident(incident.incident_data)
        
        if success and incident:
            # 1. Supprimer l'incident en attente
            incident_id_str = incident.id # keep reference before delete
            incident_qr = incident.qr_code_number
            incident.delete(db_connection)
            logger.info(f"Import réussi pour l'incident en attente {incident_id}")

            # 2. Déclencher la notification email
            try:
                from src.db.building_dao import BuildingDAO
                from src.email.tasks import send_incident_email_task
                
                building_dao = BuildingDAO()
                building = building_dao.get_building_by_qr_code(incident.building_qr_code)
                
                if building and building.email_gestionnaire:
                    # Préparer les données pour le template (même logique que dans conversation_manager)
                    collected_data = incident.incident_information
                    incident_data = {
                        "zone": collected_data.get('zone', 'N/A'),
                        "floor": str(collected_data.get('etage', 'N/A')),
                        "category": collected_data.get('categorie', 'N/A'),
                        "description": collected_data.get('informations_supplementaires', 'Pas de description'),
                        "photo_urls": [], # On n'a pas les URLs ici facilement si non stockées
                        "reporter_phone": incident.reporter_phone,
                        "created_at": incident.creation_date.strftime('%d/%m/%Y %H:%M') if incident.creation_date else datetime.now().strftime('%d/%m/%Y %H:%M')
                    }
                    
                    send_incident_email_task.delay(
                        incident_id=incident.id,
                        incident_qr_code=incident.qr_code_number,
                        building_address=building.location,
                        manager_email=building.email_gestionnaire,
                        incident_data=incident_data
                    )
                    logger.info(f"Notification email planifiée après retry réussi pour l'incident {incident.qr_code_number}")
            except Exception as e:
                logger.error(f"Erreur lors du dispatch de l'email après retry: {e}")

            return True
        else:
            # Incrémenter le compteur de tentatives et planifier la prochaine tentative
            incident.error_message = error_message
            incident.increment_retry(
                backoff_factor=float(whatsapp_config.get('conversation', 'backoff_factor', fallback=2.0)),
                base_delay=int(whatsapp_config.get('conversation', 'retry_delay', fallback=300))
            )
            incident.save(db_connection)
            
            logger.warning(f"Échec de l'import pour l'incident en attente {incident_id}, "
                          f"prochaine tentative: {incident.next_retry}, "
                          f"tentatives: {incident.retry_count}/{whatsapp_config.getint('conversation', 'max_retries', fallback=5)}")
            return False
    
    except Exception as e:
        logger.error(f"Erreur lors de la tentative d'import de l'incident en attente {incident_id}: {e}")
        return False


@celery_app.task(bind=True)
def cleanup_expired_conversations(self) -> Dict[str, Any]:
    """
    Tâche périodique pour nettoyer les conversations expirées dans Redis.
    
    Returns:
        Dict[str, Any]: Résultats de l'opération
    """
    logger.info("Démarrage de la tâche de nettoyage des conversations expirées")
    
    try:
        from src.whatsapp import redis_client
        from src.whatsapp.state_manager import StateManager
        
        ttl = whatsapp_config.getint('redis', 'ttl', fallback=86400)
        state_manager = StateManager(redis_client, ttl=ttl)
        
        # Nettoyer les conversations expirées
        count = state_manager.cleanup_expired_conversations(hours=24)
        
        logger.info(f"Tâche de nettoyage terminée: {count} conversations expirées supprimées")
        return {'cleaned': count}
    
    except Exception as e:
        logger.error(f"Erreur lors de la tâche de nettoyage des conversations expirées: {e}")
        return {'error': str(e)}


@celery_app.task(name='whatsapp.purge_old_data')
def purge_old_data():
    """
    Tâche périodique pour purger les anciennes données.
    """
    logger.info("Exécution de la tâche de purge des anciennes données")
    stats = run_data_retention_tasks()
    
    return stats


@celery_app.task(bind=True)
def send_whatsapp_message(self, to: str, message: str, media_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Tâche pour envoyer un message WhatsApp via Twilio.
    
    Args:
        to: Numéro de téléphone du destinataire
        message: Contenu du message
        media_url: URL du média à joindre (optionnel)
        
    Returns:
        Dict[str, Any]: Résultat de l'envoi
    """
    logger.info(f"Envoi d'un message WhatsApp à {to}")
    
    try:
        from src.whatsapp import twilio_client
        
        whatsapp_number = whatsapp_config.get('twilio', 'whatsapp_number')
        
        # Formater les numéros pour WhatsApp
        from_whatsapp = f"whatsapp:{whatsapp_number}"
        to_whatsapp = f"whatsapp:{to}"
        
        # Envoyer le message
        if media_url:
            message = twilio_client.messages.create(
                from_=from_whatsapp,
                to=to_whatsapp,
                body=message,
                media_url=[media_url]
            )
        else:
            message = twilio_client.messages.create(
                from_=from_whatsapp,
                to=to_whatsapp,
                body=message
            )
        
        logger.info(f"Message WhatsApp envoyé à {to}, SID: {message.sid}")
        return {
            'success': True,
            'message_sid': message.sid,
            'status': message.status
        }
    
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du message WhatsApp à {to}: {e}")
        return {
            'success': False,
            'error': str(e)
        }
