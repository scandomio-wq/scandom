# Tâches d'implémentation : QR Building Registry

**Feature Branch**: `001-qr-building`  
**Créé**: 2026-01-18  
**Status**: Draft  

## Vue d'ensemble

Cette liste de tâches détaille l'implémentation de la fonctionnalité QR Building Registry, qui permet de stocker des informations sur des immeubles dans une base de données PostgreSQL et de générer des QR codes uniques liés à ces immeubles.

## Dépendances entre user stories

```
[US1: Enregistrer un immeuble] --> [US2: Générer QR code] --> [US3: Retrouver immeuble par QR]
```

L'enregistrement d'un immeuble (US1) est un prérequis pour la génération de QR codes (US2) et la recherche d'immeubles par QR code (US3).

## Stratégie d'implémentation

1. **MVP**: User Story 1 (Enregistrer un immeuble)
2. **Incréments**:
   - User Story 2 (Générer QR code)
   - User Story 3 (Retrouver immeuble par QR)
3. **Livraison finale**: Polissage et documentation

## Phase 1: Configuration du projet

- [x] T001 Créer la structure du projet selon le plan d'implémentation et initialiser le fichier principal `src/__init__.py`
- [x] T002 Configurer l'environnement virtuel Python et créer le fichier `.venv/pyvenv.cfg`
- [x] T003 Créer le fichier `requirements.txt` avec les dépendances nécessaires
- [x] T004 Configurer PostgreSQL, créer la base de données et la config locale (fichier: `config/db_config.ini`)
- [x] T005 [P] Créer le fichier `config/db_config.ini.example` pour la configuration de la base de données
- [x] T006 Créer le dossier `qr_codes/` pour stocker les QR codes générés

## Phase 2: Fondations

- [x] T007 Créer le script `migrations/001_create_building_table.sql` pour la table T_BUILDING
- [x] T008 [P] Implémenter `src/utils/config.py` pour la gestion de la configuration
- [x] T009 Implémenter `src/db/connection.py` pour la connexion à PostgreSQL
- [x] T010 [P] Implémenter `src/utils/validators.py` pour la validation des données d'entrée
- [x] T011 Implémenter `src/models/building.py` avec la classe Building

## Phase 3: User Story 1 - Enregistrer un immeuble et lui attribuer un identifiant QR

**Objectif**: Un opérateur enregistre les informations d'un immeuble et le système attribue un identifiant QR unique lié à cet immeuble.

**Test indépendant**: En créant un immeuble, on obtient un enregistrement persistant avec un identifiant QR unique et une date de création automatiquement renseignée.

### Tâches d'implémentation

- [x] T012 [US1] Implémenter `src/db/building_dao.py` avec `create_building` et une opération de mise à jour explicitement interdite (ex: `update_building` qui lève une erreur)
- [x] T013 [US1] Implémenter la génération automatique de `QR_CODE_NUMBER` dans `src/db/building_dao.py`
- [x] T014 [P] [US1] Implémenter `src/qr/generator.py` avec `generate_qr_code`
- [x] T015 [US1] Implémenter `src/cli/import_building.py` pour l'import de données depuis JSON
- [x] T016 [US1] Ajouter la validation des données JSON dans `src/cli/import_building.py`
- [x] T017 [US1] Implémenter la gestion des erreurs dans `src/cli/import_building.py`
- [x] T018 [P] [US1] Créer `tests/test_building_dao.py` pour tester la création d'immeubles et l'interdiction de mise à jour (immutabilité)
- [x] T019 [P] [US1] Créer `tests/test_qr_generator.py` pour tester la génération de QR codes
- [x] T019a [P] [US1] Ajouter des tests pour les cas limites dans `tests/test_edge_cases.py`: email invalide, notes trop longues, QR_CODE_NUMBER avec caractères invalides

## Phase 4: User Story 2 - Générer le QR code pour un immeuble existant

