-- Script pour insérer des données de test dans les tables WhatsApp
-- Ces données permettront de vérifier les critères de succès

-- Insérer des conversations de test
INSERT INTO whatsapp_conversations (
    conversation_id, user_phone, building_qr_code, current_step, 
    collected_data, last_activity, is_completed, created_at, updated_at
) VALUES 
-- Conversation complétée en moins de 2 minutes
('conv_test_001', '+33612345678', 'QR12345', 'completed', 
 '{"description": "Fuite d''eau", "zone": "Toilettes", "etage": "RDC", "priorite": "haute", "reporter_email": "test@example.com"}',
 NOW(), TRUE, NOW() - INTERVAL '1 minute 30 seconds', NOW()),

-- Conversation complétée en plus de 2 minutes
('conv_test_002', '+33623456789', 'QR12346', 'completed', 
 '{"description": "Ampoule grillée", "zone": "Couloir", "etage": "1er", "priorite": "basse", "reporter_email": "test2@example.com"}',
 NOW(), TRUE, NOW() - INTERVAL '3 minutes', NOW() - INTERVAL '10 seconds'),

-- Conversation non complétée
('conv_test_003', '+33634567890', 'QR12347', 'description', 
 '{"building_qr_code": "QR12347"}',
 NOW(), FALSE, NOW() - INTERVAL '5 minutes', NOW()),

-- Conversation avec erreur de validation
('conv_test_004', '+33645678901', 'QR12348', 'validation_error', 
 '{"building_qr_code": "QR12348", "error_count": 2}',
 NOW(), FALSE, NOW() - INTERVAL '10 minutes', NOW());

-- Insérer des messages de test pour la première conversation (complétée rapidement)
INSERT INTO whatsapp_messages (
    message_id, conversation_id, direction, content, timestamp, status, media_url
) VALUES
-- Messages de la conversation 1
('msg_test_001_1', 'conv_test_001', 'incoming', 'Bonjour', NOW() - INTERVAL '1 minute 30 seconds', NULL, NULL),
('msg_test_001_2', 'conv_test_001', 'outgoing', 'Bienvenue au service de signalement d''incidents. Veuillez scanner ou saisir le code QR du bâtiment concerné.', NOW() - INTERVAL '1 minute 29 seconds', 'delivered', NULL),
('msg_test_001_3', 'conv_test_001', 'incoming', 'QR12345', NOW() - INTERVAL '1 minute 25 seconds', NULL, NULL),
('msg_test_001_4', 'conv_test_001', 'outgoing', 'Merci. Veuillez décrire l''incident en quelques mots.', NOW() - INTERVAL '1 minute 24 seconds', 'delivered', NULL),
('msg_test_001_5', 'conv_test_001', 'incoming', 'Fuite d''eau', NOW() - INTERVAL '1 minute 20 seconds', NULL, NULL),
('msg_test_001_6', 'conv_test_001', 'outgoing', 'Dans quelle zone se situe l''incident ?', NOW() - INTERVAL '1 minute 19 seconds', 'delivered', NULL),
('msg_test_001_7', 'conv_test_001', 'incoming', 'Toilettes', NOW() - INTERVAL '1 minute 15 seconds', NULL, NULL),
('msg_test_001_8', 'conv_test_001', 'outgoing', 'À quel étage ?', NOW() - INTERVAL '1 minute 14 seconds', 'delivered', NULL),
('msg_test_001_9', 'conv_test_001', 'incoming', 'RDC', NOW() - INTERVAL '1 minute 10 seconds', NULL, NULL),
('msg_test_001_10', 'conv_test_001', 'outgoing', 'Quelle est la priorité de cet incident ? (haute/moyenne/basse)', NOW() - INTERVAL '1 minute 9 seconds', 'delivered', NULL),
('msg_test_001_11', 'conv_test_001', 'incoming', 'haute', NOW() - INTERVAL '1 minute 5 seconds', NULL, NULL),
('msg_test_001_12', 'conv_test_001', 'outgoing', 'Veuillez indiquer votre email pour le suivi de l''incident.', NOW() - INTERVAL '1 minute 4 seconds', 'delivered', NULL),
('msg_test_001_13', 'conv_test_001', 'incoming', 'test@example.com', NOW() - INTERVAL '1 minute', NULL, NULL),
('msg_test_001_14', 'conv_test_001', 'outgoing', 'Récapitulatif de l''incident :\nDescription: Fuite d''eau\nZone: Toilettes\nÉtage: RDC\nPriorité: haute\nEmail: test@example.com\n\nConfirmez-vous ces informations ? (oui/non)', NOW() - INTERVAL '59 seconds', 'delivered', NULL),
('msg_test_001_15', 'conv_test_001', 'incoming', 'oui', NOW() - INTERVAL '30 seconds', NULL, NULL),
('msg_test_001_16', 'conv_test_001', 'outgoing', 'Merci ! Votre incident a été enregistré avec le numéro INC001. Vous recevrez un suivi par email.', NOW(), 'delivered', NULL);

