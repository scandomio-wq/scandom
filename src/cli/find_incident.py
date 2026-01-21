#!/usr/bin/env python3
"""
Script CLI pour rechercher un incident par son QR code.
"""

import sys
import json
import logging
import argparse

from src.db.incident_dao import IncidentDAO

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
    parser = argparse.ArgumentParser(description="Rechercher un incident par QR code")
    parser.add_argument("qr_code", help="Identifiant QR de l'incident à rechercher")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                       help="Format de sortie (text ou json)")
    
    return parser.parse_args()


def find_incident(qr_code: str, output_format: str = "text"):
    """
    Recherche un incident par son QR code.

    Args:
        qr_code: Identifiant QR de l'incident.
        output_format: Format de sortie (text ou json).

    Returns:
        Résultat formaté selon le format demandé.
        
    Raises:
        ValueError: Si l'incident n'est pas trouvé.
    """
    dao = IncidentDAO()
    incident = dao.get_incident_by_qr_code(qr_code)
    
    if not incident:
        raise ValueError(f"Aucun incident trouvé avec l'identifiant QR '{qr_code}'")
    
    if output_format == "json":
        return json.dumps(incident.to_dict(), indent=2, default=str)
    else:
        # Format texte
        result = [
            f"ID: {incident.id}",
            f"Building ID: {incident.building_id}",
            f"Date de création: {incident.creation_date}",
            f"QR Code: {incident.qr_code_number}",
            f"Contact déclarant: {incident.reporter_phone or 'N/A'} / {incident.reporter_email or 'N/A'}",
            f"\nInformations sur l'incident:",
            f"  Zone: {incident.incident_information.get('zone', 'N/A')}",
            f"  Étage: {incident.incident_information.get('etage', 'N/A')}",
            f"  Catégorie: {incident.incident_information.get('categorie', 'N/A')}",
            f"  Type: {incident.incident_information.get('type', 'N/A')}"
        ]
        
        # Ajouter les informations supplémentaires si présentes
        if incident.incident_information.get('informations_supplementaires'):
            result.append(f"\nInformations supplémentaires:")
            result.append(f"{incident.incident_information.get('informations_supplementaires')}")
        
        return "\n".join(result)


def main():
    """
    Point d'entrée principal du script.
    """
    args = parse_arguments()
    
    try:
        result = find_incident(args.qr_code, args.format)
        print(result)
        
    except ValueError as e:
        logger.error(f"Erreur lors de la recherche: {str(e)}")
        print(f"Erreur: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erreur inattendue: {str(e)}")
        print(f"Erreur inattendue: {str(e)}")
        sys.exit(10)


if __name__ == "__main__":
    main()
