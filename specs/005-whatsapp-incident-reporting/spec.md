# Feature Specification: WhatsApp Incident Reporting

**Feature Branch**: `005-whatsapp-incident-reporting`  
**Created**: 2026-01-22  
**Status**: Draft  
**Input**: User description: "j'ai donc un qr_code pour identifier un bâtiment. J'ai un fichier json de sortie à instancier en base de données. Je veux maintenant proposer à un utilisateur de scanner le qr_code de l'immeuble. Cette action va ouvrir une discussion whatsapp. Un chatbot va lui demander la zone, la catégorie et le type d'incident. Puis il enverra le fichier json de sortie à la base de données pour l'instancier."

## Clarifications

### Session 2026-01-22

- Q: Format du lien dans le QR code → A: URL de type `https://wa.me/<NUMERO_CHATBOT>?text=incident:<QR_CODE_NUMBER>` (deep link WhatsApp incluant le QR_CODE_NUMBER du bâtiment)
- Q: Gestion des conversations interrompues → A: État de conversation persistant en base de données
- Q: Authentification des utilisateurs → A: Numéro de téléphone comme identifiant unique
- Q: Gestion des échecs d'appel à l'API d'import d'incident → A: Stratégie hybride à deux niveaux: tentative synchrone, puis mise en file d'attente persistante et retry pour les erreurs techniques, erreurs fonctionnelles retournées directement à l'utilisateur

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Déclarer un incident via WhatsApp (Priority: P1)

Un utilisateur scanne le QR code d'un bâtiment et est dirigé vers une conversation WhatsApp où un chatbot le guide pour déclarer un incident.

**Why this priority**: C'est la fonctionnalité principale qui permet aux utilisateurs de déclarer facilement des incidents.

**Independent Test**: En scannant un QR code valide, l'utilisateur est dirigé vers WhatsApp et peut compléter la déclaration d'incident en suivant les instructions du chatbot.

**Acceptance Scenarios**:

1. **Given** un utilisateur scanne le QR code d'un bâtiment existant, **When** le QR code est scanné, **Then** une conversation WhatsApp s'ouvre avec le chatbot.
2. **Given** une conversation WhatsApp est initiée, **When** l'utilisateur répond aux questions du chatbot, **Then** le chatbot collecte toutes les informations nécessaires pour créer un incident.
3. **Given** toutes les informations sont collectées, **When** l'utilisateur confirme les informations, **Then** un incident est créé dans la base de données et l'utilisateur reçoit une confirmation avec le QR code de l'incident.
4. **Given** l'utilisateur a confirmé sa déclaration et que l'appel à l'API d'import d'incident rencontre une erreur technique (timeout, 5xx, problème réseau), **When** le système applique la stratégie de retry, **Then** la déclaration est mise en file d'attente technique pour retry ultérieur et l'utilisateur est informé que sa déclaration est prise en compte mais sera traitée plus tard.
5. **Given** l'utilisateur a confirmé sa déclaration et que l'appel à l'API d'import d'incident rencontre une erreur fonctionnelle (bâtiment introuvable, données invalides), **When** l'API renvoie une erreur fonctionnelle, **Then** l'utilisateur reçoit un message explicite décrivant le problème et est invité soit à corriger les informations, soit à interrompre la déclaration.

---

### User Story 2 - Reprendre une conversation interrompue (Priority: P2)

Un utilisateur qui a interrompu sa déclaration d'incident peut reprendre la conversation plus tard sans perdre les informations déjà fournies.

**Why this priority**: Améliore l'expérience utilisateur en permettant de gérer les interruptions.

**Independent Test**: Un utilisateur quitte la conversation en cours de déclaration et la reprend plus tard pour la compléter.

**Acceptance Scenarios**:

1. **Given** un utilisateur a commencé à déclarer un incident, **When** il quitte la conversation avant de la terminer, **Then** l'état de la conversation est sauvegardé.
2. **Given** un utilisateur a une conversation en cours, **When** il revient dans la conversation après une interruption, **Then** le chatbot lui propose de reprendre où il s'était arrêté.

---

### User Story 3 - Recevoir une confirmation d'incident créé (Priority: P3)

Après avoir complété la déclaration d'incident, l'utilisateur reçoit une confirmation avec les détails de l'incident et son QR code.

**Why this priority**: Fournit une preuve de déclaration à l'utilisateur.

**Independent Test**: Après avoir complété la déclaration, l'utilisateur reçoit un message de confirmation avec les détails de l'incident et son QR code.

**Acceptance Scenarios**:

