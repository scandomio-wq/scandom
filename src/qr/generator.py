"""
Module de génération de QR codes pour l'application QR Building Registry.
"""

import os
import logging
from datetime import datetime
from typing import Optional, Tuple

import qrcode
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
from PIL import Image

from src.utils.config import get_config

# Configuration du logging
logger = logging.getLogger(__name__)


class QRCodeGenerator:
    """Classe de génération de QR codes."""

    def __init__(self):
        """Initialise le générateur de QR codes."""
        self.config = get_config()
        self.qr_resolution = int(self.config.get('application', 'qr_resolution', fallback=1200))
        
        # Mapper les niveaux de correction d'erreur
        self.error_correction_levels = {
            'L': ERROR_CORRECT_L,  # ~7% de correction
            'M': ERROR_CORRECT_M,  # ~15% de correction
            'Q': ERROR_CORRECT_Q,  # ~25% de correction
            'H': ERROR_CORRECT_H   # ~30% de correction
        }
        
        self.error_correction = self.error_correction_levels.get(
            self.config.get('application', 'qr_error_correction', fallback='M'),
            ERROR_CORRECT_M
        )
    
    def generate_qr_code(self, qr_code_number: str, output_dir: Optional[str] = None,
                        force: bool = False) -> Tuple[bool, str]:
        """
        Génère un QR code pour un identifiant QR_CODE_NUMBER.

        Args:
            qr_code_number: Identifiant QR à encoder dans le QR code.
            output_dir: Dossier de sortie pour le QR code.
                        Si None, utilise le dossier par défaut.
            force: Si True, force la régénération même si le fichier existe déjà.

        Returns:
            Tuple (succès, chemin du fichier).
            
        Raises:
            ValueError: Si l'identifiant QR est invalide.
            OSError: Si le dossier de sortie n'existe pas ou n'est pas accessible.
        """
        if not qr_code_number:
            raise ValueError("L'identifiant QR ne peut pas être vide.")
            
        # Vérifier le format selon le préfixe
        if not (qr_code_number.startswith('QR') or qr_code_number.startswith('IN')):
            raise ValueError("L'identifiant QR doit commencer par 'QR' pour les bâtiments ou 'IN' pour les incidents.")
        
        # Déterminer le dossier de sortie
        if output_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            output_dir = os.path.join(base_dir, 'qr_codes')
            
            # Organiser par année/mois
            now = datetime.now()
            year_month_dir = os.path.join(output_dir, f"{now.year:04d}", f"{now.month:02d}")
            
            # Créer le dossier s'il n'existe pas
            os.makedirs(year_month_dir, exist_ok=True)
            
            output_dir = year_month_dir
        
        # Vérifier si le dossier existe
        if not os.path.isdir(output_dir):
            raise OSError(f"Le dossier de sortie '{output_dir}' n'existe pas ou n'est pas un dossier.")
        
        # Vérifier les permissions d'écriture
        if not os.access(output_dir, os.W_OK):
            raise OSError(f"Pas de permission d'écriture dans le dossier '{output_dir}'.")
        
        # Construire le chemin du fichier
        file_path = os.path.join(output_dir, f"{qr_code_number}.png")
        
        # Vérifier si le fichier existe déjà
        if os.path.exists(file_path) and not force:
            logger.info(f"Le QR code '{file_path}' existe déjà. Utilisez force=True pour régénérer.")
            return True, file_path
        
        # Gérer les collisions de noms de fichiers
        if os.path.exists(file_path) and force:
            # Trouver un nom de fichier unique en ajoutant un suffixe
            counter = 1
            while os.path.exists(file_path):
                file_path = os.path.join(output_dir, f"{qr_code_number}_{counter}.png")
                counter += 1
            
            logger.info(f"Collision détectée. Utilisation du nom de fichier alternatif: {file_path}")
        
        try:
            # Créer le QR code
            qr = qrcode.QRCode(
                version=None,  # Auto-détermination de la version
                error_correction=self.error_correction,
                box_size=10,
                border=4,
            )
            
            qr.add_data(qr_code_number)
            qr.make(fit=True)
            
            # Créer l'image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Redimensionner l'image à la résolution souhaitée
            img = img.resize((self.qr_resolution, self.qr_resolution), Image.LANCZOS)
            
            # Sauvegarder l'image
            img.save(file_path)
            
            logger.info(f"QR code généré avec succès: {file_path}")
            return True, file_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du QR code: {str(e)}")
            raise
    
    def qr_code_exists(self, qr_code_number: str, output_dir: Optional[str] = None) -> bool:
        """
        Vérifie si un fichier QR code existe déjà.

        Args:
            qr_code_number: Identifiant QR à vérifier.
            output_dir: Dossier de sortie pour le QR code.
                        Si None, utilise le dossier par défaut.

        Returns:
            True si le fichier existe, False sinon.
        """
        if output_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            output_dir = os.path.join(base_dir, 'qr_codes')
            
            # Vérifier dans tous les sous-dossiers année/mois
            for year_dir in os.listdir(output_dir):
                year_path = os.path.join(output_dir, year_dir)
                if os.path.isdir(year_path):
                    for month_dir in os.listdir(year_path):
                        month_path = os.path.join(year_path, month_dir)
                        if os.path.isdir(month_path):
                            file_path = os.path.join(month_path, f"{qr_code_number}.png")
                            if os.path.exists(file_path):
                                return True
            
            return False
        else:
            file_path = os.path.join(output_dir, f"{qr_code_number}.png")
            return os.path.exists(file_path)
