# Checklist qualité – Flux WhatsApp & Contrats d’API

**Feature**: WhatsApp Incident Reporting  
**Focus**: Flux de conversation + intégration API (webhook Twilio, API d’import incident)  
**But**: Tester la qualité des exigences (pas l’implémentation)

---

## Requirement Completeness (scénarios & API)

- [x] **CHK001** – Les trois user stories principales (déclarer, reprendre, confirmer) couvrent-elles **tous** les états de la machine de conversation décrits dans `conversation-flow.md` ? [Completeness][Scenario Coverage]
  - US1 (Déclarer) couvre les états: Initiation → Zone → Étage → Catégorie → Type → Infos Suppl. → Email → Récapitulatif → Confirmation → Traitement → Résultat
  - US2 (Reprendre) couvre la persistance d'état et la reprise à n'importe quelle étape après interruption
  - US3 (Confirmer) couvre les états: Traitement → Résultat (avec QR code)
  - Les commandes spéciales (Aide, Annuler, Recommencer, Retour) et la gestion des erreurs sont couvertes par les scénarios d'acceptation et les edge cases
- [x] **CHK002** – Pour chaque étape du flux (zone, étage, catégorie, type, infos supplémentaires, email, récap, confirmation), la spec indique-t-elle **quelle question exacte** est posée et **quelles réponses sont attendues** ? [Completeness][Clarity]
- [x] **CHK003** – Les cas de reprise de conversation (timeout, retour sur une conversation existante) sont-ils décrits dans la spec avec conditions d’entrée et de sortie claires ? [Completeness][Scenario Coverage]
- [x] **CHK004** – Tous les points d’intégration API mentionnés dans le plan (`webhook Twilio`, `API d’import d’incident`) ont-ils des exigences explicites dans la section Requirements (FR-008 à FR-014) ? [Completeness][Dependencies]
- [x] **CHK005** – Le format **complet** du JSON envoyé à l’API d’import (champs obligatoires / optionnels) est-il entièrement spécifié (mapping champ conversation → champ JSON) ? [Completeness][Scenario Coverage]

## Requirement Clarity (flux conversationnels)

 - [x] **CHK006** – Pour chaque question posée par le chatbot, les **formats de réponse acceptés** (texte libre, numéroté, oui/non, email, etc.) sont-ils clairement documentés ? [Clarity]
 - [x] **CHK007** – Les règles de validation (longueur min/max, formats autorisés pour étage, email, etc.) sont-elles spécifiées pour **chaque champ** collecté, pas seulement mentionnées de façon générique ? [Clarity][Edge Case Coverage]
 - [x] **CHK008** – Les messages d’erreur et de relance (réponse non reconnue, email invalide, aide) sont-ils définis de façon suffisamment précise pour éviter les interprétations ambiguës ? [Clarity][Scenario Coverage]
 - [x] **CHK009** – Les commandes spéciales (`Aide`, `Annuler`, `Recommencer`, `Retour`) ont-elles des comportements décrits explicitement pour **toutes** les étapes possibles de la conversation ? [Clarity][Consistency]

## Requirement Clarity (API & erreurs)

 - [x] **CHK010** – La distinction entre **erreurs fonctionnelles** et **erreurs techniques** dans FR‑014 est-elle accompagnée d’exemples concrets et de critères de classification (codes, messages) ? [Clarity][Non-Functional]
 - [x] **CHK011** – Pour le webhook Twilio, les paramètres obligatoires de la requête (From, Body, etc.) et les préconditions de validation (signature) sont-ils clairement listés dans le contrat d’API ? [Clarity][Dependencies]
 - [x] **CHK012** – Les formats de réponse du webhook (TwiML) sont-ils décrits pour les différents cas (succès, erreur utilisateur, erreur système) sans laisser de zones grises ? [Clarity][Scenario Coverage]