-- Insérer des messages pour la deuxième conversation (complétée lentement)
INSERT INTO whatsapp_messages (
    message_id, conversation_id, direction, content, timestamp, status, media_url
) VALUES
-- Messages de la conversation 2 (avec des temps plus longs entre les messages)
('msg_test_002_1', 'conv_test_002', 'incoming', 'Bonjour', NOW() - INTERVAL '3 minutes', NULL, NULL),
('msg_test_002_2', 'conv_test_002', 'outgoing', 'Bienvenue au service de signalement d''incidents. Veuillez scanner ou saisir le code QR du bâtiment concerné.', NOW() - INTERVAL '2 minutes 50 seconds', 'delivered', NULL),
('msg_test_002_3', 'conv_test_002', 'incoming', 'QR12346', NOW() - INTERVAL '2 minutes 30 seconds', NULL, NULL),
('msg_test_002_4', 'conv_test_002', 'outgoing', 'Merci. Veuillez décrire l''incident en quelques mots.', NOW() - INTERVAL '2 minutes 25 seconds', 'delivered', NULL),
('msg_test_002_5', 'conv_test_002', 'incoming', 'Ampoule grillée', NOW() - INTERVAL '2 minutes', NULL, NULL),
('msg_test_002_6', 'conv_test_002', 'outgoing', 'Dans quelle zone se situe l''incident ?', NOW() - INTERVAL '1 minute 55 seconds', 'delivered', NULL),
('msg_test_002_7', 'conv_test_002', 'incoming', 'Couloir', NOW() - INTERVAL '1 minute 30 seconds', NULL, NULL),
('msg_test_002_8', 'conv_test_002', 'outgoing', 'À quel étage ?', NOW() - INTERVAL '1 minute 25 seconds', 'delivered', NULL),
('msg_test_002_9', 'conv_test_002', 'incoming', '1er', NOW() - INTERVAL '1 minute', NULL, NULL),
('msg_test_002_10', 'conv_test_002', 'outgoing', 'Quelle est la priorité de cet incident ? (haute/moyenne/basse)', NOW() - INTERVAL '55 seconds', 'delivered', NULL),
('msg_test_002_11', 'conv_test_002', 'incoming', 'basse', NOW() - INTERVAL '30 seconds', NULL, NULL),
('msg_test_002_12', 'conv_test_002', 'outgoing', 'Veuillez indiquer votre email pour le suivi de l''incident.', NOW() - INTERVAL '25 seconds', 'delivered', NULL),
('msg_test_002_13', 'conv_test_002', 'incoming', 'test2@example.com', NOW() - INTERVAL '15 seconds', NULL, NULL),
('msg_test_002_14', 'conv_test_002', 'outgoing', 'Récapitulatif de l''incident :\nDescription: Ampoule grillée\nZone: Couloir\nÉtage: 1er\nPriorité: basse\nEmail: test2@example.com\n\nConfirmez-vous ces informations ? (oui/non)', NOW() - INTERVAL '10 seconds', 'delivered', NULL),
('msg_test_002_15', 'conv_test_002', 'incoming', 'oui', NOW() - INTERVAL '5 seconds', NULL, NULL),
('msg_test_002_16', 'conv_test_002', 'outgoing', 'Merci ! Votre incident a été enregistré avec le numéro INC002. Vous recevrez un suivi par email.', NOW(), 'delivered', NULL);

