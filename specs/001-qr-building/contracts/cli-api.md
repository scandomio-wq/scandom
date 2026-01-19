# Contrats d'API CLI : QR Building Registry

Ce document décrit les interfaces en ligne de commande (CLI) pour l'application QR Building Registry.

## Vue d'ensemble

L'application expose deux commandes principales :

1. `import_building.py` : Importe les informations d'un bâtiment depuis un fichier JSON
2. `generate_qr.py` : Génère ou régénère un QR code pour un bâtiment existant

## 1. Import de bâtiment

### Commande : `import_building.py`

Importe les informations d'un bâtiment depuis un fichier JSON et génère automatiquement un QR code.

#### Syntaxe

```bash
python import_building.py <chemin_fichier_json> [--output <dossier_sortie>]
```

#### Arguments

| Argument | Type | Obligatoire | Description |
|----------|------|-------------|-------------|
| chemin_fichier_json | string | Oui | Chemin vers le fichier JSON contenant les informations du bâtiment |
| --output | string | Non | Dossier de sortie pour le QR code (par défaut: ./qr_codes) |

#### Format du fichier JSON d'entrée

```json
{
  "LOCATION": "123 Rue de la Paix, 75000 Paris",
  "EMAIL_GESTIONNAIRE": "gestionnaire@example.com",
  "NOTES": "Bâtiment rénové en 2025"
}
```

#### Sorties

- **Succès** (code de sortie 0) :
  ```
  Bâtiment importé avec succès.
  ID: 42
  QR_CODE_NUMBER: QR12345
  QR code généré: /chemin/vers/qr_codes/QR12345.png
  ```

- **Erreur** (code de sortie non-zéro) :
  ```
  Erreur: <message d'erreur>
  ```

#### Codes d'erreur

| Code | Description |
|------|-------------|
| 1 | Erreur générale |
| 2 | Fichier JSON introuvable ou invalide |
| 3 | Données invalides (validation échouée) |
| 4 | Erreur de base de données |
| 5 | Erreur de génération du QR code |

## 2. Génération de QR code

### Commande : `generate_qr.py`

Génère ou régénère un QR code pour un bâtiment existant.

#### Syntaxe

```bash
python generate_qr.py (--id <id_batiment> | --qr <qr_code_number>) [--output <dossier_sortie>] [--force]
```

#### Arguments

| Argument | Type | Obligatoire | Description |
|----------|------|-------------|-------------|
| --id | integer | Oui (si --qr non fourni) | ID du bâtiment |
| --qr | string | Oui (si --id non fourni) | QR_CODE_NUMBER du bâtiment |
| --output | string | Non | Dossier de sortie pour le QR code (par défaut: ./qr_codes) |
| --force | flag | Non | Force la régénération même si le fichier existe déjà |

#### Sorties

- **Succès** (code de sortie 0) :
  ```
  QR code généré avec succès: /chemin/vers/qr_codes/QR12345.png
  ```

- **Erreur** (code de sortie non-zéro) :
  ```
  Erreur: <message d'erreur>
  ```

#### Codes d'erreur

| Code | Description |
|------|-------------|
| 1 | Erreur générale |
| 2 | Bâtiment introuvable |
| 3 | Arguments invalides (ni --id ni --qr fournis) |
| 4 | Erreur de génération du QR code |
| 5 | Erreur d'écriture du fichier |

## 3. Recherche de bâtiment par QR code

### Commande : `find_building.py`

Recherche un bâtiment à partir de son QR_CODE_NUMBER.

#### Syntaxe

```bash
python find_building.py <qr_code_number> [--format json|text]
```

#### Arguments

| Argument | Type | Obligatoire | Description |
|----------|------|-------------|-------------|
| qr_code_number | string | Oui | QR_CODE_NUMBER du bâtiment à rechercher |
| --format | string | Non | Format de sortie (json ou text, par défaut: text) |

#### Sorties

- **Succès** (code de sortie 0) :
  
  Format text (par défaut) :
  ```
  ID: 42
  LOCATION: 123 Rue de la Paix, 75000 Paris
  EMAIL_GESTIONNAIRE: gestionnaire@example.com
  NOTES: Bâtiment rénové en 2025
  QR_CODE_NUMBER: QR12345
  CREATION_DATE: 2026-01-18T10:30:00
  ```
  
  Format JSON :
  ```json
  {
    "ID": 42,
    "LOCATION": "123 Rue de la Paix, 75000 Paris",
    "EMAIL_GESTIONNAIRE": "gestionnaire@example.com",
    "NOTES": "Bâtiment rénové en 2025",
    "QR_CODE_NUMBER": "QR12345",
    "CREATION_DATE": "2026-01-18T10:30:00"
  }
  ```

- **Erreur** (code de sortie non-zéro) :
  ```
  Erreur: <message d'erreur>
  ```

#### Codes d'erreur

| Code | Description |
|------|-------------|
| 1 | Erreur générale |
| 2 | Bâtiment introuvable |
| 3 | Format de sortie invalide |
| 4 | Erreur de base de données |

## Exemples d'utilisation

### Importer un bâtiment

```bash
python import_building.py batiment.json --output /path/to/qr_codes
```

### Générer un QR code par ID

```bash
python generate_qr.py --id 42 --output /path/to/qr_codes
```

### Générer un QR code par QR_CODE_NUMBER

```bash
python generate_qr.py --qr QR12345 --force
```

### Rechercher un bâtiment par QR_CODE_NUMBER

```bash
python find_building.py QR12345 --format json
```
