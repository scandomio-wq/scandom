# Contrats d'API Python : QR Building Registry

Ce document décrit les interfaces Python pour l'application QR Building Registry, qui peuvent être utilisées par d'autres modules ou scripts Python.

## Vue d'ensemble

L'API Python expose trois modules principaux :

1. `building_dao` : Opérations CRUD pour les immeubles
2. `qr_generator` : Génération de QR codes
3. `building_importer` : Import de données d'immeubles depuis JSON

## 1. Module building_dao

### Classe BuildingDAO

Gère les opérations de base de données pour les immeubles.

#### Méthodes

##### `create_building(building: Building) -> int`

Crée un nouvel enregistrement d'immeuble dans la base de données.

**Paramètres :**
- `building` : Instance de la classe Building avec les informations de l'immeuble

**Retourne :**
- `int` : ID du nouvel immeuble créé

**Exceptions :**
- `DatabaseError` : Erreur de base de données
- `ValidationError` : Données invalides
- `DuplicateQRCodeError` : QR_CODE_NUMBER déjà utilisé

**Exemple :**
```python
from models.building import Building
from db.building_dao import BuildingDAO

building = Building(
    location="123 Rue de la Paix, 75000 Paris",
    email_gestionnaire="gestionnaire@example.com",
    notes="Bâtiment rénové en 2025"
)

dao = BuildingDAO()
building_id = dao.create_building(building)
```

##### `get_building_by_id(building_id: int) -> Building`

Récupère un immeuble par son ID.

**Paramètres :**
- `building_id` : ID de l'immeuble à récupérer

**Retourne :**
- `Building` : Instance de la classe Building avec les informations de l'immeuble

**Exceptions :**
- `DatabaseError` : Erreur de base de données
- `BuildingNotFoundError` : Immeuble introuvable

**Exemple :**
```python
from db.building_dao import BuildingDAO

dao = BuildingDAO()
building = dao.get_building_by_id(42)
```

##### `get_building_by_qr_code(qr_code_number: str) -> Building`

Récupère un immeuble par son QR_CODE_NUMBER.

**Paramètres :**
- `qr_code_number` : QR_CODE_NUMBER de l'immeuble à récupérer

**Retourne :**
- `Building` : Instance de la classe Building avec les informations de l'immeuble

**Exceptions :**
- `DatabaseError` : Erreur de base de données
- `BuildingNotFoundError` : Immeuble introuvable

**Exemple :**
```python
from db.building_dao import BuildingDAO

dao = BuildingDAO()
building = dao.get_building_by_qr_code("QR12345")
```

##### `generate_qr_code_number() -> str`

Génère un nouveau QR_CODE_NUMBER unique.

**Retourne :**
- `str` : Nouveau QR_CODE_NUMBER unique

**Exceptions :**
- `DatabaseError` : Erreur de base de données

**Exemple :**
```python
from db.building_dao import BuildingDAO

dao = BuildingDAO()
qr_code_number = dao.generate_qr_code_number()
```

## 2. Module qr_generator

### Classe QRGenerator

Gère la génération des QR codes.

#### Méthodes

##### `generate_qr_code(qr_code_number: str, output_path: str) -> str`

Génère un QR code pour un QR_CODE_NUMBER donné.

**Paramètres :**
- `qr_code_number` : QR_CODE_NUMBER à encoder dans le QR code
- `output_path` : Chemin du dossier de sortie pour le QR code

**Retourne :**
- `str` : Chemin complet du fichier QR code généré

**Exceptions :**
- `QRGenerationError` : Erreur de génération du QR code
- `IOError` : Erreur d'écriture du fichier

**Exemple :**
```python
from qr.generator import QRGenerator

generator = QRGenerator()
qr_file_path = generator.generate_qr_code("QR12345", "./qr_codes")
```

##### `qr_code_exists(qr_code_number: str, output_path: str) -> bool`

Vérifie si un QR code existe déjà pour un QR_CODE_NUMBER donné.

**Paramètres :**
- `qr_code_number` : QR_CODE_NUMBER à vérifier
- `output_path` : Chemin du dossier contenant les QR codes

**Retourne :**
- `bool` : True si le QR code existe, False sinon

**Exemple :**
```python
from qr.generator import QRGenerator

generator = QRGenerator()
exists = generator.qr_code_exists("QR12345", "./qr_codes")
```

## 3. Module building_importer

### Classe BuildingImporter

Gère l'import des données d'immeubles depuis des fichiers JSON.

#### Méthodes

##### `import_from_file(json_file_path: str) -> Building`

Importe les données d'un immeuble depuis un fichier JSON.

**Paramètres :**
- `json_file_path` : Chemin vers le fichier JSON contenant les données de l'immeuble

**Retourne :**
- `Building` : Instance de la classe Building avec les données importées

**Exceptions :**
- `FileNotFoundError` : Fichier JSON introuvable
- `JSONDecodeError` : Format JSON invalide
- `ValidationError` : Données invalides

**Exemple :**
```python
from models.building_importer import BuildingImporter

importer = BuildingImporter()
building = importer.import_from_file("batiment.json")
```

##### `validate_json_data(json_data: dict) -> bool`

Valide les données JSON selon le schéma de validation.

**Paramètres :**
- `json_data` : Dictionnaire contenant les données à valider

**Retourne :**
- `bool` : True si les données sont valides

**Exceptions :**
- `ValidationError` : Données invalides avec détails des erreurs

**Exemple :**
```python
from models.building_importer import BuildingImporter

importer = BuildingImporter()
json_data = {
    "LOCATION": "123 Rue de la Paix, 75000 Paris",
    "EMAIL_GESTIONNAIRE": "gestionnaire@example.com",
    "NOTES": "Bâtiment rénové en 2025"
}

try:
    is_valid = importer.validate_json_data(json_data)
    # Les données sont valides
except ValidationError as e:
    # Traiter les erreurs de validation
    print(e.errors)
```

## 4. Exceptions personnalisées

### `BuildingError`

Classe de base pour toutes les exceptions liées aux immeubles.

### `BuildingNotFoundError`

Levée lorsqu'un immeuble est introuvable.

### `DuplicateQRCodeError`

Levée lorsqu'un QR_CODE_NUMBER est déjà utilisé.

### `ValidationError`

Levée lorsque les données ne respectent pas le schéma de validation.

### `QRGenerationError`

Levée lorsqu'une erreur survient pendant la génération d'un QR code.

### `OperationNotAllowedException`

Levée lorsqu'une opération non autorisée est tentée (par exemple, modification d'un immeuble existant).
