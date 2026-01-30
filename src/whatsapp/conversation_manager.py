"""
Gestionnaire de conversations WhatsApp.

Ce module gère le flux de conversation pour les signalements d'incidents via WhatsApp,
en suivant les étapes définies dans le contrat de conversation.
"""

import json
import logging
import time
from flask import Flask, request
from redis import Redis
from twilio.rest import Client
from datetime import datetime
from typing import Dict, Tuple, Any, Optional, List, Union

from src.db.building_dao import BuildingDAO
from src.db.connection import DatabaseConnection
from src.utils.validators import validate_qr_code_number, validate_email
from src.whatsapp import whatsapp_config
from src.whatsapp.models import ConversationState, WhatsAppMessage
from src.whatsapp.state_manager import StateManager
from src.whatsapp.conversation_steps import VALIDATORS, generate_summary, get_next_step
from src.whatsapp.incident_api import create_incident_from_conversation
from src.whatsapp.twilio_interactive import send_template_message
from src.whatsapp import twilio_client

# Configuration du logger
logger = logging.getLogger('whatsapp.conversation')

# Content SID des templates approuvés
TEMPLATE_ZONE_SELECTION = whatsapp_config.get('templates', 'zone_selection', fallback=None)

from src.whatsapp.models import ConversationStep

# Étapes de la conversation
STEPS = [
    ConversationStep.WELCOME,
    ConversationStep.ETAGE,
    ConversationStep.ZONE,
    ConversationStep.ZONE_AUTRE,  # Étape conditionnelle si zone == 'Autre'
    ConversationStep.CATEGORIE,
    ConversationStep.CATEGORIE_AUTRE,  # Étape conditionnelle si categorie == 'Autre'
    ConversationStep.INFORMATIONS,
    ConversationStep.PHOTOS,
    ConversationStep.CONFIRMATION,
    ConversationStep.COMPLETED
]

# Commandes spéciales
COMMANDS = {
    'help': ['aide', 'help', '?'],
    'cancel': ['annuler', 'cancel', 'stop'],
    'restart': ['recommencer', 'restart', 'reset'],
    'back': ['retour', 'back', 'precedent', 'précédent']
}

# Messages pour chaque étape
MESSAGES = {
    ConversationStep.WELCOME: """Bienvenue au service de signalement des incidents pour le bâtiment {building_address}.

En quelques étapes simples, vous allez nous transmettre les informations essentielles afin de relayer efficacement votre signalement au gestionnaire du bâtiment :

📍 Étage
🏢 Zone concernée
📋 Catégorie de l'incident
📝 Description (optionnelle)
📷 Photos (optionnelles)""",
    ConversationStep.ETAGE: "À quel étage se trouve l'incident ?",
    ConversationStep.ZONE: "Dans quelle zone se trouve l'incident ?\n\n1️⃣ Hall\n2️⃣ Couloir\n3️⃣ Ascenseur\n4️⃣ Escalier\n5️⃣ Façade\n6️⃣ Boîte aux lettres\n7️⃣ Local Velo\n8️⃣ Local technique\n9️⃣ Cour / Jardin\n0️⃣ Autre\n\nRépondez avec le numéro ou le nom de la zone.",
    ConversationStep.ZONE_AUTRE: "Merci de préciser la zone de l'incident.",
    ConversationStep.CATEGORIE: "Quelle est la catégorie de l'incident ?\n\n1️⃣ Electricité\n2️⃣ Propreté\n3️⃣ Plomberie\n4️⃣ Poste / Fenêtre\n5️⃣ Consommable\n6️⃣ Autre\n\nRépondez avec le numéro ou le nom de la catégorie.",
    ConversationStep.CATEGORIE_AUTRE: "Merci de préciser la catégorie de l'incident.",
    ConversationStep.INFORMATIONS: "Pouvez-vous apporter des informations complémentaires à votre signalement ?\n(ex: disfonctionnement, remplacement demandé, fuite, ...)",
    ConversationStep.PHOTOS: "Souhaitez-vous ajouter des photos de l'incident ?\n\n1️⃣ Non\n2️⃣ Oui, j'envoie une photo\n\nRépondez avec le numéro ou 'Non'/'Oui'.",
    ConversationStep.CONFIRMATION: "Merci pour ces informations. Voici un résumé de votre signalement:\n{summary}\n\nSouhaitez-vous confirmer ?\n\n1️⃣ Je confirme ce signalement\n2️⃣ Annuler et faire un nouveau signalement\n\nRépondez avec le numéro ou votre choix.",
    ConversationStep.COMPLETED: "Merci d'avoir utilisé notre service.",
    'error': "Une erreur est survenue: {error_message}. Veuillez réessayer.",
    'help': "Commandes disponibles:\n- aide: affiche ce message\n- annuler: annule la conversation\n- recommencer: recommence depuis le début\n- retour: revient à l'étape précédente",
    'cancel': "Conversation annulée. Merci d'avoir utilisé notre service.",
    'timeout': "La conversation a expiré en raison d'inactivité. Veuillez recommencer.",
    'invalid_input': "Entrée invalide. {validation_message}",
    'building_not_found': "Bâtiment non trouvé. Veuillez vérifier le code QR et réessayer.",
    'api_error': "Une erreur technique est survenue lors de la création de l'incident. Votre demande a été enregistrée et sera traitée dès que possible."
}

