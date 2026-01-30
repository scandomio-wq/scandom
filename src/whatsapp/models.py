"""
Modèles de données PostgreSQL pour les conversations et messages WhatsApp.

Ce module définit les classes de modèles pour les entités suivantes :
- ConversationState : État d'une conversation WhatsApp
- WhatsAppMessage : Message échangé dans une conversation
- PendingIncident : Incident en attente de traitement suite à une erreur technique
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union

from src.db.connection import DatabaseConnection
from src.utils.validators import validate_email, validate_qr_code_number


class MessageDirection(Enum):
    """Énumération pour la direction des messages."""
    INCOMING = 'incoming'
    OUTGOING = 'outgoing'


class MessageStatus(Enum):
    """Énumération pour le statut des messages."""
    SENT = 'sent'
    DELIVERED = 'delivered'
    READ = 'read'
    FAILED = 'failed'


class ConversationStep(Enum):
    """Énumération pour les étapes de la conversation."""
    WELCOME = 'welcome'
    ETAGE = 'etage'
    ZONE = 'zone'
    ZONE_AUTRE = 'zone_autre'
    CATEGORIE = 'categorie'
    CATEGORIE_AUTRE = 'categorie_autre'
    INFORMATIONS = 'informations'
    PHOTOS = 'photos'
    CONFIRMATION = 'confirmation'
    COMPLETED = 'completed'


class ConversationState:
    """
    Représente l'état d'une conversation WhatsApp en cours.
    
    Attributes:
        conversation_id (str): Identifiant unique de la conversation
        user_phone (str): Numéro de téléphone de l'utilisateur
        building_qr_code (str): QR code du bâtiment concerné
        current_step (ConversationStep): Étape actuelle de la conversation
        collected_data (Dict): Données collectées jusqu'à présent
        last_activity (datetime): Date et heure de la dernière activité
        is_completed (bool): Indique si la conversation est terminée
        created_at (datetime): Date et heure de création
        updated_at (datetime): Date et heure de dernière mise à jour
    """
    
    def __init__(self, conversation_id: str = None, user_phone: str = None, 
                 building_qr_code: str = None, current_step: ConversationStep = None,
                 collected_data: Dict = None, last_activity: datetime = None,
                 is_completed: bool = False, created_at: datetime = None, 
                 updated_at: datetime = None):
        """
        Initialise un nouvel état de conversation.
        
        Args:
            conversation_id: Identifiant unique de la conversation (généré si None)
            user_phone: Numéro de téléphone de l'utilisateur
            building_qr_code: QR code du bâtiment concerné
            current_step: Étape actuelle de la conversation
            collected_data: Données collectées jusqu'à présent
            last_activity: Date et heure de la dernière activité
            is_completed: Indique si la conversation est terminée
            created_at: Date et heure de création
            updated_at: Date et heure de dernière mise à jour
        """
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.user_phone = user_phone
        self.building_qr_code = building_qr_code
        
        if current_step is None and building_qr_code is not None:
            self.current_step = ConversationStep.INITIATION
        else:
            self.current_step = current_step
        
        self.collected_data = collected_data or {}
        self.last_activity = last_activity or datetime.now()
        self.is_completed = is_completed
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversationState':
        """
        Crée une instance à partir d'un dictionnaire.
        
        Args:
            data: Dictionnaire contenant les données de l'état de conversation
            
        Returns:
            ConversationState: Une nouvelle instance
        """
        # Conversion des chaînes en types appropriés
        # current_step peut être soit une valeur de l'énumération ConversationStep,
        # soit une chaîne libre utilisée par le gestionnaire de conversation
        if 'current_step' in data and data['current_step']:
            value = data['current_step']
            # Ne convertir en ConversationStep que si la valeur est reconnue,
            # sinon laisser la chaîne telle quelle (par ex. 'welcome', 'building_qr').
            try:
                data['current_step'] = ConversationStep(value)
            except ValueError:
                data['current_step'] = value
        
        if 'last_activity' in data and isinstance(data['last_activity'], str):
            data['last_activity'] = datetime.fromisoformat(data['last_activity'])
        
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data)
    
    def to_dict(self) -> Dict:
        """
        Convertit l'instance en dictionnaire.
        
        Returns:
            Dict: Dictionnaire représentant l'état de conversation
        """
        # Gérer le cas où current_step est une chaîne de caractères ou une énumération
        if isinstance(self.current_step, str):
            current_step_value = self.current_step
        elif self.current_step:
            current_step_value = self.current_step.value
        else:
            current_step_value = None
            
        return {
            'conversation_id': self.conversation_id,
            'user_phone': self.user_phone,
            'building_qr_code': self.building_qr_code,
            'current_step': current_step_value,
            'collected_data': self.collected_data,
            'last_activity': self.last_activity.isoformat(),
            'is_completed': self.is_completed,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def to_json(self) -> str:
        """
        Convertit l'instance en chaîne JSON.
        
        Returns:
            str: Représentation JSON de l'état de conversation
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ConversationState':
        """
        Crée une instance à partir d'une chaîne JSON.
        
        Args:
            json_str: Chaîne JSON représentant l'état de conversation
            
        Returns:
            ConversationState: Une nouvelle instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def update_step(self, step: ConversationStep) -> None:
        """
        Met à jour l'étape actuelle de la conversation.
        
        Args:
            step: Nouvelle étape de la conversation
        """
        self.current_step = step
        self.last_activity = datetime.now()
        self.updated_at = datetime.now()
    
    def add_data(self, key: Union[str, ConversationStep], value: Any) -> None:
        """
        Ajoute une donnée collectée.
        
        Args:
            key: Clé de la donnée (peut être une chaîne ou une énumération ConversationStep)
            value: Valeur de la donnée
        """
        # Si la clé est une énumération, utiliser sa valeur comme clé
        if isinstance(key, ConversationStep):
            self.collected_data[key.value] = value
        else:
            self.collected_data[key] = value
        
        self.last_activity = datetime.now()
        self.updated_at = datetime.now()
    
    def complete(self) -> None:
        """Marque la conversation comme terminée."""
        self.is_completed = True
        self.last_activity = datetime.now()
        self.updated_at = datetime.now()
    
    def save(self, db_connection: DatabaseConnection) -> None:
        """
        Sauvegarde l'état de conversation dans la base de données.
        
        Args:
            db_connection: Connexion à la base de données
        """
        query = """
            INSERT INTO whatsapp_conversations 
            (conversation_id, user_phone, building_qr_code, current_step, 
             collected_data, last_activity, is_completed, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (conversation_id) DO UPDATE SET
            current_step = EXCLUDED.current_step,
            collected_data = EXCLUDED.collected_data,
            last_activity = EXCLUDED.last_activity,
            is_completed = EXCLUDED.is_completed,
            updated_at = EXCLUDED.updated_at
        """
        
        # Gérer le cas où current_step est une chaîne de caractères ou une énumération
        if isinstance(self.current_step, str):
            current_step_value = self.current_step
        elif self.current_step:
            current_step_value = self.current_step.value
        else:
            current_step_value = None
            
        params = (
            self.conversation_id,
            self.user_phone,
            self.building_qr_code,
            current_step_value,
            json.dumps(self.collected_data),
            self.last_activity,
            self.is_completed,
            self.created_at,
            self.updated_at
        )
        
        db_connection.execute_query(query, params)
    
    @classmethod
    def get_by_id(cls, db_connection: DatabaseConnection, conversation_id: str) -> Optional['ConversationState']:
        """
        Récupère un état de conversation par son ID.
        
        Args:
            db_connection: Connexion à la base de données
            conversation_id: ID de la conversation à récupérer
            
        Returns:
            Optional[ConversationState]: L'état de conversation ou None si non trouvé
        """
        query = """
            SELECT conversation_id, user_phone, building_qr_code, current_step,
                   collected_data, last_activity, is_completed, created_at, updated_at
            FROM whatsapp_conversations
            WHERE conversation_id = %s
        """
        
        result = db_connection.execute_query(query, (conversation_id,), fetch_one=True)
        
        if result:
            # current_step peut être une valeur d'énumération ou une chaîne libre
            raw_step = result[3]
            if raw_step:
                try:
                    current_step = ConversationStep(raw_step)
                except ValueError:
                    current_step = raw_step
            else:
                current_step = None

            return cls(
                conversation_id=result[0],
                user_phone=result[1],
                building_qr_code=result[2],
                current_step=current_step,
                collected_data=json.loads(result[4]),
                last_activity=result[5],
                is_completed=result[6],
                created_at=result[7],
                updated_at=result[8]
            )
        
        return None
    
    @classmethod
    def get_active_by_user_and_building(cls, db_connection: DatabaseConnection, 
                                        user_phone: str, building_qr_code: str) -> Optional['ConversationState']:
        """
        Récupère un état de conversation actif par utilisateur et bâtiment.
        
        Args:
            db_connection: Connexion à la base de données
            user_phone: Numéro de téléphone de l'utilisateur
            building_qr_code: QR code du bâtiment
            
        Returns:
            Optional[ConversationState]: L'état de conversation ou None si non trouvé
        """
        query = """
            SELECT conversation_id, user_phone, building_qr_code, current_step,
                   collected_data, last_activity, is_completed, created_at, updated_at
            FROM whatsapp_conversations
            WHERE user_phone = %s AND building_qr_code = %s AND is_completed = FALSE
            ORDER BY last_activity DESC
            LIMIT 1
        """
        
        result = db_connection.execute_query(query, (user_phone, building_qr_code), fetch_one=True)
        
        if result:
            return cls(
                conversation_id=result[0],
                user_phone=result[1],
                building_qr_code=result[2],
                current_step=ConversationStep(result[3]) if result[3] else None,
                collected_data=json.loads(result[4]),
                last_activity=result[5],
                is_completed=result[6],
                created_at=result[7],
                updated_at=result[8]
            )
        
        return None


class WhatsAppMessage:
    """
    Représente un message échangé dans une conversation WhatsApp.
    
    Attributes:
        message_id (str): Identifiant unique du message
        conversation_id (str): Référence à la conversation
        direction (MessageDirection): Direction du message (entrant/sortant)
        content (str): Contenu du message
        timestamp (datetime): Date et heure du message
        status (MessageStatus): Statut du message
        media_url (str): URL du média attaché (si applicable)
    """
    
    def __init__(self, message_id: str = None, conversation_id: str = None,
                 direction: MessageDirection = None, content: str = None,
                 timestamp: datetime = None, status: MessageStatus = None,
                 media_url: str = None):
        """
        Initialise un nouveau message WhatsApp.
        
        Args:
            message_id: Identifiant unique du message (généré si None)
            conversation_id: Référence à la conversation
            direction: Direction du message (entrant/sortant)
            content: Contenu du message
            timestamp: Date et heure du message
            status: Statut du message
            media_url: URL du média attaché (si applicable)
        """
        self.message_id = message_id or str(uuid.uuid4())
        self.conversation_id = conversation_id
        self.direction = direction
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.status = status or (MessageStatus.SENT if direction == MessageDirection.OUTGOING else None)
        self.media_url = media_url
    
    def save(self, db_connection: DatabaseConnection) -> None:
        """
        Sauvegarde le message dans la base de données.
        
        Args:
            db_connection: Connexion à la base de données
        """
        query = """
            INSERT INTO whatsapp_messages
            (message_id, conversation_id, direction, content, timestamp, status, media_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (message_id) DO UPDATE SET
            status = EXCLUDED.status
        """
        
        # Gérer le cas où direction est une chaîne de caractères ou une énumération
        if isinstance(self.direction, str):
            direction_value = self.direction
        elif self.direction:
            direction_value = self.direction.value
        else:
            direction_value = None
            
        # Gérer le cas où status est une chaîne de caractères ou une énumération
        if isinstance(self.status, str):
            status_value = self.status
        elif self.status:
            status_value = self.status.value
        else:
            status_value = None
            
        params = (
            self.message_id,
            self.conversation_id,
            direction_value,
            self.content,
            self.timestamp,
            status_value,
            self.media_url
        )
        
        db_connection.execute_query(query, params)
    
    @classmethod
    def get_by_id(cls, db_connection: DatabaseConnection, message_id: str) -> Optional['WhatsAppMessage']:
        """
        Récupère un message par son ID.
        
        Args:
            db_connection: Connexion à la base de données
            message_id: ID du message à récupérer
            
        Returns:
            Optional[WhatsAppMessage]: Le message ou None si non trouvé
        """
        query = """
            SELECT message_id, conversation_id, direction, content, timestamp, status, media_url
            FROM whatsapp_messages
            WHERE message_id = %s
        """
        
        result = db_connection.execute_query(query, (message_id,), fetch_one=True)
        
        if result:
            return cls(
                message_id=result[0],
                conversation_id=result[1],
                direction=MessageDirection(result[2]) if result[2] else None,
                content=result[3],
                timestamp=result[4],
                status=MessageStatus(result[5]) if result[5] else None,
                media_url=result[6]
            )
        
        return None
    
    @classmethod
    def get_by_conversation(cls, db_connection: DatabaseConnection, conversation_id: str) -> List['WhatsAppMessage']:
        """
        Récupère tous les messages d'une conversation.
        
        Args:
            db_connection: Connexion à la base de données
            conversation_id: ID de la conversation
            
        Returns:
            List[WhatsAppMessage]: Liste des messages de la conversation
        """
        query = """
            SELECT message_id, conversation_id, direction, content, timestamp, status, media_url
            FROM whatsapp_messages
            WHERE conversation_id = %s
            ORDER BY timestamp ASC
        """
        
        results = db_connection.execute_query(query, (conversation_id,), fetch_all=True)
        
        messages = []
        for result in results:
            messages.append(cls(
                message_id=result[0],
                conversation_id=result[1],
                direction=MessageDirection(result[2]) if result[2] else None,
                content=result[3],
                timestamp=result[4],
                status=MessageStatus(result[5]) if result[5] else None,
                media_url=result[6]
            ))
        
        return messages
    
    def update_status(self, db_connection: DatabaseConnection, status: Union[MessageStatus, str]) -> None:
        """
        Met à jour le statut du message.
        
        Args:
            db_connection: Connexion à la base de données
            status: Nouveau statut du message (MessageStatus ou chaîne)
        """
        query = """
            UPDATE whatsapp_messages
            SET status = %s
            WHERE message_id = %s
        """
        
        # Gérer le cas où status est une chaîne de caractères ou une énumération
        if isinstance(status, str):
            status_value = status
        else:
            status_value = status.value
            
        db_connection.execute_query(query, (status_value, self.message_id))
        self.status = status


class PendingIncident:
    """
    Représente un incident en attente de traitement suite à une erreur technique.
    
    Attributes:
        id (str): Identifiant unique de l'incident en attente
        conversation_id (str): Référence à la conversation
        incident_data (Dict): Données complètes de l'incident
        error_message (str): Message d'erreur rencontré
        retry_count (int): Nombre de tentatives effectuées
        next_retry (datetime): Date et heure de la prochaine tentative
        created_at (datetime): Date et heure de création
        updated_at (datetime): Date et heure de dernière mise à jour
    """
    
    def __init__(self, id: str = None, conversation_id: str = None,
                 incident_data: Dict = None, error_message: str = None,
                 retry_count: int = 0, next_retry: datetime = None,
                 created_at: datetime = None, updated_at: datetime = None):
        """
        Initialise un nouvel incident en attente.
        
        Args:
            id: Identifiant unique de l'incident en attente (généré si None)
            conversation_id: Référence à la conversation
            incident_data: Données complètes de l'incident
            error_message: Message d'erreur rencontré
            retry_count: Nombre de tentatives effectuées
            next_retry: Date et heure de la prochaine tentative
            created_at: Date et heure de création
            updated_at: Date et heure de dernière mise à jour
        """
        self.id = id or str(uuid.uuid4())
        self.conversation_id = conversation_id
        self.incident_data = incident_data or {}
        self.error_message = error_message
        self.retry_count = retry_count
        self.next_retry = next_retry or datetime.now()
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    def save(self, db_connection: DatabaseConnection) -> None:
        """
        Sauvegarde l'incident en attente dans la base de données.
        
        Args:
            db_connection: Connexion à la base de données
        """
        query = """
            INSERT INTO pending_incidents
            (id, conversation_id, incident_data, error_message, retry_count, next_retry, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
            incident_data = EXCLUDED.incident_data,
            error_message = EXCLUDED.error_message,
            retry_count = EXCLUDED.retry_count,
            next_retry = EXCLUDED.next_retry,
            updated_at = EXCLUDED.updated_at
        """
        
        params = (
            self.id,
            self.conversation_id,
            json.dumps(self.incident_data),
            self.error_message,
            self.retry_count,
            self.next_retry,
            self.created_at,
            self.updated_at
        )
        
        db_connection.execute_query(query, params)
    
    def increment_retry(self, backoff_factor: float = 2.0, base_delay: int = 300) -> None:
        """
        Incrémente le compteur de tentatives et calcule la prochaine tentative.
        
        Args:
            backoff_factor: Facteur de multiplication du délai à chaque tentative
            base_delay: Délai de base en secondes (5 minutes par défaut)
        """
        self.retry_count += 1
        delay_seconds = base_delay * (backoff_factor ** (self.retry_count - 1))
        self.next_retry = datetime.now().replace(microsecond=0)
        self.next_retry = self.next_retry.fromtimestamp(self.next_retry.timestamp() + delay_seconds)
        self.updated_at = datetime.now()
    
    @classmethod
    def get_by_id(cls, db_connection: DatabaseConnection, id: str) -> Optional['PendingIncident']:
        """
        Récupère un incident en attente par son ID.
        
        Args:
            db_connection: Connexion à la base de données
            id: ID de l'incident en attente
            
        Returns:
            Optional[PendingIncident]: L'incident en attente ou None si non trouvé
        """
        query = """
            SELECT id, conversation_id, incident_data, error_message, retry_count, next_retry, created_at, updated_at
            FROM pending_incidents
            WHERE id = %s
        """
        
        result = db_connection.execute_query(query, (id,), fetch_one=True)
        
        if result:
            return cls(
                id=result[0],
                conversation_id=result[1],
                incident_data=json.loads(result[2]),
                error_message=result[3],
                retry_count=result[4],
                next_retry=result[5],
                created_at=result[6],
                updated_at=result[7]
            )
        
        return None
    
    @classmethod
    def get_pending_retries(cls, db_connection: DatabaseConnection, limit: int = 10) -> List['PendingIncident']:
        """
        Récupère les incidents en attente de retry.
        
        Args:
            db_connection: Connexion à la base de données
            limit: Nombre maximum d'incidents à récupérer
            
        Returns:
            List[PendingIncident]: Liste des incidents en attente de retry
        """
        query = """
            SELECT id, conversation_id, incident_data, error_message, retry_count, next_retry, created_at, updated_at
            FROM pending_incidents
            WHERE next_retry <= NOW()
            ORDER BY next_retry ASC
            LIMIT %s
        """
        
        results = db_connection.execute_query(query, (limit,), fetch_all=True)
        
        incidents = []
        for result in results:
            incidents.append(cls(
                id=result[0],
                conversation_id=result[1],
                incident_data=json.loads(result[2]),
                error_message=result[3],
                retry_count=result[4],
                next_retry=result[5],
                created_at=result[6],
                updated_at=result[7]
            ))
        
        return incidents
    
    def delete(self, db_connection: DatabaseConnection) -> None:
        """
        Supprime l'incident en attente de la base de données.
        
        Args:
            db_connection: Connexion à la base de données
        """
        query = """
            DELETE FROM pending_incidents
            WHERE id = %s
        """
        
        db_connection.execute_query(query, (self.id,))
