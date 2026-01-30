#!/usr/bin/env python3
"""
Script pour exécuter une migration SQL en utilisant la connexion à la base de données configurée.
"""

import argparse
import logging
import os
import sys

from src.db.connection import get_db_connection

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """
    Parse les arguments de la ligne de commande.
    
    Returns:
        Arguments parsés.
    """
    parser = argparse.ArgumentParser(description="Exécute un fichier de migration SQL.")
    
    parser.add_argument(
        "chemin_fichier_sql",
        help="Chemin vers le fichier SQL à exécuter"
    )
    
    return parser.parse_args()


def execute_migration(sql_file_path):
    """
    Exécute un fichier de migration SQL.
    
    Args:
        sql_file_path: Chemin vers le fichier SQL.
        
    Returns:
        bool: True si l'exécution a réussi, False sinon.
    """
    if not os.path.exists(sql_file_path):
        logger.error(f"Le fichier {sql_file_path} n'existe pas.")
        return False
    
    try:
        # Lire le contenu du fichier SQL
        with open(sql_file_path, 'r') as f:
            sql_content = f.read()
        
        # Exécuter le SQL
        db_connection = get_db_connection()
        db_connection.execute_query(sql_content)
        
        logger.info(f"Migration {os.path.basename(sql_file_path)} exécutée avec succès.")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de la migration: {str(e)}")
        return False


def main():
    """Fonction principale."""
    try:
        # Parser les arguments
        args = parse_arguments()
        
        # Exécuter la migration
        success = execute_migration(args.chemin_fichier_sql)
        
        if success:
            logger.info("Migration terminée avec succès.")
            sys.exit(0)
        else:
            logger.error("Échec de la migration.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Erreur: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
