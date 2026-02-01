import os
import configparser
import re
from src.email import logger, EMAIL_CONFIG_PATH

class EmailConfig:
    """Chargeur de configuration pour le module email."""
    
    def __init__(self):
        self.config = configparser.ConfigParser()
        self._load_config()

    def _resolve_env_vars(self, value: str) -> str:
        """Résout les variables d'environnement au format ${VAR_NAME}."""
        pattern = r'\$\{([^}]+)\}'
        
        def replace_env_var(match):
            var_name = match.group(1)
            env_value = os.environ.get(var_name)
            if env_value is None:
                logger.warning(f"Variable d'environnement {var_name} non définie")
                return match.group(0)
            return env_value
        
        return re.sub(pattern, replace_env_var, value)

    def _get_int(self, section, option, default):
        """Récupère une valeur entière avec fallback sécurisé."""
        val = self.config.get(section, option, fallback=str(default))
        if val.startswith('${') or not val.isdigit():
            return default
        return int(val)

    def _load_config(self):
        """Charge la configuration depuis config.ini et les variables d'environnement."""
        # Charger les variables d'environnement depuis le fichier .env local s'il existe
        config_dir = os.path.dirname(EMAIL_CONFIG_PATH)
        env_file = os.path.join(config_dir, '.env')
        if os.path.exists(env_file):
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file)
                logger.info(f"Variables d'environnement chargées depuis {env_file}")
            except ImportError:
                # Fallback manuel si dotenv n'est pas dispo
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ.setdefault(key.strip(), value.strip())

        if os.path.exists(EMAIL_CONFIG_PATH):
            self.config.read(EMAIL_CONFIG_PATH)
            # Résoudre les variables d'environnement dans toutes les sections
            for section in self.config.sections():
                for key, value in self.config.items(section):
                    resolved_value = self._resolve_env_vars(value)
                    if resolved_value != value:
                        self.config.set(section, key, resolved_value)
        else:
            logger.warning(f"Fichier de configuration non trouvé: {EMAIL_CONFIG_PATH}")

        # Assignation des valeurs finales avec protection contre les placeholders non résolus
        self.smtp_host = self.config.get('smtp', 'host', fallback='localhost')
        if self.smtp_host.startswith('${'): self.smtp_host = 'localhost'
        
        self.smtp_port = self._get_int('smtp', 'port', 587)
        
        self.smtp_user = self.config.get('smtp', 'user', fallback='')
        if self.smtp_user.startswith('${'): self.smtp_user = ''
        
        self.smtp_password = self.config.get('smtp', 'password', fallback='')
        if self.smtp_password.startswith('${'): self.smtp_password = ''
        
        self.smtp_from_email = self.config.get('smtp', 'from_email', fallback='')
        if self.smtp_from_email.startswith('${'): self.smtp_from_email = ''
        
        use_tls_val = self.config.get('smtp', 'use_tls', fallback='true').lower()
        self.smtp_use_tls = use_tls_val == 'true' or use_tls_val.startswith('${') # Default to True

        self.max_retries = self._get_int('retry', 'max_retries', 3)
        self.retry_delay = self._get_int('retry', 'retry_delay', 60)

    def validate(self):
        """Valide que les paramètres obligatoires sont présents."""
        missing = []
        if not self.smtp_host: missing.append('SMTP_HOST')
        if not self.smtp_user: missing.append('SMTP_USER')
        if not self.smtp_password: missing.append('SMTP_PASSWORD')
        if not self.smtp_from_email: missing.append('SMTP_FROM_EMAIL')
        
        if missing:
            raise ValueError(f"Configuration email incomplète. Paramètres manquants: {', '.join(missing)}")
        return True

# Instance globale pour accès facile
email_config = EmailConfig()
