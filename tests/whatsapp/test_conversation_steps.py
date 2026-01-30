"""
Tests unitaires pour les étapes de conversation WhatsApp.

Ce module teste les fonctions de validation et de traitement des étapes
de conversation pour l'intégration WhatsApp.
"""

import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Ajouter le répertoire parent au path pour pouvoir importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.whatsapp.conversation_steps import (
    validate_building_qr, validate_description, validate_zone,
    validate_etage, validate_priorite, validate_phone,
    validate_email_address, validate_confirmation, generate_summary
)
from src.whatsapp.models import ConversationState
from src.db.connection import DatabaseConnection


class TestConversationSteps(unittest.TestCase):
    """Tests pour les fonctions de validation des étapes de conversation."""
    
    def setUp(self):
        """Configuration avant chaque test."""
        self.db_connection = MagicMock(spec=DatabaseConnection)
        
        # Mock pour le BuildingDAO
        self.building_dao_patcher = patch('src.whatsapp.conversation_steps.BuildingDAO')
        self.mock_building_dao = self.building_dao_patcher.start()
        
        # Configurer le mock pour retourner un bâtiment valide pour QR12345
        mock_dao_instance = self.mock_building_dao.return_value
        mock_dao_instance.get_building_by_qr_code.return_value = {'id': 1, 'qr_code_number': 'QR12345'}
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        self.building_dao_patcher.stop()
    
    def test_validate_building_qr_valid(self):
        """Teste la validation d'un code QR de bâtiment valide."""
        is_valid, value, error = validate_building_qr("QR12345", self.db_connection)
        self.assertTrue(is_valid)
        self.assertEqual(value, "QR12345")
        self.assertIsNone(error)
    
    def test_validate_building_qr_invalid_format(self):
        """Teste la validation d'un code QR de bâtiment avec format invalide."""
        is_valid, value, error = validate_building_qr("INVALID", self.db_connection)
        self.assertFalse(is_valid)
        self.assertIsNone(value)
        self.assertIsNotNone(error)
    
    def test_validate_building_qr_not_found(self):
        """Teste la validation d'un code QR de bâtiment qui n'existe pas."""
        # Configurer le mock pour retourner None (bâtiment non trouvé)
        mock_dao_instance = self.mock_building_dao.return_value
        mock_dao_instance.get_building_by_qr_code.return_value = None
        
        is_valid, value, error = validate_building_qr("QR99999", self.db_connection)
        self.assertFalse(is_valid)
        self.assertIsNone(value)
        self.assertIn("non trouvé", error)
    
    def test_validate_description_valid(self):
        """Teste la validation d'une description valide."""
        is_valid, value, error = validate_description("Fuite d'eau dans les toilettes")
        self.assertTrue(is_valid)
        self.assertEqual(value, "Fuite d'eau dans les toilettes")
        self.assertIsNone(error)
    
    def test_validate_description_too_short(self):
        """Teste la validation d'une description trop courte."""
        is_valid, value, error = validate_description("OK")
        self.assertFalse(is_valid)
        self.assertIsNone(value)
        self.assertIn("trop courte", error)
    
    def test_validate_description_too_long(self):
        """Teste la validation d'une description trop longue."""
        long_text = "A" * 201  # 201 caractères
        is_valid, value, error = validate_description(long_text)
        self.assertFalse(is_valid)
        self.assertIsNone(value)
        self.assertIn("trop longue", error)
    
    def test_validate_zone_valid(self):
        """Teste la validation d'une zone valide."""
        is_valid, value, error = validate_zone("Hall d'entrée")
        self.assertTrue(is_valid)
        self.assertEqual(value, "Hall d'entrée")
        self.assertIsNone(error)
    
    def test_validate_zone_too_short(self):
        """Teste la validation d'une zone trop courte."""
        is_valid, value, error = validate_zone("A")
        self.assertFalse(is_valid)
        self.assertIsNone(value)
        self.assertIn("trop courte", error)
    
    def test_validate_etage_valid(self):
        """Teste la validation d'un étage valide."""
        is_valid, value, error = validate_etage("1er")
        self.assertTrue(is_valid)
        self.assertEqual(value, "1er")
        self.assertIsNone(error)
    
    def test_validate_priorite_valid_haute(self):
        """Teste la validation d'une priorité haute."""
        is_valid, value, error = validate_priorite("haute")
        self.assertTrue(is_valid)
        self.assertEqual(value, "haute")
        self.assertIsNone(error)
    
    def test_validate_priorite_valid_alternative(self):
        """Teste la validation d'une priorité avec valeur alternative."""
        is_valid, value, error = validate_priorite("high")
        self.assertTrue(is_valid)
        self.assertEqual(value, "haute")
        self.assertIsNone(error)
    
    def test_validate_priorite_invalid(self):
        """Teste la validation d'une priorité invalide."""
        is_valid, value, error = validate_priorite("urgente")
        self.assertFalse(is_valid)
        self.assertIsNone(value)
        self.assertIn("invalide", error)
    
    def test_validate_phone_valid(self):
        """Teste la validation d'un numéro de téléphone valide."""
        is_valid, value, error = validate_phone("+33612345678")
        self.assertTrue(is_valid)
        self.assertEqual(value, "+33612345678")
        self.assertIsNone(error)
    
    def test_validate_phone_invalid(self):
        """Teste la validation d'un numéro de téléphone invalide."""
        is_valid, value, error = validate_phone("0612345678")
        self.assertFalse(is_valid)
        self.assertIsNone(value)
        self.assertIn("Format de téléphone invalide", error)
    
    def test_validate_email_valid(self):
        """Teste la validation d'un email valide."""
        with patch('src.whatsapp.conversation_steps.validate_email', return_value=True):
            is_valid, value, error = validate_email_address("test@example.com")
            self.assertTrue(is_valid)
            self.assertEqual(value, "test@example.com")
            self.assertIsNone(error)
    
    def test_validate_email_invalid(self):
        """Teste la validation d'un email invalide."""
        with patch('src.whatsapp.conversation_steps.validate_email', return_value=False):
            is_valid, value, error = validate_email_address("invalid-email")
            self.assertFalse(is_valid)
            self.assertIsNone(value)
            self.assertIn("Format d'email invalide", error)
    
    def test_validate_confirmation_positive(self):
        """Teste la validation d'une confirmation positive."""
        is_valid, confirmed, error = validate_confirmation("oui")
        self.assertTrue(is_valid)
        self.assertTrue(confirmed)
        self.assertIsNone(error)
    
    def test_validate_confirmation_negative(self):
        """Teste la validation d'une confirmation négative."""
        is_valid, confirmed, error = validate_confirmation("non")
        self.assertTrue(is_valid)
        self.assertFalse(confirmed)
        self.assertIsNone(error)
    
    def test_validate_confirmation_invalid(self):
        """Teste la validation d'une confirmation invalide."""
        is_valid, confirmed, error = validate_confirmation("peut-être")
        self.assertFalse(is_valid)
        self.assertIsNone(confirmed)
        self.assertIn("Réponse invalide", error)
    
    def test_generate_summary(self):
        """Teste la génération d'un résumé de conversation."""
        conversation = ConversationState(
            conversation_id="test_id",
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
        
        summary = generate_summary(conversation)
        
        self.assertIn("QR12345", summary)
        self.assertIn("Fuite d'eau", summary)
        self.assertIn("Toilettes", summary)
        self.assertIn("RDC", summary)
        self.assertIn("haute", summary)
        self.assertIn("+33612345678", summary)
        self.assertIn("test@example.com", summary)


if __name__ == '__main__':
    unittest.main()
