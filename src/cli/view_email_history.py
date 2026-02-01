import sys
import os
import argparse
from datetime import datetime

# Ajouter le chemin racine au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.db.connection import DatabaseConnection
from src.email.sender import EmailService

def view_history(incident_id=None, limit=10):
    db = DatabaseConnection()
    
    if incident_id:
        query = """
            SELECT n.id, n.incident_id, i.qr_code_number, n.recipient_email, n.status, 
                   n.sent_at, n.retry_count, n.error_message, n.updated_at
            FROM email_notifications n
            JOIN t_incident i ON n.incident_id = i.id
            WHERE n.incident_id = %s OR i.qr_code_number = %s
        """
        results = db.execute_query(query, (incident_id, str(incident_id)), fetch_all=True)
    else:
        query = """
            SELECT n.id, n.incident_id, i.qr_code_number, n.recipient_email, n.status, 
                   n.sent_at, n.retry_count, n.error_message, n.updated_at
            FROM email_notifications n
            JOIN t_incident i ON n.incident_id = i.id
            ORDER BY n.updated_at DESC
            LIMIT %s
        """
        results = db.execute_query(query, (limit,), fetch_all=True)

    if not results:
        print("Aucune notification trouvée.")
        return

    print(f"{'ID':<5} | {'INCIDENT':<15} | {'DESTINATAIRE':<30} | {'STATUT':<10} | {'RETRIES':<3} | {'DATE'}")
    print("-" * 100)
    
    for row in results:
        date = row['sent_at'] or row['updated_at']
        date_str = date.strftime('%d/%m/%Y %H:%M') if date else "N/A"
        print(f"{row['id']:<5} | {row['qr_code_number']:<15} | {row['recipient_email']:<30} | {row['status']:<10} | {row['retry_count']:<7} | {date_str}")
        if row['error_message']:
            print(f"  └─ Erreur: {row['error_message']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Consulter l'historique des notifications email")
    parser.add_argument("--id", type=str, help="ID de l'incident ou Numéro QR")
    parser.add_argument("--limit", type=int, default=10, help="Nombre de résultats à afficher (défaut: 10)")
    
    args = parser.parse_args()
    view_history(args.id, args.limit)