## Requirement Consistency (spec ↔ plan ↔ contrats)

 - [x] **CHK013** – Les étapes de conversation décrites dans la spec (`User Scenarios`, `FR-004`–`FR-007`) sont-elles cohérentes avec le diagramme d’état et les étapes listées dans `conversation-flow.md` ? [Consistency]
 - [x] **CHK014** – Les entités définies dans `data-model.md` (`ConversationState`, `WhatsAppMessage`, `PendingIncident`) ont-elles des champs qui correspondent 1:1 aux données mentionnées dans la spec et le plan (pas de champ « fantôme » ou manquant) ? [Consistency]
 - [x] **CHK015** – Les deep links WhatsApp (format d'URL) sont-ils décrits de façon identique dans `spec.md`, `plan.md` et le contrat d'API Twilio (même schéma incident:QRxxxx) ? [Consistency]
  - Format dans `plan.md` (L51): `https://wa.me/[numéro_chatbot]?text=incident:[qr_code_number]`
  - Format dans `conversation-flow.md` (L11): `incident:QR5050332870`
  - Format dans `spec.md` (L12): URL avec deep link vers WhatsApp incluant le QR_CODE_NUMBER du bâtiment
  - Les formats sont cohérents: URL `https://wa.me/<NUMERO_CHATBOT>?text=incident:<QR_CODE_NUMBER>` et paramètre `incident:QRxxxx`
 - [x] **CHK016** – La stratégie de retry décrite dans FR‑014 est-elle alignée avec ce qui est prévu dans le plan (Celery/Redis, file d’attente, next_retry) sans contradiction de comportement ou de timing ? [Consistency][Non-Functional]

## Acceptance Criteria Quality

- [x] **CHK017** – Les critères de succès (SC‑001 à SC‑006) couvrent-ils **explicitement** les deux axes clés du focus : 
  - qualité de l’expérience de conversation (temps, nombre d’interactions, complétion), et 
  - fiabilité de l’intégration API (taux d’erreur, retries) ? [Acceptance Criteria Quality]
- [x] **CHK018** – Chaque scénario d’acceptation des user stories 1–3 permet-il de vérifier à la fois le **comportement utilisateur** et le **comportement backend/API** (création incident, QR code, message de confirmation) ? [Acceptance Criteria Quality][Scenario Coverage]
- [x] **CHK019** – Existe-t-il au moins un scénario d’acceptation décrivant la **gestion d’un échec API technique** (file d’attente + message utilisateur) et un autre décrivant une **erreur fonctionnelle** (bâtiment introuvable, données invalides) ? [Acceptance Criteria Quality][Edge Case Coverage]

## Scenario & Edge Case Coverage (flux + API)

- [x] **CHK020** – Les edge cases listés dans `spec.md` (QR code inconnu, réponses invalides, perte de connexion, spam de messages, demande d’aide) sont-ils chacun reliés à un comportement attendu **côté conversation** et, si pertinent, **côté API** ? [Scenario Coverage][Edge Case Coverage]
- [x] **CHK021** – Le comportement en cas de **double soumission** (utilisateur relance la confirmation ou renvoie plusieurs fois le même message) est-il spécifié (idempotence, détection de doublons, message explicite) ? [Edge Case Coverage][Consistency]
- [x] **CHK022** – Le cas où l'API d'import est indisponible **pendant une longue période** (au‑delà des retries prévus) est-il couvert par des exigences (notification, journalisation, traitement manuel, limite max de retries) ? [Edge Case Coverage][Non-Functional]
  - FR-014 spécifie la stratégie hybride pour les erreurs techniques avec mise en file d'attente persistante
  - Le data-model.md définit `retry_count` et `next_retry` dans l'entité `PendingIncident`
  - Le plan.md mentionne "Monitoring et alerting en cas d'échecs répétés" (L76)
  - La section Rétention & Confidentialité précise que les incidents en attente sont supprimés après "succès ou échec après le nombre maximal de retries"
  - La stratégie complète est définie: persistance → retries avec backoff → alertes → limite max de tentatives
- [x] **CHK023** – Le comportement lorsque l’utilisateur revient après expiration du TTL de 24h (conversation supprimée) est-il décrit (nouvelle déclaration, message explicite) ? [Scenario Coverage][Edge Case Coverage]

## Non-Functional Requirements (perf, robustesse, observabilité)

- [x] **CHK024** – Les objectifs de performance (SC‑001, SC‑003, SC‑006) sont-ils déclinés en exigences observables côté API (latence du webhook, temps de réponse moyen, capacité de charge) et pas seulement du point de vue de l’utilisateur final ? [Non-Functional][Measurability]
- [x] **CHK025** – Les besoins de **journalisation** (logs de conversation, erreurs API, retrys) sont-ils explicitement mentionnés dans le plan ou la spec avec un niveau de détail suffisant (au moins quels événements doivent être loggés) ? [Non-Functional][Observability]
  - NFR-002 spécifie: "System MUST produire des logs structurés permettant de corréler une conversation donnée, les appels à l'API d'import d'incident et les erreurs associées"
  - Le plan.md mentionne "Logging structuré des conversations et états avec identifiants de corrélation" (L143)
  - La tâche T030 est dédiée à "Créer le système de journalisation des conversations et erreurs"
  - La tâche T036 couvre l'instrumentation des métriques opérationnelles
  - Les événements à logger sont clairement identifiés: conversations, appels API, erreurs, retries
- [x] **CHK026** – Les risques identifiés dans le plan (limitations WhatsApp, gestion des conversations interrompues, fiabilité de l'API d'import) ont-ils tous une **réponse explicite** dans la spec (exigences ou mesures d'atténuation) ? [Non-Functional][Dependencies]
  - Risque "Limitations de l'API WhatsApp Business": couvert par la section Assumptions qui définit les limites de responsabilité du système
  - Risque "Gestion des conversations interrompues": couvert par FR-007, FR-013, US2 et SC-005
  - Risque "Fiabilité de l'API d'import": couvert par FR-011, FR-014, SC-008 et la section Rétention & Confidentialité

## Dependencies & Assumptions

- [x] **CHK027** – Toutes les hypothèses listées dans `Assumptions` (accès WhatsApp, lisibilité des QR codes, disponibilité de l’API d’import, Twilio, langue française, connexion Internet) sont-elles reflétées par des exigences ou des limites de responsabilité claires ? [Dependencies & Assumptions]
- [x] **CHK028** – La dépendance à Twilio (ou autre fournisseur) décrit-elle ce qui se passe en cas de **changement de fournisseur** ou d’indisponibilité prolongée (fallback, migration, out-of-scope explicite) ? [Dependencies & Assumptions][Gap]

## Ambiguities & Conflicts

- [x] **CHK029** – Les zones où des termes vagues sont utilisés ("simple", "intuitif", "robuste") sont-elles soit **quantifiées** par des critères mesurables, soit marquées explicitement comme hors du champ de validation ? [Ambiguities]
- [x] **CHK030** – Y a‑t‑il des contradictions potentielles entre les exigences de temps de réponse pour l'utilisateur et les stratégies de retry asynchrones (risque de promesse non tenue côté UX) ? Si oui, sont‑elles résolues dans la spec/plan ? [Ambiguities][Consistency]
  - La contradiction potentielle est résolue par la stratégie hybride définie dans FR-014
  - Le message utilisateur en cas d'erreur technique est explicite (L146-152 dans `conversation-flow.md`): "Votre déclaration a bien été prise en compte, mais nous rencontrons actuellement un problème technique..."
  - SC-008 quantifie cette exigence: "Au moins 99% des déclarations d'incident initiées via WhatsApp aboutissent soit à la création réussie d'un incident, soit à une mise en file d'attente technique pour retry en moins de 5 minutes"
  - La gestion des attentes utilisateur est explicitement traitée