class ConversationManager:
    """Gestionnaire de conversations WhatsApp."""
    
    def __init__(self, state_manager: StateManager, db_connection: DatabaseConnection):
        """
        Initialise le gestionnaire de conversations.
        
        Args:
            state_manager: Gestionnaire d'état Redis
            db_connection: Connexion à la base de données
        """
        self.state_manager = state_manager
        self.db_connection = db_connection
        self.building_dao = BuildingDAO()
    
    def start_new_conversation(self, phone_number: str, building_qr_code: str = "QR5050332870") -> Optional[str]:
        """
        Prépare une nouvelle conversation pour un utilisateur.
        L'ancienne conversation (si elle existe) est marquée comme obsolète mais conservée.
        Le message de bienvenue sera envoyé quand l'utilisateur enverra son premier message.
        
        Args:
            phone_number: Numéro de téléphone de l'utilisateur (format: +33...)
            building_qr_code: Code QR du bâtiment (par défaut: QR5050332870)
            
        Returns:
            Optional[str]: ID de la nouvelle conversation ou None en cas d'erreur
        """
        import uuid
        
        try:
            # Formater le numéro de téléphone
            if not phone_number.startswith('+'):
                phone_number = f'+{phone_number}'
            
            logger.info(f"Préparation d'une nouvelle conversation pour {phone_number}")
            
            # 1. Marquer les anciennes conversations comme obsolètes (is_completed=true)
            try:
                update_query = """
                    UPDATE whatsapp_conversations 
                    SET is_completed = true, updated_at = NOW()
                    WHERE user_phone = %s AND is_completed = false
                """
                self.db_connection.execute_query(update_query, (phone_number,))
                logger.info(f"Anciennes conversations marquées comme obsolètes pour {phone_number}")
            except Exception as e:
                logger.warning(f"Erreur lors de la mise à jour des anciennes conversations: {e}")
            
            # 2. Supprimer l'ancienne conversation de Redis
            self.state_manager.delete_conversation(phone_number)
            
            # 3. Créer une nouvelle conversation à l'étape WELCOME
            # Le message de bienvenue sera envoyé quand l'utilisateur enverra son premier message
            conversation_id = f"conv_{uuid.uuid4().hex[:16]}"
            
            conversation = ConversationState(
                conversation_id=conversation_id,
                user_phone=phone_number,
                current_step=ConversationStep.WELCOME,
                collected_data={},
                is_completed=False,
                building_qr_code=building_qr_code
            )
            
            # 4. Sauvegarder dans PostgreSQL et Redis
            conversation.save(self.db_connection)
            self.state_manager.save_conversation(conversation)
            
            logger.info(f"Nouvelle conversation {conversation_id} préparée (en attente du premier message utilisateur)")
            return conversation_id
            
        except Exception as e:
            logger.error(f"Erreur lors de la préparation de la nouvelle conversation: {e}")
            return None
    
    def _send_whatsapp_message(self, from_number: str, to_number: str, message: str) -> Optional[str]:
        """
        Envoie un message WhatsApp via Twilio.
        
        Args:
            from_number: Numéro WhatsApp de l'expéditeur
            to_number: Numéro WhatsApp du destinataire
            message: Texte du message
            
        Returns:
            Optional[str]: SID du message ou None en cas d'erreur
        """
        try:
            # Formater les numéros pour Twilio
            if not from_number.startswith('whatsapp:'):
                from_number = f"whatsapp:{from_number}"
            if not to_number.startswith('whatsapp:'):
                to_number = f"whatsapp:{to_number}"
            
            twilio_message = twilio_client.messages.create(
                from_=from_number,
                to=to_number,
                body=message
            )
            
            logger.info(f"Message WhatsApp envoyé: {twilio_message.sid}")
            return twilio_message.sid
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message WhatsApp: {e}")
            return None
    
    def process_message(self, message: WhatsAppMessage) -> str:
        """
        Traite un message entrant et génère une réponse.
        
        Args:
            message: Message WhatsApp entrant
            
        Returns:
            str: Réponse à envoyer à l'utilisateur
        """
        start_time = time.time()
        
        try:
            # Récupérer ou créer l'état de la conversation
            conversation = self._get_or_create_conversation(message)
            logger.info(f"[process_message] from={getattr(message, 'from_phone', None)} step_avant={conversation.current_step}")
            
            # Enregistrer le message dans la base de données
            message.conversation_id = conversation.conversation_id
            message.save(self.db_connection)
            
            # Traiter les commandes spéciales
            command_response = self._process_commands(message.body, conversation)
            if command_response:
                # Mettre à jour l'état de la conversation
                self.state_manager.update_conversation(conversation)
                
                # Calculer et enregistrer le temps de réponse
                self._record_response_time(start_time)
                
                return command_response
            
            # Traiter le message selon l'étape actuelle
            response = self._process_step(message, conversation)
            logger.info(f"[process_message] step_apres={conversation.current_step}")
            
            # Mettre à jour l'état de la conversation dans Redis
            self.state_manager.update_conversation(conversation)
            
            # Synchroniser avec PostgreSQL
            conversation.save(self.db_connection)
            
            # Calculer et enregistrer le temps de réponse
            self._record_response_time(start_time)
            
            return response
        
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message: {e}")
            
            # Enregistrer l'erreur dans les métriques
            self._record_error("process_message_error")
            
            # Calculer et enregistrer le temps de réponse
            self._record_response_time(start_time)
            
            return MESSAGES['error'].format(error_message="Erreur système")
    
    def _get_or_create_conversation(self, message: WhatsAppMessage) -> ConversationState:
        """
        Récupère ou crée un état de conversation pour un message.
        Utilise un QR code fixe (QR5050332870) pour tous les incidents.
        
        Args:
            message: Message WhatsApp
            
        Returns:
            ConversationState: État de la conversation
        """
        # Ajouter l'attribut from_phone au message s'il n'existe pas déjà
        if not hasattr(message, 'from_phone'):
            # Utiliser le numéro de téléphone de l'expéditeur depuis la requête
            from_number = request.form.get('From', '') if 'From' in request.form else ''
            setattr(message, 'from_phone', from_number)
        
        # S'assurer que from_phone n'est pas vide
        if not message.from_phone:
            # Utiliser un numéro par défaut si from_phone est vide
            message.from_phone = '+33600000000'
            logger.warning(f"Numéro de téléphone manquant pour le message {message.message_id}, utilisation d'un numéro par défaut")
            
        # Essayer de récupérer une conversation existante depuis Redis
        conversation = self.state_manager.get_conversation_by_phone(message.from_phone)
        
        if not conversation:
            # Si pas dans Redis, vérifier dans PostgreSQL
            try:
                query = """
                    SELECT conversation_id, user_phone, building_qr_code, current_step, 
                           collected_data, is_completed, created_at, updated_at
                    FROM whatsapp_conversations 
                    WHERE user_phone = %s AND is_completed = false
                    ORDER BY created_at DESC LIMIT 1
                """
                result = self.db_connection.execute_query(query, (message.from_phone,), fetch_one=True)
                
                if result:
                    # Reconstruire la conversation depuis PostgreSQL
                    logger.info(f"Conversation trouvée dans PostgreSQL pour {message.from_phone}, resynchronisation avec Redis")
                    collected_data = result['collected_data'] if result['collected_data'] else {}
                    if isinstance(collected_data, str):
                        import json
                        collected_data = json.loads(collected_data)
                    
                    conversation = ConversationState(
                        conversation_id=result['conversation_id'],
                        user_phone=result['user_phone'],
                        current_step=ConversationStep(result['current_step']) if result['current_step'] else ConversationStep.WELCOME,
                        collected_data=collected_data,
                        is_completed=result['is_completed'],
                        building_qr_code=result['building_qr_code']
                    )
                    # Resynchroniser avec Redis
                    self.state_manager.save_conversation(conversation)
            except Exception as e:
                logger.warning(f"Erreur lors de la récupération depuis PostgreSQL: {e}")
        
        if not conversation:
            # Utiliser un QR code fixe pour tous les incidents
            fixed_qr_code = "QR5050332870"
            
            # Vérifier que le bâtiment existe
            building_dao = BuildingDAO()
            building = building_dao.get_building_by_qr_code(fixed_qr_code)
            
            if not building:
                # Si le bâtiment n'existe pas, créer un bâtiment avec ce QR code
                from src.models.building import Building
                try:
                    new_building = Building(
                        location="Bâtiment de test pour WhatsApp",
                        qr_code_number=fixed_qr_code
                    )
                    building_dao.create_building(new_building)
                    logger.info(f"Bâtiment de test créé avec le QR code {fixed_qr_code}")
                except Exception as e:
                    logger.error(f"Erreur lors de la création du bâtiment de test: {e}")
            
            # Créer une nouvelle conversation
            conversation = ConversationState(
                conversation_id=message.message_id,
                user_phone=message.from_phone,
                current_step=ConversationStep.WELCOME,  # Démarrer directement à l'étape WELCOME
                collected_data={},
                is_completed=False,
                building_qr_code=fixed_qr_code  # Utiliser le QR code fixe
            )
            
            # Sauvegarder la nouvelle conversation
            conversation.save(self.db_connection)
            self.state_manager.save_conversation(conversation)
        
        return conversation
    
    def _process_commands(self, message_body: str, conversation: ConversationState) -> Optional[str]:
        """
        Traite les commandes spéciales.
        
        Args:
            message_body: Corps du message
            conversation: État de la conversation
            
        Returns:
            Optional[str]: Réponse à la commande ou None
        """
        message_lower = message_body.lower().strip()
        
        # Commande d'aide
        if message_lower in COMMANDS['help']:
            return MESSAGES['help']
        
        # Commande d'annulation
        elif message_lower in COMMANDS['cancel']:
            conversation.is_completed = True
            conversation.current_step = ConversationStep.COMPLETED
            return MESSAGES['cancel']
        
        # Commande de redémarrage
        elif message_lower in COMMANDS['restart']:
            conversation.current_step = ConversationStep.WELCOME
            conversation.collected_data = {}
            conversation.building_qr_code = None
            return MESSAGES[ConversationStep.WELCOME]
        
        # Commande de retour
        elif message_lower in COMMANDS['back']:
            return self._go_back(conversation)
        
        return None
    
    def _go_back(self, conversation: ConversationState) -> str:
        """
        Revient à l'étape précédente de la conversation.
        
        Args:
            conversation: État de la conversation
            
        Returns:
            str: Message pour l'étape précédente
        """
        current_index = STEPS.index(conversation.current_step)
        
        if current_index > 0:
            # Revenir à l'étape précédente
            previous_step = STEPS[current_index - 1]
            conversation.current_step = previous_step
            
            # Supprimer les données collectées à l'étape actuelle
            if previous_step.value in conversation.collected_data:
                del conversation.collected_data[previous_step.value]
            
            return MESSAGES[previous_step]
        else:
            # Déjà à la première étape
            return MESSAGES[conversation.current_step]
    
    def _get_building_address(self, building_qr_code: str) -> str:
        """
        Récupère l'adresse du bâtiment à partir de son QR code.
        
        Args:
            building_qr_code: Code QR du bâtiment
            
        Returns:
            str: Adresse du bâtiment ou le QR code si non trouvé
        """
        try:
            building = self.building_dao.get_building_by_qr_code(building_qr_code)
            if building and building.location:
                return building.location
            else:
                logger.warning(f"Bâtiment non trouvé pour QR code: {building_qr_code}")
                return building_qr_code
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'adresse du bâtiment: {e}")
            return building_qr_code
    
    def _send_zone_template(self, message: WhatsAppMessage) -> bool:
        """
        Envoie le template interactif pour le choix de zone.
        
        Args:
            message: Message WhatsApp (pour récupérer le numéro de téléphone)
            
        Returns:
            bool: True si l'envoi a réussi, False sinon
        """
        try:
            from_number = whatsapp_config.get('twilio', 'whatsapp_number')
            to_number = getattr(message, 'from_phone', None)
            
            if not to_number:
                logger.error("Numéro de téléphone destinataire manquant pour le template zone")
                return False
            
            # Formater les numéros pour Twilio
            if not from_number.startswith('whatsapp:'):
                from_number = f"whatsapp:{from_number}"
            if not to_number.startswith('whatsapp:'):
                to_number = f"whatsapp:{to_number}"
            
            # Envoyer le template
            message_sid = send_template_message(
                client=twilio_client,
                from_number=from_number,
                to_number=to_number,
                content_sid=TEMPLATE_ZONE_SELECTION
            )
            
            if message_sid:
                logger.info(f"Template zone envoyé avec succès: {message_sid}")
                return True
            else:
                logger.error("Échec de l'envoi du template zone")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du template zone: {e}")
            return False
    
    def _process_step(self, message: WhatsAppMessage, conversation: ConversationState) -> str:
        """
        Traite le message selon l'étape actuelle de la conversation.
        
        Args:
            message: Message WhatsApp complet
            conversation: État de la conversation
            
        Returns:
            str: Réponse à envoyer à l'utilisateur
        """
        current_step = conversation.current_step
        message_body = message.body if hasattr(message, 'body') else message.content
        
        # Si la conversation est terminée, renvoyer un message d'erreur
        if conversation.is_completed:
            return MESSAGES['error'].format(error_message="La conversation est déjà terminée")
        
        # Si c'est l'étape d'accueil, afficher le message de bienvenue puis passer à l'étape suivante
        if current_step == ConversationStep.WELCOME:
            # Récupérer l'adresse du bâtiment
            building_address = self._get_building_address(conversation.building_qr_code)
            # Afficher d'abord le message de bienvenue avec l'adresse
            welcome_message = MESSAGES[ConversationStep.WELCOME].format(building_address=building_address)
            # Passer à l'étape suivante (ETAGE)
            next_step = get_next_step(current_step)
            conversation.current_step = next_step
            # Renvoyer le message de bienvenue suivi du message de l'étape suivante
            return f"{welcome_message}\n\n{MESSAGES[next_step]}"
        
        # Si c'est l'étape de confirmation
        elif current_step == ConversationStep.CONFIRMATION:
            return self._process_confirmation(message_body, conversation)
        
        # Si c'est l'étape finale
        elif current_step == ConversationStep.COMPLETED:
            return MESSAGES[ConversationStep.COMPLETED]
        
        # Pour toutes les autres étapes, valider l'entrée
        return self._process_validation_step(message, conversation)
    
    def _process_validation_step(self, message: WhatsAppMessage, conversation: ConversationState) -> str:
        """
        Traite une étape de validation.
        
        Args:
            message: Message WhatsApp complet
            conversation: État de la conversation
            
        Returns:
            str: Réponse à envoyer à l'utilisateur
        """
        current_step = conversation.current_step
        message_body = message.body if hasattr(message, 'body') else message.content
        validator = VALIDATORS.get(current_step)
        
        if not validator:
            logger.error(f"Pas de validateur pour l'étape {current_step}")
            return MESSAGES['error'].format(error_message="Étape non reconnue")
        
        # Valider l'entrée selon le type d'étape
        if current_step == ConversationStep.PHOTOS:
            # Pour l'étape photos, vérifier s'il y a une pièce jointe
            media_url = None
            if hasattr(message, 'media_url') and message.media_url:
                media_url = message.media_url
            # Passer le conversation_id pour le téléchargement local des photos
            is_valid, normalized_value, error_message = validator(message_body, media_url, conversation.conversation_id)
        else:
            is_valid, normalized_value, error_message = validator(message_body)
        
        if not is_valid:
            # Cas spécial pour la zone invalide : envoyer le message d'erreur puis le template interactif
            if current_step == ConversationStep.ZONE and TEMPLATE_ZONE_SELECTION:
                # 1. Envoyer d'abord le message d'erreur via l'API Twilio
                from_number = whatsapp_config.get('twilio', 'whatsapp_number')
                to_number = getattr(message, 'from_phone', None)
                self._send_whatsapp_message(from_number, to_number, "La zone est invalide. Merci de choisir parmi les choix proposés.")
                # 2. Puis envoyer le template interactif
                self._send_zone_template(message)
                return None  # Pas de réponse TwiML, tout est envoyé via l'API
            return MESSAGES['invalid_input'].format(validation_message=error_message)
        
        # Stocker la valeur validée
        conversation.add_data(current_step, normalized_value)
        
        # Déterminer l'étape suivante en fonction des données collectées
        next_step = get_next_step(current_step, conversation.collected_data)
        conversation.current_step = next_step
        
        # Si c'est l'étape de confirmation, générer un résumé
        if next_step == ConversationStep.CONFIRMATION:
            summary = generate_summary(conversation)
            return MESSAGES[next_step].format(summary=summary)
        
        # Si l'étape suivante est ZONE et qu'un template est configuré, envoyer le template interactif
        if next_step == ConversationStep.ZONE and TEMPLATE_ZONE_SELECTION:
            self._send_zone_template(message)
            return None  # Ne pas envoyer de message texte, le template est envoyé séparément
        
        return MESSAGES[next_step]
    
    def _process_confirmation(self, message_body: str, conversation: ConversationState) -> str:
        """
        Traite l'étape de confirmation.
        
        Args:
            message_body: Corps du message
            conversation: État de la conversation
            
        Returns:
            str: Réponse à envoyer à l'utilisateur
        """
        # Valider la confirmation avec le nouveau validateur
        validator = VALIDATORS.get(ConversationStep.CONFIRMATION)
        is_valid, response, error_message = validator(message_body)
        
        if not is_valid:
            return MESSAGES['invalid_input'].format(validation_message=error_message)
        
        # Si l'utilisateur confirme le signalement
        if response == 'confirm':
            try:
                # Créer l'incident
                success, incident_id, error = create_incident_from_conversation(conversation, self.db_connection)
                
                if success:
                    # Marquer la conversation comme terminée
                    conversation.complete()
                    conversation.current_step = ConversationStep.COMPLETED
                    
                    # Renvoyer le message de confirmation
                    return MESSAGES[ConversationStep.COMPLETED]
                else:
                    # En cas d'erreur lors de la création de l'incident
                    logger.error(f"Erreur lors de la création de l'incident: {error}")
                    return MESSAGES['api_error']
            except Exception as e:
                logger.error(f"Exception lors de la création de l'incident: {str(e)}")
                return MESSAGES['error'].format(error_message="Erreur lors de la création de l'incident")
        elif response == 'restart':
            # Si l'utilisateur veut recommencer
            conversation.current_step = ConversationStep.ETAGE  # Recommencer à l'étape ETAGE
            conversation.collected_data = {}  # Réinitialiser les données collectées
            return MESSAGES[ConversationStep.ETAGE]
        else:
            # Cas improbable mais géré par sécurité
            return MESSAGES['error'].format(error_message="Réponse non reconnue")
    
    def _record_response_time(self, start_time: float) -> None:
        """
        Enregistre le temps de réponse dans Redis pour les métriques.
        
        Args:
            start_time: Temps de début du traitement
        """
        try:
            # Désactivé pour le débogage
            response_time = time.time() - start_time
            logger.debug(f"Temps de réponse: {response_time:.3f}s")
            
            # Code désactivé pour éviter les erreurs
            # redis_client = self.state_manager.redis_client
            # redis_client.incr('whatsapp:metrics:response_count')
            # redis_client.lpush('whatsapp:metrics:response_times', str(response_time))
            # redis_client.ltrim('whatsapp:metrics:response_times', 0, 999)
            # if response_time > 2.0:
            #     redis_client.incr('whatsapp:metrics:slow_responses')
        
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement du temps de réponse: {e}")
    
    def _record_error(self, error_type: str) -> None:
        """
        Enregistre une erreur dans Redis pour les métriques.
        
        Args:
            error_type: Type d'erreur
        """
        try:
            # Désactivé pour le débogage
            logger.debug(f"Erreur enregistrée: {error_type}")
            
            # Code désactivé pour éviter les erreurs
            # redis_client = self.state_manager.redis_client
            # redis_client.incr(f'whatsapp:metrics:{error_type}')
        
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de l'erreur: {e}")
