# Tâches d'implémentation : WhatsApp Incident Reporting

Ce document liste les tâches d'implémentation pour la fonctionnalité d'intégration WhatsApp permettant aux utilisateurs de déclarer des incidents en scannant le QR code d'un bâtiment.

## Phase 1 : Configuration et environnement

- [x] T001 Créer la structure de répertoires pour l'intégration WhatsApp dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/`
- [x] T002 Installer les dépendances requises (Flask, Twilio, Redis, Celery) dans l'environnement du projet
- [x] T003 Configurer un compte Twilio et obtenir les identifiants API (Account SID, Auth Token)
- [x] T004 Créer un fichier de configuration pour les paramètres Twilio et Redis dans `/home/jeremy/Documents/Projet/scandom/config/whatsapp/config.ini`
- [x] T005 [P] Configurer Redis pour la persistance des états de conversation et les files d'attente Celery

## Phase 2 : Fondations techniques

- [x] T006 Créer le module d'initialisation dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/__init__.py`
- [x] T007 Implémenter les modèles de données PostgreSQL pour les conversations et messages dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/models.py`
- [x] T008 [P] Créer les scripts de migration SQL pour les tables WhatsApp dans `/home/jeremy/Documents/Projet/scandom/migrations/003_create_whatsapp_tables.sql`
- [x] T009 Implémenter la classe de gestion d'état Redis dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/state_manager.py`
- [x] T010 [P] Configurer Celery pour les tâches asynchrones dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/tasks.py`
- [x] T011 Créer l'utilitaire de validation de signature Twilio dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/security.py`

## Phase 3 : User Story 1 - Déclarer un incident via WhatsApp

### Objectif
Permettre à un utilisateur de scanner un QR code de bâtiment, être dirigé vers WhatsApp et compléter une déclaration d'incident guidée par le chatbot.

### Test indépendant
En scannant un QR code valide, l'utilisateur est dirigé vers WhatsApp et peut compléter la déclaration d'incident en suivant les instructions du chatbot.

### Tâches d'implémentation

- [ ] T012 [US1] Étendre le générateur de QR codes pour créer des deep links WhatsApp dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/qr_generator.py`
- [ ] T013 [US1] Implémenter l'endpoint Flask pour le webhook Twilio dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/webhook.py`
- [ ] T014 [P] [US1] Créer le gestionnaire de messages entrants dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/message_handler.py`
- [ ] T015 [US1] Implémenter la machine à états du flux de conversation dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/conversation.py`
- [ ] T016 [P] [US1] Développer les validateurs d'entrée utilisateur dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/validators.py`
- [ ] T017 [US1] Implémenter l'adaptateur pour l'API d'import d'incident dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/incident_api.py`
- [ ] T018 [US1] Créer le service d'envoi de messages WhatsApp via Twilio dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/message_service.py`
- [ ] T019 [US1] Implémenter la génération de QR codes d'incident pour les confirmations dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/incident_qr.py`

## Phase 4 : User Story 2 - Reprendre une conversation interrompue

### Objectif
Permettre à un utilisateur de reprendre une conversation interrompue sans perdre les informations déjà fournies.

### Test indépendant
Un utilisateur quitte la conversation en cours de déclaration et la reprend plus tard pour la compléter.

### Tâches d'implémentation

- [ ] T020 [US2] Implémenter la persistance des états de conversation dans Redis avec TTL dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/state_manager.py`
- [ ] T021 [US2] Développer la logique de détection des conversations existantes dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/conversation.py`
- [ ] T022 [P] [US2] Implémenter la gestion des timeouts et rappels d'inactivité dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/timeout_handler.py`
- [ ] T023 [US2] Créer la fonctionnalité de reprise de conversation au point d'interruption dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/conversation.py`

## Phase 5 : User Story 3 - Recevoir une confirmation d'incident créé

### Objectif
Fournir à l'utilisateur une confirmation avec les détails de l'incident créé et son QR code.

### Test indépendant
Après avoir complété la déclaration, l'utilisateur reçoit un message de confirmation avec les détails de l'incident et son QR code.

### Tâches d'implémentation

- [ ] T024 [US3] Implémenter la génération du message de confirmation dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/confirmation_service.py`
- [ ] T025 [US3] Développer la fonctionnalité d'envoi de QR codes en tant que média WhatsApp dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/message_service.py`
- [ ] T026 [P] [US3] Créer le gestionnaire de statut des messages envoyés dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/status_handler.py`

## Phase 6 : Gestion des erreurs et cas limites

- [ ] T027 Implémenter la gestion des erreurs fonctionnelles (bâtiment introuvable, données invalides) dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/error_handler.py`, incluant une fonction de classification d'erreurs (`classify_import_error`) qui détermine si une erreur est fonctionnelle ou technique selon les codes HTTP et le contenu de la réponse, et renvoie le message approprié à l'utilisateur
- [ ] T028 Développer la file d'attente pour les retries en cas d'erreur technique dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/retry_queue.py`, incluant la persistance des incidents techniques dans la table `pending_incidents` et la création d'un job Celery de retry périodique basé sur `next_retry` et `retry_count`
- [ ] T029 [P] Implémenter la détection et gestion des doubles soumissions dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/conversation.py`
- [ ] T030 Créer le système de journalisation des conversations et erreurs dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/logger.py`
- [ ] T036 [P] Implémenter l'instrumentation des métriques opérationnelles (temps de réponse, taux de complétion, erreurs) dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/metrics.py`
- [ ] T037 Développer les jobs de purge et d'anonymisation des données selon la politique de rétention dans `/home/jeremy/Documents/Projet/scandom/src/whatsapp/retention.py`

## Phase 7 : Tests et déploiement

- [ ] T031 [P] Écrire les tests unitaires pour chaque composant dans `/home/jeremy/Documents/Projet/scandom/tests/whatsapp/`
- [ ] T032 Créer les tests d'intégration pour le flux complet dans `/home/jeremy/Documents/Projet/scandom/tests/whatsapp/integration/`
- [ ] T033 Implémenter les tests de performance et de charge dans `/home/jeremy/Documents/Projet/scandom/tests/whatsapp/performance/`
- [ ] T034 Préparer la documentation technique dans `/home/jeremy/Documents/Projet/scandom/docs/whatsapp/`
- [ ] T035 Configurer le serveur de production avec HTTPS pour le webhook Twilio

## Dépendances

### Dépendances entre User Stories

```
User Story 1 (Déclarer un incident) → User Story 3 (Recevoir une confirmation)
                                    ↘
                                      User Story 2 (Reprendre une conversation)
```

### Exécution parallèle possible

Les tâches marquées [P] peuvent être exécutées en parallèle car elles concernent des fichiers différents ou n'ont pas de dépendances directes entre elles.

## Stratégie d'implémentation

1. **MVP** : Implémenter d'abord User Story 1 (Déclarer un incident) avec un flux de base sans gestion des erreurs avancée
2. **Itération 1** : Ajouter User Story 3 (Confirmation) pour compléter le flux principal
3. **Itération 2** : Implémenter User Story 2 (Reprise de conversation) pour améliorer l'expérience utilisateur
4. **Itération 3** : Ajouter la gestion avancée des erreurs et cas limites
5. **Itération 4** : Finaliser avec les tests, la documentation et le déploiement
