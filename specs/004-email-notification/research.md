# Research: Email Notification for Incidents

**Feature**: 004-email-notification  
**Date**: 2026-01-30

## Décisions techniques

### 1. Bibliothèque d'envoi d'email

**Decision**: `smtplib` (bibliothèque standard Python)

**Rationale**: 
- Inclus dans la bibliothèque standard Python, pas de dépendance externe
- Suffisant pour l'envoi SMTP simple
- Bien documenté et stable

**Alternatives considered**:
- `sendgrid`: API cloud, nécessite un compte externe et des coûts
- `mailgun`: Idem, dépendance externe
- `yagmail`: Simplifie Gmail mais limite les options SMTP

### 2. Templates HTML

**Decision**: `Jinja2` (déjà utilisé par Flask)

**Rationale**:
- Déjà présent dans le projet via Flask
- Syntaxe familière et puissante
- Permet la séparation template/logique

**Alternatives considered**:
- String formatting: Trop basique pour du HTML complexe
- Mako: Ajouterait une dépendance inutile

### 3. Exécution asynchrone

**Decision**: `Celery` (déjà configuré dans le projet)

**Rationale**:
- Infrastructure Celery déjà en place pour WhatsApp
- Gestion native des retries et erreurs
- Scalabilité horizontale si besoin

**Alternatives considered**:
- Threading Python: Moins robuste, pas de persistance des tâches
- asyncio: Nécessiterait une refonte de l'architecture

### 4. Stockage de l'historique

**Decision**: Table PostgreSQL `email_notifications`

**Rationale**:
- Cohérent avec la constitution (PostgreSQL source de vérité)
- Permet les requêtes SQL pour le diagnostic
- Traçabilité complète avec horodatage

**Alternatives considered**:
- Logs uniquement: Pas de requêtes structurées possibles
- Redis: Pas persistant par défaut, moins adapté à l'historique

### 5. Configuration SMTP

**Decision**: Variables d'environnement + fichier config.ini

**Rationale**:
- Cohérent avec la configuration WhatsApp existante
- Secrets via variables d'environnement (sécurité)
- Flexibilité entre environnements (dev/prod)

**Variables requises**:
- `SMTP_HOST`: Serveur SMTP
- `SMTP_PORT`: Port (587 pour TLS, 465 pour SSL)
- `SMTP_USER`: Utilisateur d'authentification
- `SMTP_PASSWORD`: Mot de passe
- `SMTP_FROM_EMAIL`: Adresse expéditeur
- `SMTP_USE_TLS`: Activer TLS (true/false)

### 6. Gestion des erreurs et retries

**Decision**: Celery avec retry exponentiel

**Rationale**:
- Gestion native des retries dans Celery
- Backoff exponentiel pour éviter de surcharger le serveur SMTP
- Nombre de tentatives configurable

**Configuration**:
- Max retries: 3
- Délai initial: 60 secondes
- Backoff factor: 2 (60s, 120s, 240s)

## Intégration avec le flux existant

### Point d'intégration

L'envoi d'email sera déclenché après la création réussie d'un incident dans `conversation_manager.py`, au moment où l'incident est validé et persisté.

```
Flux: WhatsApp → ConversationManager → IncidentAPI → [SUCCESS] → EmailTask.delay()
```

### Dépendances

- Feature `005-whatsapp-incident-reporting` doit être opérationnelle
- Table `buildings` doit contenir `EMAIL_GESTIONNAIRE`
- Celery worker doit être actif

## Risques identifiés

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Serveur SMTP indisponible | Emails non envoyés | Retries + logging + alerte |
| Email gestionnaire invalide | Bounce | Validation format + logging |
| Volume élevé d'incidents | Saturation SMTP | Rate limiting Celery |
| Template HTML mal rendu | Email illisible | Tests unitaires templates |
