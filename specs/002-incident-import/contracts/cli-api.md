# API CLI pour l'import d'incidents

Ce document décrit les commandes CLI disponibles pour l'import et la gestion des incidents dans l'application QR Building Registry.

## import_incident.py

Importe un incident depuis un fichier JSON.

### Usage

```bash
python -m src.cli.import_incident <chemin_fichier_json> [--output <dossier_sortie>]
```

### Arguments

| Argument | Description | Obligatoire |
|----------|-------------|------------|
| `chemin_fichier_json` | Chemin vers le fichier JSON contenant les données de l'incident | Oui |
| `--output` | Dossier de sortie pour le QR code | Non |

### Format du fichier JSON d'entrée

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

OU en utilisant `BUILDING_QR_CODE` au lieu de `BUILDING_ID` :

```json
{
  "BUILDING_QR_CODE": "QR5050332870",
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

Soit le champ `BUILDING_ID`, soit le champ `BUILDING_QR_CODE` doit être fourni (mais pas les deux à la fois). Le champ `INCIDENT_INFORMATION` est obligatoire. Dans `INCIDENT_INFORMATION`, les champs `zone`, `etage`, `categorie` et `type` sont obligatoires.

### Codes de retour

| Code | Description |
|------|-------------|
| 0 | Succès |
| 1 | Fichier JSON introuvable ou invalide |
| 2 | Données invalides (validation échouée) |
| 3 | Bâtiment associé introuvable |
| 10 | Erreur inattendue |

## find_incident.py

Recherche un incident par son identifiant QR.

### Usage

```bash
python -m src.cli.find_incident <qr_code_number> [--format json|text]
```

### Arguments

| Argument | Description | Obligatoire |
|----------|-------------|------------|
| `qr_code_number` | Identifiant QR de l'incident à rechercher | Oui |
| `--format` | Format de sortie (json ou text) | Non (défaut: text) |

### Codes de retour

| Code | Description |
|------|-------------|
| 0 | Succès |
| 1 | Incident introuvable |
| 10 | Erreur inattendue |

## generate_incident_qr.py

Génère un QR code pour un incident existant.

### Usage

```bash
python -m src.cli.generate_incident_qr (--id <id_incident> | --qr <qr_code_number>) [--output <dossier_sortie>] [--force]
```

### Arguments

| Argument | Description | Obligatoire |
|----------|-------------|------------|
| `--id` | ID de l'incident | Un des deux (--id ou --qr) |
| `--qr` | Identifiant QR de l'incident | Un des deux (--id ou --qr) |
| `--output` | Dossier de sortie pour le QR code | Non |
| `--force` | Force la régénération même si le fichier existe déjà | Non |

### Codes de retour

| Code | Description |
|------|-------------|
| 0 | Succès |
| 1 | Incident introuvable |
| 10 | Erreur inattendue |
