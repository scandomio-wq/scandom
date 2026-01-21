#!/usr/bin/env python3
"""
Script CLI pour générer un QR code pour un incident existant.
"""

import os
import sys
import logging
import argparse

from src.db.incident_dao import IncidentDAO
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
    parser = argparse.ArgumentParser(description="Générer un QR code pour un incident existant")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--id", type=int, help="ID de l'incident")
    group.add_argument("--qr", help="Identifiant QR de l'incident")
    parser.add_argument("--output", help="Dossier de sortie pour le QR code")
    parser.add_argument("--force", action="store_true", help="Forcer la régénération même si le fichier existe déjà")
    
    return parser.parse_args()


def generate_incident_qr(incident_id: int = None, qr_code_number: str = None, 
                        output_dir: str = None, force: bool = False):
    """
    Génère un QR code pour un incident existant.

    Args:
        incident_id: ID de l'incident.
        qr_code_number: Identifiant QR de l'incident.
        output_dir: Dossier de sortie pour le QR code.
        force: Si True, force la régénération même si le fichier existe déjà.

    Returns:
        Tuple (succès, chemin du fichier).
        
    Raises:
        ValueError: Si l'incident n'est pas trouvé.
    """
    dao = IncidentDAO()
    incident = None
    
    if incident_id:
        incident = dao.get_incident_by_id(incident_id)
    elif qr_code_number:
        incident = dao.get_incident_by_qr_code(qr_code_number)
    
    if not incident:
        identifier = f"ID {incident_id}" if incident_id else f"QR code {qr_code_number}"
        raise ValueError(f"Aucun incident trouvé avec {identifier}")
    
    # Générer le QR code
    qr_generator = QRCodeGenerator()
    try:
        success, qr_path = qr_generator.generate_qr_code(incident.qr_code_number, output_dir, force)
        return success, qr_path
    except Exception as e:
        logger.error(f"Erreur lors de la génération du QR code: {str(e)}")
        raise


def main():
    """
    Point d'entrée principal du script.
    """
    args = parse_arguments()
    
    try:
        success, qr_path = generate_incident_qr(
            incident_id=args.id,
            qr_code_number=args.qr,
            output_dir=args.output,
            force=args.force
        )
        
        if success:
            print(f"QR code généré avec succès: {qr_path}")
        else:
            print("Erreur: Impossible de générer le QR code.")
            sys.exit(1)
            
    except ValueError as e:
        logger.error(f"Erreur lors de la génération du QR code: {str(e)}")
        print(f"Erreur: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erreur inattendue: {str(e)}")
        print(f"Erreur inattendue: {str(e)}")
        sys.exit(10)


if __name__ == "__main__":
    main()
