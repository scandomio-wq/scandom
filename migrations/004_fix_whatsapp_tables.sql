-- Migration pour corriger les tables WhatsApp
-- Ajout des colonnes manquantes et des alias pour compatibilité

-- Ajouter une colonne id à whatsapp_conversations comme alias de conversation_id
ALTER TABLE whatsapp_conversations ADD COLUMN IF NOT EXISTS id VARCHAR(50) GENERATED ALWAYS AS (conversation_id) STORED;

-- Ajouter une colonne body à whatsapp_messages comme alias de content
ALTER TABLE whatsapp_messages ADD COLUMN IF NOT EXISTS body TEXT GENERATED ALWAYS AS (content) STORED;

-- Ajouter une colonne id à whatsapp_messages comme alias de message_id
ALTER TABLE whatsapp_messages ADD COLUMN IF NOT EXISTS id VARCHAR(50) GENERATED ALWAYS AS (message_id) STORED;

-- Créer des index sur les nouvelles colonnes
CREATE INDEX IF NOT EXISTS idx_whatsapp_conversations_id ON whatsapp_conversations(id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_id ON whatsapp_messages(id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_body ON whatsapp_messages(body);

-- Commentaires explicatifs
COMMENT ON COLUMN whatsapp_conversations.id IS 'Alias de conversation_id pour compatibilité avec les tests';
COMMENT ON COLUMN whatsapp_messages.id IS 'Alias de message_id pour compatibilité avec les tests';
COMMENT ON COLUMN whatsapp_messages.body IS 'Alias de content pour compatibilité avec les tests';
