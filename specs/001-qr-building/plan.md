# Plan d'implémentation : QR Building Registry

**Feature Branch**: `001-qr-building`  
**Créé**: 2026-01-18  
**Status**: Draft  

## Résumé

Cette fonctionnalité permet de stocker des informations sur des immeubles dans une base de données PostgreSQL et de générer des QR codes uniques liés à ces immeubles. L'application n'aura pas d'interface utilisateur dans sa version initiale. Les données seront insérées directement dans la base de données via des fichiers JSON, et les QR codes seront générés via une commande Python spécifiant un ID.

## Contexte technique

### Technologies et dépendances

- **Base de données**: PostgreSQL pour le stockage des données des immeubles
- **Langage de programmation**: Python pour la logique métier et les scripts CLI
- **Génération de QR code**: Bibliothèque Python (qrcode) pour la génération locale de QR codes
- **Format de sortie**: PNG pour les QR codes générés
- **Stockage des QR codes**: Système de fichiers local

### Intégrations

- Pas d'intégration externe requise, toutes les opérations sont effectuées en local
- Pas d'API externe pour la génération de QR codes

## Vérification de la constitution

| Principe | Conformité | Justification |
|----------|------------|---------------|
| Data Is Authoritative In Postgres | ✅ | Toutes les données des immeubles sont stockées dans PostgreSQL comme source de vérité |
| CLI-First Operations | ✅ | L'application est conçue pour fonctionner via des commandes Python sans interface utilisateur |
| QR Codes Are Unique, Stable, And Traceable | ✅ | QR_CODE_NUMBER est unique par immeuble et stable dans le temps |
| Security & Privacy By Default | ✅ | Seul QR_CODE_NUMBER est encodé dans le QR code, pas de données personnelles |
| Simple, Deterministic, Automatable | ✅ | Modèle de données clair, commandes simples, processus automatisable |

## Structure du projet

```
scandom/
 ├── src/
 │   ├── models/
 │   │   └── building.py       # Modèle de données pour les immeubles
 │   ├── db/
 │   │   ├── __init__.py
 │   │   ├── connection.py     # Gestion de la connexion à PostgreSQL
 │   │   └── building_dao.py   # Opérations CRUD pour les immeubles
 │   ├── qr/
 │   │   ├── __init__.py
 │   │   └── generator.py      # Logique de génération des QR codes
 │   ├── utils/
 │   │   ├── __init__.py
 │   │   ├── config.py         # Configuration de l'application
 │   │   └── validators.py     # Validation des données d'entrée
 │   └── cli/
 │       ├── __init__.py
 │       ├── import_building.py # CLI pour importer un immeuble depuis JSON
 │       ├── generate_qr.py     # CLI pour générer un QR code
 │       └── find_building.py   # CLI pour rechercher un bâtiment par QR
 ├── migrations/
 │   └── 001_create_building_table.sql  # Script de création de la table T_BUILDING
 ├── examples/                 # Exemples de fichiers JSON
 ├── tests/
 │   ├── test_building_dao.py  # Tests pour les opérations CRUD
 │   ├── test_qr_generator.py  # Tests pour la génération de QR codes
 │   └── test_cli.py           # Tests pour les commandes CLI
 ├── config/
 │   └── db_config.ini         # Configuration de la base de données
 ├── ERRORS.md                 # Codes d'erreur et messages
 └── requirements.txt          # Dépendances Python
```

## Suivi de complexité

| Composant | Complexité | Justification |
|-----------|------------|---------------|
| Modèle de données | Faible | Structure simple avec une seule entité |
| Logique métier | Faible | Opérations CRUD basiques et génération de QR codes |
| Intégrations | Aucune | Pas d'intégration avec des systèmes externes |
| Sécurité | Faible | Pas d'authentification requise, données non sensibles dans les QR codes |
| Performance | Faible | Volume de données limité, opérations simples |

## Phase 0 : Recherche et préparation

### Recherche

Voir [research.md](./research.md) pour les détails sur les choix technologiques et les meilleures pratiques.

### Décisions techniques

- **Bibliothèque QR code**: qrcode pour Python (simple, bien maintenue, supporte le format PNG)
- **Format de stockage**: Fichiers PNG nommés selon le format `[QR_CODE_NUMBER].png`
- **Structure de la base de données**: Table unique T_BUILDING avec contraintes d'unicité sur QR_CODE_NUMBER
- **Format d'import**: Fichiers JSON avec validation des champs obligatoires

## Phase 1 : Conception détaillée

### Modèle de données

Voir [data-model.md](./data-model.md) pour les détails sur le schéma de la base de données.

### Contrats d'API

Voir le dossier [contracts/](./contracts/) pour les détails sur les interfaces d'API.

### Guide de démarrage rapide

Voir [quickstart.md](./quickstart.md) pour les instructions d'installation et d'utilisation.

## Phase 2 : Implémentation

### Tâches principales

1. Configurer l'environnement de développement avec PostgreSQL
2. Créer le script de migration pour la table T_BUILDING
3. Implémenter les modèles de données et les opérations CRUD
4. Implémenter la logique de génération de QR codes
5. Développer les interfaces CLI pour l'import de données et la génération de QR codes
6. Écrire les tests unitaires et d'intégration
7. Documenter l'utilisation de l'application

### Risques et atténuations

| Risque | Impact | Probabilité | Atténuation |
|--------|--------|-------------|-------------|
| Erreurs dans la génération des QR codes | Moyen | Faible | Tests exhaustifs avec différents formats de QR_CODE_NUMBER |
| Problèmes de performance avec de grands volumes de données | Faible | Faible | Indexation appropriée dans PostgreSQL |
| Conflits d'unicité pour QR_CODE_NUMBER | Élevé | Faible | Validation stricte et gestion des erreurs robuste |

## Validation et tests

### Stratégie de test

- **Tests unitaires**: Validation des fonctions individuelles pour la génération de QR codes et les opérations CRUD
- **Tests d'intégration**: Vérification du flux complet depuis l'import jusqu'à la génération de QR codes
- **Tests de performance**: Validation des critères de succès SC-001 à SC-004

### Critères d'acceptation

Les critères d'acceptation sont définis dans la spécification et seront validés par les tests automatisés.