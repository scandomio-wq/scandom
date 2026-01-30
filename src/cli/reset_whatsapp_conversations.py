#!/usr/bin/env python3
"""
Script pour réinitialiser les conversations WhatsApp dans Redis.
"""

import argparse
import logging
import sys

from src.whatsapp import redis_client
from src.whatsapp.state_manager import StateManager
from src.db.connection import get_db_connection

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """
    Parse les arguments de la ligne de commande.
    
    Returns:
        Arguments parsés.
    """
    parser = argparse.ArgumentParser(description="Réinitialise les conversations WhatsApp dans Redis et/ou la base de données.")
    
    parser.add_argument(
        "--phone",
        help="Numéro de téléphone spécifique à réinitialiser (optionnel)"
    )
    
    parser.add_argument(
        "--redis-only",
        action="store_true",
        help="Réinitialise uniquement les conversations dans Redis (pas la base de données)"
    )
    
    parser.add_argument(
        "--db-only",
        action="store_true",
        help="Réinitialise uniquement les conversations dans la base de données (pas Redis)"
    )
    
    return parser.parse_args()


def reset_redis_conversations(phone=None):
    """
    Réinitialise les conversations WhatsApp dans Redis.
    
    Args:
        phone: Numéro de téléphone spécifique à réinitialiser (optionnel)
        
    Returns:
        int: Nombre de conversations réinitialisées
    """
    state_manager = StateManager(redis_client)
    pattern = f"{state_manager.key_prefix}*"
    all_keys = redis_client.keys(pattern)
    count = 0
    
    for key in all_keys:
        state_json = redis_client.get(key)
        if state_json:
            try:
                # Si un numéro de téléphone est spécifié, vérifier s'il correspond
                if phone:
                    from src.whatsapp.models import ConversationState
                    state = ConversationState.from_json(state_json)
                    if state.user_phone != phone:
                        continue
                
                # Supprimer la clé
                redis_client.delete(key)
                count += 1
                logger.info(f"Conversation {key} supprimée de Redis")
            except Exception as e:
                logger.error(f"Erreur lors de la suppression de la conversation {key}: {e}")
    
    return count


def reset_db_conversations(phone=None):
    """
    Réinitialise les conversations WhatsApp dans la base de données.
    
    Args:
        phone: Numéro de téléphone spécifique à réinitialiser (optionnel)
        
    Returns:
        int: Nombre de conversations réinitialisées
    """
    db_connection = get_db_connection()
    
    try:
        if phone:
            # Supprimer les conversations pour un numéro de téléphone spécifique
            query = "DELETE FROM whatsapp_conversations WHERE user_phone = %s"
            result = db_connection.execute_query(query, (phone,))
            logger.info(f"Conversations pour le numéro {phone} supprimées de la base de données")
        else:
            # Supprimer toutes les conversations
            query = "DELETE FROM whatsapp_conversations"
            result = db_connection.execute_query(query)
            logger.info("Toutes les conversations supprimées de la base de données")
        
        return 1  # Succès
    except Exception as e:
        logger.error(f"Erreur lors de la suppression des conversations de la base de données: {e}")
        return 0


def main():
    """Fonction principale."""
    try:
        # Parser les arguments
        args = parse_arguments()
        
        redis_count = 0
        db_count = 0
        
        # Réinitialiser les conversations dans Redis si demandé
        if not args.db_only:
            redis_count = reset_redis_conversations(args.phone)
        
        # Réinitialiser les conversations dans la base de données si demandé
        if not args.redis_only:
            db_count = reset_db_conversations(args.phone)
        
        logger.info(f"Réinitialisation terminée. {redis_count} conversation(s) supprimée(s) de Redis, {db_count} opération(s) effectuée(s) dans la base de données.")
        sys.exit(0)
            
    except Exception as e:
        logger.error(f"Erreur: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
