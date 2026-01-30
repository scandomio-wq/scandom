"""
Gestion de la rétention et de l'anonymisation des données WhatsApp.

Ce module implémente les tâches périodiques pour la purge et l'anonymisation
des données conformément aux politiques de rétention définies.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from src.db.connection import DatabaseConnection
from src.whatsapp import whatsapp_config
from src.whatsapp.state_manager import StateManager

# Configuration du logger
logger = logging.getLogger('whatsapp.data_retention')


def purge_expired_conversations(db_connection: DatabaseConnection) -> int:
    """
    Purge les conversations expirées selon la politique de rétention.
    
    Args:
        db_connection: Connexion à la base de données
        
    Returns:
        int: Nombre de conversations purgées
    """
    try:
        # Récupérer la durée de rétention depuis la configuration
        retention_months = int(whatsapp_config.get('retention', 'conversation_retention_months', fallback='12'))
        
        # Calculer la date limite
        cutoff_date = datetime.now() - timedelta(days=retention_months * 30)
        
        # Purger les conversations expirées
        query = """
            DELETE FROM whatsapp_conversations
            WHERE updated_at < %s
            RETURNING id
        """
        result = db_connection.execute_query(query, (cutoff_date,), fetch_all=True)
        
        purged_count = len(result) if result else 0
        logger.info(f"{purged_count} conversations expirées purgées")
        
        return purged_count
    
    except Exception as e:
        logger.error(f"Erreur lors de la purge des conversations expirées: {e}")
        return 0


def anonymize_old_conversations(db_connection: DatabaseConnection) -> int:
    """
    Anonymise les conversations anciennes selon la politique de rétention.
    
    Args:
        db_connection: Connexion à la base de données
        
    Returns:
        int: Nombre de conversations anonymisées
    """
    try:
        # Récupérer la durée avant anonymisation depuis la configuration
        anonymize_months = int(whatsapp_config.get('retention', 'anonymize_after_months', fallback='6'))
        
        # Calculer la date limite
        cutoff_date = datetime.now() - timedelta(days=anonymize_months * 30)
        
        # Anonymiser les conversations
        query = """
            UPDATE whatsapp_conversations
            SET from_phone = 'anonymized',
                collected_data = jsonb_set(
                    collected_data,
                    '{reporter_phone}',
                    '"anonymized"'
                ),
                collected_data = jsonb_set(
                    collected_data,
                    '{reporter_email}',
                    '"anonymized"'
                ),
                is_anonymized = TRUE
            WHERE updated_at < %s
            AND is_anonymized = FALSE
            RETURNING id
        """
        result = db_connection.execute_query(query, (cutoff_date,), fetch_all=True)
        
        anonymized_count = len(result) if result else 0
        logger.info(f"{anonymized_count} conversations anonymisées")
        
        return anonymized_count
    
    except Exception as e:
        logger.error(f"Erreur lors de l'anonymisation des conversations: {e}")
        return 0


def purge_old_messages(db_connection: DatabaseConnection) -> int:
    """
    Purge les messages anciens selon la politique de rétention.
    
    Args:
        db_connection: Connexion à la base de données
        
    Returns:
        int: Nombre de messages purgés
    """
    try:
        # Récupérer la durée de rétention depuis la configuration
        retention_months = int(whatsapp_config.get('retention', 'message_retention_months', fallback='12'))
        
        # Calculer la date limite
        cutoff_date = datetime.now() - timedelta(days=retention_months * 30)
        
        # Purger les messages expirés
        query = """
            DELETE FROM whatsapp_messages
            WHERE created_at < %s
            RETURNING id
        """
        result = db_connection.execute_query(query, (cutoff_date,), fetch_all=True)
        
        purged_count = len(result) if result else 0
        logger.info(f"{purged_count} messages expirés purgés")
        
        return purged_count
    
    except Exception as e:
        logger.error(f"Erreur lors de la purge des messages expirés: {e}")
        return 0


def purge_resolved_pending_incidents(db_connection: DatabaseConnection) -> int:
    """
    Purge les incidents en attente résolus.
    
    Args:
        db_connection: Connexion à la base de données
        
    Returns:
        int: Nombre d'incidents en attente purgés
    """
    try:
        # Récupérer la durée de rétention depuis la configuration
        retention_days = int(whatsapp_config.get('retention', 'pending_incident_retention_days', fallback='30'))
        
        # Calculer la date limite
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        # Purger les incidents en attente résolus
        query = """
            DELETE FROM pending_incidents
            WHERE (is_resolved = TRUE OR retry_count >= max_retries)
            AND updated_at < %s
            RETURNING id
        """
        result = db_connection.execute_query(query, (cutoff_date,), fetch_all=True)
        
        purged_count = len(result) if result else 0
        logger.info(f"{purged_count} incidents en attente résolus purgés")
        
        return purged_count
    
    except Exception as e:
        logger.error(f"Erreur lors de la purge des incidents en attente résolus: {e}")
        return 0


def run_data_retention_tasks() -> Dict[str, int]:
    """
    Exécute toutes les tâches de rétention de données.
    
    Returns:
        Dict[str, int]: Statistiques des opérations effectuées
    """
    db_connection = DatabaseConnection()
    
    stats = {
        'conversations_purged': purge_expired_conversations(db_connection),
        'conversations_anonymized': anonymize_old_conversations(db_connection),
        'messages_purged': purge_old_messages(db_connection),
        'pending_incidents_purged': purge_resolved_pending_incidents(db_connection)
    }
    
    logger.info(f"Tâches de rétention de données exécutées: {stats}")
    
    return stats


def get_data_retention_stats(db_connection: DatabaseConnection) -> Dict[str, Any]:
    """
    Récupère des statistiques sur les données stockées.
    
    Args:
        db_connection: Connexion à la base de données
        
    Returns:
        Dict[str, Any]: Statistiques sur les données
    """
    try:
        stats = {}
        
        # Compter les conversations
        query_conversations = "SELECT COUNT(*) FROM whatsapp_conversations"
        result = db_connection.execute_query(query_conversations, fetch_one=True)
        stats['total_conversations'] = result[0] if result else 0
        
        # Compter les conversations anonymisées
        query_anonymized = "SELECT COUNT(*) FROM whatsapp_conversations WHERE is_anonymized = TRUE"
        result = db_connection.execute_query(query_anonymized, fetch_one=True)
        stats['anonymized_conversations'] = result[0] if result else 0
        
        # Compter les messages
        query_messages = "SELECT COUNT(*) FROM whatsapp_messages"
        result = db_connection.execute_query(query_messages, fetch_one=True)
        stats['total_messages'] = result[0] if result else 0
        
        # Compter les incidents en attente
        query_pending = "SELECT COUNT(*) FROM pending_incidents"
        result = db_connection.execute_query(query_pending, fetch_one=True)
        stats['pending_incidents'] = result[0] if result else 0
        
        # Compter les incidents en attente résolus
        query_resolved = "SELECT COUNT(*) FROM pending_incidents WHERE is_resolved = TRUE"
        result = db_connection.execute_query(query_resolved, fetch_one=True)
        stats['resolved_pending_incidents'] = result[0] if result else 0
        
        return stats
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques de rétention: {e}")
        return {
            'error': str(e)
        }
