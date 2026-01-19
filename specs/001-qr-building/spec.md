# Feature Specification: QR Building Registry
 
 **Feature Branch**: `001-qr-building`  
 **Created**: 2026-01-17  
 **Status**: Draft  
 **Input**: User description: "je veux une application pour générer des qr codes, stocker leurs identifiants et les lier au informations des immeubles"

 ## Clarifications

 ### Session 2026-01-18

 - Q: Contenu encodé dans le QR code → A: Encoder `QR_CODE_NUMBER`
 - Q: Qui génère `QR_CODE_NUMBER` ? → A: Le système génère `QR_CODE_NUMBER` automatiquement à la création
 - Q: Comment l'utilisateur fournit les infos bâtiment à importer ? → A: Un fichier JSON = 1 bâtiment
 - Q: Quand générer l'artefact QR ? → A: Générer automatiquement à la création du bâtiment
 - Q: Génération du QR — via API externe ou en local ? → A: Générer en local (sans dépendance réseau)
 - Q: Format de sortie QR ? → A: PNG
 - Q: Est-il possible de modifier les informations d'un bâtiment après création ? → A: Non
 - Q: Où sont stockés les fichiers QR générés ? → A: Système de fichiers
 - Q: Convention de nommage des fichiers QR ? → A: `[QR_CODE_NUMBER].png` (ex: `QR12345.png`)
 
 ## User Scenarios & Testing *(mandatory)*
 
 ### User Story 1 - Enregistrer un immeuble et lui attribuer un identifiant QR (Priority: P1)
 
 Un opérateur enregistre les informations d'un immeuble et le système attribue (ou valide) un
 identifiant QR unique lié à cet immeuble.
 
 **Why this priority**: C'est la base de données nécessaire avant toute génération de QR code.
 
 **Independent Test**: En créant un immeuble, on obtient un enregistrement persistant avec un
 identifiant QR unique et une date de création automatiquement renseignée.
 
 **Acceptance Scenarios**:
 
 1. **Given** aucun immeuble n'existe pour un identifiant QR donné, **When** l'opérateur enregistre un
    nouvel immeuble, **Then** le système persiste l'immeuble avec un identifiant QR unique.
 2. **Given** un immeuble est enregistré, **When** l'opérateur le relit par son identifiant interne,
    **Then** les champs enregistrés sont retournés et `CREATION_DATE` est présent.
 
 ---
 
 ### User Story 2 - Générer le QR code pour un immeuble existant (Priority: P2)
 
 Un opérateur demande la génération du QR code d'un immeuble existant, et récupère un artefact QR
 exploitable (ex: image ou représentation équivalente) associé à l'identifiant QR stocké.
 
 **Why this priority**: Permet l'usage opérationnel du QR code une fois l'immeuble enregistré.
 
 **Independent Test**: En demandant la génération pour un immeuble existant, un artefact QR est
 produit et correspond à l'identifiant QR de l'immeuble.
 
 **Acceptance Scenarios**:
 
 1. **Given** un immeuble existe, **When** l'opérateur demande la génération du QR code pour cet
    immeuble, **Then** un artefact QR est produit pour l'identifiant QR associé.
 2. **Given** un immeuble n'existe pas, **When** l'opérateur demande la génération, **Then** le système
    retourne une erreur indiquant que l'immeuble est introuvable.
 
 ---
 
 ### User Story 3 - Retrouver l’immeuble à partir d’un identifiant QR (Priority: P3)
 
 Un opérateur peut retrouver l'enregistrement d'un immeuble en fournissant l'identifiant QR
 (par exemple obtenu suite à un scan) afin de consulter les informations associées.
 
 **Why this priority**: C'est la finalité du lien QR ↔ informations immeuble.
 
 **Independent Test**: En fournissant un identifiant QR existant, l'immeuble correspondant est
 retrouvé; en fournissant un identifiant inconnu, une erreur claire est retournée.
 
 **Acceptance Scenarios**:
 
 1. **Given** un identifiant QR correspond à un immeuble, **When** l'opérateur interroge le système
    avec cet identifiant, **Then** le système retourne les informations de l'immeuble correspondant.
 2. **Given** un identifiant QR ne correspond à aucun immeuble, **When** l'opérateur interroge le
    système, **Then** le système retourne une erreur indiquant que l'identifiant est inconnu.
 
 ### Edge Cases
 
 - What happens when l'opérateur tente d'utiliser un identifiant QR déjà attribué à un autre immeuble?
 - How does system handle un email gestionnaire invalide ou manquant?
 - How does system handle des champs texte (notes) trop longs?
 - What happens when la génération de l'artefact QR échoue (erreur de rendu, destination indisponible)?
 - What happens when l'identifiant QR fourni contient des caractères invalides?
 
 ## Requirements *(mandatory)*
 
 ### Functional Requirements
 
 - **FR-001**: System MUST permettre de créer un enregistrement d'immeuble avec les champs:
   `LOCATION`, `EMAIL_GESTIONNAIRE`, `NOTES`.
 - **FR-001a**: System MUST permettre l'import des informations d'un bâtiment depuis un fichier JSON
   représentant un seul bâtiment.
 - **FR-002**: System MUST générer automatiquement un `QR_CODE_NUMBER` unique par immeuble lors de la
   création et empêcher les doublons.
 - **FR-003**: System MUST générer et stocker automatiquement `CREATION_DATE` lors de la création
   d'un immeuble.
 - **FR-004**: System MUST permettre de récupérer un immeuble par son identifiant interne (`ID`).
 - **FR-005**: System MUST permettre de récupérer un immeuble par son identifiant QR (`QR_CODE_NUMBER`).
 - **FR-006**: System MUST générer un artefact QR automatiquement lors de la création d'un immeuble.
 - **FR-006a**: System MUST permettre de régénérer un artefact QR pour un immeuble existant.
 - **FR-006b**: System MUST générer l'artefact QR localement (sans appel à une API externe) par défaut.
 - **FR-006c**: System MUST générer l'artefact QR au format PNG.
 - **FR-006d**: System MUST stocker l'artefact QR généré dans le système de fichiers.
 - **FR-006e**: System MUST nommer le fichier QR selon le format `[QR_CODE_NUMBER].png`.
 - **FR-007**: System MUST retourner des erreurs explicites et actionnables pour:
   - immeuble introuvable
   - identifiant QR inconnu
   - violation d'unicité (identifiant QR déjà utilisé)
   - données invalides
 - **FR-008**: System MUST encoder uniquement `QR_CODE_NUMBER` dans le QR code (pas de données
  personnelles), sauf exigence explicitement demandée.
 - **FR-009**: System MUST interdire la modification des informations d'un bâtiment après sa création.

 
 ### Key Entities *(include if feature involves data)*
 
 - **Building**: Représente un immeuble.
   - Attributs clés: `ID`, `CREATION_DATE`, `LOCATION`, `EMAIL_GESTIONNAIRE`, `NOTES`, `QR_CODE_NUMBER`
   - Contrainte clé: `QR_CODE_NUMBER` unique
 
 ## Success Criteria *(mandatory)*
 
 ### Measurable Outcomes
 
 - **SC-001**: Un opérateur peut enregistrer un immeuble et obtenir un identifiant QR unique en moins
   de 5 secondes (hors latence d'infrastructure).
 - **SC-002**: Le système empêche 100% des doublons d'identifiants QR au moment de l'enregistrement.
 - **SC-003**: La génération d'un artefact QR pour un immeuble existant se termine en moins de 2
   secondes dans 95% des cas sur un poste standard.
 - **SC-004**: Pour un identifiant QR valide, la recherche de l'immeuble associé retourne un résultat
   (ou une erreur) en moins de 1 seconde dans 95% des cas.