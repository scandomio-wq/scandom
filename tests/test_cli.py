"""
Tests pour les interfaces CLI de l'application QR Building Registry.
"""

import json
import os
import sys
import unittest
from io import StringIO
from unittest.mock import patch, MagicMock

from src.cli import import_building, generate_qr, find_building
from src.models.building import Building


class TestImportBuildingCLI(unittest.TestCase):
    """Tests pour l'interface CLI d'importation de bâtiments."""

    def setUp(self):
        """Configuration avant chaque test."""
        self.building = Building(
            id=1,
            location="123 Rue de Test",
            email_gestionnaire="test@example.com",
            notes="Bâtiment de test",
            qr_code_number="QR1234567890"
        )
        
        # Capturer stdout
        self.stdout_patcher = patch('sys.stdout', new_callable=StringIO)
        self.mock_stdout = self.stdout_patcher.start()
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        self.stdout_patcher.stop()
    
    @patch('src.cli.import_building.validate_json_file')
    @patch('src.cli.import_building.BuildingDAO')
    @patch('src.cli.import_building.QRCodeGenerator')
    def test_import_building_success(self, mock_qr_generator, mock_dao, mock_validate):
        """Test d'importation d'un bâtiment avec succès."""
        # Configuration des mocks
        mock_validate.return_value = {
            "LOCATION": "123 Rue de Test",
            "EMAIL_GESTIONNAIRE": "test@example.com",
            "NOTES": "Bâtiment de test"
        }
        
        mock_dao_instance = MagicMock()
        mock_dao.return_value = mock_dao_instance
        mock_dao_instance.create_building.return_value = self.building
        
        mock_qr_generator_instance = MagicMock()
        mock_qr_generator.return_value = mock_qr_generator_instance
        mock_qr_generator_instance.generate_qr_code.return_value = (True, "/path/to/QR1234567890.png")
        
        # Exécution
        with patch.object(sys, 'argv', ['import_building.py', 'test.json']):
            with self.assertRaises(SystemExit) as cm:
                import_building.main()
            
            # Vérification du code de sortie
            self.assertEqual(cm.exception.code, 0)
        
        # Vérification des appels
        mock_validate.assert_called_once_with('test.json')
        mock_dao_instance.create_building.assert_called_once()
        mock_qr_generator_instance.generate_qr_code.assert_called_once()
        
        # Vérification de la sortie
        output = self.mock_stdout.getvalue()
        self.assertIn("Bâtiment importé avec succès", output)
        self.assertIn("ID: 1", output)
        self.assertIn("QR_CODE_NUMBER: QR1234567890", output)
    
    @patch('src.cli.import_building.validate_json_file')
    def test_import_building_invalid_json(self, mock_validate):
        """Test d'importation avec un fichier JSON invalide."""
        # Configuration du mock
        mock_validate.side_effect = ValueError("Données invalides")
        
        # Exécution
        with patch.object(sys, 'argv', ['import_building.py', 'invalid.json']):
            with self.assertRaises(SystemExit) as cm:
                import_building.main()
            
            # Vérification du code de sortie
            self.assertEqual(cm.exception.code, 3)
        
        # Vérification de la sortie
        output = self.mock_stdout.getvalue()
        self.assertIn("Erreur: Données invalides", output)


class TestGenerateQRCLI(unittest.TestCase):
    """Tests pour l'interface CLI de génération de QR codes."""

    def setUp(self):
        """Configuration avant chaque test."""
        self.building = Building(
            id=1,
            location="123 Rue de Test",
            email_gestionnaire="test@example.com",
            notes="Bâtiment de test",
            qr_code_number="QR1234567890"
        )
        
        # Capturer stdout
        self.stdout_patcher = patch('sys.stdout', new_callable=StringIO)
        self.mock_stdout = self.stdout_patcher.start()
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        self.stdout_patcher.stop()
    
    @patch('src.cli.generate_qr.BuildingDAO')
    @patch('src.cli.generate_qr.QRCodeGenerator')
    def test_generate_qr_by_id_success(self, mock_qr_generator, mock_dao):
        """Test de génération de QR code par ID avec succès."""
        # Configuration des mocks
        mock_dao_instance = MagicMock()
        mock_dao.return_value = mock_dao_instance
        mock_dao_instance.get_building_by_id.return_value = self.building
        
        mock_qr_generator_instance = MagicMock()
        mock_qr_generator.return_value = mock_qr_generator_instance
        mock_qr_generator_instance.qr_code_exists.return_value = False
        mock_qr_generator_instance.generate_qr_code.return_value = (True, "/path/to/QR1234567890.png")
        
        # Exécution
        with patch.object(sys, 'argv', ['generate_qr.py', '--id', '1']):
            with self.assertRaises(SystemExit) as cm:
                generate_qr.main()
            
            # Vérification du code de sortie
            self.assertEqual(cm.exception.code, 0)
        
        # Vérification des appels
        mock_dao_instance.get_building_by_id.assert_called_once_with(1)
        mock_qr_generator_instance.generate_qr_code.assert_called_once()
        
        # Vérification de la sortie
        output = self.mock_stdout.getvalue()
        self.assertIn("QR code généré avec succès", output)
    
    @patch('src.cli.generate_qr.BuildingDAO')
    def test_generate_qr_building_not_found(self, mock_dao):
        """Test de génération de QR code pour un bâtiment inexistant."""
        # Configuration du mock
        mock_dao_instance = MagicMock()
        mock_dao.return_value = mock_dao_instance
        mock_dao_instance.get_building_by_id.return_value = None
        
        # Exécution
        with patch.object(sys, 'argv', ['generate_qr.py', '--id', '999']):
            with self.assertRaises(SystemExit) as cm:
                generate_qr.main()
            
            # Vérification du code de sortie
            self.assertEqual(cm.exception.code, 2)
        
        # Vérification de la sortie
        output = self.mock_stdout.getvalue()
        self.assertIn("Erreur: Bâtiment introuvable", output)


