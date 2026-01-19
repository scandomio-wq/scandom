"""
Tests pour les cas limites de l'application QR Building Registry.
"""

import json
import os
import unittest
from unittest.mock import patch, MagicMock, mock_open

import jsonschema
import psycopg2

from src.db.building_dao import BuildingDAO
from src.models.building import Building
from src.qr.generator import QRCodeGenerator
from src.utils.validators import validate_email, validate_qr_code_number, validate_json_file, validate_building_data


class TestEmailValidation(unittest.TestCase):
    """Tests pour la validation des emails."""

    def test_valid_emails(self):
        """Test de validation d'emails valides."""
        valid_emails = [
            "test@example.com",
            "test.user@example.co.uk",
            "test+user@example.org",
            "test-user@example.net",
            "test_user@example.io"
        ]
        
        for email in valid_emails:
            with self.subTest(email=email):
                self.assertTrue(validate_email(email))
    
    def test_invalid_emails(self):
        """Test de validation d'emails invalides."""
        invalid_emails = [
            "test",
            "test@",
            "@example.com",
            "test@example",
            "test@.com",
            "test@example..com",
            "test@exam ple.com",
            "test user@example.com"
        ]
        
        for email in invalid_emails:
            with self.subTest(email=email):
                self.assertFalse(validate_email(email))
    
    def test_empty_email(self):
        """Test de validation d'un email vide (considéré comme valide car optionnel)."""
        self.assertTrue(validate_email(""))
        self.assertTrue(validate_email(None))


class TestQRCodeNumberValidation(unittest.TestCase):
    """Tests pour la validation des QR_CODE_NUMBER."""

    def test_valid_qr_codes(self):
        """Test de validation de QR_CODE_NUMBER valides."""
        valid_qr_codes = [
            "QR1234567890",
            "QR0000000001",
            "QR9999999999"
        ]
        
        for qr_code in valid_qr_codes:
            with self.subTest(qr_code=qr_code):
                self.assertTrue(validate_qr_code_number(qr_code))
    
    def test_invalid_qr_codes(self):
        """Test de validation de QR_CODE_NUMBER invalides."""
        invalid_qr_codes = [
            "1234567890",
            "QR",
            "QRabcdef",
            "qr1234567890",
            "QR 1234567890",
            "QR-1234567890",
            "QR_1234567890"
        ]
        
        for qr_code in invalid_qr_codes:
            with self.subTest(qr_code=qr_code):
                self.assertFalse(validate_qr_code_number(qr_code))
    
    def test_empty_qr_code(self):
        """Test de validation d'un QR_CODE_NUMBER vide (considéré comme invalide)."""
        self.assertFalse(validate_qr_code_number(""))
        self.assertFalse(validate_qr_code_number(None))


