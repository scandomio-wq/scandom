# Modèle de données pour l'intégration WhatsApp

Ce document décrit les structures de données nécessaires pour l'intégration WhatsApp avec le système d'import d'incidents SCANDOM.

## Entités principales

### ConversationState

Représente l'état d'une conversation WhatsApp en cours entre un utilisateur et le chatbot.

| Champ | Type | Description | Contraintes |
|-------|------|-------------|------------|
| conversation_id | STRING | Identifiant unique de la conversation | PRIMARY KEY |
| user_phone | STRING | Numéro de téléphone de l'utilisateur | NOT NULL, INDEX |
| building_qr_code | STRING | QR code du bâtiment concerné | NOT NULL, INDEX |
| current_step | STRING | Étape actuelle de la conversation | NOT NULL |
| collected_data | JSON | Données collectées jusqu'à présent | NOT NULL |
| last_activity | TIMESTAMP | Date et heure de la dernière activité | NOT NULL |
| is_completed | BOOLEAN | Indique si la conversation est terminée | NOT NULL, DEFAULT FALSE |
| created_at | TIMESTAMP | Date et heure de création | NOT NULL |
| updated_at | TIMESTAMP | Date et heure de dernière mise à jour | NOT NULL |

#### Structure du JSON collected_data

```json
{
  "zone": "string",
  "etage": "string",
  "categorie": "string",
  "type": "string",
  "informations_supplementaires": "string",
  "reporter_phone": "string",
  "reporter_email": "string"
}
```

### WhatsAppMessage

Représente un message échangé dans une conversation WhatsApp.

| Champ | Type | Description | Contraintes |
|-------|------|-------------|------------|
| message_id | STRING | Identifiant unique du message | PRIMARY KEY |
| conversation_id | STRING | Référence à la conversation | NOT NULL, FOREIGN KEY |
| direction | ENUM | Direction du message (entrant/sortant) | NOT NULL |
| content | TEXT | Contenu du message | NOT NULL |
| timestamp | TIMESTAMP | Date et heure du message | NOT NULL |
| status | ENUM | Statut du message (envoyé, livré, lu, échoué) | NOT NULL |
| media_url | STRING | URL du média attaché (si applicable) | NULL |

### PendingIncident

Représente un incident en attente de traitement suite à une erreur technique lors de l'appel à l'API d'import.

| Champ | Type | Description | Contraintes |
|-------|------|-------------|------------|
| id | STRING | Identifiant unique de l'incident en attente | PRIMARY KEY |
| conversation_id | STRING | Référence à la conversation | NOT NULL, FOREIGN KEY |
| incident_data | JSON | Données complètes de l'incident | NOT NULL |
| error_message | TEXT | Message d'erreur rencontré | NOT NULL |
| retry_count | INTEGER | Nombre de tentatives effectuées | NOT NULL, DEFAULT 0 |
| next_retry | TIMESTAMP | Date et heure de la prochaine tentative | NOT NULL |
| created_at | TIMESTAMP | Date et heure de création | NOT NULL |
| updated_at | TIMESTAMP | Date et heure de dernière mise à jour | NOT NULL |

## Stockage

### Redis

Redis sera utilisé pour stocker les états de conversation actifs avec une expiration automatique (TTL) de 24 heures.

#### Clés Redis

- `conversation:{user_phone}:{building_qr_code}` - Stocke l'état complet de la conversation
- `message_queue:retry` - File d'attente pour les messages à réessayer
- `rate_limit:{user_phone}` - Compteur pour la limitation de débit par utilisateur

### PostgreSQL

PostgreSQL sera utilisé pour stocker l'historique des conversations et des messages pour analyse et audit.

#### Tables PostgreSQL

- `whatsapp_conversations` - Stocke l'historique des conversations
- `whatsapp_messages` - Stocke l'historique des messages
- `pending_incidents` - Stocke les incidents en attente de traitement

## Relations

- Un `ConversationState` peut avoir plusieurs `WhatsAppMessage`
- Un `ConversationState` peut avoir un `PendingIncident`
- Un `PendingIncident` est lié à un `ConversationState`

## Indexation

Pour optimiser les performances des requêtes fréquentes, les index suivants sont créés :

1. Index sur `ConversationState.user_phone` pour accélérer la recherche par numéro de téléphone
2. Index sur `ConversationState.building_qr_code` pour accélérer la recherche par QR code de bâtiment
3. Index sur `WhatsAppMessage.conversation_id` pour accélérer la recherche des messages par conversation
4. Index sur `PendingIncident.next_retry` pour accélérer la recherche des incidents à réessayer

## Migrations

### Migration initiale

```sql
-- Table pour les conversations WhatsApp
CREATE TABLE whatsapp_conversations (
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
CREATE INDEX idx_whatsapp_conversations_user_phone ON whatsapp_conversations(user_phone);
CREATE INDEX idx_whatsapp_conversations_building_qr_code ON whatsapp_conversations(building_qr_code);
CREATE INDEX idx_whatsapp_conversations_last_activity ON whatsapp_conversations(last_activity);

-- Table pour les messages WhatsApp
CREATE TABLE whatsapp_messages (
    message_id VARCHAR(50) PRIMARY KEY,
    conversation_id VARCHAR(50) NOT NULL,
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('incoming', 'outgoing')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    status VARCHAR(10) NOT NULL CHECK (status IN ('sent', 'delivered', 'read', 'failed')),
    media_url VARCHAR(255),
    FOREIGN KEY (conversation_id) REFERENCES whatsapp_conversations(conversation_id)
);

-- Index pour les messages
CREATE INDEX idx_whatsapp_messages_conversation_id ON whatsapp_messages(conversation_id);
CREATE INDEX idx_whatsapp_messages_timestamp ON whatsapp_messages(timestamp);

-- Table pour les incidents en attente
CREATE TABLE pending_incidents (
    id VARCHAR(50) PRIMARY KEY,
    conversation_id VARCHAR(50) NOT NULL,
    incident_data JSONB NOT NULL,
    error_message TEXT NOT NULL,
    retry_count INTEGER NOT NULL DEFAULT 0,
    next_retry TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES whatsapp_conversations(conversation_id)
);

-- Index pour les incidents en attente
CREATE INDEX idx_pending_incidents_next_retry ON pending_incidents(next_retry);
CREATE INDEX idx_pending_incidents_conversation_id ON pending_incidents(conversation_id);
```
