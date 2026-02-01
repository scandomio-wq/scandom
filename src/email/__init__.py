import logging
import os

# Configuration du logger pour le module email
logger = logging.getLogger(__name__)

# Définition des chemins de configuration
EMAIL_CONFIG_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EMAIL_CONFIG_PATH = os.path.join(EMAIL_CONFIG_DIR, 'config', 'email', 'config.ini')

__all__ = ['logger', 'EMAIL_CONFIG_PATH']
