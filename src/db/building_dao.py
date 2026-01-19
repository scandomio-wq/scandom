"""
Module d'accès aux données pour les immeubles dans l'application QR Building Registry.
"""

import logging
import random
import string
from typing import Optional, List, Dict, Any

import psycopg2
from psycopg2.errors import UniqueViolation

from src.db.connection import get_db_connection
from src.models.building import Building
from src.utils.config import get_config

# Configuration du logging
logger = logging.getLogger(__name__)


class OperationNotAllowedException(Exception):
    """Exception levée lorsqu'une opération non autorisée est tentée."""
    pass


class BuildingDAO:
    """Classe d'accès aux données pour les immeubles."""

    def __init__(self):
        """Initialise l'accès aux données pour les immeubles."""
        self.db = get_db_connection()
        self.config = get_config()
    
    def generate_qr_code_number(self) -> str:
        """
        Génère un identifiant QR_CODE_NUMBER unique.

        Returns:
            Identifiant QR_CODE_NUMBER unique.
            
        Raises:
            RuntimeError: Si la génération échoue après plusieurs tentatives.
        """
        prefix = self.config.get('application', 'qr_code_prefix', fallback='QR')
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
        query = "SELECT 1 FROM t_building WHERE qr_code_number = %s"
        
        try:
            result = self.db.execute_query(query, (qr_code_number,), fetch_one=True)
            return result is not None
        except psycopg2.Error as e:
            logger.error(f"Erreur lors de la vérification de l'identifiant QR: {str(e)}")
            return False
    
    def create_building(self, building: Building) -> Building:
        """
        Crée un nouvel immeuble dans la base de données.

        Args:
            building: Objet Building à créer.

        Returns:
            Objet Building créé avec ID, QR_CODE_NUMBER et CREATION_DATE générés.
            
        Raises:
            psycopg2.Error: Si l'insertion échoue.
            UniqueViolation: Si l'identifiant QR existe déjà.
        """
        # Générer un QR_CODE_NUMBER si non fourni
        if not building.qr_code_number:
            building.qr_code_number = self.generate_qr_code_number()
        
        query = """
            INSERT INTO t_building (location, email_gestionnaire, notes, qr_code_number)
            VALUES (%s, %s, %s, %s)
            RETURNING id, creation_date
        """
        
        params = (
            building.location,
            building.email_gestionnaire,
            building.notes,
            building.qr_code_number
        )
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            
            if result:
                building.id = result["id"]
                building.creation_date = result["creation_date"]
                
                logger.info(f"Immeuble créé avec succès: ID={building.id}, QR={building.qr_code_number}")
                return building
            else:
                logger.error("Erreur lors de la création de l'immeuble: aucun ID retourné.")
                raise RuntimeError("Erreur lors de la création de l'immeuble: aucun ID retourné.")
                
        except UniqueViolation:
            logger.error(f"L'identifiant QR '{building.qr_code_number}' existe déjà.")
            raise
        except psycopg2.Error as e:
            logger.error(f"Erreur lors de la création de l'immeuble: {str(e)}")
            raise
    
    def get_building_by_id(self, building_id: int) -> Optional[Building]:
        """
        Récupère un immeuble par son ID.

        Args:
            building_id: ID de l'immeuble à récupérer.

        Returns:
            Objet Building correspondant ou None si non trouvé.
        """
        query = """
            SELECT id, creation_date, location, email_gestionnaire, notes, qr_code_number
            FROM t_building
            WHERE id = %s
        """
        
        try:
            result = self.db.execute_query(query, (building_id,), fetch_one=True)
            
            if result:
                return Building.from_db_row(result)
            else:
                logger.info(f"Aucun immeuble trouvé avec l'ID {building_id}.")
                return None
                
        except psycopg2.Error as e:
            logger.error(f"Erreur lors de la récupération de l'immeuble: {str(e)}")
            raise
    
    def get_building_by_qr_code(self, qr_code_number: str) -> Optional[Building]:
        """
        Récupère un immeuble par son identifiant QR.

        Args:
            qr_code_number: Identifiant QR de l'immeuble à récupérer.

        Returns:
            Objet Building correspondant ou None si non trouvé.
        """
        query = """
            SELECT id, creation_date, location, email_gestionnaire, notes, qr_code_number
            FROM t_building
            WHERE qr_code_number = %s
        """
        
        try:
            result = self.db.execute_query(query, (qr_code_number,), fetch_one=True)
            
            if result:
                return Building.from_db_row(result)
            else:
                logger.info(f"Aucun immeuble trouvé avec l'identifiant QR {qr_code_number}.")
                return None
                
        except psycopg2.Error as e:
            logger.error(f"Erreur lors de la récupération de l'immeuble: {str(e)}")
            raise
    
    def update_building(self, building_id: int, data: Dict[str, Any]) -> None:
        """
        Cette méthode lève toujours une exception car la modification des immeubles est interdite.

        Args:
            building_id: ID de l'immeuble à mettre à jour.
            data: Données à mettre à jour.

        Raises:
            OperationNotAllowedException: Toujours levée car l'opération est interdite.
        """
        logger.warning(f"Tentative de modification de l'immeuble {building_id} bloquée.")
        raise OperationNotAllowedException(
            "La modification des informations d'un bâtiment après création n'est pas autorisée."
        )
    
    def delete_building(self, building_id: int) -> None:
        """
        Cette méthode lève toujours une exception car la suppression des immeubles est interdite.

        Args:
            building_id: ID de l'immeuble à supprimer.

        Raises:
            OperationNotAllowedException: Toujours levée car l'opération est interdite.
        """
        logger.warning(f"Tentative de suppression de l'immeuble {building_id} bloquée.")
        raise OperationNotAllowedException(
            "La suppression d'un bâtiment n'est pas autorisée."
        )
    
    def list_buildings(self, limit: int = 100, offset: int = 0) -> List[Building]:
        """
        Liste les immeubles avec pagination.

        Args:
            limit: Nombre maximum d'immeubles à retourner.
            offset: Nombre d'immeubles à sauter.

        Returns:
            Liste d'objets Building.
        """
        query = """
            SELECT id, creation_date, location, email_gestionnaire, notes, qr_code_number
            FROM t_building
            ORDER BY id
            LIMIT %s OFFSET %s
        """
        
        try:
            results = self.db.execute_query(query, (limit, offset), fetch_all=True)
            
            buildings = []
            for row in results:
                buildings.append(Building.from_db_row(row))
            
            return buildings
                
        except psycopg2.Error as e:
            logger.error(f"Erreur lors de la récupération des immeubles: {str(e)}")
            raise
