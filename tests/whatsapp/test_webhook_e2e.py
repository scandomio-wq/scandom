"""
Tests de bout en bout pour le webhook Twilio WhatsApp.

Ce module simule des requêtes webhook Twilio pour tester l'intégration complète
du système de signalement d'incidents via WhatsApp.
"""

import unittest
import sys
import os
import json
import requests
from unittest.mock import patch

# Ajouter le répertoire parent au path pour pouvoir importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# URL de base pour les tests (à remplacer par l'URL ngrok lors des tests réels)
BASE_URL = "http://localhost:5000/api/webhook"


class TestWebhookE2E(unittest.TestCase):
    """Tests de bout en bout pour le webhook Twilio."""
    
    def setUp(self):
        """Configuration avant chaque test."""
        # Désactiver la validation de signature Twilio pour les tests
        self.validation_patcher = patch('src.whatsapp.security.validate_twilio_request', return_value=True)
        self.validation_patcher.start()
        
        # Numéro de téléphone de test
        self.test_phone = "+33612345678"
        
        # Compteur pour les SIDs uniques
        self.message_counter = 0
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        self.validation_patcher.stop()
    
    def _get_next_sid(self):
        """Génère un SID unique pour chaque message."""
        self.message_counter += 1
        return f"SM{self.message_counter:012d}"
    
    def _send_message(self, body, from_phone=None):
        """
        Envoie un message simulé au webhook Twilio.
        
        Args:
            body: Corps du message
            from_phone: Numéro de téléphone de l'expéditeur (optionnel)
            
        Returns:
            Response: Réponse du webhook
        """
        if from_phone is None:
            from_phone = self.test_phone
        
        # Créer les données du formulaire Twilio
        data = {
            'MessageSid': self._get_next_sid(),
            'From': from_phone,
            'To': '+14155238886',  # Numéro Twilio
            'Body': body,
            'NumMedia': '0'
        }
        
        # Envoyer la requête POST au webhook
        response = requests.post(f"{BASE_URL}/twilio", data=data)
        
        return response
    
    def test_conversation_flow(self):
        """Teste un flux de conversation complet."""
        # Séquence de messages pour un flux complet
        messages = [
            "Bonjour",                      # Message initial
            "QR12345",                      # Code QR du bâtiment
            "Fuite d'eau dans les toilettes", # Description
            "Toilettes hommes",             # Zone
            "RDC",                          # Étage
            "haute",                        # Priorité
            "+33612345678",                 # Téléphone
            "test@example.com",             # Email
            "oui"                           # Confirmation
        ]
        
        # Envoyer chaque message et vérifier les réponses
        for message in messages:
            response = self._send_message(message)
            
            # Vérifier que la requête a réussi
            self.assertEqual(response.status_code, 200)
            
            # Vérifier que la réponse est au format TwiML
            self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', response.text)
            self.assertIn('<Response>', response.text)
            self.assertIn('<Message>', response.text)
            
            # Vérifier les réponses spécifiques
            if message == "Bonjour":
                self.assertIn("code QR", response.text)
            elif message == "QR12345":
                self.assertIn("décrire", response.text)
            elif message == "oui":
                # Après la confirmation, on attend un message de succès
                self.assertIn("succès", response.text.lower())
    
    def test_special_commands(self):
        """Teste les commandes spéciales."""
        # Démarrer une conversation
        self._send_message("Bonjour")
        
        # Tester la commande d'aide
        response = self._send_message("aide")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Commandes disponibles", response.text)
        
        # Tester la commande d'annulation
        response = self._send_message("annuler")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Conversation annulée", response.text)
    
    def test_message_status_callback(self):
        """Teste le callback de statut de message."""
        # Créer les données du formulaire pour un callback de statut
        data = {
            'MessageSid': self._get_next_sid(),
            'MessageStatus': 'delivered',
            'To': self.test_phone,
            'From': '+14155238886'
        }
        
        # Envoyer la requête POST au webhook de statut
        response = requests.post(f"{BASE_URL}/status", data=data)
        
        # Vérifier que la requête a réussi
        self.assertEqual(response.status_code, 200)


class TestWebhookMock(unittest.TestCase):
    """Tests avec mock pour le webhook Twilio."""
    
    def setUp(self):
        """Configuration avant chaque test."""
        # Patcher les dépendances
        self.app_patcher = patch('src.app.app')
        self.mock_app = self.app_patcher.start()
        
        # Importer le blueprint après le patch
        from src.whatsapp.webhook import whatsapp_bp
        
        # Configurer le client de test
        self.mock_app.test_client.return_value.post.return_value.status_code = 200
        self.mock_app.test_client.return_value.post.return_value.data = b'<Response><Message>Test</Message></Response>'
        
        # Numéro de téléphone de test
        self.test_phone = "+33612345678"
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        self.app_patcher.stop()
    
    @patch('src.whatsapp.webhook.validate_twilio_request', return_value=True)
    @patch('src.whatsapp.webhook.conversation_manager.process_message')
    def test_webhook_message_processing(self, mock_process_message, mock_validate):
        """Teste le traitement des messages par le webhook."""
        # Configurer le mock pour retourner une réponse
        mock_process_message.return_value = "Message reçu"
        
        # Créer un client de test
        client = self.mock_app.test_client()
        
        # Créer les données du formulaire
        data = {
            'MessageSid': 'SM123456789012',
            'From': self.test_phone,
            'To': '+14155238886',
            'Body': 'Test message',
            'NumMedia': '0'
        }
        
        # Envoyer la requête POST au webhook
        response = client.post('/api/webhook/twilio', data=data)
        
        # Vérifier que la requête a réussi
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que le message a été traité
        mock_process_message.assert_called_once()
        
        # Vérifier que l'objet WhatsAppMessage a été créé correctement
        message_arg = mock_process_message.call_args[0][0]
        self.assertEqual(message_arg.from_phone, self.test_phone)
        self.assertEqual(message_arg.body, 'Test message')


if __name__ == '__main__':
    unittest.main()
