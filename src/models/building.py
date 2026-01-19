"""
Modèle de données pour les immeubles dans l'application QR Building Registry.
"""

from datetime import datetime
from typing import Dict, Any, Optional


class Building:
    """Classe représentant un immeuble."""

    def __init__(self, location: str, email_gestionnaire: Optional[str] = None,
                 notes: Optional[str] = None, qr_code_number: Optional[str] = None,
                 id: Optional[int] = None, creation_date: Optional[datetime] = None):
        """
        Initialise un nouvel objet Building.

        Args:
            location: Adresse ou emplacement de l'immeuble.
            email_gestionnaire: Email du gestionnaire de l'immeuble (optionnel).
            notes: Notes ou informations supplémentaires (optionnel).
            qr_code_number: Identifiant unique utilisé dans le QR code (généré automatiquement si None).
            id: Identifiant unique de l'immeuble dans la base de données (généré automatiquement si None).
            creation_date: Date et heure de création de l'enregistrement (générée automatiquement si None).
        """
        self.id = id
        self.location = location
        self.email_gestionnaire = email_gestionnaire
        self.notes = notes
        self.qr_code_number = qr_code_number
        self.creation_date = creation_date

    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> 'Building':
        """
        Crée un objet Building à partir de données JSON.

        Args:
            json_data: Dictionnaire contenant les données de l'immeuble.

        Returns:
            Nouvel objet Building.
        """
        return cls(
            location=json_data["LOCATION"],
            email_gestionnaire=json_data.get("EMAIL_GESTIONNAIRE"),
            notes=json_data.get("NOTES")
        )

    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'Building':
        """
        Crée un objet Building à partir d'une ligne de la base de données.

        Args:
            row: Dictionnaire représentant une ligne de la table T_BUILDING.

        Returns:
            Nouvel objet Building avec toutes les données de la base.
        """
        return cls(
            id=row["id"],
            location=row["location"],
            email_gestionnaire=row["email_gestionnaire"],
            notes=row["notes"],
            qr_code_number=row["qr_code_number"],
            creation_date=row["creation_date"]
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'objet Building en dictionnaire.

        Returns:
            Dictionnaire contenant les attributs de l'immeuble.
        """
        return {
            "ID": self.id,
            "LOCATION": self.location,
            "EMAIL_GESTIONNAIRE": self.email_gestionnaire,
            "NOTES": self.notes,
            "QR_CODE_NUMBER": self.qr_code_number,
            "CREATION_DATE": self.creation_date.isoformat() if self.creation_date else None
        }

    def __str__(self) -> str:
        """
        Représentation textuelle de l'objet Building.

        Returns:
            Chaîne de caractères représentant l'immeuble.
        """
        return (f"Building(id={self.id}, location='{self.location}', "
                f"qr_code_number='{self.qr_code_number}')")

    def __repr__(self) -> str:
        """
        Représentation de l'objet Building pour le débogage.

        Returns:
            Chaîne de caractères représentant l'immeuble.
        """
        return (f"Building(id={self.id}, location='{self.location}', "
                f"email_gestionnaire='{self.email_gestionnaire}', "
                f"notes='{self.notes if self.notes else ''}', "
                f"qr_code_number='{self.qr_code_number}', "
                f"creation_date={self.creation_date})")
