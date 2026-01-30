-- Migration pour corriger la longueur du champ user_phone
-- Augmente la taille du champ pour accommoder le format whatsapp:+XXXXXXXXXXX

-- Modifier la colonne user_phone pour augmenter sa taille
ALTER TABLE whatsapp_conversations ALTER COLUMN user_phone TYPE VARCHAR(50);

-- Commentaire explicatif
COMMENT ON COLUMN whatsapp_conversations.user_phone IS 'Numéro de téléphone de l''utilisateur (format: whatsapp:+XXXXXXXXXXX ou +XXXXXXXXXXX)';
