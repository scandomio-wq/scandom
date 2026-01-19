#!/usr/bin/env python3
"""
Script de génération de QR code pour un immeuble existant.
"""

import argparse
import logging
import os
import signal
import sys
from typing import Optional, Dict, Any

from src.db.building_dao import BuildingDAO
from src.qr.generator import QRCodeGenerator

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
    parser = argparse.ArgumentParser(description="Génère un QR code pour un immeuble existant.")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--id",
        type=int,
        help="ID du bâtiment"
    )
    group.add_argument(
        "--qr",
        help="QR_CODE_NUMBER du bâtiment"
    )
    
    parser.add_argument(
        "--output",
        help="Dossier de sortie pour le QR code (par défaut: ./qr_codes)",
        default=None
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force la régénération même si le fichier existe déjà"
    )
    
    return parser.parse_args()


def generate_qr(building_id: Optional[int] = None, qr_code_number: Optional[str] = None,
               output_dir: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
    """
    Génère un QR code pour un immeuble existant.
    
    Args:
        building_id: ID du bâtiment.
        qr_code_number: QR_CODE_NUMBER du bâtiment.
        output_dir: Dossier de sortie pour le QR code.
        force: Si True, force la régénération même si le fichier existe déjà.
    
    Returns:
        Dictionnaire contenant les informations du QR code généré.
        
    Raises:
        ValueError: Si ni building_id ni qr_code_number n'est fourni.
        FileNotFoundError: Si le bâtiment n'existe pas.
        Exception: Pour toute autre erreur.
    """
    if building_id is None and qr_code_number is None:
        raise ValueError("Vous devez fournir soit l'ID du bâtiment, soit son QR_CODE_NUMBER.")
    
    try:
        # Récupérer le bâtiment
        dao = BuildingDAO()
        building = None
        
        if building_id is not None:
            building = dao.get_building_by_id(building_id)
        else:
            building = dao.get_building_by_qr_code(qr_code_number)
        
        if building is None:
            raise FileNotFoundError("Bâtiment introuvable.")
        
        # Vérifier si le QR code existe déjà
        qr_generator = QRCodeGenerator()
        if not force and qr_generator.qr_code_exists(building.qr_code_number, output_dir):
            # Le QR code existe déjà, retourner le chemin
            if output_dir is None:
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                output_dir = os.path.join(base_dir, 'qr_codes')
                
                # Rechercher dans tous les sous-dossiers année/mois
                for year_dir in os.listdir(output_dir):
                    year_path = os.path.join(output_dir, year_dir)
                    if os.path.isdir(year_path):
                        for month_dir in os.listdir(year_path):
                            month_path = os.path.join(year_path, month_dir)
                            if os.path.isdir(month_path):
                                file_path = os.path.join(month_path, f"{building.qr_code_number}.png")
                                if os.path.exists(file_path):
                                    return {
                                        "building_id": building.id,
                                        "qr_code_number": building.qr_code_number,
                                        "qr_file_path": file_path,
                                        "regenerated": False
                                    }
            else:
                file_path = os.path.join(output_dir, f"{building.qr_code_number}.png")
                return {
                    "building_id": building.id,
                    "qr_code_number": building.qr_code_number,
                    "qr_file_path": file_path,
                    "regenerated": False
                }
        
        # Générer le QR code
        success, qr_file_path = qr_generator.generate_qr_code(building.qr_code_number, output_dir, force)
        
        if not success:
            raise RuntimeError("Erreur lors de la génération du QR code.")
        
        return {
            "building_id": building.id,
            "qr_code_number": building.qr_code_number,
            "qr_file_path": qr_file_path,
            "regenerated": True
        }
        
    except FileNotFoundError as e:
        logger.error(f"Bâtiment introuvable: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la génération du QR code: {str(e)}")
        raise


def main():
    """Fonction principale."""
    try:
        # Configurer les gestionnaires de signaux
        setup_signal_handlers()
        
        # Parser les arguments
        args = parse_arguments()
        
        # Générer le QR code
        result = generate_qr(args.id, args.qr, args.output, args.force)
        
        # Afficher le résultat
        print(f"QR code généré avec succès: {result['qr_file_path']}")
        
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