1. **Given** un utilisateur a complété sa déclaration d'incident, **When** l'incident est créé avec succès, **Then** l'utilisateur reçoit un message de confirmation avec les détails de l'incident.
2. **Given** un incident est créé avec succès, **When** l'utilisateur reçoit la confirmation, **Then** le message contient le QR code de l'incident.

### Edge Cases

- System MUST informer l'utilisateur lorsque le QR code scanné ne correspond à aucun bâtiment existant et ne pas créer d'incident.
- System MUST, en cas de réponse utilisateur ne correspondant pas au format attendu, expliquer l'erreur et redemander une réponse valide (en rappelant les options si nécessaire).
- System MUST gérer la perte de connexion pendant la conversation en permettant à l'utilisateur de reprendre là où il en était dans un délai de 24 heures grâce à la persistance de l'état dans Redis.
- System MUST gérer des messages multiples envoyés rapidement en ne considérant que le dernier message valide pour l'étape courante et en ignorant les doublons éventuels.
- System MUST, à tout moment, fournir une commande d'aide ("Aide", "Help", "?") qui affiche la liste des commandes disponibles et rappelle comment continuer la déclaration.
- System MUST, en cas d'erreur technique lors de l'appel à l'API d'import d'incident (timeout, erreurs réseau, 5xx), informer l'utilisateur que la déclaration a été prise en compte mais sera finalisée plus tard, créer un enregistrement `PendingIncident` et planifier un retry conformément à FR-014.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST générer des QR codes pour les bâtiments contenant une URL avec deep link vers WhatsApp.
- **FR-002**: System MUST ouvrir automatiquement WhatsApp avec le numéro du chatbot pré-rempli lorsque le QR code est scanné.
- **FR-003**: System MUST envoyer un message d'accueil personnalisé mentionnant le bâtiment concerné.
- **FR-004**: System MUST guider l'utilisateur à travers un processus structuré pour collecter:
  - Zone concernée par l'incident
  - Étage
  - Catégorie de l'incident
  - Type spécifique
  - Informations supplémentaires
  - Coordonnées du déclarant (si non disponibles via WhatsApp)
