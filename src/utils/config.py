"""
Module de gestion de la configuration pour l'application QR Building Registry.
Permet de charger et d'accéder aux paramètres de configuration depuis un fichier INI.
"""

import configparser
import os
from typing import Dict, Any, Optional


class Config:
    """Classe de gestion de la configuration de l'application."""

    def __init__(self, config_file: str = None):
        """
        Initialise la configuration à partir d'un fichier INI.

        Args:
            config_file: Chemin vers le fichier de configuration.
                         Si None, utilise le chemin par défaut.
        """
        self.config = configparser.ConfigParser()
        
        if config_file is None:
            # Chemin par défaut relatif à la racine du projet
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_file = os.path.join(base_dir, 'config', 'db_config.ini')
        
        if not os.path.exists(config_file):
            example_file = f"{config_file}.example"
            if os.path.exists(example_file):
                raise FileNotFoundError(
                    f"Fichier de configuration '{config_file}' non trouvé. "
                    f"Veuillez copier '{example_file}' vers '{config_file}' "
                    f"et configurer les paramètres."
                )
            else:
                raise FileNotFoundError(
                    f"Fichier de configuration '{config_file}' et exemple non trouvés."
                )
        
        self.config.read(config_file)
    
    def get_postgresql_config(self) -> Dict[str, str]:
        """
        Récupère la configuration PostgreSQL.

        Returns:
            Dictionnaire contenant les paramètres de connexion PostgreSQL.
        """
        if 'postgresql' not in self.config:
            raise KeyError("Section 'postgresql' manquante dans le fichier de configuration.")
        
        return {
            'host': self.config.get('postgresql', 'host', fallback='localhost'),
            'port': self.config.get('postgresql', 'port', fallback='5432'),
            'database': self.config.get('postgresql', 'database'),
            'user': self.config.get('postgresql', 'user'),
            'password': self.config.get('postgresql', 'password')
        }
    
    def get_application_config(self) -> Dict[str, Any]:
        """
        Récupère la configuration de l'application.

        Returns:
            Dictionnaire contenant les paramètres de l'application.
        """
        if 'application' not in self.config:
            raise KeyError("Section 'application' manquante dans le fichier de configuration.")
        
        return {
            'qr_code_prefix': self.config.get('application', 'qr_code_prefix', fallback='QR'),
            'qr_resolution': self.config.getint('application', 'qr_resolution', fallback=1200),
            'qr_error_correction': self.config.get('application', 'qr_error_correction', fallback='M'),
            'max_json_size': self.config.getint('application', 'max_json_size', fallback=1048576)
        }
    
    def get(self, section: str, key: str, fallback: Optional[Any] = None) -> Any:
        """
        Récupère une valeur spécifique de la configuration.

        Args:
            section: Nom de la section dans le fichier de configuration.
            key: Nom de la clé dans la section.
            fallback: Valeur par défaut si la clé n'existe pas.

        Returns:
            Valeur de la configuration ou fallback si non trouvée.
        """
        if section not in self.config:
            return fallback
        
        return self.config.get(section, key, fallback=fallback)


# Instance globale de configuration
_config_instance = None


def get_config(config_file: str = None) -> Config:
    """
    Récupère l'instance globale de configuration ou en crée une nouvelle.

    Args:
        config_file: Chemin vers le fichier de configuration.
                     Si None, utilise le chemin par défaut.

    Returns:
        Instance de la classe Config.
    """
    global _config_instance
    
    if _config_instance is None or config_file is not None:
        _config_instance = Config(config_file)
    
    return _config_instance
