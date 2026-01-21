"""
Module définissant le modèle de données pour les incidents.
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional

import jsonschema
from jsonschema import ValidationError

from src.utils.schemas.incident_schema import INCIDENT_SCHEMA, INCIDENT_SCHEMA_QR, INCIDENT_SCHEMA_ID, INCIDENT_INFORMATION_SCHEMA


class Incident:
    """Classe représentant un incident."""

    def __init__(self, incident_information: Dict[str, Any],
                 building_id: Optional[int] = None, building_qr_code: Optional[str] = None,
                 reporter_phone: Optional[str] = None, reporter_email: Optional[str] = None,
                 id: Optional[int] = None, creation_date: Optional[datetime] = None,
                 qr_code_number: Optional[str] = None):
        """
        Initialise un incident.

        Args:
            incident_information: Informations sur l'incident (zone, étage, catégorie, type, etc.).
            building_id: ID du bâtiment concerné.
            building_qr_code: QR_CODE_NUMBER du bâtiment concerné (alternative à building_id).
            reporter_phone: Numéro de téléphone du déclarant.
            reporter_email: Email du déclarant.
            id: ID de l'incident (généré automatiquement si None).
            creation_date: Date de création (générée automatiquement si None).
            qr_code_number: Identifiant QR (généré automatiquement si None).
        """
        self.id = id
        self.building_id = building_id
        self.building_qr_code = building_qr_code  # Utilisé uniquement pour la conversion
        self.incident_information = incident_information
        self.reporter_phone = reporter_phone
        self.reporter_email = reporter_email
        self.creation_date = creation_date
        self.qr_code_number = qr_code_number

    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> 'Incident':
        """
        Crée un incident à partir de données JSON.

        Args:
            json_data: Dictionnaire contenant les données JSON.

        Returns:
            Incident créé.

        Raises:
            ValidationError: Si les données ne sont pas valides.
        """
        # Valider les données selon le schéma principal (qui accepte les deux formats)
        try:
            jsonschema.validate(instance=json_data, schema=INCIDENT_SCHEMA)
        except ValidationError as e:
            raise ValidationError(f"Validation échouée: {str(e)}")
        
        # Déterminer si nous avons BUILDING_ID ou BUILDING_QR_CODE
        building_id = json_data.get('BUILDING_ID')
        building_qr_code = json_data.get('BUILDING_QR_CODE')

        # Extraire les autres données
        incident_information = json_data.get('INCIDENT_INFORMATION')
        reporter_phone = json_data.get('REPORTER_PHONE')
        reporter_email = json_data.get('REPORTER_EMAIL')

        # Créer l'incident
        return cls(
            incident_information=incident_information,
            building_id=building_id,
            building_qr_code=building_qr_code,
            reporter_phone=reporter_phone,
            reporter_email=reporter_email
        )

    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'Incident':
        """
        Crée un incident à partir d'une ligne de la base de données.

        Args:
            row: Dictionnaire contenant les données de la base de données.

        Returns:
            Incident créé.
        """
        # Convertir la chaîne JSON en dictionnaire si nécessaire
        incident_information = row.get('incident_information')
        if isinstance(incident_information, str):
            incident_information = json.loads(incident_information)

        return cls(
            id=row.get('id'),
            building_id=row.get('building_id'),
            incident_information=incident_information,
            reporter_phone=row.get('reporter_phone'),
            reporter_email=row.get('reporter_email'),
            creation_date=row.get('creation_date'),
            qr_code_number=row.get('qr_code_number')
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'incident en dictionnaire.

        Returns:
            Dictionnaire représentant l'incident.
        """
        return {
            'id': self.id,
            'building_id': self.building_id,
            'incident_information': self.incident_information,
            'reporter_phone': self.reporter_phone,
            'reporter_email': self.reporter_email,
            'creation_date': self.creation_date.isoformat() if self.creation_date else None,
            'qr_code_number': self.qr_code_number
        }

    def __str__(self) -> str:
        """
        Retourne une représentation textuelle de l'incident.

        Returns:
            Chaîne représentant l'incident.
        """
        return (f"Incident(id={self.id}, building_id={self.building_id}, "
                f"type={self.incident_information.get('type', 'N/A')}, "
                f"qr_code_number={self.qr_code_number})")
