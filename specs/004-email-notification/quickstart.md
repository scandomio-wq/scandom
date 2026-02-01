# Quickstart: Email Notification for Incidents

**Feature**: 004-email-notification  
**Date**: 2026-01-30

## Prérequis

- Python 3.11+
- PostgreSQL avec la base SCANDOM configurée
- Redis (pour Celery)
- Celery worker actif
- Serveur SMTP accessible

## Configuration

### 1. Variables d'environnement

Créer ou mettre à jour le fichier `config/email/.env` :

```bash
# Configuration SMTP
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=notifications@scandom.io
SMTP_PASSWORD=your_secure_password
SMTP_FROM_EMAIL=noreply@scandom.io
SMTP_USE_TLS=true

# Configuration retry
EMAIL_MAX_RETRIES=3
EMAIL_RETRY_DELAY=60
```

### 2. Migration base de données

```bash
python run_migrations.py
```

Cela exécutera `migrations/006_create_email_notifications.sql`.

### 3. Vérifier la configuration

```bash
python -c "from src.email import EmailService; EmailService().test_connection()"
```

## Démarrage

### 1. Démarrer le worker Celery

```bash
celery -A src.whatsapp.tasks worker --loglevel=info
```

### 2. Lancer l'application

```bash
python app.py
```

## Test manuel

### Envoyer un email de test

```python
from src.email.tasks import send_incident_email_task

# Envoyer un email de test
result = send_incident_email_task.delay(
    incident_id=1,
    incident_qr_code="IN00000001",
    building_address="123 Rue de Test, 75001 Paris",
    manager_email="gestionnaire@example.com",
    incident_data={
        "zone": "Hall d'entrée",
        "floor": "RDC",
        "category": "Propreté",
        "description": "Sol glissant près de l'entrée",
        "photo_urls": [],
        "reporter_phone": "+33612345678",
        "created_at": "2026-01-30 18:00:00"
    }
)

# Vérifier le résultat
print(result.get(timeout=30))
```

### Vérifier l'historique

#### Via SQL
```sql
SELECT * FROM email_notifications ORDER BY created_at DESC LIMIT 10;
```

#### Via CLI
```bash
python src/cli/view_email_history.py --limit 10
```

## Dépannage

### Email non envoyé

1. Vérifier les logs Celery
2. Vérifier la table `email_notifications` (colonne `error_message`)
3. Tester la connexion SMTP manuellement

### Erreur de connexion SMTP

```bash
# Test connexion SMTP
python -c "
import smtplib
import os
server = smtplib.SMTP(os.environ['SMTP_HOST'], int(os.environ['SMTP_PORT']))
server.starttls()
server.login(os.environ['SMTP_USER'], os.environ['SMTP_PASSWORD'])
print('Connexion SMTP OK')
server.quit()
"
```

### Template non trouvé

Vérifier que le fichier `src/email/templates/incident_created.html` existe.

## Structure des fichiers

```
src/email/
├── __init__.py
├── config.py
├── sender.py
├── tasks.py
└── templates/
    └── incident_created.html

config/email/
├── config.ini
└── .env.example

migrations/
└── 006_create_email_notifications.sql
```
