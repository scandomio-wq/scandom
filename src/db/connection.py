"""
Module de connexion à la base de données PostgreSQL pour l'application QR Building Registry.
"""

import logging
import time
from typing import Optional, Dict, Any, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor

from src.utils.config import get_config

# Configuration du logging
logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Classe de gestion de la connexion à la base de données PostgreSQL."""

    def __init__(self, config: Optional[Dict[str, str]] = None):
        """
        Initialise la connexion à la base de données.

        Args:
            config: Dictionnaire contenant les paramètres de connexion.
                   Si None, utilise la configuration par défaut.
        """
        self.config = config or get_config().get_postgresql_config()
        self.connection = None
        self.max_retries = 3
        self.retry_delay = 1  # secondes
    
    def connect(self) -> None:
        """
        Établit une connexion à la base de données PostgreSQL.
        
        Raises:
            psycopg2.Error: Si la connexion échoue après les tentatives de reconnexion.
        """
        if self.connection is not None and not self.connection.closed:
            return
        
        retries = 0
        last_error = None
        
        while retries < self.max_retries:
            try:
                self.connection = psycopg2.connect(
                    host=self.config['host'],
                    port=self.config['port'],
                    database=self.config['database'],
                    user=self.config['user'],
                    password=self.config['password']
                )
                logger.info("Connexion à la base de données établie avec succès.")
                return
            except psycopg2.Error as e:
                last_error = e
                retries += 1
                logger.warning(f"Tentative {retries}/{self.max_retries} de connexion échouée: {str(e)}")
                
                if retries < self.max_retries:
                    time.sleep(self.retry_delay * retries)  # Délai exponentiel
        
        # Si on arrive ici, toutes les tentatives ont échoué
        logger.error(f"Impossible de se connecter à la base de données après {self.max_retries} tentatives.")
        raise last_error
    
    def disconnect(self) -> None:
        """Ferme la connexion à la base de données."""
        if self.connection is not None and not self.connection.closed:
            self.connection.close()
            self.connection = None
            logger.info("Connexion à la base de données fermée.")
    
    def execute_query(self, query: str, params: Optional[Tuple] = None, 
                     fetch_one: bool = False, fetch_all: bool = False) -> Optional[Any]:
        """
        Exécute une requête SQL et retourne éventuellement des résultats.

        Args:
            query: Requête SQL à exécuter.
            params: Paramètres de la requête (pour les requêtes préparées).
            fetch_one: Si True, retourne un seul résultat.
            fetch_all: Si True, retourne tous les résultats.

        Returns:
            Résultat(s) de la requête ou None.
            
        Raises:
            psycopg2.Error: Si l'exécution de la requête échoue.
        """
        if self.connection is None or self.connection.closed:
            self.connect()
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                
                result = None
                if fetch_one:
                    result = cursor.fetchone()
                elif fetch_all:
                    result = cursor.fetchall()
                
                # Valider la transaction dans tous les cas
                self.connection.commit()
                return result
                    
        except psycopg2.Error as e:
            self.connection.rollback()
            logger.error(f"Erreur lors de l'exécution de la requête: {str(e)}")
            raise
    
    def __enter__(self):
        """Permet l'utilisation avec le contexte 'with'."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ferme la connexion à la sortie du contexte 'with'."""
        self.disconnect()


# Instance globale de connexion
_db_connection = None


def get_db_connection() -> DatabaseConnection:
    """
    Récupère l'instance globale de connexion à la base de données ou en crée une nouvelle.

    Returns:
        Instance de la classe DatabaseConnection.
    """
    global _db_connection
    
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    
    return _db_connection
