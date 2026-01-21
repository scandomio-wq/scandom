"""
Module d'accès aux données pour les incidents dans l'application QR Building Registry.
"""

import logging
import random
import string
import json
from typing import Optional, List, Dict, Any

import psycopg2
from psycopg2.errors import UniqueViolation

from src.db.connection import get_db_connection
from src.db.building_dao import BuildingDAO
from src.models.incident import Incident
from src.utils.config import get_config

# Configuration du logging
logger = logging.getLogger(__name__)


class IncidentNotFoundException(Exception):
    """Exception levée lorsqu'un incident n'est pas trouvé."""
    pass


class BuildingNotFoundException(Exception):
    """Exception levée lorsqu'un bâtiment n'est pas trouvé."""
    pass


class IncidentDAO:
    """Classe d'accès aux données pour les incidents."""

    def __init__(self):
        """Initialise l'accès aux données pour les incidents."""
        self.db = get_db_connection()
        self.config = get_config()
        self.building_dao = BuildingDAO()
    
    def generate_qr_code_number(self) -> str:
        """
        Génère un identifiant QR_CODE_NUMBER unique pour un incident.

        Returns:
            Identifiant QR_CODE_NUMBER unique.
            
        Raises:
            RuntimeError: Si la génération échoue après plusieurs tentatives.
        """
        prefix = "IN"  # Préfixe pour les incidents
        max_attempts = 10
        
        for attempt in range(max_attempts):
            # Générer un nombre aléatoire à 10 chiffres
            random_digits = ''.join(random.choices(string.digits, k=10))
            qr_code_number = f"{prefix}{random_digits}"
            
            # Vérifier si l'identifiant existe déjà
            if not self.qr_code_number_exists(qr_code_number):
                return qr_code_number
        
        # Si on arrive ici, impossible de générer un identifiant unique
        logger.error(f"Impossible de générer un QR_CODE_NUMBER unique après {max_attempts} tentatives.")
        raise RuntimeError(f"Impossible de générer un QR_CODE_NUMBER unique après {max_attempts} tentatives.")
    
    def qr_code_number_exists(self, qr_code_number: str) -> bool:
        """
        Vérifie si un identifiant QR_CODE_NUMBER existe déjà.

        Args:
            qr_code_number: Identifiant QR à vérifier.

        Returns:
            True si l'identifiant existe déjà, False sinon.
        """
        query = "SELECT 1 FROM t_incident WHERE qr_code_number = %s"
        
        try:
            result = self.db.execute_query(query, (qr_code_number,), fetch_one=True)
            return result is not None
        except psycopg2.Error as e:
            logger.error(f"Erreur lors de la vérification de l'identifiant QR: {str(e)}")
            return False
    
    def create_incident(self, incident: Incident) -> Incident:
        """
        Crée un nouvel incident dans la base de données.

        Args:
            incident: Objet Incident à créer.

        Returns:
            Objet Incident créé avec ID, QR_CODE_NUMBER et CREATION_DATE générés.
            
        Raises:
            BuildingNotFoundException: Si le bâtiment associé n'existe pas.
            psycopg2.Error: Si l'insertion échoue.
            UniqueViolation: Si l'identifiant QR existe déjà.
        """
        # Si nous avons un building_qr_code mais pas de building_id, nous devons le récupérer
        if incident.building_qr_code is not None and incident.building_id is None:
            building = self.building_dao.get_building_by_qr_code(incident.building_qr_code)
            if not building:
                logger.error(f"Le bâtiment avec le QR code {incident.building_qr_code} n'existe pas.")
                raise BuildingNotFoundException(f"Le bâtiment avec le QR code {incident.building_qr_code} n'existe pas.")
            incident.building_id = building.id
        
        # Vérifier si le bâtiment existe avec l'ID
        if not self.building_dao.get_building_by_id(incident.building_id):
            logger.error(f"Le bâtiment avec l'ID {incident.building_id} n'existe pas.")
            raise BuildingNotFoundException(f"Le bâtiment avec l'ID {incident.building_id} n'existe pas.")
        
        # Générer un QR_CODE_NUMBER si non fourni
        if not incident.qr_code_number:
            incident.qr_code_number = self.generate_qr_code_number()
        
        query = """
            INSERT INTO t_incident (building_id, reporter_phone, reporter_email, incident_information, qr_code_number)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, creation_date
        """
        
        # Convertir incident_information en JSON si nécessaire
        incident_information_json = json.dumps(incident.incident_information)
        
        # Générer un QR_CODE_NUMBER si non fourni
        if not incident.qr_code_number:
            incident.qr_code_number = self.generate_qr_code_number()
        
        params = (
            incident.building_id,
            incident.reporter_phone,
            incident.reporter_email,
            incident_information_json,
            incident.qr_code_number
        )
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            
            if result:
                incident.id = result["id"]
                incident.creation_date = result["creation_date"]
                
                logger.info(f"Incident créé avec succès: ID={incident.id}, QR={incident.qr_code_number}")
                return incident
            else:
                logger.error("Erreur lors de la création de l'incident: aucun ID retourné.")
                raise RuntimeError("Erreur lors de la création de l'incident: aucun ID retourné.")
                
        except UniqueViolation:
            logger.error(f"L'identifiant QR '{incident.qr_code_number}' existe déjà.")
            raise
        except psycopg2.Error as e:
            logger.error(f"Erreur lors de la création de l'incident: {str(e)}")
            raise
    
    def get_incident_by_id(self, incident_id: int) -> Optional[Incident]:
        """
        Récupère un incident par son ID.

        Args:
            incident_id: ID de l'incident à récupérer.

        Returns:
            Objet Incident correspondant ou None si non trouvé.
        """
        query = """
            SELECT id, building_id, creation_date, reporter_phone, reporter_email, incident_information, qr_code_number
            FROM t_incident
            WHERE id = %s
        """
        
        try:
            result = self.db.execute_query(query, (incident_id,), fetch_one=True)
            
            if result:
                return Incident.from_db_row(result)
            else:
                logger.info(f"Aucun incident trouvé avec l'ID {incident_id}.")
                return None
                
        except psycopg2.Error as e:
            logger.error(f"Erreur lors de la récupération de l'incident: {str(e)}")
            raise
    
    def get_incident_by_qr_code(self, qr_code_number: str) -> Optional[Incident]:
        """
        Récupère un incident par son identifiant QR.

        Args:
            qr_code_number: Identifiant QR de l'incident à récupérer.

        Returns:
            Objet Incident correspondant ou None si non trouvé.
        """
        query = """
            SELECT id, building_id, creation_date, reporter_phone, reporter_email, incident_information, qr_code_number
            FROM t_incident
            WHERE qr_code_number = %s
        """
        
        try:
            result = self.db.execute_query(query, (qr_code_number,), fetch_one=True)
            
            if result:
                return Incident.from_db_row(result)
            else:
                logger.info(f"Aucun incident trouvé avec l'identifiant QR {qr_code_number}.")
                return None
                
        except psycopg2.Error as e:
            logger.error(f"Erreur lors de la récupération de l'incident: {str(e)}")
            raise
    
    def get_incidents_by_building_id(self, building_id: int) -> List[Incident]:
        """
        Récupère tous les incidents associés à un bâtiment par son ID.

        Args:
            building_id: ID du bâtiment.

        Returns:
            Liste d'objets Incident.
        """
        query = """
            SELECT id, building_id, creation_date, reporter_phone, reporter_email, incident_information, qr_code_number
            FROM t_incident
            WHERE building_id = %s
            ORDER BY creation_date DESC
        """
        
        try:
            results = self.db.execute_query(query, (building_id,), fetch_all=True)
            
            incidents = []
            for row in results:
                incidents.append(Incident.from_db_row(row))
            
            return incidents
                
        except psycopg2.Error as e:
            logger.error(f"Erreur lors de la récupération des incidents: {str(e)}")
            raise
    
    def list_incidents(self, limit: int = 100, offset: int = 0) -> List[Incident]:
        """
        Liste les incidents avec pagination.

        Args:
            limit: Nombre maximum d'incidents à retourner.
            offset: Nombre d'incidents à sauter.

        Returns:
            Liste d'objets Incident.
        """
        query = """
            SELECT id, building_id, creation_date, reporter_phone, reporter_email, incident_information, qr_code_number
            FROM t_incident
            ORDER BY creation_date DESC
            LIMIT %s OFFSET %s
        """
        
        try:
            results = self.db.execute_query(query, (limit, offset), fetch_all=True)
            
            incidents = []
            for row in results:
                incidents.append(Incident.from_db_row(row))
            
            return incidents
                
        except psycopg2.Error as e:
            logger.error(f"Erreur lors de la récupération des incidents: {str(e)}")
            raise
            
    def get_incidents_by_building_qr_code(self, building_qr_code: str) -> List[Incident]:
        """
        Récupère tous les incidents associés à un bâtiment par son QR code.

        Args:
            building_qr_code: QR code du bâtiment.

        Returns:
            Liste d'objets Incident.
        """
        # Récupérer d'abord le building_id à partir du QR code
        building = self.building_dao.get_building_by_qr_code(building_qr_code)
        if not building:
            logger.error(f"Le bâtiment avec le QR code {building_qr_code} n'existe pas.")
            raise BuildingNotFoundException(f"Le bâtiment avec le QR code {building_qr_code} n'existe pas.")
        
        # Ensuite, récupérer les incidents par building_id
        return self.get_incidents_by_building_id(building.id)
