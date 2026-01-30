"""
Tests d'intégration pour le gestionnaire de conversations WhatsApp.

Ce module teste le flux complet de conversation pour l'intégration WhatsApp,
en simulant une séquence de messages et en vérifiant les réponses et l'état de la conversation.
"""

import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Ajouter le répertoire parent au path pour pouvoir importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.whatsapp.conversation_manager import ConversationManager
from src.whatsapp.state_manager import StateManager
from src.whatsapp.models import WhatsAppMessage, ConversationState
from src.db.connection import DatabaseConnection


class TestConversationManager(unittest.TestCase):
    """Tests pour le gestionnaire de conversations WhatsApp."""
    
    def setUp(self):
        """Configuration avant chaque test."""
        # Créer des mocks pour les dépendances
        self.db_connection = MagicMock(spec=DatabaseConnection)
        self.state_manager = MagicMock(spec=StateManager)
        
        # Créer l'instance du gestionnaire de conversations
        self.conversation_manager = ConversationManager(self.state_manager, self.db_connection)
        
        # Configurer le mock pour le state_manager
        self.state_manager.get_conversation_by_phone.return_value = None
        
        # Configurer le mock pour le building_dao
        self.building_dao_patcher = patch('src.whatsapp.conversation_steps.BuildingDAO')
        self.mock_building_dao = self.building_dao_patcher.start()
        mock_dao_instance = self.mock_building_dao.return_value
        mock_dao_instance.get_building_by_qr_code.return_value = {'id': 1, 'qr_code_number': 'QR12345'}
        
        # Configurer le mock pour l'API d'incident
        self.incident_api_patcher = patch('src.whatsapp.conversation_manager.create_incident_from_conversation')
        self.mock_incident_api = self.incident_api_patcher.start()
        self.mock_incident_api.return_value = (True, "INC123", None)
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        self.building_dao_patcher.stop()
        self.incident_api_patcher.stop()
    
    def test_new_conversation_welcome(self):
        """Teste la création d'une nouvelle conversation."""
        # Créer un message initial
        message = WhatsAppMessage(
            message_id="msg_1",
            conversation_id=None,
            user_phone="+33612345678",
            content="Bonjour",
            media_url=None,
            direction="inbound"
        )
        
        # Configurer le mock pour la sauvegarde de la conversation
        self.state_manager.get_conversation_by_phone.return_value = None
        
        # Traiter le message
        response = self.conversation_manager.process_message(message)
        
        # Vérifier que la réponse est le message de bienvenue
        self.assertIn("code QR du bâtiment", response)
        
        # Vérifier que la conversation a été créée et sauvegardée
        self.state_manager.save_conversation.assert_called_once()
    
    def test_complete_conversation_flow(self):
        """Teste un flux de conversation complet."""
        # Séquence de messages pour un flux complet
        messages = [
            # Message initial
            WhatsAppMessage(
                message_id="msg_1",
                conversation_id=None,
                user_phone="+33612345678",
                content="Bonjour",
                media_url=None,
                direction="inbound"
            ),
            # Code QR du bâtiment
            WhatsAppMessage(
                message_id="msg_2",
                conversation_id=None,
                user_phone="+33612345678",
                content="QR12345",
                media_url=None,
                direction="inbound"
            ),
            # Description de l'incident
            WhatsAppMessage(
                message_id="msg_3",
                conversation_id=None,
                user_phone="+33612345678",
                content="Fuite d'eau dans les toilettes",
                media_url=None,
                direction="inbound"
            ),
            # Zone
            WhatsAppMessage(
                message_id="msg_4",
                conversation_id=None,
                user_phone="+33612345678",
                content="Toilettes hommes",
                media_url=None,
                direction="inbound"
            ),
            # Étage
            WhatsAppMessage(
                message_id="msg_5",
                conversation_id=None,
                user_phone="+33612345678",
                content="RDC",
                media_url=None,
                direction="inbound"
            ),
            # Priorité
            WhatsAppMessage(
                message_id="msg_6",
                conversation_id=None,
                user_phone="+33612345678",
                content="haute",
                media_url=None,
                direction="inbound"
            ),
            # Téléphone
            WhatsAppMessage(
                message_id="msg_7",
                conversation_id=None,
                user_phone="+33612345678",
                content="+33612345678",
                media_url=None,
                direction="inbound"
            ),
            # Email
            WhatsAppMessage(
                message_id="msg_8",
                conversation_id=None,
                user_phone="+33612345678",
                content="test@example.com",
                media_url=None,
                direction="inbound"
            ),
            # Confirmation
            WhatsAppMessage(
                message_id="msg_9",
                conversation_id=None,
                user_phone="+33612345678",
                content="oui",
                media_url=None,
                direction="inbound"
            )
        ]
        
        # Simuler une conversation en cours
        conversation = ConversationState(
            conversation_id="conv_1",
            user_phone="+33612345678",
            current_step="welcome",
            building_qr_code=None,
            collected_data={},
            is_completed=False
        )
        
        # Configurer le mock pour retourner la conversation
        self.state_manager.get_conversation_by_phone.return_value = conversation
        
        # Traiter chaque message et vérifier les réponses
        expected_steps = [
            "building_qr",  # Après le message de bienvenue
            "description",  # Après le code QR
            "zone",         # Après la description
            "etage",        # Après la zone
            "priorite",     # Après l'étage
            "reporter_phone", # Après la priorité
            "reporter_email", # Après le téléphone
            "confirmation", # Après l'email
            "completed"     # Après la confirmation
        ]
        
        for i, message in enumerate(messages):
            response = self.conversation_manager.process_message(message)
            
            # Vérifier que l'étape a été mise à jour correctement
            if i < len(expected_steps):
                self.assertEqual(conversation.current_step, expected_steps[i])
            
            # Vérifier les réponses spécifiques
            if i == 0:  # Après le message de bienvenue
                self.assertIn("code QR du bâtiment", response)
            elif i == 7:  # Après l'email, on attend un résumé
                self.assertIn("résumé", response.lower())
            elif i == 8:  # Après la confirmation
                self.assertIn("INC123", response)  # ID de l'incident créé
                self.assertTrue(conversation.is_completed)
        
        # Vérifier que l'incident a été créé
        self.mock_incident_api.assert_called_once()
    
    def test_special_commands(self):
        """Teste les commandes spéciales (aide, annuler, etc.)."""
        # Créer une conversation en cours
        conversation = ConversationState(
            conversation_id="conv_1",
            user_phone="+33612345678",
            current_step="description",
            building_qr_code="QR12345",
            collected_data={},
            is_completed=False
        )
        
        # Configurer le mock pour retourner la conversation
        self.state_manager.get_conversation_by_phone.return_value = conversation
        
        # Tester la commande d'aide
        help_message = WhatsAppMessage(
            message_id="msg_help",
            conversation_id="conv_1",
            user_phone="+33612345678",
            content="aide",
            media_url=None,
            direction="inbound"
        )
        
        response = self.conversation_manager.process_message(help_message)
        self.assertIn("Commandes disponibles", response)
        
        # Tester la commande d'annulation
        cancel_message = WhatsAppMessage(
            message_id="msg_cancel",
            conversation_id="conv_1",
            user_phone="+33612345678",
            content="annuler",
            media_url=None,
            direction="inbound"
        )
        
        response = self.conversation_manager.process_message(cancel_message)
        self.assertIn("Conversation annulée", response)
        self.assertTrue(conversation.is_completed)
    
    def test_validation_errors(self):
        """Teste les erreurs de validation des entrées."""
        # Créer une conversation en cours à l'étape de la priorité
        conversation = ConversationState(
            conversation_id="conv_1",
            user_phone="+33612345678",
            current_step="priorite",
            building_qr_code="QR12345",
            collected_data={
                "description": "Fuite d'eau",
                "zone": "Toilettes",
                "etage": "RDC"
            },
            is_completed=False
        )
        
        # Configurer le mock pour retourner la conversation
        self.state_manager.get_conversation_by_phone.return_value = conversation
        
        # Envoyer une priorité invalide
        invalid_message = WhatsAppMessage(
            message_id="msg_invalid",
            conversation_id="conv_1",
            user_phone="+33612345678",
            content="urgente",  # Priorité invalide
            media_url=None,
            direction="inbound"
        )
        
        response = self.conversation_manager.process_message(invalid_message)
        self.assertIn("invalide", response)
        
        # Vérifier que l'étape n'a pas changé
        self.assertEqual(conversation.current_step, "priorite")
    
    def test_incident_creation_error(self):
        """Teste la gestion des erreurs lors de la création d'incident."""
        # Configurer le mock pour simuler une erreur lors de la création d'incident
        self.mock_incident_api.return_value = (False, None, "Erreur technique: Base de données indisponible")
        
        # Créer une conversation à l'étape de confirmation
        conversation = ConversationState(
            conversation_id="conv_1",
            user_phone="+33612345678",
            current_step="confirmation",
            building_qr_code="QR12345",
            collected_data={
                "description": "Fuite d'eau",
                "zone": "Toilettes",
                "etage": "RDC",
                "priorite": "haute",
                "reporter_phone": "+33612345678",
                "reporter_email": "test@example.com"
            },
            is_completed=False
        )
        
        # Configurer le mock pour retourner la conversation
        self.state_manager.get_conversation_by_phone.return_value = conversation
        
        # Envoyer une confirmation positive
        confirm_message = WhatsAppMessage(
            message_id="msg_confirm",
            conversation_id="conv_1",
            user_phone="+33612345678",
            content="oui",
            media_url=None,
            direction="inbound"
        )
        
        response = self.conversation_manager.process_message(confirm_message)
        self.assertIn("Erreur technique", response)


if __name__ == '__main__':
    unittest.main()
