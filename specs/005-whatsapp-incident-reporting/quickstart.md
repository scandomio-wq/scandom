# Guide de démarrage rapide : Intégration WhatsApp

Ce guide vous aidera à démarrer rapidement l'implémentation de l'intégration WhatsApp pour le système de déclaration d'incidents SCANDOM.

## Prérequis

1. **Compte Twilio**
   - Créer un compte sur [Twilio](https://www.twilio.com/)
   - Activer l'API WhatsApp Business
   - Obtenir un numéro de téléphone dédié

2. **Environnement de développement**
   - Python 3.8+ avec pip
   - Redis
   - PostgreSQL (déjà configuré pour SCANDOM)
   - Serveur accessible depuis Internet (pour le webhook)
   - Certificat SSL valide

## Installation rapide

### 1. Cloner le projet et installer les dépendances

```bash
# Dans le répertoire du projet SCANDOM
cd /home/jeremy/Documents/Projet/scandom

# Créer un environnement virtuel (si ce n'est pas déjà fait)
python -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install flask twilio redis celery psycopg2-binary
```

### 2. Configuration de Twilio

1. Dans votre compte Twilio, accédez à la console WhatsApp
2. Configurez un sandbox WhatsApp pour les tests
3. Notez votre Account SID et Auth Token
4. Configurez l'URL de votre webhook : `https://votre-domaine.com/api/webhook/twilio`

### 3. Configuration de l'application

Créez un fichier de configuration pour l'intégration WhatsApp :

```bash
mkdir -p /home/jeremy/Documents/Projet/scandom/config/whatsapp
touch /home/jeremy/Documents/Projet/scandom/config/whatsapp/config.ini
```

Éditez le fichier avec les informations suivantes :

```ini
[twilio]
account_sid = VOTRE_ACCOUNT_SID
auth_token = VOTRE_AUTH_TOKEN
phone_number = +33612345678

[redis]
host = localhost
port = 6379
db = 0
password = 

[webhook]
url = https://votre-domaine.com/api/webhook/twilio
```

### 4. Structure des fichiers

Créez la structure de fichiers suivante :

```
src/
  whatsapp/
    __init__.py
    webhook.py         # Endpoint Flask pour le webhook Twilio
    conversation.py    # Logique de gestion des conversations
    state_manager.py   # Gestionnaire d'état avec Redis
    incident_api.py    # Intégration avec l'API d'import d'incident
    qr_generator.py    # Générateur de QR codes avec deep links
```

## Implémentation pas à pas

### 1. Webhook Flask

Créez le fichier `src/whatsapp/webhook.py` :

```python
from flask import Flask, request, Response
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse
from src.whatsapp.conversation import ConversationManager
from src.utils.config import get_config

app = Flask(__name__)
config = get_config()
validator = RequestValidator(config.get('twilio', 'auth_token'))

@app.route('/api/webhook/twilio', methods=['POST'])
def webhook():
    # Valider la requête Twilio
    signature = request.headers.get('X-Twilio-Signature', '')
    url = request.url
    params = request.form.to_dict()
    
    if not validator.validate(url, params, signature):
        return Response('Invalid signature', status=403)
    
    # Extraire les informations du message
    message_body = request.form.get('Body', '')
    from_number = request.form.get('From', '').replace('whatsapp:', '')
    
    # Traiter le message avec le gestionnaire de conversation
    conversation_manager = ConversationManager()
    response_text = conversation_manager.process_message(from_number, message_body)
    
    # Créer la réponse TwiML
    resp = MessagingResponse()
    resp.message(response_text)
    
    return str(resp)

if __name__ == '__main__':
    app.run(debug=True, ssl_context='adhoc')
```

### 2. Gestionnaire d'état

Créez le fichier `src/whatsapp/state_manager.py` :

```python
import json
import redis
import uuid
from datetime import datetime, timedelta
from src.utils.config import get_config

class StateManager:
    def __init__(self):
        config = get_config()
        self.redis = redis.Redis(
            host=config.get('redis', 'host'),
            port=int(config.get('redis', 'port')),
            db=int(config.get('redis', 'db')),
            password=config.get('redis', 'password')
        )
        self.ttl = 24 * 60 * 60  # 24 heures en secondes
    
    def get_conversation_state(self, user_phone, building_qr_code):
        """Récupère l'état de la conversation pour un utilisateur et un bâtiment."""
        key = f"conversation:{user_phone}:{building_qr_code}"
        state_json = self.redis.get(key)
        
        if state_json:
            return json.loads(state_json)
        
        # Créer un nouvel état si aucun n'existe
        conversation_id = str(uuid.uuid4())
        state = {
            'conversation_id': conversation_id,
            'user_phone': user_phone,
            'building_qr_code': building_qr_code,
            'current_step': 'zone',
            'collected_data': {},
            'last_activity': datetime.now().isoformat(),
            'is_completed': False
        }
        
        self.save_conversation_state(state)
        return state
    
    def save_conversation_state(self, state):
        """Sauvegarde l'état de la conversation dans Redis."""
        key = f"conversation:{state['user_phone']}:{state['building_qr_code']}"
        state['last_activity'] = datetime.now().isoformat()
        
        self.redis.set(key, json.dumps(state), ex=self.ttl)
        return state
    
    def update_conversation_step(self, user_phone, building_qr_code, step, data=None):
        """Met à jour l'étape de la conversation et ajoute des données collectées."""
        state = self.get_conversation_state(user_phone, building_qr_code)
        state['current_step'] = step
        
        if data:
            if 'collected_data' not in state:
                state['collected_data'] = {}
            state['collected_data'].update(data)
        
        return self.save_conversation_state(state)
    
    def mark_conversation_completed(self, user_phone, building_qr_code):
        """Marque une conversation comme terminée."""
        state = self.get_conversation_state(user_phone, building_qr_code)
        state['is_completed'] = True
        return self.save_conversation_state(state)
```

### 3. Gestionnaire de conversation

Créez le fichier `src/whatsapp/conversation.py` :

```python
from src.whatsapp.state_manager import StateManager
from src.whatsapp.incident_api import IncidentAPI
import re

class ConversationManager:
    def __init__(self):
        self.state_manager = StateManager()
        self.incident_api = IncidentAPI()
    
    def process_message(self, user_phone, message):
        """Traite un message entrant et retourne la réponse appropriée."""
        # Vérifier si c'est un message initial avec un QR code
        qr_match = re.match(r'incident:(QR\d+)', message)
        if qr_match:
            building_qr_code = qr_match.group(1)
            return self.start_conversation(user_phone, building_qr_code)
        
        # Vérifier les commandes spéciales
        if message.lower() in ['aide', 'help', '?']:
            return self.get_help_message()
        
        if message.lower() in ['annuler', 'cancel', 'stop']:
            return "Êtes-vous sûr de vouloir annuler cette déclaration d'incident ? (Oui/Non)"
        
        # Traiter le message selon l'étape actuelle
        # Note: Ceci est simplifié, vous devrez implémenter la logique complète
        # pour gérer toutes les étapes et transitions
        
        # Pour l'exemple, nous supposons que nous avons un état de conversation existant
        # avec un building_qr_code connu
        building_qr_code = "QR5050332870"  # À remplacer par la récupération réelle
        
        state = self.state_manager.get_conversation_state(user_phone, building_qr_code)
        current_step = state.get('current_step')
        
        # Logique simplifiée pour l'exemple
        if current_step == 'zone':
            self.state_manager.update_conversation_step(
                user_phone, building_qr_code, 'etage', {'zone': message}
            )
            return "Merci. À quel étage se situe l'incident ?"
        
        # Implémentez les autres étapes selon le flux de conversation
        
        return "Je n'ai pas compris votre message. Tapez 'Aide' pour obtenir de l'aide."
    
    def start_conversation(self, user_phone, building_qr_code):
        """Démarre une nouvelle conversation."""
        # Vérifier si le bâtiment existe
        building = self.get_building_info(building_qr_code)
        if not building:
            return "Désolé, ce bâtiment n'existe pas dans notre système."
        
        # Vérifier s'il y a une conversation en cours
        state = self.state_manager.get_conversation_state(user_phone, building_qr_code)
        if state and not state.get('is_completed') and 'collected_data' in state and state['collected_data']:
            return f"""
Bonjour ! Je vois que vous avez une déclaration d'incident en cours pour le bâtiment situé au {building['location']}.

Souhaitez-vous reprendre cette déclaration ? (Oui/Non)
            """
        
        # Démarrer une nouvelle conversation
        self.state_manager.update_conversation_step(user_phone, building_qr_code, 'zone')
        
        return f"""
Bonjour ! 👋

Je vois que vous souhaitez signaler un incident pour le bâtiment situé au {building['location']}.

Pour commencer, veuillez m'indiquer dans quelle zone du bâtiment se trouve l'incident (ex: hall d'entrée, escalier, parking, etc.) ?
        """
    
    def get_building_info(self, building_qr_code):
        """Récupère les informations d'un bâtiment par son QR code."""
        # Implémentez l'appel à l'API existante
        # Pour l'exemple, nous retournons des données fictives
        return {
            'id': 7,
            'location': '789 Boulevard Haussmann, 75009 Paris',
            'qr_code_number': building_qr_code
        }
    
    def get_help_message(self):
        """Retourne le message d'aide."""
        return """
📌 Aide - Commandes disponibles :

• "Aide" - Affiche ce message
• "Annuler" - Annule la déclaration en cours
• "Recommencer" - Redémarre la déclaration depuis le début
• "Retour" - Revient à l'étape précédente

Pour continuer votre déclaration, répondez simplement à la dernière question posée.
        """
```

### 4. Intégration avec l'API d'import d'incident

Créez le fichier `src/whatsapp/incident_api.py` :

```python
import json
import requests
from datetime import datetime, timedelta
import celery
from src.utils.config import get_config

class IncidentAPI:
    def __init__(self):
        self.config = get_config()
    
    def create_incident(self, conversation_state):
        """Crée un incident à partir des données de conversation."""
        collected_data = conversation_state.get('collected_data', {})
        building_qr_code = conversation_state.get('building_qr_code')
        
        # Construire le JSON pour l'API d'import d'incident
        incident_data = {
            "BUILDING_QR_CODE": building_qr_code,
            "REPORTER_PHONE": conversation_state.get('user_phone'),
            "REPORTER_EMAIL": collected_data.get('email'),
            "INCIDENT_INFORMATION": {
                "zone": collected_data.get('zone'),
                "etage": collected_data.get('etage'),
                "categorie": collected_data.get('categorie'),
                "type": collected_data.get('type'),
                "informations_supplementaires": collected_data.get('informations_supplementaires')
            }
        }
        
        try:
            # Appel à l'API d'import d'incident existante
            response = self.call_import_api(incident_data)
            return response
        except Exception as e:
            # En cas d'erreur technique, mettre en file d'attente pour retry
            if self.is_technical_error(e):
                self.queue_for_retry(conversation_state, incident_data, str(e))
                return {
                    "status": "queued",
                    "message": "Votre déclaration a été prise en compte et sera traitée dès que possible."
                }
            # En cas d'erreur fonctionnelle, retourner l'erreur
            return {
                "status": "error",
                "message": f"Erreur: {str(e)}"
            }
    
    def call_import_api(self, incident_data):
        """Appelle l'API d'import d'incident existante."""
        # Implémentez l'appel à votre API existante
        # Pour l'exemple, nous simulons une réponse réussie
        return {
            "status": "success",
            "incident_id": 123,
            "qr_code_number": "IN12345678"
        }
    
    def is_technical_error(self, error):
        """Détermine si une erreur est technique ou fonctionnelle."""
        # Implémentez la logique pour distinguer les erreurs
        # Pour l'exemple, nous considérons toutes les erreurs comme techniques
        return True
    
    def queue_for_retry(self, conversation_state, incident_data, error_message):
        """Met en file d'attente un incident pour retry ultérieur."""
        # Implémentez la logique de mise en file d'attente
        # Pour l'exemple, nous simulons l'enregistrement dans la base de données
        print(f"Incident mis en file d'attente: {incident_data}")
```

### 5. Générateur de QR codes avec deep links

Créez le fichier `src/whatsapp/qr_generator.py` :

```python
from src.qr.generator import QRCodeGenerator
from src.utils.config import get_config
import urllib.parse

class WhatsAppQRGenerator:
    def __init__(self):
        self.qr_generator = QRCodeGenerator()
        self.config = get_config()
        self.phone_number = self.config.get('twilio', 'phone_number').replace('+', '')
    
    def generate_building_qr_with_whatsapp_link(self, building_qr_code, output_path=None):
        """Génère un QR code pour un bâtiment avec un deep link WhatsApp."""
        # Créer le lien WhatsApp avec le QR code du bâtiment
        message = f"incident:{building_qr_code}"
        whatsapp_link = f"https://wa.me/{self.phone_number}?text={urllib.parse.quote(message)}"
        
        # Générer le QR code avec le lien
        return self.qr_generator.generate_qr_code(whatsapp_link, output_path)
```

## Démarrage du serveur

Créez un script de démarrage `src/whatsapp/run.py` :

```python
from src.whatsapp.webhook import app
import os
from src.utils.config import get_config

if __name__ == '__main__':
    config = get_config()
    port = int(os.environ.get('PORT', 5000))
    
    # En production, utilisez un serveur WSGI comme Gunicorn
    # Pour le développement, utilisez le serveur de développement Flask
    app.run(host='0.0.0.0', port=port, debug=False, ssl_context='adhoc')
```

## Déploiement

Pour déployer l'application en production :

1. Utilisez un serveur WSGI comme Gunicorn :
   ```bash
   pip install gunicorn
   gunicorn --bind 0.0.0.0:5000 src.whatsapp.webhook:app
   ```

2. Configurez un proxy inverse (Nginx, Apache) pour gérer HTTPS

3. Assurez-vous que le serveur est accessible depuis Internet pour que Twilio puisse envoyer des webhooks

## Prochaines étapes

1. Implémentez la logique complète du flux de conversation
2. Ajoutez des tests unitaires et d'intégration
3. Configurez le monitoring et la journalisation
4. Mettez en place un système de déploiement continu

## Ressources utiles

- [Documentation Twilio WhatsApp API](https://www.twilio.com/docs/whatsapp/api)
- [Documentation Flask](https://flask.palletsprojects.com/)
- [Documentation Redis](https://redis.io/documentation)
- [Documentation Celery](https://docs.celeryproject.org/)