- **FR-005**: System MUST valider les réponses de l'utilisateur à chaque étape et demander une correction si nécessaire.
- **FR-006**: System MUST permettre à l'utilisateur de revenir en arrière pour modifier une réponse précédente.
- **FR-007**: System MUST sauvegarder l'état de la conversation pour permettre une reprise ultérieure.
- **FR-008**: System MUST générer un fichier JSON conforme au schéma attendu par l'API d'import d'incident.
- **FR-009**: System MUST envoyer le JSON à l'API d'import d'incident existante.
- **FR-010**: System MUST envoyer une confirmation à l'utilisateur avec les détails de l'incident créé et son QR code.
- **FR-011**: System MUST gérer les erreurs de communication avec l'API et informer l'utilisateur en cas d'échec.
- **FR-012**: System MUST fournir une option d'aide à chaque étape de la conversation.
 - **FR-013**: System MUST limiter le temps d'inactivité d'une conversation à 24 heures avant de la considérer comme abandonnée.
 - **FR-014**: System MUST distinguer les erreurs fonctionnelles (ex: bâtiment introuvable, données invalides) des erreurs techniques (timeout, erreurs réseau, 5xx) lors de l'appel à l'API d'import d'incident, tenter une création synchrone, puis en cas d'erreur technique mettre la demande en file d'attente persistante pour retry ultérieur tout en informant l'utilisateur de la prise en compte différée.
   - Les erreurs **fonctionnelles** doivent être remontées immédiatement à l'utilisateur avec un message explicite et ne doivent pas être placées en file d'attente.
   - Les erreurs **techniques** doivent créer un enregistrement `PendingIncident` contenant l'intégralité des données d'incident et l'erreur rencontrée, afin d'être rejouées ultérieurement par un worker asynchrone.
   - La classification des erreurs doit être basée sur les codes de retour HTTP et/ou le contenu de la réponse de l'API d'import (schéma de mapping documenté au niveau de l'implémentation).
- **FR-015**: System MUST synchroniser l'état de conversation entre le cache Redis et le stockage persistant PostgreSQL. Lors de la reprise d'une conversation, le système doit vérifier PostgreSQL si l'état n'est pas présent dans Redis.
- **FR-016**: System MUST dédupliquer les messages entrants en utilisant l'identifiant unique du message (`MessageSid`) pour éviter le traitement multiple d'un même message.
- **FR-017**: System MUST, lors du démarrage d'une nouvelle conversation pour un utilisateur ayant une conversation existante, marquer l'ancienne conversation comme obsolète (`is_completed=true`) tout en la conservant dans l'historique.
- **FR-018**: System MUST attendre qu'un utilisateur envoie un message pour déclencher l'envoi du message de bienvenue. Le système ne doit pas envoyer de message proactif sans action préalable de l'utilisateur.
- **FR-019**: System MUST, pour les étapes utilisant des templates interactifs approuvés par Meta, prévoir un mécanisme de fallback vers un message texte simple si le template n'est pas disponible ou non approuvé.
- **FR-020**: System MUST, en cas de saisie invalide pour une étape utilisant un template interactif, envoyer d'abord un message d'erreur explicatif puis renvoyer le template interactif pour permettre une nouvelle sélection.
- **FR-021**: System MUST inclure l'adresse du bâtiment dans le message de bienvenue pour confirmer à l'utilisateur qu'il interagit avec le bon service.
- **FR-022**: System MUST annoncer dès le message de bienvenue les étapes du processus de déclaration (Étage, Zone, Catégorie, Description, Photos) pour permettre à l'utilisateur de se projeter.
- **FR-023**: System MUST accepter les variations de saisie utilisateur (majuscules/minuscules, avec ou sans accents, numéros ou texte) lors de la validation des réponses.

#### Mapping vers le JSON d'import d'incident

Le JSON envoyé à l'API d'import d'incident (feature `002-incident-import`) doit respecter au minimum la structure suivante :

```json
{
  "BUILDING_QR_CODE": "QR12345678",
  "REPORTER_PHONE": "+33123456789",
  "REPORTER_EMAIL": "user@example.com",
  "INCIDENT_INFORMATION": {
    "zone": "Hall d'entrée",
    "etage": "RDC",
    "categorie": "Plomberie",
    "type": "Fuite d'eau",
    "informations_supplementaires": "Fuite près de l'ascenseur"
  }
}
```

Les données collectées pendant la conversation sont mappées vers ce JSON comme suit :

- Le QR code du bâtiment scanné (`building_qr_code`) est envoyé dans le champ `BUILDING_QR_CODE`.
- Le numéro WhatsApp de l'utilisateur est utilisé comme `REPORTER_PHONE`.
- L'email fourni (si présent) pendant la conversation est utilisé comme `REPORTER_EMAIL`.
- Les champs `zone`, `etage`, `categorie`, `type` et `informations_supplementaires` collectés par le chatbot sont recopiés tels quels dans l'objet `INCIDENT_INFORMATION`.

Les champs obligatoires et validations détaillées restent ceux définis dans la spécification `002-incident-import` (modèle de données et schéma JSON de référence).

### Key Entities *(include if feature involves data)*

- **ConversationState**: Représente l'état d'une conversation WhatsApp en cours.
  - Attributs clés: `conversation_id`, `user_phone`, `building_qr_code`, `current_step`, `collected_data`, `last_activity`, `is_completed`
  - Contrainte clé: `conversation_id` unique
  - Contrainte clé: `user_phone` et `building_qr_code` forment une clé composite

- **WhatsAppMessage**: Représente un message échangé dans une conversation.
  - Attributs clés: `message_id`, `conversation_id`, `direction` (entrant/sortant), `content`, `timestamp`
  - Contrainte clé: `message_id` unique
  - Contrainte clé: `conversation_id` référence une conversation existante

## Non-Functional Requirements

- **NFR-001**: System MUST exposer des métriques opérationnelles pour l'intégration WhatsApp (temps de réponse du webhook, nombre de conversations démarrées/complétées, nombre d'erreurs fonctionnelles et techniques) afin de permettre la mesure des critères de succès SC-001, SC-002, SC-003 et SC-006.
- **NFR-002**: System MUST produire des logs structurés permettant de corréler une conversation donnée, les appels à l'API d'import d'incident et les erreurs associées.
- **NFR-003**: System MUST appliquer les règles de rétention et de confidentialité décrites dans la section "Rétention & Confidentialité" (durée de conservation, purge/anonymisation des données personnelles).
- **NFR-004**: System SHOULD être évalué au moyen d'un questionnaire System Usability Scale (SUS) sur un panel d'utilisateurs représentatifs, avec un objectif de score ≥ 80/100.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un utilisateur peut déclarer un incident complet en moins de 2 minutes et en moins de 10 interactions.
- **SC-002**: Le taux de complétion des conversations (conversations aboutissant à un incident créé) est d'au moins 90%.
- **SC-003**: Le temps de réponse du chatbot est inférieur à 2 secondes dans 95% des cas.
 - **SC-004**: Le taux d'erreur de validation des données collectées est inférieur à 5%.
 - **SC-005**: Au moins 80% des utilisateurs peuvent reprendre une conversation interrompue sans perte de données.
 - **SC-006**: Le système peut gérer au moins 100 conversations simultanées sans dégradation de performance.
 - **SC-007**: Le système obtient un score SUS (System Usability Scale) d'au moins 80/100 lors d'un test utilisateur mené sur un panel représentatif.
 - **SC-008**: Au moins 99% des déclarations d'incident initiées via WhatsApp aboutissent soit à la création réussie d'un incident, soit à une mise en file d'attente technique pour retry en moins de 5 minutes.

