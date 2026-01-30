"""
Gestionnaire d'état Redis pour les conversations WhatsApp.

Ce module fournit une classe pour gérer la persistance des états de conversation
dans Redis, avec un TTL configurable pour les conversations inactives.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

from redis import Redis

from src.whatsapp.models import ConversationState, ConversationStep

# Configuration du logger
logger = logging.getLogger('whatsapp.state_manager')


class StateManager:
    """
    Gestionnaire d'état Redis pour les conversations WhatsApp.
    
    Cette classe gère la persistance des états de conversation dans Redis,
    avec un TTL configurable pour les conversations inactives.
    
    Attributes:
        redis_client (Redis): Client Redis pour la persistance des états
        ttl (int): Durée de vie en secondes des états de conversation (24h par défaut)
        key_prefix (str): Préfixe pour les clés Redis des états de conversation
    """
    
    def __init__(self, redis_client: Redis, ttl: int = 86400, key_prefix: str = 'whatsapp:conversation:'):
        """
        Initialise le gestionnaire d'état.
        
        Args:
            redis_client: Client Redis pour la persistance des états
            ttl: Durée de vie en secondes des états de conversation (24h par défaut)
            key_prefix: Préfixe pour les clés Redis des états de conversation
        """
        self.redis_client = redis_client
        self.ttl = ttl
        self.key_prefix = key_prefix
        logger.info(f"StateManager initialisé avec TTL={ttl}s")
    
    def _get_key(self, conversation_id: str) -> str:
        """
        Génère la clé Redis pour un état de conversation.
        
        Args:
            conversation_id: ID de la conversation
            
        Returns:
            str: Clé Redis pour l'état de conversation
        """
        return f"{self.key_prefix}{conversation_id}"
    
    def save_state(self, state: ConversationState) -> bool:
        """
        Sauvegarde un état de conversation dans Redis.
        
        Args:
            state: État de conversation à sauvegarder
            
        Returns:
            bool: True si la sauvegarde a réussi, False sinon
        """
        try:
            key = self._get_key(state.conversation_id)
            state_json = state.to_json()
            self.redis_client.set(key, state_json, ex=self.ttl)
            logger.debug(f"État de conversation {state.conversation_id} sauvegardé dans Redis")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de l'état de conversation {state.conversation_id}: {e}")
            return False
    
    def get_state(self, conversation_id: str) -> Optional[ConversationState]:
        """
        Récupère un état de conversation depuis Redis.
        
        Args:
            conversation_id: ID de la conversation
            
        Returns:
            Optional[ConversationState]: L'état de conversation ou None si non trouvé
        """
        try:
            key = self._get_key(conversation_id)
            state_json = self.redis_client.get(key)
            
            if state_json:
                # Rafraîchir le TTL
                self.redis_client.expire(key, self.ttl)
                logger.debug(f"État de conversation {conversation_id} récupéré depuis Redis")
                return ConversationState.from_json(state_json)
            else:
                logger.debug(f"Aucun état de conversation trouvé pour {conversation_id}")
                return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'état de conversation {conversation_id}: {e}")
            return None
    
    def get_state_by_user_and_building(self, user_phone: str, building_qr_code: str) -> Optional[ConversationState]:
        """
        Récupère un état de conversation par utilisateur et bâtiment.
        
        Args:
            user_phone: Numéro de téléphone de l'utilisateur
            building_qr_code: QR code du bâtiment
            
        Returns:
            Optional[ConversationState]: L'état de conversation ou None si non trouvé
        """
        try:
            # Recherche par pattern pour trouver toutes les conversations
            pattern = f"{self.key_prefix}*"
            all_keys = self.redis_client.keys(pattern)
            
            for key in all_keys:
                state_json = self.redis_client.get(key)
                if state_json:
                    state = ConversationState.from_json(state_json)
                    if (state.user_phone == user_phone and 
                        state.building_qr_code == building_qr_code and 
                        not state.is_completed):
                        # Rafraîchir le TTL
                        self.redis_client.expire(key, self.ttl)
                        logger.debug(f"État de conversation trouvé pour {user_phone} et {building_qr_code}")
                        return state
            
            logger.debug(f"Aucun état de conversation actif trouvé pour {user_phone} et {building_qr_code}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la recherche d'état de conversation pour {user_phone} et {building_qr_code}: {e}")
            return None
    
    def delete_state(self, conversation_id: str) -> bool:
        """
        Supprime un état de conversation de Redis.
        
        Args:
            conversation_id: ID de la conversation
            
        Returns:
            bool: True si la suppression a réussi, False sinon
        """
        try:
            key = self._get_key(conversation_id)
            result = self.redis_client.delete(key)
            if result > 0:
                logger.debug(f"État de conversation {conversation_id} supprimé de Redis")
                return True
            else:
                logger.debug(f"Aucun état de conversation trouvé pour suppression: {conversation_id}")
                return False
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de l'état de conversation {conversation_id}: {e}")
            return False
    
    def update_state(self, conversation_id: str, 
                     step: Optional[ConversationStep] = None, 
                     data_updates: Optional[Dict[str, Any]] = None) -> Optional[ConversationState]:
        """
        Met à jour un état de conversation dans Redis.
        
        Args:
            conversation_id: ID de la conversation
            step: Nouvelle étape de la conversation (si None, l'étape n'est pas modifiée)
            data_updates: Mises à jour des données collectées (si None, les données ne sont pas modifiées)
            
        Returns:
            Optional[ConversationState]: L'état de conversation mis à jour ou None si non trouvé
        """
        state = self.get_state(conversation_id)
        if not state:
            logger.warning(f"Tentative de mise à jour d'un état de conversation inexistant: {conversation_id}")
            return None
        
        if step:
            state.update_step(step)
        
        if data_updates:
            for key, value in data_updates.items():
                state.add_data(key, value)
        
        if self.save_state(state):
            return state
        else:
            return None
    
    def complete_conversation(self, conversation_id: str) -> Optional[ConversationState]:
        """
        Marque une conversation comme terminée dans Redis.
        
        Args:
            conversation_id: ID de la conversation
            
        Returns:
            Optional[ConversationState]: L'état de conversation mis à jour ou None si non trouvé
        """
        state = self.get_state(conversation_id)
        if not state:
            logger.warning(f"Tentative de complétion d'un état de conversation inexistant: {conversation_id}")
            return None
        
        state.complete()
        
        if self.save_state(state):
            return state
        else:
            return None
    
    def create_new_conversation(self, user_phone: str, building_qr_code: str) -> ConversationState:
        """
        Crée un nouvel état de conversation dans Redis.
        
        Args:
            user_phone: Numéro de téléphone de l'utilisateur
            building_qr_code: QR code du bâtiment
            
        Returns:
            ConversationState: Le nouvel état de conversation
        """
        # Vérifier s'il existe déjà une conversation active pour cet utilisateur et ce bâtiment
        existing_state = self.get_state_by_user_and_building(user_phone, building_qr_code)
        if existing_state:
            logger.info(f"Conversation existante trouvée pour {user_phone} et {building_qr_code}, réutilisation")
            return existing_state
        
        # Créer un nouvel état de conversation
        state = ConversationState(
            user_phone=user_phone,
            building_qr_code=building_qr_code,
            current_step=ConversationStep.INITIATION
        )
        
        if self.save_state(state):
            logger.info(f"Nouvelle conversation créée pour {user_phone} et {building_qr_code}: {state.conversation_id}")
            return state
        else:
            logger.error(f"Erreur lors de la création d'une nouvelle conversation pour {user_phone} et {building_qr_code}")
            # En cas d'erreur, on retourne quand même l'état créé
            return state
    
    def get_expired_conversations(self, hours: int = 24) -> List[str]:
        """
        Récupère les IDs des conversations expirées (inactives depuis plus de X heures).
        
        Args:
            hours: Nombre d'heures d'inactivité pour considérer une conversation comme expirée
            
        Returns:
            List[str]: Liste des IDs des conversations expirées
        """
        try:
            # Recherche par pattern pour trouver toutes les conversations
            pattern = f"{self.key_prefix}*"
            all_keys = self.redis_client.keys(pattern)
            expired_ids = []
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            for key in all_keys:
                state_json = self.redis_client.get(key)
                if state_json:
                    state = ConversationState.from_json(state_json)
                    if state.last_activity < cutoff_time and not state.is_completed:
                        conversation_id = key.decode('utf-8').replace(self.key_prefix, '')
                        expired_ids.append(conversation_id)
            
            return expired_ids
        except Exception as e:
            logger.error(f"Erreur lors de la recherche des conversations expirées: {e}")
            return []
    
    def cleanup_expired_conversations(self, hours: int = 24) -> int:
        """
        Nettoie les conversations expirées (inactives depuis plus de X heures).
        
        Args:
            hours: Nombre d'heures d'inactivité pour considérer une conversation comme expirée
            
        Returns:
            int: Nombre de conversations supprimées
        """
        expired_ids = self.get_expired_conversations(hours)
        count = 0
        
        for conversation_id in expired_ids:
            if self.delete_state(conversation_id):
                count += 1
        
        if count > 0:
            logger.info(f"{count} conversations expirées ont été supprimées")
        
        return count
        
    def get_conversation_by_phone(self, user_phone: str) -> Optional[ConversationState]:
        """
        Récupère une conversation active par numéro de téléphone.
        
        Args:
            user_phone: Numéro de téléphone de l'utilisateur
            
        Returns:
            Optional[ConversationState]: L'état de conversation ou None si non trouvé
        """
        try:
            # Recherche par pattern pour trouver toutes les conversations
            pattern = f"{self.key_prefix}*"
            all_keys = self.redis_client.keys(pattern)
            
            # Trier les clés par date de dernière activité (la plus récente d'abord)
            conversations = []
            
            for key in all_keys:
                state_json = self.redis_client.get(key)
                if state_json:
                    state = ConversationState.from_json(state_json)
                    if state.user_phone == user_phone and not state.is_completed:
                        conversations.append(state)
            
            # Trier par date de dernière activité (la plus récente d'abord)
            if conversations:
                conversations.sort(key=lambda x: x.last_activity, reverse=True)
                # Rafraîchir le TTL
                self.redis_client.expire(self._get_key(conversations[0].conversation_id), self.ttl)
                logger.debug(f"Conversation active trouvée pour {user_phone}")
                return conversations[0]
            
            logger.debug(f"Aucune conversation active trouvée pour {user_phone}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de conversation pour {user_phone}: {e}")
            return None
            
    def save_conversation(self, conversation: ConversationState) -> bool:
        """
        Sauvegarde une conversation dans Redis.
        
        Args:
            conversation: Conversation à sauvegarder
            
        Returns:
            bool: True si la sauvegarde a réussi, False sinon
        """
        return self.save_state(conversation)
        
    def update_conversation(self, conversation: ConversationState) -> bool:
        """
        Met à jour une conversation dans Redis.
        
        Args:
            conversation: Conversation à mettre à jour
            
        Returns:
            bool: True si la mise à jour a réussi, False sinon
        """
        return self.save_state(conversation)
    
    def delete_conversation(self, user_phone: str) -> bool:
        """
        Supprime toutes les conversations d'un utilisateur par numéro de téléphone.
        
        Args:
            user_phone: Numéro de téléphone de l'utilisateur
            
        Returns:
            bool: True si au moins une conversation a été supprimée, False sinon
        """
        try:
            # Recherche par pattern pour trouver toutes les conversations
            pattern = f"{self.key_prefix}*"
            all_keys = self.redis_client.keys(pattern)
            deleted = False
            
            for key in all_keys:
                state_json = self.redis_client.get(key)
                if state_json:
                    state = ConversationState.from_json(state_json)
                    if state.user_phone == user_phone:
                        self.redis_client.delete(key)
                        logger.info(f"Conversation {state.conversation_id} supprimée pour {user_phone}")
                        deleted = True
            
            return deleted
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des conversations pour {user_phone}: {e}")
            return False
