# Requirement Quality Checklist: Non-Functional & Reliability for Email Notifications

**Purpose**: Validate non-functional, reliability, and observability requirements for the Email Notification feature.
**Created**: 2026-01-30
**Feature**: [spec.md](../spec.md)

## Requirement Completeness

- [ ] CHK001: Les critères de performance (SC-001 à SC-004) couvrent-ils tous les scénarios critiques (pics de charge, envois en rafale, incidents multiples) ? [Spec §Success Criteria]
- [ ] CHK002: Les contraintes d'usage de Celery (workers, file de tâches, Redis) sont-elles décrites quelque part (capacité minimale, tolérance aux pannes) ? [Plan §Technical Context]
- [ ] CHK003: Les dépendances critiques (SMTP, Celery, PostgreSQL, Redis) sont-elles toutes listées explicitement avec leurs prérequis dans la spec ou le plan ? [Spec §Assumptions]

## Requirement Clarity

- [ ] CHK004: Les objectifs de performance "<30s" et "95% en 5 minutes" sont-ils associés à un contexte précis (environnement, charge attendue, plage horaire) ? [Spec §Success Criteria]
- [ ] CHK005: Le comportement attendu en cas de latence SMTP élevée (mais pas d'erreur) est-il spécifié (timeout maximal, abandon, log) ? [Gap]
- [ ] CHK006: La notion de "pas de données sensibles" dans les emails est-elle explicitement définie (quels champs sont interdits) ? [Spec §Assumptions]

## Scenario & Edge Case Coverage

- [ ] CHK007: Le comportement après échec de la DERNIÈRE tentative Celery (max retries atteint) est-il spécifié (niveau de log, alerte, suivi manuel) ? [Research §Gestion des erreurs]
- [ ] CHK008: Existe-t-il une exigence sur la gestion des emails en file d'attente lors d'une coupure prolongée du serveur SMTP (ex: reprise ordonnée, limitation) ? [Gap]
- [ ] CHK009: La spec décrit-elle le comportement si plusieurs incidents sont créés simultanément pour le même bâtiment (risque de flood vers un même gestionnaire) ? [Gap]

## Non-Functional Requirements (Performance, Fiabilité, Sécurité)

- [ ] CHK010: Les limites de volume (emails/minute) sont-elles reliées à une stratégie de throttling ou de rate limiting documentée ? [Spec §Success Criteria]
- [ ] CHK011: Les exigences de disponibilité (taux de réussite global des envois) sont-elles définies avec des seuils minimums et une méthode de mesure ? [Gap]
- [ ] CHK012: Les exigences de sécurité autour des secrets SMTP (stockage .env, rotation, non-logging du mot de passe) sont-elles écrites explicitement ? [Plan §Technical Context]

## Observability & Traçabilité

- [ ] CHK013: Les types de logs attendus (INFO pour succès, WARNING pour erreurs fonctionnelles, ERROR pour erreurs techniques) sont-ils définis dans la spec ou le plan ? [Spec §Edge Cases]
- [ ] CHK014: La table `email_notifications` couvre-t-elle tous les champs nécessaires pour reconstituer un incident d'envoi (horodatage, statut, dernière erreur, nombre de retries) ? [Data Model §EmailNotification]
- [ ] CHK015: Une exigence de métriques (compteurs d'emails envoyés, échoués, retries) est-elle présente ou marquée comme hors-scope ? [Gap]

## Dependencies & Assumptions

- [ ] CHK016: Toutes les hypothèses listées dans la section Assumptions (feature 005-whatsapp-incident-reporting, EMAIL_GESTIONNAIRE, worker actif) ont-elles des préconditions ou checks documentés dans les tâches ? [Spec §Assumptions, tasks.md]
- [ ] CHK017: Les impacts d'une modification future du schéma `email_notifications` sur la rétrocompatibilité sont-ils abordés (Constitution: compatibilité ascendante) ? [Constitution §Règles d'évolution]

## Ambiguities & Conflicts

- [ ] CHK018: Y a-t-il des termes ambigus ou non quantifiés ("rapide", "fiable") encore présents dans la spec ou le plan pour cette feature ? [Global]
- [ ] CHK019: Existe-t-il des contradictions potentielles entre les critères de performance et les stratégies de retry (ex: trop de retries augmentant la latence globale) non résolues dans la spec ? [Research §Gestion des erreurs]

## Notes

- Cette checklist ne teste pas l'implémentation, uniquement la qualité et la complétude des exigences non-fonctionnelles.
- Les items marqués [Gap] signalent des zones où la spec ou le plan gagneraient à être complétés avant l'implémentation.
