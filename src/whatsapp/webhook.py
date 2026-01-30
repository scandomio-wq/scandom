"""
Webhook pour recevoir les messages WhatsApp via Twilio.

Ce module implémente les endpoints Flask pour recevoir les messages WhatsApp
et les notifications de statut de message via Twilio.
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from flask import Blueprint, request, Response
from twilio.twiml.messaging_response import MessagingResponse
import re

from src.db.connection import DatabaseConnection
from src.whatsapp import whatsapp_config, twilio_client
from src.whatsapp.models import WhatsAppMessage, ConversationStep, ConversationState, MessageDirection
from src.whatsapp.security import validate_twilio_request
from twilio.request_validator import RequestValidator as TwilioRequestValidator
from src.whatsapp.state_manager import StateManager
from src.whatsapp.conversation_manager import ConversationManager

# Créer le blueprint Flask
whatsapp_bp = Blueprint('whatsapp', __name__, url_prefix='/api/whatsapp')

# Configuration du logger
logger = logging.getLogger('whatsapp.webhook')

# Initialiser les gestionnaires
from src.whatsapp import redis_client
db_connection = DatabaseConnection()
state_manager = StateManager(redis_client)
conversation_manager = ConversationManager(state_manager, db_connection)

# Déduplication des messages via Redis (fonctionne avec plusieurs workers)
_DEDUP_TTL = 60  # Durée de vie en secondes
_DEDUP_PREFIX = "whatsapp:dedup:"


def _is_message_already_processed(message_sid: str) -> bool:
    """Vérifie si un message a déjà été traité récemment (via Redis)."""
    key = f"{_DEDUP_PREFIX}{message_sid}"
    
    # SETNX retourne True si la clé a été créée, False si elle existait déjà
    was_set = redis_client.setnx(key, "1")
    
    if was_set:
        # Définir le TTL pour auto-expiration
        redis_client.expire(key, _DEDUP_TTL)
        return False  # Message pas encore traité
    
    return True  # Message déjà traité


@whatsapp_bp.route('/twilio', methods=['POST'])
def receive_message() -> Response:
    """Endpoint pour recevoir les messages WhatsApp via Twilio.

    Returns:
        Response: Réponse TwiML ou erreur
    """
    try:
        # Valider la requête Twilio
        if not validate_twilio_request(request):
            logger.warning("Requête Twilio invalide")
            return Response("Signature invalide", status=403)

        # Extraire les données du message
        message_sid = request.form.get('MessageSid', '')
        
        # Vérifier si le message a déjà été traité (déduplication)
        if _is_message_already_processed(message_sid):
            logger.debug(f"Message {message_sid} déjà traité, ignoré")
            return Response(str(MessagingResponse()), mimetype='text/xml')
        
        from_number = request.form.get('From', '')
        # Nettoyer le numéro de téléphone pour enlever le préfixe 'whatsapp:' si présent
        if from_number.startswith('whatsapp:'):
            from_number = from_number[9:]  # Enlever 'whatsapp:'
        to_number = request.form.get('To', '')
        body = request.form.get('Body', '')
        num_media = int(request.form.get('NumMedia', '0'))

        # Extraire les médias si présents
        media_urls = []
        for i in range(num_media):
            media_url = request.form.get(f'MediaUrl{i}', '')
            if media_url:
                media_urls.append(media_url)

        # Créer l'objet message
        message = WhatsAppMessage(
            message_id=message_sid,
            conversation_id=None,  # Sera défini par le gestionnaire de conversation
            direction='incoming',  # Utiliser la chaîne au lieu de l'énumération
            content=body,
            media_url=media_urls[0] if media_urls else None
        )
        
        # Ajouter explicitement l'attribut from_phone au message
        setattr(message, 'from_phone', from_number)

        # Traiter le message avec le gestionnaire de conversation
        response_text = conversation_manager.process_message(message)
        
        # Récupérer l'état de la conversation pour vérifier l'étape actuelle
        conversation = state_manager.get_conversation_by_phone(from_number)
        
        # Si l'étape actuelle est ZONE, utiliser le template Twilio interactif
        # NOTE: Template désactivé temporairement car non approuvé par Meta (statut: failed)
        # Réactiver quand le template sera approuvé
        # if conversation and conversation.current_step == ConversationStep.ZONE:
        #     try:
        #         twilio_message = twilio_client.messages.create(
        #             from_=f"whatsapp:{whatsapp_config.get('twilio', 'whatsapp_number')}",
        #             to=f"whatsapp:{from_number}",
        #             content_sid="HXef3cdf175c6234e02fd4622a50a442bb",
        #             content_variables="{}"
        #         )
        #         logger.info(f"Message interactif envoyé via template Twilio: {twilio_message.sid}")
        #         return Response(str(MessagingResponse()), mimetype='text/xml')
        #     except Exception as e:
        #         logger.warning(f"Échec de l'envoi du template Twilio: {e}. Fallback sur message texte.")
        
        # Si response_text est None, le template a été envoyé séparément via l'API Twilio
        if response_text is None:
            logger.info("Template interactif envoyé via API Twilio, pas de réponse TwiML")
            return Response(str(MessagingResponse()), mimetype='text/xml')
        
        # Message texte normal
        twiml_response = MessagingResponse()
        twiml_response.message(response_text)
        
        # Log pour le débogage
        logger.info(f"Message traité avec succès. Réponse: {response_text}")

        return Response(str(twiml_response), mimetype='text/xml')

    except Exception as e:
        logger.error(f"Erreur lors du traitement du message: {e}")
        
        # Réponse d'erreur générique
        twiml_response = MessagingResponse()
        twiml_response.message("Désolé, une erreur est survenue. Veuillez réessayer plus tard.")

        return Response(str(twiml_response), mimetype='text/xml')


@whatsapp_bp.route('/reset/<phone>', methods=['GET'])
def reset_conversation(phone: str) -> Response:
    """Endpoint pour réinitialiser une conversation existante.
    
    Args:
        phone: Numéro de téléphone (sans le préfixe +)
        
    Returns:
        Response: Réponse JSON
    """
    try:
        # Ajouter le préfixe + si nécessaire
        if not phone.startswith('+'):
            phone = f'+{phone}'
        
        # Supprimer la conversation existante de Redis
        deleted_redis = state_manager.delete_conversation(phone)
        
        # Supprimer aussi de PostgreSQL (conversations non terminées)
        deleted_db = False
        try:
            delete_query = """
                DELETE FROM whatsapp_conversations 
                WHERE user_phone = %s AND is_completed = false
            """
            db_connection.execute_query(delete_query, (phone,))
            deleted_db = True
            logger.info(f"Conversation supprimée de PostgreSQL pour {phone}")
        except Exception as db_error:
            logger.warning(f"Erreur lors de la suppression en DB: {db_error}")
        
        if deleted_redis or deleted_db:
            logger.info(f"Conversation réinitialisée pour {phone}")
            return Response(
                json.dumps({"status": "success", "message": f"Conversation réinitialisée pour {phone}"}),
                status=200,
                mimetype='application/json'
            )
        else:
            logger.info(f"Aucune conversation trouvée pour {phone}")
            return Response(
                json.dumps({"status": "not_found", "message": f"Aucune conversation trouvée pour {phone}"}),
                status=404,
                mimetype='application/json'
            )
    
    except Exception as e:
        logger.error(f"Erreur lors de la réinitialisation de la conversation: {e}")
        return Response(
            json.dumps({"status": "error", "message": str(e)}),
            status=500,
            mimetype='application/json'
        )


@whatsapp_bp.route('/status', methods=['POST'])
def message_status() -> Response:
    """Endpoint pour recevoir les mises à jour de statut des messages WhatsApp.

    Returns:
        Response: Réponse HTTP
    """
    try:
        # Valider la requête Twilio
        if not validate_twilio_request(request):
            logger.warning("Requête Twilio invalide")
            return Response("Signature invalide", status=403)

        # Extraire les données de statut
        message_sid = request.form.get('MessageSid', '')
        message_status = request.form.get('MessageStatus', '')

        # Mettre à jour le statut du message dans la base de données
        _update_message_status(message_sid, message_status)
        
        # Log pour le débogage
        logger.info(f"Statut du message {message_sid} mis à jour: {message_status}")
        
        return Response(status=200)
    
    except Exception as e:
        logger.error(f"Erreur lors du traitement du statut: {e}")
        return Response(status=500)


# La fonction _record_metric a été supprimée car elle n'est plus utilisée


def _update_message_status(message_sid: str, status: str) -> None:
    """
    Met à jour le statut d'un message dans la base de données.
    
    Args:
        message_sid: ID du message
        status: Nouveau statut
    """
    try:
        # Récupérer le message
        query = """
            SELECT * FROM whatsapp_messages
            WHERE message_id = %s
        """
        result = db_connection.execute_query(query, (message_sid,), fetch_one=True)
        
        if result:
            # Mettre à jour le statut
            update_query = """
                UPDATE whatsapp_messages
                SET status = %s, updated_at = NOW()
                WHERE message_id = %s
            """
            db_connection.execute_query(update_query, (status, message_sid))
            logger.info(f"Statut du message {message_sid} mis à jour: {status}")
        else:
            logger.warning(f"Message {message_sid} non trouvé pour mise à jour de statut")
    
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du statut du message: {e}")


def extract_building_qr_code(message: str) -> Optional[str]:
    """
    Extrait un QR code de bâtiment d'un message.
    
    Args:
        message: Le message à analyser
        
    Returns:
        Optional[str]: Le QR code de bâtiment ou None si non trouvé
    """
    if not message:
        return None
    
    # Format attendu: QR12345 ou QR-12345
    # Rechercher un pattern QR suivi de chiffres, avec ou sans tiret
    match = re.search(r'QR[-]?(\d+)', message.upper())
    if match:
        return f"QR{match.group(1)}"
    
    return None


def process_message(from_number: str, message: str, building_qr_code: Optional[str], 
                   db_connection: DatabaseConnection) -> Tuple[str, str]:
    """
    Traite un message entrant et génère une réponse.
    
    Args:
        from_number: Numéro de téléphone de l'expéditeur
        message: Contenu du message
        building_qr_code: QR code du bâtiment (si présent dans le message)
        db_connection: Connexion à la base de données
        
    Returns:
        Tuple[str, str]: (Texte de réponse, ID de conversation)
    """
    # Vérifier si c'est un message de démarrage avec un deep link
    if building_qr_code:
        # Créer ou récupérer une conversation pour ce bâtiment
        conversation = state_manager.create_new_conversation(from_number, building_qr_code)
        
        # Sauvegarder la conversation dans la base de données si elle est nouvelle
        if not ConversationState.get_by_id(db_connection, conversation.conversation_id):
            conversation.save(db_connection)
        
        # Message de bienvenue
        welcome_message = whatsapp_config.get('messages', 'welcome', 
                                            fallback="Bienvenue ! Je vais vous aider à déclarer un incident pour le bâtiment {building_qr_code}.")
        welcome_message = welcome_message.format(building_qr_code=building_qr_code)
        
        # Message pour la première étape
        next_step_message = get_step_message(conversation.current_step)
        
        return f"{welcome_message}\n\n{next_step_message}", conversation.conversation_id
    
    # Sinon, rechercher une conversation active pour cet utilisateur
    active_conversations = ConversationState.get_active_by_user(db_connection, from_number)
    
    if not active_conversations:
        # Aucune conversation active trouvée
        no_conversation_message = whatsapp_config.get('messages', 'no_active_conversation', 
                                                   fallback="Désolé, je ne trouve pas de conversation active pour vous. Veuillez scanner un QR code de bâtiment pour commencer.")
        
        # Générer un ID de conversation temporaire
        import uuid
        temp_conversation_id = str(uuid.uuid4())
        
        return no_conversation_message, temp_conversation_id
    
    # Si plusieurs conversations actives, utiliser la plus récente
    conversation = active_conversations[0]
    
    # Vérifier les commandes spéciales
    if message.lower() == 'help' or message.lower() == 'aide':
        help_message = whatsapp_config.get('messages', 'help', 
                                         fallback="Commandes disponibles:\n- help/aide: Afficher ce message\n- cancel/annuler: Annuler la déclaration\n- restart/recommencer: Recommencer la déclaration\n- back/retour: Revenir à l'étape précédente")
        return help_message, conversation.conversation_id
    
    elif message.lower() == 'cancel' or message.lower() == 'annuler':
        # Marquer la conversation comme terminée
        state_manager.complete_conversation(conversation.conversation_id)
        conversation.complete()
        conversation.save(db_connection)
        
        cancel_message = whatsapp_config.get('messages', 'cancel', 
                                           fallback="Votre déclaration d'incident a été annulée. Merci d'avoir utilisé notre service.")
        return cancel_message, conversation.conversation_id
    
    elif message.lower() == 'restart' or message.lower() == 'recommencer':
        # Réinitialiser la conversation
        conversation.reset()
        conversation.save(db_connection)
        state_manager.save_state(conversation)
        
        restart_message = whatsapp_config.get('messages', 'restart', 
                                            fallback="Votre déclaration a été réinitialisée. Commençons à nouveau.")
        next_step_message = get_step_message(conversation.current_step)
        
        return f"{restart_message}\n\n{next_step_message}", conversation.conversation_id
    
    elif message.lower() == 'back' or message.lower() == 'retour':
        # Revenir à l'étape précédente
        previous_step = get_previous_step(conversation.current_step)
        if previous_step:
            conversation.update_step(previous_step)
            conversation.save(db_connection)
            state_manager.save_state(conversation)
            
            back_message = whatsapp_config.get('messages', 'back', 
                                             fallback="Revenons à l'étape précédente.")
            next_step_message = get_step_message(previous_step)
            
            return f"{back_message}\n\n{next_step_message}", conversation.conversation_id
        else:
            # Déjà à la première étape
            no_previous_step_message = whatsapp_config.get('messages', 'no_previous_step', 
                                                        fallback="Vous êtes déjà à la première étape.")
            return no_previous_step_message, conversation.conversation_id
    
    # Traiter la réponse en fonction de l'étape actuelle
    return process_step_response(conversation, message, db_connection), conversation.conversation_id


def get_step_message(step: ConversationStep) -> str:
    """
    Récupère le message pour une étape donnée.
    
    Args:
        step: L'étape de la conversation
        
    Returns:
        str: Le message pour cette étape
    """
    step_messages = {
        ConversationStep.INITIATION: whatsapp_config.get('messages', 'step_initiation', 
                                                      fallback="Quelle est la zone concernée par l'incident ?"),
        ConversationStep.ZONE: whatsapp_config.get('messages', 'step_zone', 
                                                fallback="À quel étage se trouve l'incident ?"),
        ConversationStep.ETAGE: whatsapp_config.get('messages', 'step_etage', 
                                                 fallback="Veuillez décrire l'incident en quelques mots."),
        ConversationStep.DESCRIPTION: whatsapp_config.get('messages', 'step_description', 
                                                       fallback="Quelle est la priorité de cet incident ? (haute/moyenne/basse)"),
        ConversationStep.PRIORITE: whatsapp_config.get('messages', 'step_priorite', 
                                                    fallback="Veuillez indiquer votre numéro de téléphone pour être contacté."),
        ConversationStep.CONTACT: whatsapp_config.get('messages', 'step_contact', 
                                                   fallback="Veuillez indiquer votre adresse email."),
        ConversationStep.EMAIL: whatsapp_config.get('messages', 'step_email', 
                                                 fallback="Merci pour ces informations. Voici un récapitulatif de votre déclaration:\n\n{summary}\n\nEst-ce correct ? (oui/non)"),
        ConversationStep.CONFIRMATION: whatsapp_config.get('messages', 'step_confirmation', 
                                                        fallback="Votre incident a été enregistré avec succès. Merci de votre signalement.")
    }
    
    return step_messages.get(step, "Étape inconnue")


def get_previous_step(current_step: ConversationStep) -> Optional[ConversationStep]:
    """
    Récupère l'étape précédente dans le flux de conversation.
    
    Args:
        current_step: L'étape actuelle
        
    Returns:
        Optional[ConversationStep]: L'étape précédente ou None si déjà à la première étape
    """
    step_sequence = [
        ConversationStep.INITIATION,
        ConversationStep.ZONE,
        ConversationStep.ETAGE,
        ConversationStep.DESCRIPTION,
        ConversationStep.PRIORITE,
        ConversationStep.CONTACT,
        ConversationStep.EMAIL,
        ConversationStep.CONFIRMATION
    ]
    
    try:
        current_index = step_sequence.index(current_step)
        if current_index > 0:
            return step_sequence[current_index - 1]
        else:
            return None
    except ValueError:
        return None


def get_next_step(current_step: ConversationStep) -> Optional[ConversationStep]:
    """
    Récupère l'étape suivante dans le flux de conversation.
    
    Args:
        current_step: L'étape actuelle
        
    Returns:
        Optional[ConversationStep]: L'étape suivante ou None si déjà à la dernière étape
    """
    step_sequence = [
        ConversationStep.INITIATION,
        ConversationStep.ZONE,
        ConversationStep.ETAGE,
        ConversationStep.DESCRIPTION,
        ConversationStep.PRIORITE,
        ConversationStep.CONTACT,
        ConversationStep.EMAIL,
        ConversationStep.CONFIRMATION
    ]
    
    try:
        current_index = step_sequence.index(current_step)
        if current_index < len(step_sequence) - 1:
            return step_sequence[current_index + 1]
        else:
            return None
    except ValueError:
        return None


def process_step_response(conversation: ConversationState, message: str, 
                         db_connection: DatabaseConnection) -> str:
    """
    Traite la réponse de l'utilisateur en fonction de l'étape actuelle.
    
    Args:
        conversation: L'état de la conversation
        message: Le message de l'utilisateur
        db_connection: Connexion à la base de données
        
    Returns:
        str: La réponse à envoyer à l'utilisateur
    """
    current_step = conversation.current_step
    
    # Valider et traiter la réponse en fonction de l'étape
    if current_step == ConversationStep.INITIATION:
        # Validation de la zone
        if not message.strip():
            return whatsapp_config.get('messages', 'invalid_zone', 
                                     fallback="Veuillez indiquer une zone valide.")
        
        # Enregistrer la zone
        conversation.add_data('zone', message.strip())
        
        # Passer à l'étape suivante
        next_step = get_next_step(current_step)
        conversation.update_step(next_step)
        
        # Sauvegarder l'état
        conversation.save(db_connection)
        state_manager.save_state(conversation)
        
        return get_step_message(next_step)
    
    elif current_step == ConversationStep.ZONE:
        # Validation de l'étage
        if not message.strip():
            return whatsapp_config.get('messages', 'invalid_etage', 
                                     fallback="Veuillez indiquer un étage valide.")
        
        # Enregistrer l'étage
        conversation.add_data('etage', message.strip())
        
        # Passer à l'étape suivante
        next_step = get_next_step(current_step)
        conversation.update_step(next_step)
        
        # Sauvegarder l'état
        conversation.save(db_connection)
        state_manager.save_state(conversation)
        
        return get_step_message(next_step)
    
    elif current_step == ConversationStep.ETAGE:
        # Validation de la description
        if not message.strip() or len(message.strip()) < 10:
            return whatsapp_config.get('messages', 'invalid_description', 
                                     fallback="Veuillez fournir une description plus détaillée (au moins 10 caractères).")
        
        # Enregistrer la description
        conversation.add_data('description', message.strip())
        
        # Passer à l'étape suivante
        next_step = get_next_step(current_step)
        conversation.update_step(next_step)
        
        # Sauvegarder l'état
        conversation.save(db_connection)
        state_manager.save_state(conversation)
        
        return get_step_message(next_step)
    
    elif current_step == ConversationStep.DESCRIPTION:
        # Validation de la priorité
        priority = message.strip().lower()
        valid_priorities = ['haute', 'high', 'moyenne', 'medium', 'basse', 'low']
        
        if priority not in valid_priorities:
            return whatsapp_config.get('messages', 'invalid_priority', 
                                     fallback="Veuillez indiquer une priorité valide (haute/moyenne/basse).")
        
        # Normaliser la priorité
        if priority in ['haute', 'high']:
            normalized_priority = 'haute'
        elif priority in ['moyenne', 'medium']:
            normalized_priority = 'moyenne'
        else:
            normalized_priority = 'basse'
        
        # Enregistrer la priorité
        conversation.add_data('priorite', normalized_priority)
        
        # Passer à l'étape suivante
        next_step = get_next_step(current_step)
        conversation.update_step(next_step)
        
        # Sauvegarder l'état
        conversation.save(db_connection)
        state_manager.save_state(conversation)
        
        return get_step_message(next_step)
    
    elif current_step == ConversationStep.PRIORITE:
        # Validation du numéro de téléphone
        import re
        
        phone_pattern = r'^\+?[0-9]{10,15}$'
        if not re.match(phone_pattern, message.strip()):
            return whatsapp_config.get('messages', 'invalid_phone', 
                                     fallback="Veuillez indiquer un numéro de téléphone valide (10 à 15 chiffres).")
        
        # Enregistrer le numéro de téléphone
        conversation.add_data('reporter_phone', message.strip())
        
        # Passer à l'étape suivante
        next_step = get_next_step(current_step)
        conversation.update_step(next_step)
        
        # Sauvegarder l'état
        conversation.save(db_connection)
        state_manager.save_state(conversation)
        
        return get_step_message(next_step)
    
    elif current_step == ConversationStep.CONTACT:
        # Validation de l'email
        import re
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, message.strip()):
            return whatsapp_config.get('messages', 'invalid_email', 
                                     fallback="Veuillez indiquer une adresse email valide.")
        
        # Enregistrer l'email
        conversation.add_data('reporter_email', message.strip())
        
        # Passer à l'étape suivante
        next_step = get_next_step(current_step)
        conversation.update_step(next_step)
        
        # Sauvegarder l'état
        conversation.save(db_connection)
        state_manager.save_state(conversation)
        
        # Préparer le récapitulatif
        summary = generate_summary(conversation)
        
        # Remplacer le placeholder dans le message
        confirmation_message = get_step_message(next_step).format(summary=summary)
        
        return confirmation_message
    
    elif current_step == ConversationStep.EMAIL:
        # Validation de la confirmation
        confirmation = message.strip().lower()
        
        if confirmation in ['oui', 'yes', 'o', 'y']:
            # Créer l'incident
            from src.whatsapp.incident_api import create_incident_from_conversation
            
            success, incident_id, error = create_incident_from_conversation(conversation, db_connection)
            
            if success:
                # Passer à l'étape suivante
                next_step = get_next_step(current_step)
                conversation.update_step(next_step)
                conversation.complete()
                
                # Sauvegarder l'état
                conversation.save(db_connection)
                state_manager.save_state(conversation)
                
                # Message de confirmation avec l'ID de l'incident
                success_message = whatsapp_config.get('messages', 'success', 
                                                   fallback="Votre incident a été enregistré avec succès. Numéro de référence: {incident_id}")
                return success_message.format(incident_id=incident_id)
            else:
                # Erreur lors de la création de l'incident
                error_message = whatsapp_config.get('messages', 'incident_creation_error', 
                                                 fallback="Une erreur est survenue lors de la création de l'incident: {error}")
                return error_message.format(error=error)
        
        elif confirmation in ['non', 'no', 'n']:
            # Revenir à l'étape INITIATION pour recommencer
            conversation.reset()
            
            # Sauvegarder l'état
            conversation.save(db_connection)
            state_manager.save_state(conversation)
            
            restart_message = whatsapp_config.get('messages', 'restart_after_rejection', 
                                                fallback="D'accord, recommençons la déclaration.")
            return f"{restart_message}\n\n{get_step_message(ConversationStep.INITIATION)}"
        
        else:
            # Réponse invalide
            invalid_confirmation_message = whatsapp_config.get('messages', 'invalid_confirmation', 
                                                            fallback="Veuillez répondre par 'oui' ou 'non'.")
            return invalid_confirmation_message
    
    # Si on arrive ici, c'est une étape inconnue ou la conversation est déjà terminée
    return whatsapp_config.get('messages', 'unknown_step', 
                             fallback="Désolé, je ne comprends pas votre demande.")


def generate_summary(conversation: ConversationState) -> str:
    """
    Génère un récapitulatif de la déclaration d'incident.
    
    Args:
        conversation: L'état de la conversation
        
    Returns:
        str: Le récapitulatif formaté
    """
    data = conversation.collected_data
    
    summary = f"Bâtiment: {conversation.building_qr_code}\n"
    summary += f"Zone: {data.get('zone', 'Non spécifiée')}\n"
    summary += f"Étage: {data.get('etage', 'Non spécifié')}\n"
    summary += f"Description: {data.get('description', 'Non spécifiée')}\n"
    summary += f"Priorité: {data.get('priorite', 'Non spécifiée')}\n"
    summary += f"Contact: {data.get('reporter_phone', 'Non spécifié')}\n"
    summary += f"Email: {data.get('reporter_email', 'Non spécifié')}"
    
    return summary
