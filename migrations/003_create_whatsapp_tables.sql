-- Migration pour l'intégration WhatsApp
-- Création des tables pour les conversations, messages et incidents en attente

-- Table pour les conversations WhatsApp
CREATE TABLE IF NOT EXISTS whatsapp_conversations (
    conversation_id VARCHAR(50) PRIMARY KEY,
    user_phone VARCHAR(20) NOT NULL,
    building_qr_code VARCHAR(50) NOT NULL,
    current_step VARCHAR(50) NOT NULL,
    collected_data JSONB NOT NULL DEFAULT '{}',
    last_activity TIMESTAMP NOT NULL,
    is_completed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index pour les conversations
CREATE INDEX IF NOT EXISTS idx_whatsapp_conversations_user_phone ON whatsapp_conversations(user_phone);
CREATE INDEX IF NOT EXISTS idx_whatsapp_conversations_building_qr_code ON whatsapp_conversations(building_qr_code);
CREATE INDEX IF NOT EXISTS idx_whatsapp_conversations_last_activity ON whatsapp_conversations(last_activity);
CREATE INDEX IF NOT EXISTS idx_whatsapp_conversations_is_completed ON whatsapp_conversations(is_completed);
CREATE UNIQUE INDEX IF NOT EXISTS idx_whatsapp_conversations_active_user_building ON whatsapp_conversations(user_phone, building_qr_code) WHERE is_completed = FALSE;

-- Table pour les messages WhatsApp
CREATE TABLE IF NOT EXISTS whatsapp_messages (
    message_id VARCHAR(50) PRIMARY KEY,
    conversation_id VARCHAR(50) NOT NULL,
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('incoming', 'outgoing')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    status VARCHAR(10) CHECK (status IN ('sent', 'delivered', 'read', 'failed')),
    media_url VARCHAR(255),
    FOREIGN KEY (conversation_id) REFERENCES whatsapp_conversations(conversation_id) ON DELETE CASCADE
);

-- Index pour les messages
CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_conversation_id ON whatsapp_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_timestamp ON whatsapp_messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_status ON whatsapp_messages(status);

-- Table pour les incidents en attente
CREATE TABLE IF NOT EXISTS pending_incidents (
    id VARCHAR(50) PRIMARY KEY,
    conversation_id VARCHAR(50) NOT NULL,
    incident_data JSONB NOT NULL,
    error_message TEXT NOT NULL,
    retry_count INTEGER NOT NULL DEFAULT 0,
    next_retry TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES whatsapp_conversations(conversation_id) ON DELETE CASCADE
);

-- Index pour les incidents en attente
CREATE INDEX IF NOT EXISTS idx_pending_incidents_next_retry ON pending_incidents(next_retry);
CREATE INDEX IF NOT EXISTS idx_pending_incidents_conversation_id ON pending_incidents(conversation_id);
CREATE INDEX IF NOT EXISTS idx_pending_incidents_retry_count ON pending_incidents(retry_count);

-- Fonction pour mettre à jour le champ updated_at automatiquement
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers pour mettre à jour updated_at automatiquement
CREATE TRIGGER update_whatsapp_conversations_updated_at
BEFORE UPDATE ON whatsapp_conversations
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pending_incidents_updated_at
BEFORE UPDATE ON pending_incidents
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Commentaires explicatifs
COMMENT ON TABLE whatsapp_conversations IS 'Stocke l''état des conversations WhatsApp pour la déclaration d''incidents';
COMMENT ON TABLE whatsapp_messages IS 'Stocke les messages échangés dans les conversations WhatsApp';
COMMENT ON TABLE pending_incidents IS 'Stocke les incidents en attente suite à des erreurs techniques';

COMMENT ON COLUMN whatsapp_conversations.conversation_id IS 'Identifiant unique de la conversation';
COMMENT ON COLUMN whatsapp_conversations.user_phone IS 'Numéro de téléphone de l''utilisateur';
COMMENT ON COLUMN whatsapp_conversations.building_qr_code IS 'QR code du bâtiment concerné';
COMMENT ON COLUMN whatsapp_conversations.current_step IS 'Étape actuelle de la conversation (initiation, zone, etage, etc.)';
COMMENT ON COLUMN whatsapp_conversations.collected_data IS 'Données collectées au cours de la conversation au format JSON';
COMMENT ON COLUMN whatsapp_conversations.last_activity IS 'Date et heure de la dernière activité dans la conversation';
COMMENT ON COLUMN whatsapp_conversations.is_completed IS 'Indique si la conversation est terminée';

COMMENT ON COLUMN whatsapp_messages.message_id IS 'Identifiant unique du message';
COMMENT ON COLUMN whatsapp_messages.conversation_id IS 'Référence à la conversation';
COMMENT ON COLUMN whatsapp_messages.direction IS 'Direction du message (incoming/outgoing)';
COMMENT ON COLUMN whatsapp_messages.content IS 'Contenu du message';
COMMENT ON COLUMN whatsapp_messages.timestamp IS 'Date et heure du message';
COMMENT ON COLUMN whatsapp_messages.status IS 'Statut du message (sent, delivered, read, failed)';
COMMENT ON COLUMN whatsapp_messages.media_url IS 'URL du média attaché (si applicable)';

COMMENT ON COLUMN pending_incidents.id IS 'Identifiant unique de l''incident en attente';
COMMENT ON COLUMN pending_incidents.conversation_id IS 'Référence à la conversation';
COMMENT ON COLUMN pending_incidents.incident_data IS 'Données complètes de l''incident au format JSON';
COMMENT ON COLUMN pending_incidents.error_message IS 'Message d''erreur rencontré';
COMMENT ON COLUMN pending_incidents.retry_count IS 'Nombre de tentatives effectuées';
COMMENT ON COLUMN pending_incidents.next_retry IS 'Date et heure de la prochaine tentative';
