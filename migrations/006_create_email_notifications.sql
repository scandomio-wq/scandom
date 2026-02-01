-- Migration: 006_create_email_notifications.sql
-- Description: Table pour le suivi des notifications par email envoyées pour les incidents

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
        REFERENCES t_incident(id)
        ON DELETE CASCADE,
    
    CONSTRAINT chk_status
        CHECK (status IN ('pending', 'sent', 'failed'))
);

-- Index pour les requêtes fréquentes
CREATE INDEX IF NOT EXISTS idx_email_notifications_status ON email_notifications(status);
CREATE INDEX IF NOT EXISTS idx_email_notifications_incident ON email_notifications(incident_id);

-- Trigger pour updated_at
CREATE OR REPLACE FUNCTION update_email_notifications_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_email_notifications_updated_at ON email_notifications;
CREATE TRIGGER trg_email_notifications_updated_at
    BEFORE UPDATE ON email_notifications
    FOR EACH ROW
    EXECUTE FUNCTION update_email_notifications_updated_at();