-- Insérer des messages pour la troisième conversation (non complétée)
INSERT INTO whatsapp_messages (
    message_id, conversation_id, direction, content, timestamp, status, media_url
) VALUES
('msg_test_003_1', 'conv_test_003', 'incoming', 'Bonjour', NOW() - INTERVAL '5 minutes', NULL, NULL),
('msg_test_003_2', 'conv_test_003', 'outgoing', 'Bienvenue au service de signalement d''incidents. Veuillez scanner ou saisir le code QR du bâtiment concerné.', NOW() - INTERVAL '4 minutes 55 seconds', 'delivered', NULL),
('msg_test_003_3', 'conv_test_003', 'incoming', 'QR12347', NOW() - INTERVAL '4 minutes 30 seconds', NULL, NULL),
('msg_test_003_4', 'conv_test_003', 'outgoing', 'Merci. Veuillez décrire l''incident en quelques mots.', NOW() - INTERVAL '4 minutes 25 seconds', 'delivered', NULL);

-- Insérer des messages pour la quatrième conversation (avec erreurs de validation)
INSERT INTO whatsapp_messages (
    message_id, conversation_id, direction, content, timestamp, status, media_url
) VALUES
('msg_test_004_1', 'conv_test_004', 'incoming', 'Bonjour', NOW() - INTERVAL '10 minutes', NULL, NULL),
('msg_test_004_2', 'conv_test_004', 'outgoing', 'Bienvenue au service de signalement d''incidents. Veuillez scanner ou saisir le code QR du bâtiment concerné.', NOW() - INTERVAL '9 minutes 55 seconds', 'delivered', NULL),
('msg_test_004_3', 'conv_test_004', 'incoming', 'QR12348', NOW() - INTERVAL '9 minutes 30 seconds', NULL, NULL),
('msg_test_004_4', 'conv_test_004', 'outgoing', 'Merci. Veuillez décrire l''incident en quelques mots.', NOW() - INTERVAL '9 minutes 25 seconds', 'delivered', NULL),
('msg_test_004_5', 'conv_test_004', 'incoming', 'x', NOW() - INTERVAL '9 minutes', NULL, NULL),
('msg_test_004_6', 'conv_test_004', 'outgoing', 'La description est trop courte. Veuillez fournir plus de détails.', NOW() - INTERVAL '8 minutes 55 seconds', 'delivered', NULL),
('msg_test_004_7', 'conv_test_004', 'incoming', 'y', NOW() - INTERVAL '8 minutes 30 seconds', NULL, NULL),
('msg_test_004_8', 'conv_test_004', 'outgoing', 'La description est trop courte. Veuillez fournir plus de détails.', NOW() - INTERVAL '8 minutes 25 seconds', 'delivered', NULL);

-- Insérer des données dans la table Redis pour les temps de réponse
-- Note: Ces données seraient normalement stockées dans Redis, mais nous les simulons ici
-- Créer une table temporaire pour les métriques Redis
CREATE TABLE IF NOT EXISTS whatsapp_metrics (
    metric_key VARCHAR(100) PRIMARY KEY,
    metric_value FLOAT
);

-- Insérer des métriques de temps de réponse
INSERT INTO whatsapp_metrics (metric_key, metric_value) VALUES
('avg_response_time', 1.2),
('max_response_time', 3.5),
('min_response_time', 0.5),
('response_count', 32);
