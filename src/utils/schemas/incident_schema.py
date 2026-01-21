"""
Module définissant les schémas de validation pour les incidents.
"""

# Schéma de validation pour les informations d'incident
INCIDENT_INFORMATION_SCHEMA = {
    "type": "object",
    "required": ["zone", "etage", "categorie", "type"],
    "properties": {
        "zone": {"type": "string", "minLength": 1, "maxLength": 100},
        "etage": {"type": "string", "minLength": 1, "maxLength": 20},
        "categorie": {"type": "string", "minLength": 1, "maxLength": 50},
        "type": {"type": "string", "minLength": 1, "maxLength": 50},
        "informations_supplementaires": {"type": "string"}
    },
    "additionalProperties": False
}

# Schéma de validation pour un incident avec BUILDING_QR_CODE
INCIDENT_SCHEMA_QR = {
    "type": "object",
    "required": ["BUILDING_QR_CODE", "INCIDENT_INFORMATION"],
    "properties": {
        "BUILDING_QR_CODE": {"type": "string", "pattern": "^QR\\d+$"},
        "REPORTER_PHONE": {"type": "string", "maxLength": 20},
        "REPORTER_EMAIL": {"type": "string", "format": "email", "maxLength": 100},
        "INCIDENT_INFORMATION": INCIDENT_INFORMATION_SCHEMA
    },
    "additionalProperties": False
}

# Schéma de validation pour un incident avec BUILDING_ID
INCIDENT_SCHEMA_ID = {
    "type": "object",
    "required": ["BUILDING_ID", "INCIDENT_INFORMATION"],
    "properties": {
        "BUILDING_ID": {"type": "integer", "minimum": 1},
        "REPORTER_PHONE": {"type": "string", "maxLength": 20},
        "REPORTER_EMAIL": {"type": "string", "format": "email", "maxLength": 100},
        "INCIDENT_INFORMATION": INCIDENT_INFORMATION_SCHEMA
    },
    "additionalProperties": False
}

# Schéma principal qui accepte l'un ou l'autre
INCIDENT_SCHEMA = {
    "oneOf": [
        INCIDENT_SCHEMA_QR,
        INCIDENT_SCHEMA_ID
    ]
}
