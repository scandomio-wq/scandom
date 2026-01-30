"""
Module d'initialisation pour l'intégration WhatsApp.

Ce module initialise les composants nécessaires pour l'intégration WhatsApp,
notamment la configuration, la connexion Redis, et l'application Flask.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
import configparser
from typing import Dict, Any

from flask import Flask
from redis import Redis
from twilio.rest import Client

# Import de l'extension du gestionnaire d'état
import src.whatsapp.state_manager_extension
# Import de l'adaptateur de messages
import src.whatsapp.message_adapter
# Import du patch d'énumération
import src.whatsapp.enum_patch

# Chemins des fichiers de configuration
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config', 'whatsapp')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.ini')

# Initialisation du logger
logger = logging.getLogger('whatsapp')

def _resolve_env_vars(value: str) -> str:
    """
    Résout les variables d'environnement dans une valeur de configuration.
    Format supporté: ${VAR_NAME}
    
    Args:
        value: Valeur pouvant contenir des références à des variables d'environnement
        
    Returns:
        str: Valeur avec les variables d'environnement résolues
    """
    import re
    pattern = r'\$\{([^}]+)\}'
    
    def replace_env_var(match):
        var_name = match.group(1)
        env_value = os.environ.get(var_name)
        if env_value is None:
            logger.warning(f"Variable d'environnement {var_name} non définie")
            return match.group(0)  # Garder le placeholder si non défini
        return env_value
    
    return re.sub(pattern, replace_env_var, value)


def load_config():
    """
    Charge la configuration depuis le fichier config.ini.
    Les valeurs au format ${VAR_NAME} sont résolues depuis les variables d'environnement.
    
    Returns:
        configparser.ConfigParser: Configuration chargée
    """
    # Charger les variables d'environnement depuis .env si présent
    env_file = os.path.join(CONFIG_DIR, '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())
        logger.info(f"Variables d'environnement chargées depuis {env_file}")
    
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        logger.info(f"Configuration chargée depuis {CONFIG_FILE}")
    else:
        logger.error(f"Fichier de configuration non trouvé: {CONFIG_FILE}")
        raise FileNotFoundError(f"Fichier de configuration non trouvé: {CONFIG_FILE}")
    
    # Résoudre les variables d'environnement dans les valeurs
    for section in config.sections():
        for key, value in config.items(section):
            resolved_value = _resolve_env_vars(value)
            if resolved_value != value:
                config.set(section, key, resolved_value)
    
    return config

def setup_logging(config):
    """
    Configure le système de journalisation.
    
    Args:
        config (ConfigParser): L'objet de configuration.
    """
    log_level = getattr(logging, config.get('logging', 'level', fallback='INFO'))
    log_file = config.get('logging', 'file', fallback='/tmp/whatsapp.log')
    log_format = config.get('logging', 'format', fallback='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    max_size = int(config.get('logging', 'max_size', fallback=10485760))  # 10 Mo par défaut
    backup_count = int(config.get('logging', 'backup_count', fallback=5))
    
    # Créer le répertoire de logs s'il n'existe pas
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    handler = RotatingFileHandler(log_file, maxBytes=max_size, backupCount=backup_count)
    formatter = logging.Formatter(log_format)
    handler.setFormatter(formatter)
    
    logger.setLevel(log_level)
    logger.addHandler(handler)
    
    # Ajouter également un handler pour la console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    logger.info("Système de journalisation initialisé")

def create_redis_client(config):
    """
    Crée et configure un client Redis.
    
    Args:
        config (ConfigParser): L'objet de configuration.
        
    Returns:
        Redis: Le client Redis configuré.
    """
    host = config.get('redis', 'host', fallback='localhost')
    port = config.getint('redis', 'port', fallback=6379)
    db = config.getint('redis', 'db', fallback=0)
    password = config.get('redis', 'password', fallback=None)
    
    if not password:
        password = None  # Redis n'accepte pas une chaîne vide comme mot de passe
    
    redis_client = Redis(host=host, port=port, db=db, password=password, decode_responses=True)
    try:
        redis_client.ping()
        logger.info(f"Connexion Redis établie sur {host}:{port}, db={db}")
        return redis_client
    except Exception as e:
        logger.error(f"Erreur de connexion à Redis: {e}")
        raise

def create_twilio_client(config):
    """
    Crée et configure un client Twilio.
    
    Args:
        config (ConfigParser): L'objet de configuration.
        
    Returns:
        Client: Le client Twilio configuré.
    """
    account_sid = config.get('twilio', 'account_sid')
    auth_token = config.get('twilio', 'auth_token')
    
    twilio_client = Client(account_sid, auth_token)
    logger.info("Client Twilio initialisé")
    return twilio_client

def create_app():
    """
    Crée et configure l'application Flask.
    
    Returns:
        Flask: L'application Flask configurée.
    """
    app = Flask(__name__)
    
    # Définir une clé secrète pour les sessions et les messages flash
    app.secret_key = os.urandom(24)
    
    # Charger la configuration
    config = load_config()
    
    # Configurer le logging
    setup_logging(config)
    
    # Configurer Redis
    redis_client = create_redis_client(config)
    app.config['REDIS_CLIENT'] = redis_client
    
    # Configurer Twilio
    twilio_client = create_twilio_client(config)
    app.config['TWILIO_CLIENT'] = twilio_client
    app.config['TWILIO_WHATSAPP_NUMBER'] = config.get('twilio', 'whatsapp_number')
    
    # Stocker la configuration dans l'app
    app.config['WHATSAPP_CONFIG'] = config
    
    # Enregistrer les routes et les blueprints
    from . import webhook  # Import ici pour éviter les imports circulaires
    app.register_blueprint(webhook.whatsapp_bp)
    
    # Enregistrer le blueprint d'administration
    try:
        from src.admin import admin_bp
        app.register_blueprint(admin_bp)
        logger.info("Blueprint d'administration enregistré")
    except ImportError as e:
        logger.warning(f"Impossible d'enregistrer le blueprint d'administration: {e}")
    
    logger.info("Application Flask initialisée")
    return app

# Initialisation globale
config = load_config()
setup_logging(config)
redis_client = create_redis_client(config)
twilio_client = create_twilio_client(config)

# Variables globales pour l'accès facile depuis d'autres modules
whatsapp_config = config