class TestJSONValidation(unittest.TestCase):
    """Tests pour la validation des fichiers JSON."""

    def setUp(self):
        """Configuration avant chaque test."""
        self.config_patcher = patch('src.utils.validators.get_config')
        self.mock_get_config = self.config_patcher.start()
        self.mock_config = MagicMock()
        self.mock_config.get.return_value = 1048576  # max_json_size (1 Mo)
        self.mock_get_config.return_value = self.mock_config
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        self.config_patcher.stop()
    
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('builtins.open', new_callable=mock_open, read_data='{"LOCATION": "123 Rue de Test"}')
    def test_valid_json_file(self, mock_file, mock_getsize, mock_exists):
        """Test de validation d'un fichier JSON valide."""
        # Configuration des mocks
        mock_exists.return_value = True
        mock_getsize.return_value = 100
        
        # Exécution
        result = validate_json_file("test.json")
        
        # Vérifications
        self.assertEqual(result, {"LOCATION": "123 Rue de Test"})
    
    @patch('os.path.exists')
    def test_file_not_found(self, mock_exists):
        """Test de validation d'un fichier JSON inexistant."""
        # Configuration du mock
        mock_exists.return_value = False
        
        # Vérification que l'exception est bien levée
        with self.assertRaises(FileNotFoundError):
            validate_json_file("nonexistent.json")
    
    @patch('os.path.exists')
    @patch('os.path.getsize')
    def test_empty_file(self, mock_getsize, mock_exists):
        """Test de validation d'un fichier JSON vide."""
        # Configuration des mocks
        mock_exists.return_value = True
        mock_getsize.return_value = 0
        
        # Vérification que l'exception est bien levée
        with self.assertRaises(ValueError):
            validate_json_file("empty.json")
    
    @patch('os.path.exists')
    @patch('os.path.getsize')
    def test_file_too_large(self, mock_getsize, mock_exists):
        """Test de validation d'un fichier JSON trop volumineux."""
        # Configuration des mocks
        mock_exists.return_value = True
        mock_getsize.return_value = 2000000  # 2 Mo
        
        # Vérification que l'exception est bien levée
        with self.assertRaises(ValueError):
            validate_json_file("large.json")
    
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('builtins.open', new_callable=mock_open, read_data='{"LOCATION": "123 Rue de Test", "INVALID_FIELD": "test"}')
    def test_invalid_schema(self, mock_file, mock_getsize, mock_exists):
        """Test de validation d'un fichier JSON avec un schéma invalide."""
        # Configuration des mocks
        mock_exists.return_value = True
        mock_getsize.return_value = 100
        
        # Vérification que l'exception est bien levée
        with self.assertRaises(jsonschema.ValidationError):
            validate_json_file("invalid_schema.json")
    
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('builtins.open', new_callable=mock_open, read_data='{"LOCATION": "123 Rue de Test", "EMAIL_GESTIONNAIRE": "invalid"}')
    def test_invalid_email_in_json(self, mock_file, mock_getsize, mock_exists):
        """Test de validation d'un fichier JSON avec un email invalide."""
        # Configuration des mocks
        mock_exists.return_value = True
        mock_getsize.return_value = 100
        
        # Vérification que l'exception est bien levée
        with self.assertRaises(jsonschema.ValidationError):
            validate_json_file("invalid_email.json")


class TestBuildingDataValidation(unittest.TestCase):
    """Tests pour la validation des données d'un bâtiment."""

    def test_valid_building_data(self):
        """Test de validation de données valides."""
        data = {
            "LOCATION": "123 Rue de Test",
            "EMAIL_GESTIONNAIRE": "test@example.com",
            "NOTES": "Bâtiment de test"
        }
        
        errors = validate_building_data(data)
        self.assertEqual(len(errors), 0)
    
    def test_missing_location(self):
        """Test de validation de données sans LOCATION."""
        data = {
            "EMAIL_GESTIONNAIRE": "test@example.com",
            "NOTES": "Bâtiment de test"
        }
        
        errors = validate_building_data(data)
        self.assertEqual(len(errors), 1)
        self.assertIn("LOCATION est obligatoire", errors[0])
    
    def test_empty_location(self):
        """Test de validation de données avec LOCATION vide."""
        data = {
            "LOCATION": "",
            "EMAIL_GESTIONNAIRE": "test@example.com",
            "NOTES": "Bâtiment de test"
        }
        
        errors = validate_building_data(data)
        self.assertEqual(len(errors), 1)
        self.assertIn("LOCATION est obligatoire", errors[0])
    
    def test_location_too_long(self):
        """Test de validation de données avec LOCATION trop longue."""
        data = {
            "LOCATION": "x" * 256,
            "EMAIL_GESTIONNAIRE": "test@example.com",
            "NOTES": "Bâtiment de test"
        }
        
        errors = validate_building_data(data)
        self.assertEqual(len(errors), 1)
        self.assertIn("LOCATION ne doit pas dépasser 255 caractères", errors[0])
    
    def test_invalid_email(self):
        """Test de validation de données avec un email invalide."""
        data = {
            "LOCATION": "123 Rue de Test",
            "EMAIL_GESTIONNAIRE": "invalid",
            "NOTES": "Bâtiment de test"
        }
        
        errors = validate_building_data(data)
        self.assertEqual(len(errors), 1)
        self.assertIn("format de l'email", errors[0])
    
    def test_email_too_long(self):
        """Test de validation de données avec un email trop long."""
        data = {
            "LOCATION": "123 Rue de Test",
            "EMAIL_GESTIONNAIRE": "x" * 90 + "@example.com",
            "NOTES": "Bâtiment de test"
        }
        
        errors = validate_building_data(data)
        self.assertEqual(len(errors), 1)
        self.assertIn("email du gestionnaire ne doit pas dépasser 100 caractères", errors[0])
    
    def test_invalid_qr_code_number(self):
        """Test de validation de données avec un QR_CODE_NUMBER invalide."""
        data = {
            "LOCATION": "123 Rue de Test",
            "EMAIL_GESTIONNAIRE": "test@example.com",
            "NOTES": "Bâtiment de test",
            "QR_CODE_NUMBER": "invalid"
        }
        
        errors = validate_building_data(data)
        self.assertEqual(len(errors), 1)
        self.assertIn("format de QR_CODE_NUMBER est invalide", errors[0])


