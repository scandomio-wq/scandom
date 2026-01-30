"""
Module d'administration pour l'application Scandom.

Ce module fournit une interface d'administration pour gérer les bâtiments.
"""

from flask import Blueprint

# Créer le blueprint Flask
admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='templates')

# Importer les routes pour éviter les imports circulaires
from . import routes
