# Guide de configuration du compte Twilio pour WhatsApp Business API

Ce guide explique comment configurer un compte Twilio et obtenir les identifiants nécessaires pour l'intégration WhatsApp.

## 1. Création du compte Twilio

1. Visitez [https://www.twilio.com/try-twilio](https://www.twilio.com/try-twilio)
2. Inscrivez-vous avec votre adresse email professionnelle
3. Vérifiez votre numéro de téléphone
4. Complétez les informations de votre compte

## 2. Activation de l'API WhatsApp Business

1. Dans le tableau de bord Twilio, naviguez vers "Messaging" > "Try it out" > "Send a WhatsApp message"
2. Suivez les instructions pour activer un sandbox WhatsApp
3. Notez le numéro de téléphone WhatsApp qui vous est attribué

## 3. Obtention des identifiants API

1. Dans le tableau de bord Twilio, cliquez sur "Account" > "API keys & tokens"
2. Notez votre **Account SID** et votre **Auth Token**
3. Ces identifiants seront utilisés pour authentifier les requêtes à l'API Twilio

## 4. Configuration du webhook

1. Dans le tableau de bord Twilio, allez dans "Messaging" > "Settings" > "WhatsApp Sandbox Settings"
2. Dans la section "When a message comes in", configurez l'URL de votre webhook:
   ```
   https://votre-domaine.com/api/webhook/twilio
   ```
3. Assurez-vous de sélectionner la méthode HTTP POST

## 5. Test de la configuration

1. Envoyez un message au numéro WhatsApp sandbox en utilisant le code d'activation fourni
2. Vérifiez que vous recevez une réponse automatique
3. Vérifiez que votre webhook reçoit les messages

## 6. Sécurité des identifiants

- Ne partagez jamais votre Account SID et Auth Token
- Stockez ces identifiants dans des variables d'environnement ou un fichier de configuration sécurisé
- N'incluez pas ces identifiants directement dans le code source

## 7. Passage en production

Pour passer de l'environnement sandbox à la production:

1. Complétez le processus de vérification d'entreprise de Twilio
2. Soumettez votre modèle de message pour approbation à WhatsApp
3. Achetez un numéro de téléphone dédié pour WhatsApp Business

**Note**: Le processus de passage en production peut prendre plusieurs semaines et nécessite une approbation de WhatsApp.
