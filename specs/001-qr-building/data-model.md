# Modèle de données : QR Building Registry

Ce document décrit le modèle de données pour la fonctionnalité QR Building Registry, qui permet de stocker des informations sur des immeubles et de générer des QR codes uniques liés à ces immeubles.

## Schéma de base de données

### Table T_BUILDING

La table principale qui stocke les informations des immeubles.

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| ID                    | SERIAL        | PRIMARY KEY  | Identifiant unique auto-incrémenté |
| CREATION_DATE         | TIMESTAMP     | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Date et heure de création de l'enregistrement |
| LOCATION              | VARCHAR(255)  | NOT NULL     | Adresse ou emplacement de l'immeuble |
| EMAIL_GESTIONNAIRE    | VARCHAR(100)  | NULL         | Email du gestionnaire de l'immeuble |
| NOTES                 | TEXT          | NULL         | Notes ou informations supplémentaires |
| QR_CODE_NUMBER        | VARCHAR(50)   | NOT NULL, UNIQUE | Identifiant unique utilisé dans le QR code |

### Indexes

| Nom | Colonnes | Type | Description |
|-----|---------|------|-------------|
| pk_building | ID | PRIMARY KEY | Index de clé primaire |
| idx_qr_code_number | QR_CODE_NUMBER | UNIQUE | Index pour recherche rapide par QR_CODE_NUMBER |

## Script de création de la table

```sql
CREATE TABLE T_BUILDING (
    ID SERIAL PRIMARY KEY,
    CREATION_DATE TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LOCATION VARCHAR(255) NOT NULL,
    EMAIL_GESTIONNAIRE VARCHAR(100),
    NOTES TEXT,
    QR_CODE_NUMBER VARCHAR(50) NOT NULL
);

ALTER TABLE T_BUILDING ADD CONSTRAINT uq_building_qr_code_number UNIQUE (QR_CODE_NUMBER);
CREATE INDEX idx_qr_code_number ON T_BUILDING(QR_CODE_NUMBER);
```

## Règles de validation

### Validation des champs

| Champ | Règles de validation |
|-------|----------------------|
| LOCATION | - Obligatoire<br>- Longueur maximum: 255 caractères |
| EMAIL_GESTIONNAIRE | - Format email valide<br>- Longueur maximum: 100 caractères |
| NOTES | - Pas de limite de taille spécifique |
| QR_CODE_NUMBER | - Obligatoire<br>- Format: "QR" suivi de chiffres<br>- Unique dans la table |

### Schéma de validation JSON

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

## Modèle Python

```python
class Building:
    def __init__(self, location, email_gestionnaire=None, notes=None, qr_code_number=None, id=None, creation_date=None):
        self.id = id
        self.location = location
        self.email_gestionnaire = email_gestionnaire
        self.notes = notes
        self.qr_code_number = qr_code_number
        self.creation_date = creation_date

    @classmethod
    def from_json(cls, json_data):
        return cls(
            location=json_data["LOCATION"],
            email_gestionnaire=json_data.get("EMAIL_GESTIONNAIRE"),
            notes=json_data.get("NOTES")
        )

    def to_dict(self):
        return {
            "ID": self.id,
            "LOCATION": self.location,
            "EMAIL_GESTIONNAIRE": self.email_gestionnaire,
            "NOTES": self.notes,
            "QR_CODE_NUMBER": self.qr_code_number,
            "CREATION_DATE": self.creation_date.isoformat() if self.creation_date else None
        }
```

## Stockage des QR codes

Les QR codes générés seront stockés dans le système de fichiers avec la convention de nommage suivante :

- Format du nom de fichier : `[QR_CODE_NUMBER].png`
- Exemple : `QR12345.png`

## Diagramme de classe

```
+----------------+
|   Building     |
+----------------+
| id: int        |
| creation_date: |
|   timestamp    |
| location: str  |
| email_gest: str|
| notes: str     |
| qr_code_num: str|
+----------------+
| from_json()    |
| to_dict()      |
+----------------+
```

## Flux de données

1. L'utilisateur fournit un fichier JSON contenant les informations de l'immeuble
2. Le système valide les données selon le schéma de validation
3. Le système génère un QR_CODE_NUMBER unique
4. Le système insère les données dans la table T_BUILDING
5. Le système génère un QR code au format PNG basé sur le QR_CODE_NUMBER
6. Le système stocke le QR code dans le système de fichiers avec le nom `[QR_CODE_NUMBER].png`

## Contraintes d'immutabilité

Conformément à la spécification, les informations d'un bâtiment ne peuvent pas être modifiées après leur création. Cette contrainte sera appliquée au niveau de l'application plutôt qu'au niveau de la base de données, car PostgreSQL ne fournit pas de mécanisme natif pour rendre une ligne immuable.

```python
def update_building(building_id, data):
    # Cette fonction lèvera toujours une exception
    raise OperationNotAllowedException("La modification des informations d'un bâtiment après création n'est pas autorisée.")
```
