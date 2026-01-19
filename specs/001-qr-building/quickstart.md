# Guide de démarrage rapide : QR Building Registry

Ce guide vous aidera à configurer et utiliser l'application QR Building Registry pour stocker des informations sur des immeubles et générer des QR codes uniques.

## Prérequis

- Python 3.8 ou supérieur
- PostgreSQL 12 ou supérieur
- pip (gestionnaire de paquets Python)

## Installation

1. Clonez le dépôt :
   ```bash
   git clone <repository_url>
   cd scandom
   ```

2. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

3. Configurez la base de données PostgreSQL :
   ```bash
   # Créez une base de données PostgreSQL
   createdb scandom_db
   
   # Exécutez le script de migration
   psql -d scandom_db -f migrations/001_create_building_table.sql
   ```

4. Configurez les paramètres de connexion à la base de données :
   ```bash
   # Copiez le fichier de configuration exemple
   cp config/db_config.ini.example config/db_config.ini
   
   # Éditez le fichier avec vos paramètres
   nano config/db_config.ini
   ```

   Exemple de contenu pour `db_config.ini` :
   ```ini
   [postgresql]
   host = localhost
   database = scandom_db
   user = postgres
   password = your_password
   port = 5432
   ```

5. Créez le dossier pour stocker les QR codes :
   ```bash
   mkdir -p qr_codes
   ```

## Utilisation

### 1. Importer un bâtiment

Créez un fichier JSON avec les informations du bâtiment :

```json
{
  "LOCATION": "123 Rue de la Paix, 75000 Paris",
  "EMAIL_GESTIONNAIRE": "gestionnaire@example.com",
  "NOTES": "Bâtiment rénové en 2025"
}
```

Puis importez-le avec la commande :

```bash
python src/cli/import_building.py batiment.json --output ./qr_codes
```

La commande affichera l'ID du bâtiment créé, son QR_CODE_NUMBER et le chemin vers le QR code généré.

### 2. Générer ou régénérer un QR code

Pour générer ou régénérer un QR code pour un bâtiment existant :

```bash
# Par ID
python src/cli/generate_qr.py --id 42 --output ./qr_codes

# Par QR_CODE_NUMBER
python src/cli/generate_qr.py --qr QR12345 --output ./qr_codes
```

Utilisez l'option `--force` pour écraser un QR code existant :

```bash
python src/cli/generate_qr.py --id 42 --force
```

### 3. Rechercher un bâtiment par QR code

Pour rechercher un bâtiment à partir de son QR_CODE_NUMBER (par exemple après avoir scanné un QR code) :

```bash
# Format texte (par défaut)
python src/cli/find_building.py QR12345

# Format JSON
python src/cli/find_building.py QR12345 --format json
```

## Structure des fichiers

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
│       └── find_building.py   # CLI pour rechercher un bâtiment par QR code
├── migrations/
│   └── 001_create_building_table.sql  # Script de création de la table T_BUILDING
├── tests/
│   ├── test_building_dao.py  # Tests pour les opérations CRUD
│   ├── test_qr_generator.py  # Tests pour la génération de QR codes
│   └── test_cli.py           # Tests pour les commandes CLI
├── config/
│   ├── db_config.ini.example # Exemple de configuration de la base de données
│   └── db_config.ini         # Configuration de la base de données (à créer)
├── qr_codes/                 # Dossier pour stocker les QR codes générés
└── requirements.txt          # Dépendances Python
```

## Dépendances Python

Voici les principales dépendances utilisées par l'application :

```
psycopg2-binary==2.9.9  # Interface PostgreSQL pour Python
qrcode[pil]==7.4.2      # Génération de QR codes
Pillow==10.0.0          # Traitement d'images (utilisé par qrcode)
jsonschema==4.19.0      # Validation des schémas JSON
```

## Exemples de code

### Exemple d'utilisation de l'API Python

```python
from db.connection import get_connection
from db.building_dao import BuildingDAO
from models.building import Building
from qr.generator import QRGenerator

# Créer un nouvel immeuble
building = Building(
    location="123 Rue de la Paix, 75000 Paris",
    email_gestionnaire="gestionnaire@example.com",
    notes="Bâtiment rénové en 2025"
)

# Enregistrer l'immeuble dans la base de données
dao = BuildingDAO(get_connection())
building_id = dao.create_building(building)

# Récupérer l'immeuble avec son QR_CODE_NUMBER généré
building = dao.get_building_by_id(building_id)

# Générer le QR code
generator = QRGenerator()
qr_file_path = generator.generate_qr_code(building.qr_code_number, "./qr_codes")

print(f"Immeuble créé avec ID: {building_id}")
print(f"QR_CODE_NUMBER: {building.qr_code_number}")
print(f"QR code généré: {qr_file_path}")
```

## Dépannage

### Problèmes de connexion à la base de données

- Vérifiez que PostgreSQL est en cours d'exécution
- Vérifiez les paramètres de connexion dans `config/db_config.ini`
- Assurez-vous que l'utilisateur a les droits nécessaires sur la base de données

### Erreurs de génération de QR codes

- Vérifiez que le dossier de sortie existe et est accessible en écriture
- Assurez-vous que la bibliothèque Pillow est correctement installée

### Erreurs d'import de données

- Vérifiez que le fichier JSON est valide et contient les champs requis
- Assurez-vous que le champ LOCATION est présent et non vide

## Ressources supplémentaires

- [Documentation de la bibliothèque qrcode](https://github.com/lincolnloop/python-qrcode)
- [Documentation de psycopg2](https://www.psycopg.org/docs/)
- [Documentation de jsonschema](https://python-jsonschema.readthedocs.io/)
