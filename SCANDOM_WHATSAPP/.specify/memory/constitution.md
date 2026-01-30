# SCANDOM WhatsApp Integration Constitution

## Core Principles

### I. Seamless User Experience
Le processus de déclaration d'incident doit être simple et intuitif. L'utilisateur doit pouvoir déclarer un incident en moins de 2 minutes, avec un minimum d'étapes et sans friction technique.

### II. QR Code comme Point d'Entrée Unique
Le QR code du bâtiment est le point d'entrée unique pour la déclaration d'incident. Il doit contenir toutes les informations nécessaires pour initier la conversation WhatsApp sans nécessiter d'autres données.

### III. Conversation Guidée et Structurée
Le chatbot WhatsApp doit guider l'utilisateur à travers un processus structuré pour collecter toutes les informations nécessaires. Les questions doivent être claires, concises et adaptées au contexte.

### IV. Intégration Transparente avec le Système Existant
L'intégration WhatsApp doit s'interfacer de manière transparente avec le système existant d'import d'incidents. Les données collectées doivent être formatées selon le schéma JSON attendu par l'API existante.

### V. Sécurité et Confidentialité
Les données personnelles des utilisateurs doivent être traitées avec le plus grand soin. Les conversations WhatsApp doivent être sécurisées et les données sensibles ne doivent pas être stockées plus longtemps que nécessaire.

## Architecture Technique

1. **Twilio** comme fournisseur pour l'API WhatsApp Business
2. **Webhook Flask** pour recevoir et traiter les messages WhatsApp
3. **Base de données PostgreSQL** pour stocker les états de conversation
4. **API REST** pour communiquer avec le système d'import d'incidents existant
5. **QR codes dynamiques** contenant des liens deep vers WhatsApp

## Flux de Conversation

1. L'utilisateur scanne le QR code du bâtiment
2. Le QR code ouvre une conversation WhatsApp avec le numéro du chatbot
3. Le chatbot accueille l'utilisateur et demande séquentiellement:
   - Zone concernée par l'incident
   - Étage
   - Catégorie de l'incident
   - Type spécifique
   - Informations supplémentaires
   - Coordonnées du déclarant (téléphone, email)
4. Le chatbot génère un fichier JSON conforme au schéma attendu
5. Le JSON est envoyé à l'API d'import d'incident
6. L'utilisateur reçoit une confirmation avec le QR code de l'incident créé

## Critères de Qualité

1. **Temps de réponse** : Le chatbot doit répondre en moins de 2 secondes
2. **Taux de complétion** : Au moins 90% des conversations doivent aboutir à un incident créé
3. **Facilité d'utilisation** : Score SUS (System Usability Scale) d'au moins 80/100
4. **Robustesse** : Le système doit gérer les interruptions de conversation et permettre la reprise
5. **Multilinguisme** : Support initial du français, avec possibilité d'extension

**Version**: 1.0.0 | **Ratified**: 2026-01-22 | **Last Amended**: 2026-01-22
