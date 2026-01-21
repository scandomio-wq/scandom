# Feature Specification: Incident Import

**Feature Branch**: `002-incident-import`  
**Created**: 2026-01-21  
**Status**: Draft  
**Input**: User description: "je veux pouvoir créer un incident pour un bâtiment en utilisant un fichier JSON dédié"

## Clarifications

### Session 2026-01-21

- Q: Contenu encodé dans le QR code → A: Encoder `QR_CODE_NUMBER` avec préfixe "IN" pour les incidents
- Q: Qui génère `QR_CODE_NUMBER` ? → A: Le système génère `QR_CODE_NUMBER` automatiquement à la création
- Q: Comment l'utilisateur fournit les infos d'incident à importer ? → A: Un fichier JSON = 1 incident
- Q: Quand générer l'artefact QR ? → A: Générer automatiquement à la création de l'incident
- Q: Format de sortie QR ? → A: PNG (comme pour les bâtiments)
- Q: Où sont stockés les fichiers QR générés ? → A: Système de fichiers
- Q: Convention de nommage des fichiers QR ? → A: `[QR_CODE_NUMBER].png` (ex: `IN12345.png`)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Importer un incident pour un bâtiment (Priority: P1)

Un opérateur importe les informations d'un incident lié à un bâtiment existant et le système attribue un identifiant QR unique à cet incident.

**Why this priority**: C'est la fonctionnalité principale pour l'import des incidents.

**Independent Test**: En important un incident, on obtient un enregistrement persistant avec un identifiant QR unique et une date de création automatiquement renseignée.

**Acceptance Scenarios**:

1. **Given** un bâtiment existe, **When** l'opérateur importe un nouvel incident pour ce bâtiment, **Then** le système persiste l'incident avec un identifiant QR unique.
2. **Given** un incident est importé, **When** l'opérateur le relit par son identifiant interne, **Then** les champs enregistrés sont retournés et `CREATION_DATE` est présent.
3. **Given** le bâtiment référencé n'existe pas, **When** l'opérateur tente d'importer un incident, **Then** le système retourne une erreur indiquant que le bâtiment est introuvable.

---

### User Story 2 - Générer le QR code pour un incident existant (Priority: P2)

Un opérateur demande la génération du QR code d'un incident existant, et récupère un artefact QR exploitable associé à l'identifiant QR stocké.

**Why this priority**: Permet l'usage opérationnel du QR code une fois l'incident importé.

**Independent Test**: En demandant la génération pour un incident existant, un artefact QR est produit et correspond à l'identifiant QR de l'incident.

**Acceptance Scenarios**:

1. **Given** un incident existe, **When** l'opérateur demande la génération du QR code pour cet incident, **Then** un artefact QR est produit pour l'identifiant QR associé.
2. **Given** un incident n'existe pas, **When** l'opérateur demande la génération, **Then** le système retourne une erreur indiquant que l'incident est introuvable.

---

### User Story 3 - Retrouver l'incident à partir d'un identifiant QR (Priority: P3)

Un opérateur peut retrouver l'enregistrement d'un incident en fournissant l'identifiant QR afin de consulter les informations associées.

**Why this priority**: C'est la finalité du lien QR ↔ informations incident.

**Independent Test**: En fournissant un identifiant QR existant, l'incident correspondant est retrouvé; en fournissant un identifiant inconnu, une erreur claire est retournée.

**Acceptance Scenarios**:

1. **Given** un identifiant QR correspond à un incident, **When** l'opérateur interroge le système avec cet identifiant, **Then** le système retourne les informations de l'incident correspondant.
2. **Given** un identifiant QR ne correspond à aucun incident, **When** l'opérateur interroge le système, **Then** le système retourne une erreur indiquant que l'identifiant est inconnu.

### Edge Cases

- What happens when l'opérateur tente d'importer un incident avec un identifiant QR déjà attribué?
- What happens when l'opérateur fournit à la fois `BUILDING_ID` et `BUILDING_QR_CODE` qui ne correspondent pas au même bâtiment?
- How does system handle un email de déclarant invalide ou manquant?
- How does system handle des champs JSON (informations_supplementaires) trop longs?
- What happens when la génération de l'artefact QR échoue?
- What happens when l'identifiant QR fourni contient des caractères invalides?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST permettre d'importer un incident avec les champs:
  `BUILDING_ID` ou `BUILDING_QR_CODE`, `REPORTER_PHONE`, `REPORTER_EMAIL`, `INCIDENT_INFORMATION`.
- **FR-001a**: System MUST permettre l'import des informations d'un incident depuis un fichier JSON
  représentant un seul incident.
- **FR-001b**: System MUST valider que le champ `INCIDENT_INFORMATION` contient les sous-champs obligatoires:
  `zone`, `etage`, `categorie`, `type`.
- **FR-002**: System MUST générer automatiquement un `QR_CODE_NUMBER` unique par incident lors de
  l'import et empêcher les doublons.
- **FR-003**: System MUST générer et stocker automatiquement `CREATION_DATE` lors de l'import
  d'un incident.
- **FR-004**: System MUST permettre de récupérer un incident par son identifiant interne (`ID`).
- **FR-005**: System MUST permettre de récupérer un incident par son identifiant QR (`QR_CODE_NUMBER`).
- **FR-006**: System MUST générer un artefact QR automatiquement lors de l'import d'un incident.
- **FR-006a**: System MUST permettre de régénérer un artefact QR pour un incident existant.
- **FR-006b**: System MUST générer l'artefact QR localement (sans appel à une API externe).
- **FR-006c**: System MUST générer l'artefact QR au format PNG.
- **FR-006d**: System MUST stocker l'artefact QR généré dans le système de fichiers.
- **FR-006e**: System MUST nommer le fichier QR selon le format `[QR_CODE_NUMBER].png`.
- **FR-007**: System MUST retourner des erreurs explicites et actionnables pour:
  - incident introuvable
  - bâtiment référencé introuvable
  - identifiant QR inconnu
  - violation d'unicité (identifiant QR déjà utilisé)
  - données invalides
- **FR-008**: System MUST encoder uniquement `QR_CODE_NUMBER` dans le QR code.
- **FR-009**: System MUST vérifier l'existence du bâtiment référencé (via `BUILDING_ID` ou `BUILDING_QR_CODE`) avant d'importer un incident.
- **FR-010**: System MUST convertir `BUILDING_QR_CODE` en `BUILDING_ID` lors de l'importation si l'utilisateur fournit `BUILDING_QR_CODE` au lieu de `BUILDING_ID`.

### Key Entities *(include if feature involves data)*

- **Incident**: Représente un incident lié à un bâtiment.
  - Attributs clés: `ID`, `BUILDING_ID`, `CREATION_DATE`, `REPORTER_PHONE`, `REPORTER_EMAIL`, `INCIDENT_INFORMATION`, `QR_CODE_NUMBER`
  - Contrainte clé: `QR_CODE_NUMBER` unique
  - Contrainte clé: `BUILDING_ID` doit référencer un bâtiment existant

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un opérateur peut importer un incident et obtenir un identifiant QR unique en moins
  de 5 secondes (hors latence d'infrastructure).
- **SC-002**: Le système empêche 100% des doublons d'identifiants QR au moment de l'import.
- **SC-003**: La génération d'un artefact QR pour un incident existant se termine en moins de 2
  secondes dans 95% des cas sur un poste standard.
- **SC-004**: Pour un identifiant QR valide, la recherche de l'incident associé retourne un résultat
  (ou une erreur) en moins de 1 seconde dans 95% des cas.