## Rétention & Confidentialité

- Les états de conversation actifs sont stockés dans Redis avec un TTL maximal de 24 heures ; au-delà, ils sont automatiquement supprimés et la conversation est considérée comme abandonnée.
- L'historique des conversations et messages stocké dans PostgreSQL (`whatsapp_conversations`, `whatsapp_messages`) ne doit pas être conservé indéfiniment : une durée de rétention par défaut (par exemple 12 mois) doit être définie et configurable, après quoi les données doivent être purgées ou anonymisées.
- Les incidents en attente stockés dans `pending_incidents` doivent être supprimés ou anonymisés après leur traitement définitif (succès ou échec après le nombre maximal de retries) et au plus tard à l'expiration de la durée de rétention définie.
- Les données personnelles (numéro de téléphone, email) ne doivent pas être conservées plus longtemps que nécessaire à la gestion opérationnelle des incidents et à l'analyse statistique, et doivent être prises en compte par les mécanismes de purge/anonymisation.

## Enseignements et Retours d'Expérience

### Gestion de l'état de conversation

- **Double stockage Redis/PostgreSQL** : L'utilisation de Redis comme cache rapide et PostgreSQL comme stockage persistant nécessite une synchronisation rigoureuse. Lors de la reprise d'une conversation, il faut toujours vérifier PostgreSQL si Redis ne contient pas l'état.
- **Réinitialisation de conversation** : Pour démarrer une nouvelle conversation proprement, il faut marquer l'ancienne comme obsolète (`is_completed=true`) plutôt que la supprimer, afin de conserver l'historique.
- **Déclenchement par l'utilisateur** : Le message de bienvenue ne doit pas être envoyé automatiquement au lancement de l'application. C'est l'utilisateur qui, en envoyant un message, déclenche l'envoi du message de bienvenue.

### Messages interactifs WhatsApp (Templates Meta)

- **Approbation Meta obligatoire** : Les templates interactifs (listes de choix, boutons) doivent être approuvés par Meta avant utilisation. Prévoir un délai d'approbation et un fallback en message texte.
- **Ordre des messages** : Lors d'une erreur de validation suivie d'un renvoi du template interactif, l'ordre d'envoi est crucial pour l'expérience utilisateur :
  1. D'abord le message d'erreur explicatif
  2. Ensuite le template interactif pour redemander le choix
- **Messages d'erreur clairs** : Préférer des messages d'erreur spécifiques et bienveillants (ex: "La zone est invalide. Merci de choisir parmi les choix proposés.") plutôt que des messages génériques.

### Gestion des webhooks Twilio

- **Déduplication des messages** : Les webhooks Twilio peuvent être appelés plusieurs fois pour le même message (notamment en mode debug Flask avec plusieurs workers). Une déduplication basée sur le `MessageSid` est indispensable.
- **Envoi via API vs TwiML** : Pour un contrôle précis de l'ordre des messages, préférer l'envoi via l'API Twilio plutôt que la réponse TwiML du webhook.

### Expérience utilisateur

- **Message de bienvenue personnalisé** : Inclure l'adresse du bâtiment dans le message de bienvenue renforce la confiance de l'utilisateur et confirme qu'il interagit avec le bon service.
- **Étapes claires** : Annoncer dès le début les étapes du processus (Étage, Zone, Catégorie, Description, Photos) permet à l'utilisateur de se projeter et réduit l'abandon.
- **Validation tolérante** : Accepter les variations de saisie (majuscules/minuscules, accents, numéros ou texte) améliore l'expérience utilisateur.

## Assumptions

- Les utilisateurs ont accès à WhatsApp sur leur smartphone.
- Les QR codes des bâtiments sont accessibles et lisibles.
- Le système d'import d'incident existant est disponible via une API REST.
- Twilio est utilisé comme fournisseur pour l'API WhatsApp Business.
- Les utilisateurs parlent français.
- Les utilisateurs ont une connexion Internet stable pendant la conversation.