<!--
 Sync Impact Report
 - Version change: N/A -> 1.0.0
 - Modified principles: N/A (initial constitution)
 - Added sections: Core Principles, Technical Scope & Data Model, Delivery & Quality Gates, Governance
 - Removed sections: N/A
 - Templates requiring updates:
   - .specify/templates/plan-template.md (reference to non-existent commands path)
   - .specify/templates/spec-template.md (no change)
   - .specify/templates/tasks-template.md (no change)
   - .specify/templates/checklist-template.md (no change)
 - Deferred items: none
 -->
 
 # SCANDOM QR Building Constitution
 
 ## Core Principles
 
 ### Data Is Authoritative In Postgres
 Les informations d'un bâtiment sont stockées de manière source-of-truth dans PostgreSQL.
 Le QR code généré pour un bâtiment doit être dérivable/re-générable à partir
 des données persistées (et jamais l'inverse).
 
 ### CLI-First Operations (No UI For MVP)
 Tant qu'aucune UX n'est demandée, les opérations doivent être accessibles via scripts/commande
 (ex: commande Python) pour générer un QR code à partir de l'ID du bâtiment.
 Les sorties doivent être prévisibles (stdout pour le résultat, stderr pour les erreurs) et
 automatisables (format texte ou JSON si pertinent).

 La manipulation des données (insertion, mise à jour, lecture) se fait via un processus Python
 (scripts/CLI) connecté à PostgreSQL.
 
 ### QR Codes Are Unique, Stable, And Traceable
 Un QR code doit être unique par bâtiment et stable dans le temps.
 La valeur utilisée pour l'identifiant QR (ex: `QR_CODE_NUMBER`) doit être:
 
 - Définie et validée en base (contraintes d'unicité)
 - Traçable (lien clair vers `T_BUILDING.ID`)
 - Non ambiguë (pas de réutilisation silencieuse)
 
 ### Security & Privacy By Default
 Les champs potentiellement sensibles (ex: `EMAIL_GESTIONNAIRE`, `NOTES`) doivent être traités
 comme des données à protéger.
 
 - Ne pas exposer d'informations personnelles dans le contenu du QR code si ça n'est pas requis.
 - Préférer encoder dans le QR un identifiant/référence (ex: `ID` ou `QR_CODE_NUMBER`) plutôt
   que l'ensemble des données.
 - Journaliser sans fuite de données sensibles (masking si besoin).
 
 ### Simple, Deterministic, Automatable
 Le système doit rester simple: un modèle de données clair, une commande de génération, et des
 règles explicites. Toute complexité ajoutée doit être justifiée par un besoin produit.
 
 ## Technical Scope & Data Model
 
 Le projet doit au minimum supporter l'entité `T_BUILDING` avec les colonnes suivantes:
 
 - `ID`
 - `CREATION_DATE`
 - `LOCATION`
 - `EMAIL_GESTIONNAIRE`
 - `NOTES`
 - `QR_CODE_NUMBER`
 
 Les règles minimales attendues:
 
 - `ID` est la clé primaire.
 - `CREATION_DATE` est un timestamp défini automatiquement à l'insertion (valeur par défaut).
 - `QR_CODE_NUMBER` est unique (contrainte d'unicité).
 - La génération du QR code se fait à partir d'un identifiant stable (ex: `ID` ou `QR_CODE_NUMBER`).
 
 ## Delivery & Quality Gates
 
 - Chaque fonctionnalité doit être exécutable en local via commande/script.
 - Les erreurs doivent être explicites et actionnables.
 - Les changements de schéma PostgreSQL doivent être gérés de manière reproductible (migrations ou
   à défaut scripts versionnés).
 - Les sorties artefacts (ex: image QR) doivent être produites dans un emplacement contrôlé et
   éviter d'écraser sans avertissement.
 
 ## Governance
 
 - Cette constitution est la référence de priorité pour les décisions d'implémentation.
 - Toute modification doit:
   - Mettre à jour la version sémantique.
   - Mettre à jour `Last Amended`.
   - Documenter le rationnel et les impacts sur les artefacts Speckit.
 - Les changements cassants (ex: modification du contenu encodé dans le QR, changement de clé
   d'identification, rupture du contrat CLI) exigent une stratégie de migration.
 - Revue de conformité attendue avant fusion (principes: données en Postgres, QR unique/stable,
   sécurité, automation).
 
 **Version**: 1.0.0 | **Ratified**: 2026-01-17 | **Last Amended**: 2026-01-17
