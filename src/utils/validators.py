"""
Module de validation des données pour l'application QR Building Registry.
"""

import re
import json
import os
from typing import Dict, Any, Union, List, Optional

import jsonschema
from jsonschema import ValidationError

from src.utils.config import get_config
from src.utils.schemas.incident_schema import INCIDENT_SCHEMA


# Schéma de validation pour les données d'un immeuble
BUILDING_SCHEMA = {
    "type": "object",
    "required": ["LOCATION"],
    "properties": {
        "LOCATION": {"type": "string", "minLength": 3, "maxLength": 255},
        "EMAIL_GESTIONNAIRE": {"type": "string", "format": "email", "maxLength": 100},
        "NOTES": {"type": "string"}
    },
    "additionalProperties": False
}


def validate_email(email: str) -> bool:
    """
    Valide un format d'email selon RFC 5322.

    Args:
        email: Adresse email à valider.

    Returns:
        True si l'email est valide, False sinon.
    """
    if not email:
        return True  # Email peut être vide/null
    
    # Expression régulière simplifiée pour la validation d'email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_qr_code_number(qr_code: str, prefix: str = None) -> bool:
    """
    Valide un identifiant QR_CODE_NUMBER.

    Args:
        qr_code: Identifiant QR à valider.
        prefix: Préfixe attendu ("QR" pour les bâtiments, "IN" pour les incidents).
               Si None, accepte les deux formats.

    Returns:
        True si l'identifiant QR est valide, False sinon.
    """
    if not qr_code:
        return False  # QR_CODE_NUMBER ne peut pas être vide
    
    if prefix == "QR":
        # Format: "QR" suivi de chiffres
        pattern = r'^QR\d+$'
    elif prefix == "IN":
        # Format: "IN" suivi de chiffres
        pattern = r'^IN\d+$'
    else:
        # Accepte les deux formats
        pattern = r'^(QR|IN)\d+$'
    
    return bool(re.match(pattern, qr_code))


def validate_json_file(file_path: str, schema=None) -> Dict[str, Any]:
    """
    Valide un fichier JSON selon le schéma défini.

    Args:
        file_path: Chemin vers le fichier JSON à valider.
        schema: Schéma de validation à utiliser. Si None, tente de détecter automatiquement.

    Returns:
        Dictionnaire contenant les données JSON validées.

    Raises:
        FileNotFoundError: Si le fichier n'existe pas.
        ValueError: Si le fichier est vide ou trop volumineux.
        json.JSONDecodeError: Si le fichier n'est pas un JSON valide.
        ValidationError: Si les données ne correspondent pas au schéma.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Le fichier '{file_path}' n'existe pas.")
    
    # Vérifier la taille du fichier
    file_size = os.path.getsize(file_path)
    max_size = int(get_config().get('application', 'max_json_size', fallback=1048576))    
    if file_size == 0:
        raise ValueError(f"Le fichier '{file_path}' est vide.")
    
    if file_size > max_size:
        raise ValueError(
            f"Le fichier '{file_path}' est trop volumineux ({file_size} octets). "
            f"La taille maximale autorisée est de {max_size} octets."
        )
    
    # Charger et valider le JSON
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Le fichier '{file_path}' n'est pas un JSON valide: {str(e)}", e.doc, e.pos)
    
    # Déterminer le schéma à utiliser
    if schema is None:
        # Détection automatique du type de données
        if "BUILDING_ID" in data and "INCIDENT_INFORMATION" in data:
            schema = INCIDENT_SCHEMA
        else:
            schema = BUILDING_SCHEMA
    
    # Valider selon le schéma
    try:
        jsonschema.validate(instance=data, schema=schema)
    except ValidationError as e:
        raise ValidationError(f"Validation échouée: {str(e)}")
    
    # Validation supplémentaire pour les emails
    if schema == BUILDING_SCHEMA and "EMAIL_GESTIONNAIRE" in data and data["EMAIL_GESTIONNAIRE"]:
        if not validate_email(data["EMAIL_GESTIONNAIRE"]):
            raise ValidationError("Le format de l'email du gestionnaire est invalide.")
    elif schema == INCIDENT_SCHEMA and "REPORTER_EMAIL" in data and data["REPORTER_EMAIL"]:
        if not validate_email(data["REPORTER_EMAIL"]):
            raise ValidationError("Le format de l'email du déclarant est invalide.")
    
    return data


def validate_building_data(data: Dict[str, Any]) -> List[str]:
    """
    Valide les données d'un immeuble.

    Args:
        data: Dictionnaire contenant les données à valider.

    Returns:
        Liste des erreurs de validation (vide si aucune erreur).
    """
    errors = []
    
    # Vérifier les champs obligatoires
    if "LOCATION" not in data or not data["LOCATION"]:
        errors.append("Le champ LOCATION est obligatoire.")
    elif len(data["LOCATION"]) > 255:
        errors.append("Le champ LOCATION ne doit pas dépasser 255 caractères.")
    
    # Vérifier l'email si présent
    if "EMAIL_GESTIONNAIRE" in data and data["EMAIL_GESTIONNAIRE"]:
        if not validate_email(data["EMAIL_GESTIONNAIRE"]):
            errors.append("Le format de l'email du gestionnaire est invalide.")
        elif len(data["EMAIL_GESTIONNAIRE"]) > 100:
            errors.append("L'email du gestionnaire ne doit pas dépasser 100 caractères.")
    
    # Vérifier QR_CODE_NUMBER si présent (normalement généré par le système)
    if "QR_CODE_NUMBER" in data and data["QR_CODE_NUMBER"]:
        if not validate_qr_code_number(data["QR_CODE_NUMBER"]):
            errors.append("Le format de QR_CODE_NUMBER est invalide (doit commencer par 'QR' suivi de chiffres).")
    
    return errors


def sanitize_input(text: str) -> str:
    """
    Nettoie une chaîne de caractères en supprimant les caractères de contrôle.

    Args:
        text: Texte à nettoyer.

    Returns:
        Texte nettoyé.
    """
    if not text:
        return ""
    
    # Supprimer les caractères de contrôle sauf les sauts de ligne et tabulations
    return re.sub(r'[^\x20-\x7E\x0A\x0D\x09]', '', text)
