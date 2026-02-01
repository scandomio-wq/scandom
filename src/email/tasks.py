from datetime import datetime
from src.whatsapp.tasks import celery_app
from src.email.sender import EmailService
from src.email import logger
from src.db.connection import DatabaseConnection

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True
)
def send_incident_email_task(
    self,
    incident_id: int,
    incident_qr_code: str,
    building_address: str,
    manager_email: str,
    incident_data: dict
):
    """
    Tâche Celery asynchrone pour l'envoi d'email de notification d'incident.
    """
    logger.info(f"Démarrage de la tâche d'envoi d'email pour l'incident {incident_qr_code} à {manager_email}")
    
    db_connection = DatabaseConnection()
    
    try:
        email_service = EmailService()
        
        # 1. Générer le contenu de l'email
        subject, html_body = email_service.render_incident_notification(
            incident_qr_code, building_address, incident_data
        )
        
        # 2. Créer ou mettre à jour l'entrée 'pending' avec le contenu rendu
        query_upsert = """
            INSERT INTO email_notifications (incident_id, recipient_email, subject, body_html, status)
            VALUES (%s, %s, %s, %s, 'pending')
            ON CONFLICT (incident_id) DO UPDATE SET
                subject = EXCLUDED.subject,
                body_html = EXCLUDED.body_html,
                retry_count = email_notifications.retry_count + 1,
                updated_at = NOW()
            RETURNING id
        """
        db_connection.execute_query(query_upsert, (incident_id, manager_email, subject, html_body))
        
        # 3. Envoi effectif
        success = email_service.send_email(manager_email, subject, html_body)
        
        if success:
            # Mise à jour du statut en 'sent'
            query_update = """
                UPDATE email_notifications 
                SET status = 'sent', sent_at = NOW(), updated_at = NOW()
                WHERE incident_id = %s
            """
            db_connection.execute_query(query_update, (incident_id,))
            return {"status": "sent", "incident_id": incident_id}
            
    except Exception as exc:
        logger.error(f"Échec de l'envoi d'email pour l'incident {incident_qr_code} (tentative {self.request.retries + 1}): {exc}")
        
        # Mise à jour du statut en 'failed' avec le message d'erreur
        error_msg = str(exc)
        
        # On tente de mettre à jour l'enregistrement s'il existe déjà
        query_fail = """
            UPDATE email_notifications 
            SET status = 'failed', 
                error_message = %s, 
                updated_at = NOW()
            WHERE incident_id = %s
        """
        db_connection.execute_query(query_fail, (error_msg, incident_id))
        
        # Si c'est la dernière tentative, log CRITICAL
        if self.request.retries >= self.max_retries:
            logger.critical(f"DÉFAILLANCE CRITIQUE : Échec final de l'envoi d'email pour l'incident {incident_qr_code} après {self.max_retries + 1} tentatives. Destinataire : {manager_email}. Erreur : {error_msg}")
        
        # Relancer l'exception pour que Celery gère le retry
        raise self.retry(exc=exc)
