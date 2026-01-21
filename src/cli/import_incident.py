#!/usr/bin/env python3
"""
Script CLI pour importer un incident depuis un fichier JSON.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, Any

from src.db.incident_dao import IncidentDAO, BuildingNotFoundException
from src.models.incident import Incident
from src.utils.validators import validate_json_file
from src.utils.schemas.incident_schema import INCIDENT_SCHEMA
from src.qr.generator import QRCodeGenerator

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
    parser = argparse.ArgumentParser(description="Importer un incident depuis un fichier JSON")
    parser.add_argument("json_file", help="Chemin vers le fichier JSON contenant les données de l'incident")
    parser.add_argument("--output", help="Dossier de sortie pour le QR code")
    
    return parser.parse_args()


def import_incident(json_file: str, output_dir: str = None) -> Dict[str, Any]:
    """
    Importe un incident depuis un fichier JSON.

    Args:
        json_file: Chemin vers le fichier JSON.
        output_dir: Dossier de sortie pour le QR code.

    Returns:
        Dictionnaire contenant les informations sur l'incident importé.
        
    Raises:
        FileNotFoundError: Si le fichier JSON n'existe pas.
        ValueError: Si les données JSON sont invalides.
        BuildingNotFoundException: Si le bâtiment associé n'existe pas.
    """
    # Valider et charger le fichier JSON
    data = validate_json_file(json_file, schema=INCIDENT_SCHEMA)
    
    # Créer l'objet Incident
    try:
        incident = Incident.from_json(data)
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'incident: {str(e)}")
        raise ValueError(f"Données d'incident invalides: {str(e)}")
    
    # Enregistrer l'incident dans la base de données
    dao = IncidentDAO()
    try:
        incident = dao.create_incident(incident)
    except BuildingNotFoundException as e:
        logger.error(f"Erreur lors de la création de l'incident: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'incident: {str(e)}")
        raise ValueError(f"Impossible de créer l'incident: {str(e)}")
    
    # Générer le QR code
    qr_generator = QRCodeGenerator()
    try:
        success, qr_path = qr_generator.generate_qr_code(incident.qr_code_number, output_dir)
        if not success:
            logger.warning(f"Impossible de générer le QR code pour l'incident {incident.id}")
    except Exception as e:
        logger.error(f"Erreur lors de la génération du QR code: {str(e)}")
        # Ne pas lever d'exception ici, l'incident a déjà été créé
    
    # Retourner les informations sur l'incident importé
    return {
        "id": incident.id,
        "building_id": incident.building_id,
        "qr_code_number": incident.qr_code_number,
        "qr_code_path": qr_path if success else None
    }


def main():
    """
    Point d'entrée principal du script.
    """
    args = parse_arguments()
    
    try:
        result = import_incident(args.json_file, args.output)
        
        print("Incident importé avec succès.")
        print(f"ID: {result['id']}")
        print(f"Building ID: {result['building_id']}")
        print(f"QR_CODE_NUMBER: {result['qr_code_number']}")
        
        if result['qr_code_path']:
            print(f"QR code généré: {result['qr_code_path']}")
        else:
            print("Attention: Le QR code n'a pas pu être généré.")
            
    except FileNotFoundError as e:
        logger.error(f"Erreur lors de l'importation: {str(e)}")
        print(f"Erreur: {str(e)}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Erreur lors de l'importation: {str(e)}")
        print(f"Erreur: {str(e)}")
        sys.exit(2)
    except BuildingNotFoundException as e:
        logger.error(f"Erreur lors de l'importation: {str(e)}")
        print(f"Erreur: {str(e)}")
        sys.exit(3)
    except Exception as e:
        logger.error(f"Erreur inattendue: {str(e)}")
        print(f"Erreur inattendue: {str(e)}")
        sys.exit(10)


if __name__ == "__main__":
    main()
