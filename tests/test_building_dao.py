"""
Tests pour le module building_dao.py.
"""

import unittest
from unittest.mock import patch, MagicMock

import psycopg2
from psycopg2.errors import UniqueViolation

from src.db.building_dao import BuildingDAO, OperationNotAllowedException
from src.models.building import Building


class TestBuildingDAO(unittest.TestCase):
    """Tests pour la classe BuildingDAO."""

    def setUp(self):
        """Configuration avant chaque test."""
        self.patcher = patch('src.db.building_dao.get_db_connection')
        self.mock_get_db = self.patcher.start()
        self.mock_db = MagicMock()
        self.mock_get_db.return_value = self.mock_db
        
        self.dao = BuildingDAO()
        
        # Données de test
        self.test_building = Building(
            location="123 Rue de Test",
            email_gestionnaire="test@example.com",
            notes="Bâtiment de test"
        )
        
        self.db_row = {
            "id": 1,
            "location": "123 Rue de Test",
            "email_gestionnaire": "test@example.com",
            "notes": "Bâtiment de test",
            "qr_code_number": "QR1234567890",
            "creation_date": "2026-01-18T10:30:00"
        }
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        self.patcher.stop()
    
    def test_create_building_success(self):
        """Test de création d'un bâtiment avec succès."""
        # Configuration du mock
        self.mock_db.execute_query.return_value = {"id": 1, "creation_date": "2026-01-18T10:30:00"}
        
        # Patch de la méthode generate_qr_code_number
        with patch.object(self.dao, 'generate_qr_code_number', return_value="QR1234567890"):
            # Exécution
            result = self.dao.create_building(self.test_building)
            
            # Vérifications
            self.assertEqual(result.id, 1)
            self.assertEqual(result.qr_code_number, "QR1234567890")
            self.mock_db.execute_query.assert_called_once()
    
    def test_create_building_duplicate_qr(self):
        """Test de création d'un bâtiment avec un QR_CODE_NUMBER en doublon."""
        # Configuration du mock pour lever une exception UniqueViolation
        self.mock_db.execute_query.side_effect = UniqueViolation("Duplicate QR_CODE_NUMBER")
        
        # Patch de la méthode generate_qr_code_number
        with patch.object(self.dao, 'generate_qr_code_number', return_value="QR1234567890"):
            # Vérification que l'exception est bien levée
            with self.assertRaises(UniqueViolation):
                self.dao.create_building(self.test_building)
    
    def test_get_building_by_id_found(self):
        """Test de récupération d'un bâtiment par ID avec succès."""
        # Configuration du mock
        self.mock_db.execute_query.return_value = self.db_row
        
        # Exécution
        result = self.dao.get_building_by_id(1)
        
        # Vérifications
        self.assertIsNotNone(result)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.location, "123 Rue de Test")
        self.assertEqual(result.qr_code_number, "QR1234567890")
    
    def test_get_building_by_id_not_found(self):
        """Test de récupération d'un bâtiment par ID non trouvé."""
        # Configuration du mock
        self.mock_db.execute_query.return_value = None
        
        # Exécution
        result = self.dao.get_building_by_id(999)
        
        # Vérifications
        self.assertIsNone(result)
    
    def test_get_building_by_qr_code_found(self):
        """Test de récupération d'un bâtiment par QR_CODE_NUMBER avec succès."""
        # Configuration du mock
        self.mock_db.execute_query.return_value = self.db_row
        
        # Exécution
        result = self.dao.get_building_by_qr_code("QR1234567890")
        
        # Vérifications
        self.assertIsNotNone(result)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.location, "123 Rue de Test")
        self.assertEqual(result.qr_code_number, "QR1234567890")
    
    def test_get_building_by_qr_code_not_found(self):
        """Test de récupération d'un bâtiment par QR_CODE_NUMBER non trouvé."""
        # Configuration du mock
        self.mock_db.execute_query.return_value = None
        
        # Exécution
        result = self.dao.get_building_by_qr_code("QR9999999999")
        
        # Vérifications
        self.assertIsNone(result)
    
    def test_update_building_not_allowed(self):
        """Test que la mise à jour d'un bâtiment n'est pas autorisée."""
        # Vérification que l'exception est bien levée
        with self.assertRaises(OperationNotAllowedException):
            self.dao.update_building(1, {"LOCATION": "Nouvelle adresse"})
    
    def test_delete_building_not_allowed(self):
        """Test que la suppression d'un bâtiment n'est pas autorisée."""
        # Vérification que l'exception est bien levée
        with self.assertRaises(OperationNotAllowedException):
            self.dao.delete_building(1)
    
    def test_generate_qr_code_number(self):
        """Test de génération d'un QR_CODE_NUMBER unique."""
        # Configuration du mock
        with patch.object(self.dao, 'qr_code_number_exists', return_value=False):
            # Exécution
            result = self.dao.generate_qr_code_number()
            
            # Vérifications
            self.assertTrue(result.startswith("QR"))
            self.assertEqual(len(result), 12)  # "QR" + 10 chiffres
    
    def test_generate_qr_code_number_retry(self):
        """Test de génération d'un QR_CODE_NUMBER avec collision."""
        # Configuration du mock pour simuler une collision puis un succès
        with patch.object(self.dao, 'qr_code_number_exists', side_effect=[True, False]):
            # Exécution
            result = self.dao.generate_qr_code_number()
            
            # Vérifications
            self.assertTrue(result.startswith("QR"))
            self.assertEqual(len(result), 12)  # "QR" + 10 chiffres
    
    def test_list_buildings(self):
        """Test de listage des bâtiments avec pagination."""
        # Configuration du mock
        self.mock_db.execute_query.return_value = [self.db_row, self.db_row]
        
        # Exécution
        results = self.dao.list_buildings(limit=2, offset=0)
        
        # Vérifications
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].id, 1)
        self.assertEqual(results[0].qr_code_number, "QR1234567890")


if __name__ == '__main__':
    unittest.main()