**Objectif**: Un opérateur demande la génération du QR code d'un immeuble existant, et récupère un artefact QR exploitable associé à l'identifiant QR stocké.

**Test indépendant**: En demandant la génération pour un immeuble existant, un artefact QR est produit et correspond à l'identifiant QR de l'immeuble.

### Tâches d'implémentation

- [x] T020 [US2] Ajouter `get_building_by_id` dans `src/db/building_dao.py`
- [x] T021 [US2] Implémenter `src/cli/generate_qr.py` pour la génération de QR codes
- [x] T022 [US2] Ajouter l'option `--force` dans `src/cli/generate_qr.py` pour forcer la régénération
- [x] T023 [US2] Implémenter la vérification d'existence du QR code dans `src/qr/generator.py`
- [x] T024 [US2] Implémenter la gestion des erreurs dans `src/cli/generate_qr.py`
- [x] T025 [P] [US2] Ajouter des tests pour la régénération de QR codes dans `tests/test_qr_generator.py`
- [x] T025a [P] [US2] Ajouter des tests pour les cas d'échec de génération QR dans `tests/test_edge_cases.py` (destination indisponible, erreurs de rendu)

## Phase 5: User Story 3 - Retrouver l'immeuble à partir d'un identifiant QR

**Objectif**: Un opérateur peut retrouver l'enregistrement d'un immeuble en fournissant l'identifiant QR afin de consulter les informations associées.

**Test indépendant**: En fournissant un identifiant QR existant, l'immeuble correspondant est retrouvé; en fournissant un identifiant inconnu, une erreur claire est retournée.

### Tâches d'implémentation

- [x] T026 [US3] Ajouter `get_building_by_qr_code` dans `src/db/building_dao.py`
- [x] T027 [US3] Implémenter `src/cli/find_building.py` pour la recherche d'immeubles par QR code
- [x] T028 [US3] Ajouter l'option `--format` dans `src/cli/find_building.py` pour le format de sortie
- [x] T029 [US3] Implémenter la gestion des erreurs dans `src/cli/find_building.py`
- [x] T030 [P] [US3] Ajouter des tests pour la recherche par QR code dans `tests/test_building_dao.py`
- [x] T031 [P] [US3] Créer `tests/test_cli.py` pour tester les interfaces CLI

## Phase 6: Polissage et documentation

- [x] T032 Ajouter des docstrings à toutes les fonctions et classes (dossier: `src/`)
- [x] T033 [P] Créer un `README.md` avec les instructions d'installation et d'utilisation
- [x] T034 [P] Documenter les codes d'erreur et messages dans `ERRORS.md`
- [x] T035 Optimiser les performances des requêtes PostgreSQL (requêtes dans `src/db/building_dao.py`)
- [x] T036 Ajouter des logs pour faciliter le débogage (fichiers: `src/cli/*.py`, `src/db/*.py`, `src/qr/*.py`)
- [x] T037 [P] Créer des exemples de fichiers JSON pour l'import de bâtiments (dossier: `examples/`)
- [x] T038 [P] Créer un script de benchmark `scripts/benchmarks/perf_test.py` pour mesurer les critères de succès SC-001 à SC-004
- [x] T039 Documenter la procédure de test de performance dans `docs/performance.md`

## Exécution parallèle

### User Story 1

Les tâches suivantes peuvent être exécutées en parallèle:
- T014 (Implémenter generator.py) et T012 (Implémenter building_dao.py)
- T018 (Tests DAO) et T019 (Tests QR)

### User Story 2

Les tâches suivantes peuvent être exécutées en parallèle:
- T025 (Tests régénération) peut être fait en parallèle avec T022-T024

### User Story 3

Les tâches suivantes peuvent être exécutées en parallèle:
- T030 (Tests DAO) et T031 (Tests CLI)

### Polissage

Les tâches suivantes peuvent être exécutées en parallèle:
- T033 (README), T034 (ERRORS), T037 (Exemples JSON), T038 (Benchmark) et T039 (Doc performance)
