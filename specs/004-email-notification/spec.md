# Feature Specification: Email Notification for Incidents

**Feature Branch**: `004-email-notification`  
**Created**: 2026-01-30  
**Status**: Implemented  
**Input**: User description: "Création d'un serveur d'envoi d'emails - on doit créer un serveur pour envoyer des emails - on doit créer un template d'email : objet : « l'incident n°XXX a été créé », body : summary de l'incident - lorsque l'incident est validé par l'utilisateur - l'email est envoyé au gestionnaire"

## Clarifications

### Session 2026-01-30

- Q: Qui est le "gestionnaire" destinataire de l'email ? → A: Le gestionnaire du bâtiment associé à l'incident (email stocké dans la table buildings)
- Q: Que contient exactement le "summary" de l'incident ? → A: Les informations collectées pendant la conversation WhatsApp (étage, zone, catégorie, description, photos)
- Q: Comment le serveur d'envoi d'emails est-il configuré ? → A: Via un serveur SMTP configurable (variables d'environnement)
- Q: Quel format doit être utilisé pour le corps de l'email ? → A: HTML (pour une mise en forme structurée et des liens cliquables)
- Q: Quelle adresse doit être utilisée comme expéditeur ? → A: Adresse configurable via variable d'environnement (ex: noreply@scandom.io)
- Q: Comment les photos de l'incident doivent-elles être incluses ? → A: Liens vers les photos uniquement (pas de pièces jointes)
- Q: Quel est le mode d'exécution de l'envoi d'email ? → A: Asynchrone (via Celery/Worker) pour ne pas bloquer l'utilisateur
- Q: Comment l'historique des notifications doit-il être stocké ? → A: Table PostgreSQL dédiée (email_notifications) pour une traçabilité structurée

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Notifier le gestionnaire lors de la création d'un incident (Priority: P1)

Un utilisateur déclare un incident via WhatsApp, le système envoie automatiquement une notification par email au gestionnaire du bâtiment avec le résumé de l'incident.

**Why this priority**: C'est la fonctionnalité principale qui permet aux gestionnaires d'être informés des incidents dans leurs bâtiments en temps réel.

**Independent Test**: En déclarant un incident via WhatsApp et en le validant, le gestionnaire du bâtiment reçoit un email avec le résumé de l'incident.

**Acceptance Scenarios**:

1. **Given** un utilisateur déclare un incident via WhatsApp, **When** l'incident est validé et créé dans la base de données, **Then** un email est envoyé au gestionnaire du bâtiment avec l'objet "l'incident n°XXX a été créé" et le résumé de l'incident dans le corps.
2. **Given** un incident est créé, **When** l'email est envoyé, **Then** l'objet contient le numéro QR de l'incident et le corps contient toutes les informations collectées (étage, zone, catégorie, description, photos).
3. **Given** le gestionnaire du bâtiment n'a pas d'email configuré, **When** l'incident est créé, **Then** l'incident est créé mais aucun email n'est envoyé et un avertissement est journalisé.

---

### User Story 2 - Consulter l'historique des notifications envoyées (Priority: P2)

Un administrateur peut consulter l'historique des notifications email envoyées pour un incident donné.

**Why this priority**: Permet le diagnostic et le suivi des notifications envoyées.

**Independent Test**: En consultant un incident, l'administrateur peut voir si une notification a été envoyée et son statut.

**Acceptance Scenarios**:

1. **Given** un incident avec une notification envoyée, **When** l'administrateur consulte l'incident, **Then** il peut voir le statut de la notification (envoyé/échoué), la date d'envoi et le destinataire.

---

### Edge Cases

- System MUST gérer les erreurs d'envoi d'email (serveur SMTP non disponible, adresse email invalide) sans bloquer la création de l'incident.
- System MUST journaliser les erreurs d'envoi d'email pour permettre le diagnostic ultérieur.
- System MUST permettre la configuration de plusieurs tentatives d'envoi en cas d'échec temporaire.
- System MUST journaliser une erreur de niveau CRITICAL après l'échec de la dernière tentative d'envoi (max retries atteint) pour permettre une intervention manuelle.
- System MUST ne pas envoyer d'email si l'incident est marqué comme "en attente" (pending) suite à une erreur technique lors de l'appel à l'API d'import.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST envoyer un email au gestionnaire du bâtiment lorsqu'un incident est validé et créé avec succès.
- **FR-002**: System MUST utiliser un template d'email avec l'objet "l'incident n°XXX a été créé" où XXX est le numéro QR de l'incident.
- **FR-003**: System MUST inclure dans le corps de l'email le résumé de l'incident au format HTML contenant obligatoirement : étage, zone, catégorie, description, date de création, et liens vers les photos (si présentes).
- **FR-004**: System MUST récupérer l'email du gestionnaire depuis les informations du bâtiment associé à l'incident.
- **FR-005**: System MUST utiliser un serveur d'envoi d'emails configurable via variables d'environnement (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_EMAIL).
- **FR-011**: System MUST envoyer les notifications email de manière asynchrone (via Celery) pour garantir la réactivité de l'interface utilisateur.
- **FR-006**: System MUST journaliser les erreurs d'envoi d'email sans bloquer la création de l'incident.
- **FR-007**: System MUST ne pas envoyer d'email si l'incident est marqué comme "en attente" suite à une erreur technique.
- **FR-008**: System MUST permettre la configuration du nombre de tentatives d'envoi et du délai entre les tentatives en cas d'échec temporaire.
- **FR-009**: System MUST ne pas envoyer d'email si aucun gestionnaire n'est associé au bâtiment ou si l'email du gestionnaire n'est pas configuré.
- **FR-010**: System MUST conserver un historique des notifications envoyées dans une table PostgreSQL dédiée `email_notifications` (statut, date, destinataire, erreur éventuelle).

### Key Entities

- **EmailNotification**: Représente une notification email envoyée pour un incident (stockée dans la table `email_notifications`).
  - Attributs clés: identifiant de l'incident (clé étrangère), email du destinataire, objet, corps HTML, date d'envoi, statut (envoyé/échoué), message d'erreur éventuel
  - Contrainte clé: un seul email de notification par incident

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Au moins 95% des emails de notification sont envoyés avec succès dans les 5 minutes suivant la création de l'incident.
- **SC-002**: Le temps d'envoi de l'email après la création de l'incident est inférieur à 30 secondes dans 90% des cas.
- **SC-003**: Les erreurs d'envoi d'email n'empêchent pas la création de l'incident (taux d'échec de création dû aux emails < 1%).
- **SC-004**: Le système peut gérer au moins 100 envois d'emails par minute sans dégradation de performance.

## Assumptions

- Les gestionnaires de bâtiments ont une adresse email valide configurée dans les informations du bâtiment.
- Un serveur d'envoi d'emails est disponible et configuré.
- Le système a accès au réseau pour contacter le serveur d'envoi d'emails.
- Les emails envoyés ne contiennent pas de données sensibles autres que les informations de l'incident déjà stockées dans la base de données.
- La fonctionnalité de déclaration d'incident via WhatsApp (feature 005-whatsapp-incident-reporting) est opérationnelle.
