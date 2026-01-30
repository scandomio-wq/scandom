"""
Générateur de QR codes avec liens WhatsApp pour les bâtiments.

Ce module permet de générer des QR codes contenant des liens deep WhatsApp
qui ouvrent directement une conversation avec le numéro de téléphone configuré.
"""

import os
import logging
import qrcode
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, Tuple

from src.qr.generator import QRCodeGenerator as BaseQRCodeGenerator
from src.whatsapp import whatsapp_config

# Configuration du logger
logger = logging.getLogger('whatsapp.qr_generator')

class WhatsAppQRGenerator:
    """Générateur de QR codes avec liens WhatsApp."""
    
    def __init__(self):
        """Initialise le générateur de QR codes WhatsApp."""
        self.base_generator = BaseQRCodeGenerator()
        self.config = whatsapp_config
        self.qr_resolution = int(self.config.get('application', 'qr_resolution', fallback=1200))
        self.output_dir = self.config.get('application', 'qr_output_dir', fallback='qr_codes')
        
        # Créer le répertoire de sortie s'il n'existe pas
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_whatsapp_link(self, building_qr_code: str) -> str:
        """
        Génère un lien deep WhatsApp pour un bâtiment.
        
        Args:
            building_qr_code: Code QR du bâtiment
            
        Returns:
            str: Lien deep WhatsApp
        """
        phone_number = self.config.get('twilio', 'phone_number', fallback='')
        
        # Supprimer le '+' du numéro de téléphone
        if phone_number.startswith('+'):
            phone_number = phone_number[1:]
        
        # Créer le lien deep WhatsApp avec le code QR du bâtiment comme message initial
        message = f"Signalement incident {building_qr_code}"
        
        # Format: https://wa.me/PHONE_NUMBER/?text=URL_ENCODED_MESSAGE
        import urllib.parse
        encoded_message = urllib.parse.quote(message)
        
        return f"https://wa.me/{phone_number}/?text={encoded_message}"
    
    def generate_qr_code(self, building_qr_code: str, output_path: Optional[str] = None) -> str:
        """
        Génère un QR code avec un lien WhatsApp pour un bâtiment.
        
        Args:
            building_qr_code: Code QR du bâtiment
            output_path: Chemin de sortie pour le QR code (optionnel)
            
        Returns:
            str: Chemin du fichier QR code généré
        """
        try:
            # Générer le lien WhatsApp
            whatsapp_link = self.generate_whatsapp_link(building_qr_code)
            
            # Créer le QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(whatsapp_link)
            qr.make(fit=True)
            
            # Créer l'image du QR code
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Redimensionner l'image
            img = img.resize((self.qr_resolution, self.qr_resolution), Image.LANCZOS)
            
            # Ajouter le texte en bas du QR code
            img = self._add_text_to_qr(img, f"Signaler un incident: {building_qr_code}", "Scannez pour signaler un incident")
            
            # Déterminer le chemin de sortie
            if output_path is None:
                output_path = os.path.join(self.output_dir, f"whatsapp_{building_qr_code}.png")
            
            # Sauvegarder l'image
            img.save(output_path)
            
            logger.info(f"QR code WhatsApp généré pour {building_qr_code}: {output_path}")
            
            return output_path
        
        except Exception as e:
            logger.error(f"Erreur lors de la génération du QR code WhatsApp: {e}")
            raise
    
    def _add_text_to_qr(self, img: Image.Image, title: str, subtitle: str) -> Image.Image:
        """
        Ajoute du texte à l'image du QR code.
        
        Args:
            img: Image du QR code
            title: Titre à ajouter
            subtitle: Sous-titre à ajouter
            
        Returns:
            Image.Image: Image avec texte
        """
        # Créer une nouvelle image avec de l'espace pour le texte
        width, height = img.size
        new_height = height + 200  # Espace pour le texte
        new_img = Image.new('RGB', (width, new_height), color='white')
        
        # Coller le QR code
        new_img.paste(img, (0, 0))
        
        # Ajouter le texte
        draw = ImageDraw.Draw(new_img)
        
        # Essayer de charger une police, sinon utiliser la police par défaut
        try:
            title_font = ImageFont.truetype("Arial", 48)
            subtitle_font = ImageFont.truetype("Arial", 36)
        except IOError:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
        
        # Calculer les positions de texte
        title_width = draw.textlength(title, font=title_font)
        subtitle_width = draw.textlength(subtitle, font=subtitle_font)
        
        title_position = ((width - title_width) // 2, height + 40)
        subtitle_position = ((width - subtitle_width) // 2, height + 120)
        
        # Dessiner le texte
        draw.text(title_position, title, fill='black', font=title_font)
        draw.text(subtitle_position, subtitle, fill='black', font=subtitle_font)
        
        return new_img
    
    def generate_qr_codes_for_all_buildings(self, db_connection) -> int:
        """
        Génère des QR codes WhatsApp pour tous les bâtiments.
        
        Args:
            db_connection: Connexion à la base de données
            
        Returns:
            int: Nombre de QR codes générés
        """
        from src.db.building_dao import BuildingDAO
        
        try:
            # Récupérer tous les bâtiments
            building_dao = BuildingDAO(db_connection)
            buildings = building_dao.list_buildings()
            
            count = 0
            for building in buildings:
                # Générer un QR code pour chaque bâtiment
                qr_code = building.get('qr_code_number')
                if qr_code:
                    self.generate_qr_code(qr_code)
                    count += 1
            
            logger.info(f"{count} QR codes WhatsApp générés")
            return count
        
        except Exception as e:
            logger.error(f"Erreur lors de la génération des QR codes WhatsApp: {e}")
            raise