class TestFindBuildingCLI(unittest.TestCase):
    """Tests pour l'interface CLI de recherche d'immeubles."""

    def setUp(self):
        """Configuration avant chaque test."""
        self.building = Building(
            id=1,
            location="123 Rue de Test",
            email_gestionnaire="test@example.com",
            notes="Bâtiment de test",
            qr_code_number="QR1234567890"
        )
        
        # Capturer stdout
        self.stdout_patcher = patch('sys.stdout', new_callable=StringIO)
        self.mock_stdout = self.stdout_patcher.start()
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        self.stdout_patcher.stop()
    
    @patch('src.cli.find_building.BuildingDAO')
    def test_find_building_text_format(self, mock_dao):
        """Test de recherche d'un immeuble avec format de sortie texte."""
        # Configuration du mock
        mock_dao_instance = MagicMock()
        mock_dao.return_value = mock_dao_instance
        mock_dao_instance.get_building_by_qr_code.return_value = self.building
        
        # Exécution
        with patch.object(sys, 'argv', ['find_building.py', 'QR1234567890']):
            with self.assertRaises(SystemExit) as cm:
                find_building.main()
            
            # Vérification du code de sortie
            self.assertEqual(cm.exception.code, 0)
        
        # Vérification des appels
        mock_dao_instance.get_building_by_qr_code.assert_called_once_with('QR1234567890')
        
        # Vérification de la sortie
        output = self.mock_stdout.getvalue()
        self.assertIn("ID: 1", output)
        self.assertIn("LOCATION: 123 Rue de Test", output)
        self.assertIn("QR_CODE_NUMBER: QR1234567890", output)
    
    @patch('src.cli.find_building.BuildingDAO')
    def test_find_building_json_format(self, mock_dao):
        """Test de recherche d'un immeuble avec format de sortie JSON."""
        # Configuration du mock
        mock_dao_instance = MagicMock()
        mock_dao.return_value = mock_dao_instance
        mock_dao_instance.get_building_by_qr_code.return_value = self.building
        
        # Exécution
        with patch.object(sys, 'argv', ['find_building.py', 'QR1234567890', '--format', 'json']):
            with self.assertRaises(SystemExit) as cm:
                find_building.main()
            
            # Vérification du code de sortie
            self.assertEqual(cm.exception.code, 0)
        
        # Vérification des appels
        mock_dao_instance.get_building_by_qr_code.assert_called_once_with('QR1234567890')
        
        # Vérification de la sortie
        output = self.mock_stdout.getvalue()
        # Vérifier que la sortie est un JSON valide
        building_data = json.loads(output)
        self.assertEqual(building_data["ID"], 1)
        self.assertEqual(building_data["LOCATION"], "123 Rue de Test")
        self.assertEqual(building_data["QR_CODE_NUMBER"], "QR1234567890")
    
    @patch('src.cli.find_building.BuildingDAO')
    def test_find_building_not_found(self, mock_dao):
        """Test de recherche d'un immeuble inexistant."""
        # Configuration du mock
        mock_dao_instance = MagicMock()
        mock_dao.return_value = mock_dao_instance
        mock_dao_instance.get_building_by_qr_code.return_value = None
        
        # Exécution
        with patch.object(sys, 'argv', ['find_building.py', 'QR9999999999']):
            with self.assertRaises(SystemExit) as cm:
                find_building.main()
            
            # Vérification du code de sortie
            self.assertEqual(cm.exception.code, 2)
        
        # Vérification de la sortie
        output = self.mock_stdout.getvalue()
        self.assertIn("Erreur: Aucun immeuble trouvé", output)
    
    def test_find_building_invalid_qr(self):
        """Test de recherche avec un identifiant QR invalide."""
        # Exécution
        with patch.object(sys, 'argv', ['find_building.py', 'INVALID']):
            with self.assertRaises(SystemExit) as cm:
                find_building.main()
            
            # Vérification du code de sortie
            self.assertEqual(cm.exception.code, 3)
        
        # Vérification de la sortie
        output = self.mock_stdout.getvalue()
        self.assertIn("Erreur: Format d'identifiant QR invalide", output)


if __name__ == '__main__':
    unittest.main()
