#!/usr/bin/env python3
"""
Script pour exécuter les migrations SQL pour l'intégration WhatsApp.

Ce script utilise la connexion à la base de données configurée dans l'application
pour exécuter les scripts de migration SQL.
"""

import os
import sys
import logging
from typing import List

from src.db.connection import get_db_connection

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_migration_file(file_path: str) -> bool:
    """
    Exécute un script de migration SQL.
    
    Args:
        file_path: Chemin vers le fichier de migration SQL.
        
    Returns:
        bool: True si la migration a réussi, False sinon.
    """
    logger.info(f"Exécution de la migration: {file_path}")
    
    try:
        # Lire le contenu du fichier SQL
        with open(file_path, 'r') as f:
            sql_script = f.read()
        
        # Obtenir une connexion à la base de données
        db_connection = get_db_connection()
        
        # Exécuter le script SQL
        db_connection.execute_query(sql_script)
        
        logger.info(f"Migration réussie: {file_path}")
        return True
    
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de la migration {file_path}: {str(e)}")
        return False

def run_migrations(migration_dir: str = None) -> None:
    """
    Exécute tous les scripts de migration SQL dans le répertoire spécifié.
    
    Args:
        migration_dir: Répertoire contenant les scripts de migration SQL.
                      Si None, utilise le répertoire 'migrations' par défaut.
    """
    # Déterminer le répertoire des migrations
    if migration_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        migration_dir = os.path.join(base_dir, 'migrations')
    
    # Vérifier que le répertoire existe
    if not os.path.exists(migration_dir):
        logger.error(f"Répertoire de migrations non trouvé: {migration_dir}")
        sys.exit(1)
    
    # Lister les fichiers de migration SQL
    migration_files = [f for f in os.listdir(migration_dir) if f.endswith('.sql')]
    migration_files.sort()  # Trier par ordre alphabétique
    
    if not migration_files:
        logger.warning(f"Aucun fichier de migration SQL trouvé dans {migration_dir}")
        sys.exit(0)
    
    logger.info(f"Fichiers de migration trouvés: {len(migration_files)}")
    
    # Exécuter chaque migration
    success_count = 0
    for file_name in migration_files:
        file_path = os.path.join(migration_dir, file_name)
        if run_migration_file(file_path):
            success_count += 1
    
    # Afficher le résumé
    logger.info(f"Migrations terminées: {success_count}/{len(migration_files)} réussies")
    
    if success_count < len(migration_files):
        logger.warning("Certaines migrations ont échoué. Vérifiez les logs pour plus de détails.")
        sys.exit(1)

if __name__ == '__main__':
    logger.info("Démarrage de l'exécution des migrations...")
    run_migrations()
    logger.info("Exécution des migrations terminée.")
