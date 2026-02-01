# Feature Specification: QR Code WhatsApp Redirect

**Feature Branch**: `006-qr-whatsapp-redirect`  
**Created**: 2026-02-01  
**Status**: Draft  
**Input**: User description: "Un utilisateur scanne un qrcode et est redirigé vers une conversation whatsapp : le qrcode contient un lien, le numéro de téléphone du service whatsapp scandom et le message d'ouverture. L'utilisateur scanne le QR code, est redirigé vers WhatsApp, la conversation est réinitialisée, le message d'ouverture est prérempli et l'utilisateur n'a plus qu'à appuyer sur envoyer."

## Clarifications

### Session 2026-02-01

- Q: Quel format de lien doit être utilisé pour la redirection WhatsApp ? → A: Lien universel WhatsApp `https://wa.me/<numéro>?text=<message>` (standard WhatsApp Click to Chat)
- Q: Le QR code doit-il être associé à un bâtiment spécifique ? → A: Oui, chaque QR code est lié à un bâtiment existant et le message d'ouverture inclut l'identifiant du bâtiment
- Q: Comment la conversation précédente est-elle réinitialisée ? → A: Le backend détecte le message d'ouverture et réinitialise l'état de conversation pour cet utilisateur
- Q: Le message d'ouverture doit-il contenir des informations spécifiques ? → A: Oui, il doit contenir un identifiant permettant d'associer la conversation au bâtiment (ex: QR code du bâtiment)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Scanner un QR code et démarrer une conversation WhatsApp (Priority: P1)

Un utilisateur scanne le QR code affiché dans un bâtiment avec son smartphone. Il est automatiquement redirigé vers l'application WhatsApp avec un message prérempli. En appuyant sur "Envoyer", il démarre une nouvelle conversation pour signaler un incident.

**Why this priority**: C'est le point d'entrée principal pour les utilisateurs souhaitant signaler un incident. L'expérience doit être fluide et sans friction.

**Independent Test**: Scanner un QR code de test avec un smartphone, vérifier la redirection vers WhatsApp, le message prérempli, et l'envoi qui démarre une nouvelle conversation.

**Acceptance Scenarios**:

1. **Given** un QR code valide affiché dans un bâtiment, **When** un utilisateur scanne le QR code avec son smartphone, **Then** l'application WhatsApp s'ouvre automatiquement.
2. **Given** l'application WhatsApp ouverte via le QR code, **When** l'utilisateur voit le champ de message, **Then** le message d'ouverture est prérempli avec le texte configuré incluant l'identifiant du bâtiment.
3. **Given** un message d'ouverture prérempli, **When** l'utilisateur appuie sur "Envoyer", **Then** une nouvelle conversation est initialisée côté backend (toute conversation précédente de cet utilisateur est réinitialisée).
4. **Given** un utilisateur ayant déjà une conversation en cours, **When** il scanne à nouveau un QR code et envoie le message d'ouverture, **Then** sa conversation précédente est réinitialisée et une nouvelle conversation démarre.

---

### User Story 2 - Générer un QR code pour un bâtiment (Priority: P1)

Un administrateur génère un QR code pour un bâtiment. Ce QR code contient le lien de redirection WhatsApp avec le message d'ouverture approprié.

**Why this priority**: Sans QR code généré, les utilisateurs ne peuvent pas accéder au service de signalement.

**Independent Test**: Générer un QR code pour un bâtiment existant et vérifier qu'il contient le bon lien WhatsApp.

**Acceptance Scenarios**:

1. **Given** un bâtiment existant dans le système, **When** un administrateur demande la génération d'un QR code, **Then** un QR code est créé contenant le lien WhatsApp avec le numéro du service et le message d'ouverture.
2. **Given** un QR code généré, **When** on décode le QR code, **Then** le lien est au format `https://wa.me/<numéro>?text=<message_encodé>`.
3. **Given** un QR code généré pour un bâtiment, **When** on examine le message encodé, **Then** il contient l'identifiant QR du bâtiment pour permettre l'association.

---

### Edge Cases

- System MUST gérer le cas où l'utilisateur n'a pas WhatsApp installé (le lien universel redirige vers le web ou propose l'installation).
- System MUST valider que le bâtiment existe avant de générer un QR code.
- System MUST encoder correctement les caractères spéciaux dans le message d'ouverture (URL encoding).
- System MUST réinitialiser la conversation même si l'utilisateur envoie le message d'ouverture manuellement (sans scanner le QR code).
- System MUST gérer le cas où le QR code du bâtiment référencé dans le message n'existe pas (répondre avec un message d'erreur approprié).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST générer des QR codes contenant un lien WhatsApp universel au format `https://wa.me/<numéro>?text=<message>`.
- **FR-002**: System MUST inclure dans le message d'ouverture l'identifiant QR du bâtiment associé pour permettre l'association automatique.
- **FR-003**: System MUST utiliser le numéro de téléphone WhatsApp du service Scandom configuré dans les variables d'environnement.
- **FR-004**: System MUST encoder correctement le message d'ouverture pour l'URL (URL encoding des caractères spéciaux).
- **FR-005**: System MUST réinitialiser toute conversation existante de l'utilisateur lorsqu'un message d'ouverture est reçu.
- **FR-006**: System MUST associer automatiquement la nouvelle conversation au bâtiment identifié dans le message d'ouverture.
- **FR-007**: System MUST permettre la configuration du texte du message d'ouverture via une variable d'environnement ou un fichier de configuration.
- **FR-008**: System MUST stocker le QR code généré (image PNG) dans le système de fichiers avec un nommage cohérent.
- **FR-009**: System MUST valider l'existence du bâtiment avant de générer un QR code.
- **FR-010**: System MUST retourner un message d'erreur approprié si le bâtiment référencé dans le message d'ouverture n'existe pas.

### Key Entities

- **QRCodeWhatsApp**: Représente un QR code généré pour un bâtiment, contenant le lien de redirection WhatsApp.
  - Attributs clés: identifiant du bâtiment (clé étrangère), lien WhatsApp complet, chemin vers l'image PNG, date de génération
  - Contrainte clé: un seul QR code WhatsApp actif par bâtiment

- **MessageOuverture**: Template du message prérempli dans WhatsApp.
  - Format: "Bonjour, je souhaite signaler un incident dans le bâtiment {QR_CODE_BATIMENT}."
  - Doit être configurable

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% des QR codes générés redirigent correctement vers WhatsApp avec le message prérempli.
- **SC-002**: Le temps de génération d'un QR code est inférieur à 2 secondes.
- **SC-003**: 100% des messages d'ouverture reçus déclenchent une réinitialisation de conversation.
- **SC-004**: L'association bâtiment-conversation est correcte dans 100% des cas où le bâtiment existe.
- **SC-005**: Le taux d'erreur pour les QR codes invalides ou bâtiments inexistants est géré avec un message utilisateur clair dans 100% des cas.

## Assumptions

- Le numéro de téléphone WhatsApp du service Scandom est déjà configuré et opérationnel (feature 003-whatsapp-integration).
- Les bâtiments ont déjà un QR code d'identification unique (feature 001-qr-building).
- L'utilisateur dispose d'un smartphone avec une application de lecture de QR code (native ou tierce).
- L'utilisateur a accès à Internet pour que la redirection WhatsApp fonctionne.
- Le format de lien WhatsApp universel (`wa.me`) est supporté par tous les smartphones modernes.
- La fonctionnalité de conversation WhatsApp (feature 003-whatsapp-integration) est opérationnelle.
