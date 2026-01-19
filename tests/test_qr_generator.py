"""
Tests pour le module qr/generator.py.
"""

import os
import unittest
from unittest.mock import patch, MagicMock

from src.qr.generator import QRCodeGenerator


class TestQRCodeGenerator(unittest.TestCase):
    """Tests pour la classe QRCodeGenerator."""

    def setUp(self):
        """Configuration avant chaque test."""
        # Patch de la configuration
        self.config_patcher = patch('src.qr.generator.get_config')
        self.mock_get_config = self.config_patcher.start()
        self.mock_config = MagicMock()
        self.mock_config.get.return_value = 1200  # qr_resolution
        self.mock_get_config.return_value = self.mock_config
        
        # Créer le générateur
        self.generator = QRCodeGenerator()
        
        # Dossier de test temporaire
        self.test_dir = "/tmp/qr_test"
        os.makedirs(self.test_dir, exist_ok=True)
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        self.config_patcher.stop()
        
        # Supprimer les fichiers de test
        for file in os.listdir(self.test_dir):
            os.remove(os.path.join(self.test_dir, file))
        
        # Supprimer le dossier de test
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)
    
    @patch('qrcode.QRCode')
    @patch('qrcode.make_image')
    @patch('PIL.Image.Image.resize')
    @patch('PIL.Image.Image.save')
    def test_generate_qr_code_success(self, mock_save, mock_resize, mock_make_image, mock_qrcode):
        """Test de génération d'un QR code avec succès."""
        # Configuration des mocks
        mock_qr = MagicMock()
        mock_qrcode.return_value = mock_qr
        mock_img = MagicMock()
        mock_qr.make_image.return_value = mock_img
        mock_img.resize.return_value = mock_img
        
        # Exécution
        success, file_path = self.generator.generate_qr_code("QR1234567890", self.test_dir)
        
        # Vérifications
        self.assertTrue(success)
        self.assertEqual(file_path, os.path.join(self.test_dir, "QR1234567890.png"))
        mock_qr.add_data.assert_called_once_with("QR1234567890")
        mock_qr.make.assert_called_once_with(fit=True)
        mock_qr.make_image.assert_called_once()
        mock_img.resize.assert_called_once()
        mock_img.save.assert_called_once_with(file_path)
    
    def test_generate_qr_code_invalid_id(self):
        """Test de génération d'un QR code avec un identifiant invalide."""
        # Vérification que l'exception est bien levée
        with self.assertRaises(ValueError):
            self.generator.generate_qr_code("INVALID", self.test_dir)
    
    @patch('os.path.exists')
    def test_generate_qr_code_file_exists(self, mock_exists):
        """Test de génération d'un QR code lorsque le fichier existe déjà."""
        # Configuration du mock
        mock_exists.return_value = True
        
        # Exécution
        success, file_path = self.generator.generate_qr_code("QR1234567890", self.test_dir)
        
        # Vérifications
        self.assertTrue(success)
        self.assertEqual(file_path, os.path.join(self.test_dir, "QR1234567890.png"))
    
    @patch('os.path.exists')
    @patch('qrcode.QRCode')
    @patch('qrcode.make_image')
    @patch('PIL.Image.Image.resize')
    @patch('PIL.Image.Image.save')
    def test_generate_qr_code_force_regenerate(self, mock_save, mock_resize, mock_make_image, mock_qrcode, mock_exists):
        """Test de régénération forcée d'un QR code."""
        # Configuration des mocks
        mock_exists.side_effect = [True, True, False]  # Fichier existe, puis collision, puis nouveau nom ok
        mock_qr = MagicMock()
        mock_qrcode.return_value = mock_qr
        mock_img = MagicMock()
        mock_qr.make_image.return_value = mock_img
        mock_img.resize.return_value = mock_img
        
        # Exécution
        success, file_path = self.generator.generate_qr_code("QR1234567890", self.test_dir, force=True)
        
        # Vérifications
        self.assertTrue(success)
        self.assertEqual(file_path, os.path.join(self.test_dir, "QR1234567890_1.png"))
        mock_qr.add_data.assert_called_once_with("QR1234567890")
        mock_img.save.assert_called_once_with(file_path)
    
    @patch('os.path.isdir')
    def test_generate_qr_code_invalid_dir(self, mock_isdir):
        """Test de génération d'un QR code avec un dossier invalide."""
        # Configuration du mock
        mock_isdir.return_value = False
        
        # Vérification que l'exception est bien levée
        with self.assertRaises(OSError):
            self.generator.generate_qr_code("QR1234567890", "/invalid/dir")
    
    @patch('os.access')
    @patch('os.path.isdir')
    def test_generate_qr_code_no_write_permission(self, mock_isdir, mock_access):
        """Test de génération d'un QR code sans permission d'écriture."""
        # Configuration des mocks
        mock_isdir.return_value = True
        mock_access.return_value = False
        
        # Vérification que l'exception est bien levée
        with self.assertRaises(OSError):
            self.generator.generate_qr_code("QR1234567890", self.test_dir)
    
    @patch('os.path.exists')
    def test_qr_code_exists_true(self, mock_exists):
        """Test de vérification d'existence d'un QR code (existe)."""
        # Configuration du mock
        mock_exists.return_value = True
        
        # Exécution
        result = self.generator.qr_code_exists("QR1234567890", self.test_dir)
        
        # Vérifications
        self.assertTrue(result)
    
    @patch('os.path.exists')
    def test_qr_code_exists_false(self, mock_exists):
        """Test de vérification d'existence d'un QR code (n'existe pas)."""
        # Configuration du mock
        mock_exists.return_value = False
        
        # Exécution
        result = self.generator.qr_code_exists("QR1234567890", self.test_dir)
        
        # Vérifications
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
