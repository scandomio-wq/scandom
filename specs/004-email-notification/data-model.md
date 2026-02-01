# Data Model: Email Notification for Incidents

**Feature**: 004-email-notification  
**Date**: 2026-01-30

## Entités

### EmailNotification

Représente une notification email envoyée pour un incident.

| Attribut | Type | Contraintes | Description |
|----------|------|-------------|-------------|
| `id` | SERIAL | PK | Identifiant unique |
| `incident_id` | INTEGER | FK → incidents.id, UNIQUE | Référence à l'incident |
| `recipient_email` | VARCHAR(255) | NOT NULL | Email du destinataire (gestionnaire) |
| `subject` | VARCHAR(500) | NOT NULL | Objet de l'email |
| `body_html` | TEXT | NOT NULL | Corps de l'email en HTML |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | Statut: pending, sent, failed |
| `error_message` | TEXT | NULL | Message d'erreur si échec |
| `retry_count` | INTEGER | DEFAULT 0 | Nombre de tentatives |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Date de création |
| `sent_at` | TIMESTAMP | NULL | Date d'envoi réussi |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Dernière mise à jour |

### Relations

```
T_BUILDING (1) ──────< (N) T_INCIDENT (1) ──────< (1) email_notifications
     │                         │                           │
     │ EMAIL_GESTIONNAIRE      │ id                        │ incident_id (FK)
     │                         │ BUILDING_ID (FK)          │ recipient_email
     └─────────────────────────┴───────────────────────────┘
```

### États et transitions

```
                    ┌─────────┐
                    │ pending │ (création initiale)
                    └────┬────┘
                         │
            ┌────────────┼────────────┐
            │            │            │
            ▼            │            ▼
       ┌────────┐        │       ┌────────┐
       │  sent  │        │       │ failed │
       └────────┘        │       └───┬────┘
                         │           │
                         │    retry_count < max_retries
                         │           │
                         └───────────┘
```

## Migration SQL

```sql
-- Migration: 006_create_email_notifications.sql

CREATE TABLE IF NOT EXISTS email_notifications (
    id SERIAL PRIMARY KEY,
    incident_id INTEGER NOT NULL UNIQUE,
    recipient_email VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    body_html TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    sent_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_incident
        FOREIGN KEY (incident_id)
        REFERENCES incidents(id)
        ON DELETE CASCADE,
    
    CONSTRAINT chk_status
        CHECK (status IN ('pending', 'sent', 'failed'))
);

-- Index pour les requêtes fréquentes
CREATE INDEX idx_email_notifications_status ON email_notifications(status);
CREATE INDEX idx_email_notifications_incident ON email_notifications(incident_id);

-- Trigger pour updated_at
CREATE OR REPLACE FUNCTION update_email_notifications_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_email_notifications_updated_at
    BEFORE UPDATE ON email_notifications
    FOR EACH ROW
    EXECUTE FUNCTION update_email_notifications_updated_at();
```

## Validation

| Champ | Règle de validation |
|-------|---------------------|
| `recipient_email` | Format email valide (regex) |
| `subject` | Non vide, max 500 caractères |
| `body_html` | Non vide |
| `status` | Valeur parmi: pending, sent, failed |
| `retry_count` | >= 0 |

## Requêtes fréquentes

```sql
-- Notifications en attente d'envoi
SELECT * FROM email_notifications 
WHERE status = 'pending' 
ORDER BY created_at ASC;

-- Notifications échouées à réessayer
SELECT * FROM email_notifications 
WHERE status = 'failed' AND retry_count < 3
ORDER BY updated_at ASC;

-- Historique pour un incident
SELECT * FROM email_notifications 
WHERE incident_id = :incident_id;

-- Statistiques d'envoi
SELECT status, COUNT(*) 
FROM email_notifications 
GROUP BY status;
```
