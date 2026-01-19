#!/usr/bin/env python3
"""
Script d'importation d'un bâtiment depuis un fichier JSON.
"""

import argparse
import json
import logging
import os
import signal
import sys
from typing import Dict, Any, Optional

from src.db.building_dao import BuildingDAO
from src.models.building import Building
from src.qr.generator import QRCodeGenerator
from src.utils.validators import validate_json_file, validate_building_data

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_signal_handlers():
    """Configure les gestionnaires de signaux pour une interruption propre."""
    def signal_handler(sig, frame):
        logger.info("Interruption détectée. Nettoyage et sortie...")
        sys.exit(1)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def parse_arguments():
    """
    Parse les arguments de la ligne de commande.
    
    Returns:
        Arguments parsés.
    """
    parser = argparse.ArgumentParser(description="Importe un bâtiment depuis un fichier JSON.")
    
    parser.add_argument(
        "chemin_fichier_json",
        help="Chemin vers le fichier JSON contenant les informations du bâtiment"
    )
    
    parser.add_argument(
        "--output",
        help="Dossier de sortie pour le QR code (par défaut: ./qr_codes)",
        default=None
    )
    
    return parser.parse_args()


def import_building(json_file: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Importe un bâtiment depuis un fichier JSON et génère un QR code.
    
    Args:
        json_file: Chemin vers le fichier JSON.
        output_dir: Dossier de sortie pour le QR code.
    
    Returns:
        Dictionnaire contenant les informations du bâtiment importé.
        
    Raises:
        FileNotFoundError: Si le fichier JSON n'existe pas.
        ValueError: Si les données sont invalides.
        Exception: Pour toute autre erreur.
    """
    try:
        # Valider le fichier JSON
        data = validate_json_file(json_file)
        
        # Valider les données du bâtiment
        errors = validate_building_data(data)
        if errors:
            error_message = "Erreurs de validation:\n" + "\n".join(f"- {error}" for error in errors)
            raise ValueError(error_message)
        
        # Créer l'objet Building
        building = Building.from_json(data)
        
        # Créer le bâtiment dans la base de données
        dao = BuildingDAO()
        building = dao.create_building(building)
        
        # Générer le QR code
        qr_generator = QRCodeGenerator()
        success, qr_file_path = qr_generator.generate_qr_code(building.qr_code_number, output_dir)
        
        if not success:
            logger.warning("Le QR code n'a pas pu être généré.")
        
        # Préparer la réponse
        result = building.to_dict()
        result["QR_FILE_PATH"] = qr_file_path
        
        return result
        
    except FileNotFoundError as e:
        logger.error(f"Fichier introuvable: {str(e)}")
        raise
    except ValueError as e:
        logger.error(f"Données invalides: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'importation: {str(e)}")
        raise


def main():
    """Fonction principale."""
    try:
        # Configurer les gestionnaires de signaux
        setup_signal_handlers()
        
        # Parser les arguments
        args = parse_arguments()
        
        # Importer le bâtiment
        result = import_building(args.chemin_fichier_json, args.output)
        
        # Afficher le résultat
        print("Bâtiment importé avec succès.")
        print(f"ID: {result['ID']}")
        print(f"QR_CODE_NUMBER: {result['QR_CODE_NUMBER']}")
        print(f"QR code généré: {result['QR_FILE_PATH']}")
        
        sys.exit(0)
        
    except FileNotFoundError as e:
        print(f"Erreur: {str(e)}")
        sys.exit(2)
    except ValueError as e:
        print(f"Erreur: {str(e)}")
        sys.exit(3)
    except Exception as e:
        print(f"Erreur: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
