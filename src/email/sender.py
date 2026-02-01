import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os

from src.email import logger
from src.email.config import email_config

class EmailService:
    """Service d'envoi d'emails pour les notifications d'incidents."""
    
    def __init__(self):
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def render_incident_notification(
        self,
        incident_qr_code: str,
        building_address: str,
        incident_data: dict
    ) -> tuple[str, str]:
        """
        Génère le sujet et le corps HTML de l'email.
        
        Returns:
            tuple[str, str]: (sujet, corps_html)
        """
        subject = f"L'incident n°{incident_qr_code} a été créé"
        
        template = self.jinja_env.get_template('incident_created.html')
        html_content = template.render(
            incident_qr_code=incident_qr_code,
            building_address=building_address,
            zone=incident_data.get('zone', 'N/A'),
            floor=incident_data.get('floor', 'N/A'),
            category=incident_data.get('category', 'N/A'),
            description=incident_data.get('description', 'Pas de description'),
            photo_urls=incident_data.get('photo_urls', []),
            reporter_phone=incident_data.get('reporter_phone', 'N/A'),
            created_at=incident_data.get('created_at', datetime.now().strftime('%d/%m/%Y %H:%M'))
        )
        return subject, html_content

    def send_email(self, to_email: str, subject: str, html_body: str) -> bool:
        """
        Envoie un email via SMTP.
        """
        try:
            email_config.validate()
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = email_config.smtp_from_email
            msg['To'] = to_email
            msg.attach(MIMEText(html_body, 'html'))
            
            with smtplib.SMTP(email_config.smtp_host, email_config.smtp_port) as server:
                if email_config.smtp_use_tls:
                    server.starttls()
                
                server.login(email_config.smtp_user, email_config.smtp_password)
                server.send_message(msg)
                
            return True
        except Exception as e:
            logger.error(f"Erreur SMTP lors de l'envoi à {to_email}: {e}")
            raise

    def get_notification_status(self, incident_id: int) -> Optional[dict]:
        """
        Récupère le statut de la notification pour un incident donné.
        """
        from src.db.connection import DatabaseConnection
        db = DatabaseConnection()
        
        query = """
            SELECT status, recipient_email, sent_at, error_message, retry_count, updated_at
            FROM email_notifications
            WHERE incident_id = %s
        """
        return db.execute_query(query, (incident_id,), fetch_one=True)

    def test_connection(self) -> bool:
        """
        Teste la connexion au serveur SMTP.
        
        Returns:
            bool: True si la connexion et l'authentification ont réussi.
            
        Raises:
            Exception: Si une erreur survient lors de la connexion.
        """
        try:
            email_config.validate()
            with smtplib.SMTP(email_config.smtp_host, email_config.smtp_port) as server:
                if email_config.smtp_use_tls:
                    server.starttls()
                server.login(email_config.smtp_user, email_config.smtp_password)
            logger.info("Connexion SMTP testée avec succès.")
            return True
        except Exception as e:
            logger.error(f"Échec du test de connexion SMTP: {e}")
            raise
