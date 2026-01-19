# QR Building Registry

Application pour stocker des informations sur des immeubles dans une base de données PostgreSQL et générer des QR codes uniques liés à ces immeubles.

## Fonctionnalités

- Enregistrement d'immeubles avec leurs informations (emplacement, email du gestionnaire, notes)
- Génération automatique d'identifiants QR uniques
- Génération de QR codes au format PNG
- Recherche d'immeubles par identifiant QR
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

## Format des données

### Fichier JSON d'entrée

```json
{
  "LOCATION": "123 Rue de la Paix, 75000 Paris",
  "EMAIL_GESTIONNAIRE": "gestionnaire@example.com",
  "NOTES": "Bâtiment rénové en 2025"
}
```

Seul le champ `LOCATION` est obligatoire.

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

## Licence

Ce projet est sous licence [MIT](LICENSE).
