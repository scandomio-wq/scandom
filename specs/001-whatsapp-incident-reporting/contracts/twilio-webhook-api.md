# Contrat d'API pour le Webhook Twilio

Ce document décrit les contrats d'API pour l'intégration du webhook Twilio avec le système d'import d'incidents SCANDOM.

## Endpoint Webhook

### Réception de messages WhatsApp

**URL** : `/api/webhook/twilio`

**Méthode** : `POST`

**En-têtes requis** :
- `X-Twilio-Signature`: Signature de validation Twilio

**Corps de la requête** :
```
AccountSid=ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
ApiVersion=2010-04-01
Body=<message content>
From=whatsapp:+33612345678
To=whatsapp:+33687654321
NumMedia=0
ProfileName=John Doe
SmsMessageSid=SMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
SmsSid=SMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
SmsStatus=received
```

**Réponse de succès** :
- **Code** : `200 OK`
- **Contenu** : TwiML response
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>
        <Body>Message de réponse</Body>
    </Message>
</Response>
```

**Réponse d'erreur** :
- **Code** : `400 Bad Request`
- **Contenu** : TwiML response avec message d'erreur
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>
        <Body>Désolé, une erreur s'est produite. Veuillez réessayer plus tard.</Body>
    </Message>
</Response>
```

## Envoi de messages WhatsApp via Twilio API

### Envoi de message texte

**URL** : `https://api.twilio.com/2010-04-01/Accounts/{AccountSid}/Messages.json`

**Méthode** : `POST`

**En-têtes requis** :
- `Authorization`: Basic Auth avec AccountSid et AuthToken
- `Content-Type`: `application/x-www-form-urlencoded`

**Corps de la requête** :
```
From=whatsapp:+33687654321
To=whatsapp:+33612345678
Body=Votre message ici
```

**Réponse de succès** :
- **Code** : `201 Created`
- **Contenu** : JSON avec détails du message
```json
{
  "sid": "SMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "date_created": "2026-01-22T21:00:00Z",
  "date_updated": "2026-01-22T21:00:00Z",
  "date_sent": null,
  "account_sid": "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "to": "whatsapp:+33612345678",
  "from": "whatsapp:+33687654321",
  "body": "Votre message ici",
  "status": "queued",
  "num_segments": "1",
  "num_media": "0",
  "direction": "outbound-api",
  "api_version": "2010-04-01",
  "price": null,
  "price_unit": "USD",
  "error_code": null,
  "error_message": null,
  "uri": "/2010-04-01/Accounts/ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX/Messages/SMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX.json"
}
```

### Envoi de message avec média (QR code)

**URL** : `https://api.twilio.com/2010-04-01/Accounts/{AccountSid}/Messages.json`

**Méthode** : `POST`

**En-têtes requis** :
- `Authorization`: Basic Auth avec AccountSid et AuthToken
- `Content-Type`: `application/x-www-form-urlencoded`

**Corps de la requête** :
```
From=whatsapp:+33687654321
To=whatsapp:+33612345678
Body=Voici le QR code de votre incident
MediaUrl=https://example.com/qr_codes/IN12345678.png
```

**Réponse de succès** :
- **Code** : `201 Created`
- **Contenu** : JSON avec détails du message (similaire à l'exemple précédent)

## Statut des messages

### Webhook de statut de message

**URL** : `/api/webhook/twilio/status`

**Méthode** : `POST`

**Corps de la requête** :
```
MessageSid=SMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
MessageStatus=delivered
To=whatsapp:+33612345678
From=whatsapp:+33687654321
ApiVersion=2010-04-01
```

**Réponse de succès** :
- **Code** : `200 OK`
- **Contenu** : Vide ou confirmation simple

## Sécurité

### Validation de la signature Twilio

Pour sécuriser le webhook, toutes les requêtes entrantes doivent être validées en utilisant la signature Twilio :

1. Récupérer l'en-tête `X-Twilio-Signature`
2. Concaténer l'URL complète du webhook avec les paramètres de la requête (triés par ordre alphabétique)
3. Calculer le HMAC-SHA1 de cette chaîne en utilisant le AuthToken Twilio comme clé
4. Comparer le résultat avec la valeur de l'en-tête `X-Twilio-Signature`

Exemple de code Python pour la validation :

```python
from twilio.request_validator import RequestValidator

def validate_twilio_request(request, twilio_auth_token):
    validator = RequestValidator(twilio_auth_token)
    signature = request.headers.get('X-Twilio-Signature', '')
    url = request.url
    params = request.form.to_dict()
    
    return validator.validate(url, params, signature)
```

## Gestion des erreurs

| Code d'erreur | Description | Action |
|---------------|-------------|--------|
| 400 | Requête invalide | Vérifier les paramètres de la requête |
| 401 | Non autorisé | Vérifier les identifiants Twilio |
| 404 | Endpoint non trouvé | Vérifier l'URL du webhook |
| 429 | Trop de requêtes | Implémenter une stratégie de limitation de débit |
| 500 | Erreur serveur | Vérifier les logs du serveur |

## Exemples d'utilisation

### Exemple de réception d'un message WhatsApp

1. L'utilisateur envoie un message via WhatsApp
2. Twilio envoie une requête POST au webhook
3. Le webhook valide la signature Twilio
4. Le webhook traite le message et met à jour l'état de la conversation
5. Le webhook répond avec un message TwiML

### Exemple d'envoi d'un message WhatsApp

1. L'application décide d'envoyer un message à l'utilisateur
2. L'application appelle l'API Twilio avec les paramètres appropriés
3. Twilio envoie le message à l'utilisateur via WhatsApp
4. Twilio envoie une notification de statut au webhook de statut
