# Recherche et choix technologiques : QR Building Registry

## Bibliothèque de génération de QR codes

### Décision : qrcode pour Python

La bibliothèque `qrcode` pour Python a été choisie pour la génération des QR codes.

**Rationale** :
- Bibliothèque mature et bien maintenue
- Support natif pour la génération de fichiers PNG
- API simple et bien documentée
- Personnalisation du niveau de correction d'erreur et de la taille
- Pas de dépendance externe à une API web

**Alternatives considérées** :
- **pyqrcode** : Plus légère mais moins de fonctionnalités de personnalisation
- **segno** : Très performante mais API légèrement plus complexe
- **API externe** : Rejetée car la constitution exige une génération locale

**Exemple d'utilisation** :
```python
import qrcode

def generate_qr_code(qr_code_number, output_path):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_code_number)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(f"{output_path}/{qr_code_number}.png")
    
    return f"{output_path}/{qr_code_number}.png"
```

## Stockage des données

### Décision : PostgreSQL avec psycopg2

PostgreSQL sera utilisé comme base de données avec la bibliothèque psycopg2 pour l'interface Python.

**Rationale** :
- Exigé par la constitution du projet
- Support robuste des contraintes d'unicité et d'intégrité
- Excellente performance pour les requêtes simples
- Facilité d'indexation pour les recherches par QR_CODE_NUMBER
- psycopg2 est la bibliothèque Python la plus mature pour PostgreSQL

**Alternatives considérées** :
- **SQLAlchemy ORM** : Pourrait être ajouté comme couche d'abstraction, mais pas nécessaire pour la simplicité du modèle
- **asyncpg** : Plus performant mais complexité supplémentaire non justifiée pour ce cas d'usage

**Exemple de schéma** :
```sql
CREATE TABLE T_BUILDING (
    ID SERIAL PRIMARY KEY,
    CREATION_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    LOCATION VARCHAR(255) NOT NULL,
    EMAIL_GESTIONNAIRE VARCHAR(100),
    NOTES TEXT,
    QR_CODE_NUMBER VARCHAR(50) NOT NULL UNIQUE
);

CREATE INDEX idx_qr_code_number ON T_BUILDING(QR_CODE_NUMBER);
```

## Format d'import des données

### Décision : JSON avec validation

Les données des immeubles seront importées via des fichiers JSON avec validation des champs obligatoires.

**Rationale** :
- Format standard facile à produire et à consommer
- Support natif en Python via le module json
- Structure flexible permettant d'ajouter des champs optionnels à l'avenir
- Facilité de validation avec des schémas JSON

**Alternatives considérées** :
- **CSV** : Plus simple mais moins flexible pour les données structurées
- **XML** : Trop verbeux pour ce cas d'usage
- **YAML** : Moins standard pour l'échange de données

**Exemple de format** :
```json
{
  "LOCATION": "123 Rue de la Paix, 75000 Paris",
  "EMAIL_GESTIONNAIRE": "gestionnaire@example.com",
  "NOTES": "Bâtiment rénové en 2025"
}
```

## Stockage des QR codes générés

### Décision : Système de fichiers avec structure organisée

Les QR codes générés seront stockés dans le système de fichiers avec une convention de nommage basée sur QR_CODE_NUMBER.

**Rationale** :
- Simplicité d'accès et de gestion
- Pas besoin de base de données binaire
- Facilité de sauvegarde et de partage
- Conforme aux exigences de la spécification

**Alternatives considérées** :
- **Stockage en base de données** : Ajouterait une complexité inutile
- **Stockage cloud** : Non nécessaire pour une application locale

**Structure proposée** :
```
/qr_codes/
    ├── QR12345.png
    ├── QR12346.png
    └── ...
```

## Génération d'identifiants QR_CODE_NUMBER

### Décision : Préfixe "QR" + identifiant numérique séquentiel

Les identifiants QR_CODE_NUMBER seront générés avec un préfixe "QR" suivi d'un nombre séquentiel.

**Rationale** :
- Format simple et lisible
- Facilement identifiable comme code QR
- Évite les confusions avec d'autres identifiants
- Facile à générer de manière séquentielle

**Alternatives considérées** :
- **UUID** : Trop long pour un QR code simple
- **Identifiants aléatoires** : Risque de collisions
- **Hash des données** : Changerait si les données changent (non applicable car les données sont immuables)

**Exemple d'implémentation** :
```python
def generate_qr_code_number(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("SELECT MAX(SUBSTRING(QR_CODE_NUMBER FROM 3)::integer) FROM T_BUILDING")
    result = cursor.fetchone()[0]
    
    next_number = 1 if result is None else result + 1
    return f"QR{next_number:05d}"  # Format: QR00001, QR00002, etc.
```

## Validation des données

### Décision : Validation côté serveur avec jsonschema

La validation des données JSON sera effectuée côté serveur avec la bibliothèque jsonschema.

**Rationale** :
- Validation stricte avant insertion en base
- Messages d'erreur clairs et actionnables
- Support des règles de validation complexes
- Facilité d'extension pour de nouvelles règles

**Alternatives considérées** :
- **Validation manuelle** : Propice aux erreurs et moins maintenable
- **Validation par base de données uniquement** : Moins de contrôle sur les messages d'erreur

**Exemple de schéma de validation** :
```python
building_schema = {
    "type": "object",
    "required": ["LOCATION"],
    "properties": {
        "LOCATION": {"type": "string", "minLength": 3, "maxLength": 255},
        "EMAIL_GESTIONNAIRE": {"type": "string", "format": "email", "maxLength": 100},
        "NOTES": {"type": "string"}
    },
    "additionalProperties": False
}
```

## Interface en ligne de commande

### Décision : argparse pour les CLI Python

La bibliothèque standard argparse sera utilisée pour créer les interfaces en ligne de commande.

**Rationale** :
- Fait partie de la bibliothèque standard Python
- Support complet pour les sous-commandes et options
- Génération automatique de l'aide
- Facile à étendre

**Alternatives considérées** :
- **click** : Plus élégant mais dépendance externe
- **docopt** : Syntaxe basée sur la documentation mais moins flexible
- **typer** : Moderne mais peut-être trop complexe pour ce cas d'usage simple

**Exemple d'implémentation** :
```python
import argparse

def setup_import_parser():
    parser = argparse.ArgumentParser(description="Importer un bâtiment depuis un fichier JSON")
    parser.add_argument("json_file", help="Chemin vers le fichier JSON contenant les données du bâtiment")
    return parser

def setup_generate_parser():
    parser = argparse.ArgumentParser(description="Générer un QR code pour un bâtiment existant")
    parser.add_argument("--id", help="ID du bâtiment")
    parser.add_argument("--qr", help="QR_CODE_NUMBER du bâtiment")
    parser.add_argument("--output", help="Dossier de sortie pour le QR code", default="./qr_codes")
    return parser
```
