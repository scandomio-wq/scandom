# QR Building Registry

Application pour stocker des informations sur des immeubles dans une base de données PostgreSQL, gérer des incidents et générer des QR codes uniques.

## Fonctionnalités

- Enregistrement d'immeubles avec leurs informations (emplacement, email du gestionnaire, notes)
- Gestion des incidents liés aux immeubles (localisation, type, catégorie)
- Génération automatique d'identifiants QR uniques pour les immeubles et les incidents
- Génération de QR codes au format PNG
- Recherche d'immeubles et d'incidents par identifiant QR
- Interface en ligne de commande (CLI)

## Prérequis

- Python 3.8 ou supérieur
- PostgreSQL 12.0 ou supérieur
- Bibliothèques Python (voir `requirements.txt`)

## Installation

1. Cloner le dépôt :
   ```bash
   git clone <url-du-depot>
   cd scandom
   ```

2. Créer et activer un environnement virtuel :
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Sur Linux/macOS
   # ou
   .venv\Scripts\activate     # Sur Windows
   ```

3. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

4. Configurer la base de données :
   ```bash
   # Copier le fichier de configuration exemple
   cp config/db_config.ini.example config/db_config.ini
   
   # Éditer le fichier avec vos paramètres PostgreSQL
   nano config/db_config.ini
   
   # Initialiser la base de données
   cd migrations
   ./init_database.sh
   cd ..
   ```

## Utilisation

### Importer un immeuble

```bash
python src/cli/import_building.py <chemin_fichier_json> [--output <dossier_sortie>]
```

Exemple :
```bash
python src/cli/import_building.py examples/building.json
```

### Générer un QR code pour un immeuble existant

```bash
python src/cli/generate_qr.py (--id <id_batiment> | --qr <qr_code_number>) [--output <dossier_sortie>] [--force]
```

Exemples :
```bash
python src/cli/generate_qr.py --id 1
python src/cli/generate_qr.py --qr QR1234567890 --force
```

### Rechercher un immeuble par QR code

```bash
python src/cli/find_building.py <qr_code_number> [--format json|text]
```

Exemple :
```bash
python src/cli/find_building.py QR1234567890 --format json
```

### Importer un incident

```bash
python src/cli/import_incident.py <chemin_fichier_json> [--output <dossier_sortie>]
```

Exemple :
```bash
python src/cli/import_incident.py examples/incident_complete.json
```

### Générer un QR code pour un incident existant

```bash
python src/cli/generate_incident_qr.py (--id <id_incident> | --qr <qr_code_number>) [--output <dossier_sortie>] [--force]
```

Exemples :
```bash
python src/cli/generate_incident_qr.py --id 1
python src/cli/generate_incident_qr.py --qr IN1234567890 --force
```

### Rechercher un incident par QR code

```bash
python src/cli/find_incident.py <qr_code_number> [--format json|text]
```

Exemple :
```bash
python src/cli/find_incident.py IN1234567890 --format json
```

## Format des données

### Fichier JSON pour les immeubles

```json
{
  "LOCATION": "123 Rue de la Paix, 75000 Paris",
  "EMAIL_GESTIONNAIRE": "gestionnaire@example.com",
  "NOTES": "Bâtiment rénové en 2025"
}
```

Seul le champ `LOCATION` est obligatoire.

### Fichier JSON pour les incidents

```json
{
  "BUILDING_ID": 1,
  "REPORTER_PHONE": "+33123456789",
  "REPORTER_EMAIL": "reporter@example.com",
  "INCIDENT_INFORMATION": {
    "zone": "Escalier principal",
    "etage": "3ème",
    "categorie": "Plomberie",
    "type": "Fuite d'eau",
    "informations_supplementaires": "Fuite importante au niveau du palier."
  }
}
```

Les champs `BUILDING_ID` et `INCIDENT_INFORMATION` sont obligatoires. Dans `INCIDENT_INFORMATION`, les champs `zone`, `etage`, `categorie` et `type` sont obligatoires.

## Codes d'erreur

Voir le fichier [ERRORS.md](ERRORS.md) pour la liste complète des codes d'erreur.

## Tests

Exécuter les tests unitaires :

```bash
pytest
```

Exécuter les tests avec couverture de code :

```bash
pytest --cov=src
```

## Performance

Pour exécuter les tests de performance :

```bash
python scripts/benchmarks/perf_test.py
```

Voir le fichier [docs/performance.md](docs/performance.md) pour plus d'informations sur les tests de performance.

## Structure du projet

```
scandom/
├── src/
│   ├── models/
│   │   ├── building.py       # Modèle de données pour les immeubles
│   │   └── incident.py       # Modèle de données pour les incidents
│   ├── db/
│   │   ├── __init__.py
│   │   ├── connection.py     # Gestion de la connexion à PostgreSQL
│   │   ├── building_dao.py   # Opérations CRUD pour les immeubles
│   │   └── incident_dao.py   # Opérations CRUD pour les incidents
│   ├── qr/
│   │   ├── __init__.py
│   │   └── generator.py      # Logique de génération des QR codes
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py         # Configuration de l'application
│   │   ├── validators.py     # Validation des données d'entrée
│   │   └── schemas/          # Schémas de validation JSON
│   │       └── incident_schema.py # Schéma pour les incidents
│   └── cli/
│       ├── __init__.py
│       ├── import_building.py # CLI pour importer un immeuble depuis JSON
│       ├── generate_qr.py     # CLI pour générer un QR code pour un immeuble
│       ├── find_building.py   # CLI pour rechercher un immeuble par QR
│       ├── import_incident.py # CLI pour importer un incident depuis JSON
│       ├── generate_incident_qr.py # CLI pour générer un QR code pour un incident
│       └── find_incident.py   # CLI pour rechercher un incident par QR
├── migrations/
│   ├── 001_create_building_table.sql  # Script de création de la table T_BUILDING
│   └── 002_create_incident_table.sql  # Script de création de la table T_INCIDENT
├── examples/                 # Exemples de fichiers JSON
│   ├── building_*.json       # Exemples pour les immeubles
│   └── incident_*.json       # Exemples pour les incidents
├── tests/
│   ├── test_building_dao.py  # Tests pour les opérations CRUD des immeubles
│   ├── test_incident_dao.py  # Tests pour les opérations CRUD des incidents
│   ├── test_qr_generator.py  # Tests pour la génération de QR codes
│   └── test_cli.py           # Tests pour les commandes CLI
├── config/
│   └── db_config.ini         # Configuration de la base de données
├── ERRORS.md                 # Codes d'erreur et messages
└── requirements.txt          # Dépendances Python
```

## Licence

Ce projet est sous licence [MIT](LICENSE).
