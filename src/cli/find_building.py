#!/usr/bin/env python3
"""
Script de recherche d'un immeuble à partir de son identifiant QR.
"""

import argparse
import json
import logging
import signal
import sys
from typing import Dict, Any, Optional

from src.db.building_dao import BuildingDAO
from src.utils.validators import validate_qr_code_number

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
    parser = argparse.ArgumentParser(description="Recherche un immeuble à partir de son identifiant QR.")
    
    parser.add_argument(
        "qr_code_number",
        help="QR_CODE_NUMBER du bâtiment à rechercher"
    )
    
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Format de sortie (json ou text, par défaut: text)"
    )
    
    return parser.parse_args()


def find_building(qr_code_number: str, output_format: str = "text") -> Dict[str, Any]:
    """
    Recherche un immeuble à partir de son identifiant QR.
    
    Args:
        qr_code_number: Identifiant QR du bâtiment à rechercher.
        output_format: Format de sortie (json ou text).
    
    Returns:
        Dictionnaire contenant les informations du bâtiment et le format de sortie.
        
    Raises:
        ValueError: Si l'identifiant QR est invalide.
        FileNotFoundError: Si le bâtiment n'existe pas.
        Exception: Pour toute autre erreur.
    """
    # Valider le format de l'identifiant QR
    if not validate_qr_code_number(qr_code_number):
        raise ValueError(f"Format d'identifiant QR invalide: {qr_code_number}")
    
    try:
        # Rechercher le bâtiment
        dao = BuildingDAO()
        building = dao.get_building_by_qr_code(qr_code_number)
        
        if building is None:
            raise FileNotFoundError(f"Aucun immeuble trouvé avec l'identifiant QR {qr_code_number}.")
        
        # Préparer la réponse
        building_data = building.to_dict()
        
        return {
            "building": building_data,
            "format": output_format
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche de l'immeuble: {str(e)}")
        raise


def format_output(result: Dict[str, Any]) -> str:
    """
    Formate la sortie selon le format demandé.
    
    Args:
        result: Résultat de la recherche.
    
    Returns:
        Sortie formatée.
        
    Raises:
        ValueError: Si le format de sortie est invalide.
    """
    building = result["building"]
    output_format = result["format"]
    
    if output_format == "json":
        return json.dumps(building, indent=2)
    elif output_format == "text":
        return "\n".join([
            f"ID: {building['ID']}",
            f"LOCATION: {building['LOCATION']}",
            f"EMAIL_GESTIONNAIRE: {building['EMAIL_GESTIONNAIRE'] or 'Non spécifié'}",
            f"NOTES: {building['NOTES'] or 'Non spécifié'}",
            f"QR_CODE_NUMBER: {building['QR_CODE_NUMBER']}",
            f"CREATION_DATE: {building['CREATION_DATE']}"
        ])
    else:
        raise ValueError(f"Format de sortie invalide: {output_format}")


def main():
    """Fonction principale."""
    try:
        # Configurer les gestionnaires de signaux
        setup_signal_handlers()
        
        # Parser les arguments
        args = parse_arguments()
        
        # Rechercher le bâtiment
        result = find_building(args.qr_code_number, args.format)
        
        # Formater et afficher le résultat
        output = format_output(result)
        print(output)
        
        sys.exit(0)
        
    except ValueError as e:
        print(f"Erreur: {str(e)}")
        sys.exit(3)
    except FileNotFoundError as e:
        print(f"Erreur: {str(e)}")
        sys.exit(2)
    except Exception as e:
        print(f"Erreur: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