class TestQRGenerationFailures(unittest.TestCase):
    """Tests pour les échecs de génération de QR codes."""

    def setUp(self):
        """Configuration avant chaque test."""
        self.generator = QRCodeGenerator()
    
    @patch('os.path.isdir')
    def test_destination_not_exists(self, mock_isdir):
        """Test de génération avec une destination inexistante."""
        # Configuration du mock
        mock_isdir.return_value = False
        
        # Vérification que l'exception est bien levée
        with self.assertRaises(OSError):
            self.generator.generate_qr_code("QR1234567890", "/nonexistent/dir")
    
    @patch('os.path.isdir')
    @patch('os.access')
    def test_destination_not_writable(self, mock_access, mock_isdir):
        """Test de génération avec une destination non accessible en écriture."""
        # Configuration des mocks
        mock_isdir.return_value = True
        mock_access.return_value = False
        
        # Vérification que l'exception est bien levée
        with self.assertRaises(OSError):
            self.generator.generate_qr_code("QR1234567890", "/tmp")
    
    @patch('os.path.isdir')
    @patch('os.access')
    @patch('qrcode.QRCode')
    def test_qr_generation_error(self, mock_qrcode, mock_access, mock_isdir):
        """Test d'erreur lors de la génération du QR code."""
        # Configuration des mocks
        mock_isdir.return_value = True
        mock_access.return_value = True
        mock_qr = MagicMock()
        mock_qrcode.return_value = mock_qr
        mock_qr.make.side_effect = Exception("QR generation error")
        
        # Vérification que l'exception est bien levée
        with self.assertRaises(Exception):
            self.generator.generate_qr_code("QR1234567890", "/tmp")
    
    @patch('os.path.isdir')
    @patch('os.access')
    @patch('qrcode.QRCode')
    @patch('PIL.Image.Image.save')
    def test_save_error(self, mock_save, mock_qrcode, mock_access, mock_isdir):
        """Test d'erreur lors de la sauvegarde du QR code."""
        # Configuration des mocks
        mock_isdir.return_value = True
        mock_access.return_value = True
        mock_qr = MagicMock()
        mock_qrcode.return_value = mock_qr
        mock_img = MagicMock()
        mock_qr.make_image.return_value = mock_img
        mock_img.resize.return_value = mock_img
        mock_save.side_effect = OSError("Save error")
        
        # Vérification que l'exception est bien levée
        with self.assertRaises(OSError):
            self.generator.generate_qr_code("QR1234567890", "/tmp")


if __name__ == '__main__':
    unittest.main()
