# Plan d'implémentation : WhatsApp Incident Reporting

## Contexte technique

### Environnement existant
- Application SCANDOM avec système de QR codes pour bâtiments
- API d'import d'incident existante (JSON → PostgreSQL)
- Base de données PostgreSQL pour le stockage des données
- Système de génération de QR codes existant

### Nouvelles technologies requises
- **Twilio API** pour l'intégration WhatsApp Business
- **Flask** pour le serveur webhook recevant les messages WhatsApp
- **Redis** pour la gestion des états de conversation et file d'attente de messages
- **Celery** pour les tâches asynchrones (retry des appels API échoués)

### Points d'intégration
- **API WhatsApp Business** via Twilio
- **API d'import d'incident** existante
- **Générateur de QR codes** existant

## Vérification de conformité avec la constitution

| Principe | Conformité | Justification |
|----------|------------|---------------|
| Seamless User Experience | ✅ | Le flux de conversation est conçu pour être simple et intuitif, avec moins de 2 minutes pour déclarer un incident |
| QR Code comme Point d'Entrée Unique | ✅ | Le QR code du bâtiment contient toutes les informations nécessaires pour initier la conversation |
| Conversation Guidée et Structurée | ✅ | Le chatbot guide l'utilisateur à travers un processus structuré avec des questions claires |
| Intégration Transparente | ✅ | L'intégration avec l'API d'import d'incident existante est transparente pour l'utilisateur |
| Sécurité et Confidentialité | ✅ | Les données personnelles sont traitées avec soin et les conversations sont sécurisées |

## Portes qualité

### Critères de passage
- ✅ Toutes les exigences fonctionnelles sont couvertes dans le plan
- ✅ Les critères de succès sont mesurables et vérifiables
- ✅ L'architecture technique est conforme aux principes de la constitution
- ✅ Les risques techniques sont identifiés et des stratégies d'atténuation sont définies

### Risques identifiés
- Limitations de l'API WhatsApp Business (nombre de messages, templates)
- Gestion des conversations interrompues
- Fiabilité de l'API d'import d'incident existante

## Phase 1 : Architecture et conception

### Composants principaux

1. **Module de génération de QR codes avec deep links WhatsApp**
   - Génère des QR codes contenant des URLs avec deep links vers WhatsApp
   - Format: `https://wa.me/[numéro_chatbot]?text=incident:[qr_code_number]`

2. **Webhook Flask pour Twilio**
   - Endpoint `/webhook/twilio` pour recevoir les messages WhatsApp
   - Authentification via signature Twilio
   - Traitement des messages entrants et envoi des réponses

3. **Gestionnaire d'état de conversation**
   - Stockage des états de conversation dans Redis
   - Structure de données clé-valeur avec TTL de 24 heures
   - Clé composite: `conversation:[user_phone]:[building_qr_code]`

4. **Moteur de conversation**
   - Machine à états pour guider l'utilisateur à travers le processus de déclaration
   - Validation des entrées utilisateur à chaque étape
   - Gestion des commandes spéciales (aide, retour, annulation)

5. **Intégrateur d'API d'import d'incident**
   - Conversion des données collectées en JSON conforme au schéma attendu
   - Appel à l'API d'import d'incident existante
   - Gestion des erreurs et stratégie de retry

6. **File d'attente de messages**
   - Utilisation de Celery avec Redis comme broker
   - Tâches asynchrones pour les retries en cas d'erreur technique
   - Monitoring et alerting en cas d'échecs répétés

### Flux de données

```
[QR Code] → [Scan] → [WhatsApp] → [Webhook] → [Moteur de conversation] → [Gestionnaire d'état]
                                                      ↓
                                            [Validation des données]
                                                      ↓
                                     [Intégrateur d'API d'import d'incident]
                                                      ↓
                                    [API d'import d'incident existante] → [PostgreSQL]
                                                      ↓
                                            [Confirmation à l'utilisateur]
```

## Phase 2 : Implémentation

### Étape 1 : Configuration de l'environnement Twilio
- Création d'un compte Twilio
- Configuration du numéro WhatsApp Business
- Configuration du webhook pour recevoir les messages
- Tests de base de l'API WhatsApp

### Étape 2 : Développement du webhook Flask
- Création du serveur Flask
- Implémentation de l'endpoint webhook
- Validation des signatures Twilio
- Logging et monitoring

### Étape 3 : Implémentation du gestionnaire d'état
- Configuration de Redis
- Implémentation des fonctions CRUD pour les états de conversation
- Gestion des TTL et nettoyage des conversations abandonnées

### Étape 4 : Développement du moteur de conversation
- Implémentation de la machine à états
- Définition des étapes de conversation
- Validation des entrées utilisateur
- Gestion des commandes spéciales

### Étape 5 : Intégration avec l'API d'import d'incident
- Implémentation de l'adaptateur pour l'API existante
- Conversion des données collectées en JSON
- Classification des erreurs d'appel API (mapping codes HTTP/réponses → fonctionnel/technique)
- Création d'enregistrements `pending_incidents` dans PostgreSQL pour les erreurs techniques
- Configuration des jobs Celery pour rejouer les incidents en attente selon une stratégie de retry

### Étape 6 : Génération des QR codes avec deep links
- Extension du générateur de QR codes existant
- Implémentation des deep links WhatsApp
- Tests de scan et redirection

### Étape 7 : Tests et validation
- Tests unitaires pour chaque composant
- Tests d'intégration du flux complet
- Tests de performance et de charge
- Tests de récupération après erreur

## Phase 3 : Déploiement et monitoring

### Infrastructure
- Serveur Flask pour le webhook (avec HTTPS)
- Instance Redis pour la gestion des états et file d'attente
- Worker Celery pour les tâches asynchrones

### Monitoring
- Logging structuré des conversations et états avec identifiants de corrélation
- Instrumentation des temps de réponse du webhook et du moteur de conversation
- Métriques opérationnelles pour mesurer les critères de succès :
  - Temps de réponse moyen et distribution (p95, p99) pour SC-003
  - Taux de complétion des conversations pour SC-002
  - Nombre d'interactions par conversation pour SC-001
  - Compteurs d'erreurs fonctionnelles et techniques
  - Nombre de conversations simultanées pour SC-006
- Exposition des métriques via un endpoint dédié ou logs structurés
- Alertes en cas d'erreurs répétées ou de dégradation des métriques

### Documentation
- Guide d'utilisation pour les utilisateurs
- Documentation technique pour les développeurs
- Procédures de troubleshooting

## Dépendances et prérequis

### Externes
- Compte Twilio avec WhatsApp Business API
- Numéro de téléphone dédié pour le chatbot
- Certificat SSL valide pour le webhook

### Internes
- Accès à l'API d'import d'incident existante
- Accès au générateur de QR codes existant
- Accès à la base de données PostgreSQL

## Estimation et planification

### Effort estimé
- Configuration Twilio et webhook : 2 jours
- Gestionnaire d'état et moteur de conversation : 5 jours
- Intégration API et génération QR codes : 3 jours
- Tests et corrections : 4 jours
- Documentation et déploiement : 1 jour

**Total** : 15 jours de développement

### Jalons clés
1. Configuration Twilio et webhook fonctionnels
2. Prototype de conversation simple
3. Intégration complète avec l'API d'import d'incident
4. Tests de bout en bout réussis
5. Déploiement en production