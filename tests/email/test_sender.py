import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from src.email.sender import EmailService

class TestEmailService(unittest.TestCase):
    def setUp(self):
        self.email_service = EmailService()
        self.incident_data = {
            "zone": "Hall d'entrée",
            "floor": "RDC",
            "category": "Propreté",
            "description": "Sol glissant",
            "photo_urls": ["http://example.com/photo1.jpg"],
            "reporter_phone": "+33612345678",
            "created_at": "31/01/2026 10:00"
        }

    def test_render_incident_notification(self):
        """Teste le rendu du template HTML."""
        subject, html_body = self.email_service.render_incident_notification(
            incident_qr_code="IN1234567890",
            building_address="123 Rue de Test",
            incident_data=self.incident_data
        )
        
        self.assertIn("IN1234567890", subject)
        self.assertIn("123 Rue de Test", html_body)
        # Jinja2 échappe les caractères spéciaux par défaut
        self.assertIn("Hall d&#39;entrée", html_body)
        self.assertIn("Propreté", html_body)
        self.assertIn("Sol glissant", html_body)
        self.assertIn("http://example.com/photo1.jpg", html_body)

    @patch('smtplib.SMTP')
    @patch('src.email.sender.email_config')
    def test_send_email_success(self, mock_config, mock_smtp):
        """Teste l'envoi d'email avec succès (mock SMTP)."""
        mock_config.smtp_host = "localhost"
        mock_config.smtp_port = 587
        mock_config.smtp_user = "user"
        mock_config.smtp_password = "password"
        mock_config.smtp_from_email = "noreply@test.com"
        mock_config.smtp_use_tls = True
        mock_config.validate.return_value = True

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        success = self.email_service.send_email(
            to_email="manager@test.com",
            subject="Test Subject",
            html_body="<p>Test Body</p>"
        )

        self.assertTrue(success)
        mock_server.login.assert_called_with("user", "password")
        mock_server.send_message.assert_called_once()

    @patch('smtplib.SMTP')
    @patch('src.email.sender.email_config')
    def test_send_email_failure(self, mock_config, mock_smtp):
        """Teste la gestion des erreurs lors de l'envoi d'email."""
        mock_config.smtp_host = "localhost"
        mock_config.smtp_port = 587
        mock_config.validate.return_value = True
        
        mock_smtp.side_effect = Exception("SMTP Error")

        with self.assertRaises(Exception):
            self.email_service.send_email(
                to_email="manager@test.com",
                subject="Test Subject",
                html_body="<p>Test Body</p>"
            )

if __name__ == '__main__':
    unittest.main()
