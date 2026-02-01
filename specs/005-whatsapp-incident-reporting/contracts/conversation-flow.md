# Flux de conversation du chatbot WhatsApp

Ce document décrit en détail le flux de conversation entre l'utilisateur et le chatbot WhatsApp pour la déclaration d'incidents.

## Étapes de la conversation

### 1. Initiation de la conversation

**Déclencheur** : L'utilisateur scanne le QR code du bâtiment et est redirigé vers WhatsApp avec un message pré-rempli.

**Message pré-rempli** : `incident:QR5050332870`

**Réponse du chatbot** :
```
Bonjour ! 👋

Je vois que vous souhaitez signaler un incident pour le bâtiment situé au 789 Boulevard Haussmann.

Pour commencer, veuillez m'indiquer dans quelle zone du bâtiment se trouve l'incident (ex: hall d'entrée, escalier, parking, etc.) ?
```

### 2. Collecte de la zone

**Entrée utilisateur** : L'utilisateur indique la zone concernée (texte libre).

**Réponse du chatbot** :
```
Merci. À quel étage se situe l'incident ?
```

### 3. Collecte de l'étage

**Entrée utilisateur** : L'utilisateur indique l'étage concerné (texte libre).

**Réponse du chatbot** :
```
J'ai bien noté : [zone] à l'étage [étage].

Quelle est la catégorie de l'incident ?
1️⃣ Plomberie
2️⃣ Électricité
3️⃣ Chauffage/Climatisation
4️⃣ Sécurité
5️⃣ Propreté
6️⃣ Structure du bâtiment
7️⃣ Autre (précisez)

Répondez avec le numéro ou le nom de la catégorie.
```

### 4. Collecte de la catégorie

**Entrée utilisateur** : L'utilisateur sélectionne une catégorie (numéro ou texte).

**Réponse du chatbot** :
```
Vous avez sélectionné : [catégorie].

Quel est le type spécifique d'incident ?
```

**Si catégorie = Plomberie** :
```
Quel est le type spécifique d'incident ?
1️⃣ Fuite d'eau
2️⃣ Canalisation bouchée
3️⃣ Problème de chasse d'eau
4️⃣ Absence d'eau chaude
5️⃣ Autre (précisez)
```

**Si catégorie = Électricité** :
```
Quel est le type spécifique d'incident ?
1️⃣ Panne d'électricité
2️⃣ Court-circuit
3️⃣ Prise défectueuse
4️⃣ Éclairage défectueux
5️⃣ Autre (précisez)
```

*[Autres catégories avec leurs types spécifiques...]*

### 5. Collecte du type d'incident

**Entrée utilisateur** : L'utilisateur sélectionne un type d'incident (numéro ou texte).

**Réponse du chatbot** :
```
Merci. Avez-vous des informations supplémentaires à fournir concernant cet incident ? (détails, urgence, etc.)

Si non, répondez simplement "Non".
```

### 6. Collecte des informations supplémentaires

**Entrée utilisateur** : L'utilisateur fournit des informations supplémentaires ou répond "Non".

**Réponse du chatbot** :
```
J'ai bien enregistré ces informations.

Pour finaliser votre déclaration, pourriez-vous me communiquer votre adresse email ? (facultatif)
```

### 7. Collecte de l'email

**Entrée utilisateur** : L'utilisateur fournit son email ou répond "Non" / "Pas nécessaire".

**Réponse du chatbot** :
```
Merci. Voici un récapitulatif de votre déclaration d'incident :

📍 Bâtiment : 789 Boulevard Haussmann
🔍 Zone : [zone]
🏢 Étage : [étage]
📋 Catégorie : [catégorie]
🔧 Type : [type]
📝 Informations : [informations supplémentaires]
📧 Email : [email]

Est-ce correct ? (Oui/Non)
```

### 8. Confirmation

**Entrée utilisateur** : L'utilisateur confirme ("Oui") ou demande des modifications ("Non").

**Si "Oui"** :
```
Merci ! Je traite votre déclaration d'incident...
```

*[Traitement de l'incident via l'API]*

**Réponse après traitement réussi** :
```
✅ Votre incident a été enregistré avec succès !

📱 Identifiant de l'incident : IN12345678

Vous pouvez suivre l'évolution de votre incident en scannant le QR code ci-joint.
```
*[Envoi du QR code de l'incident]*

**Réponse en cas d'erreur technique** :
```
⚠️ Votre déclaration a bien été prise en compte, mais nous rencontrons actuellement un problème technique pour finaliser l'enregistrement.

Ne vous inquiétez pas, votre déclaration sera traitée dès que possible et vous recevrez une confirmation avec l'identifiant de l'incident.

Merci de votre compréhension.
```

**Si "Non"** :
```
Que souhaitez-vous modifier ?
1️⃣ Zone
2️⃣ Étage
3️⃣ Catégorie
4️⃣ Type
5️⃣ Informations supplémentaires
6️⃣ Email
```

### 9. Modification (si nécessaire)

**Entrée utilisateur** : L'utilisateur sélectionne ce qu'il souhaite modifier.

**Réponse du chatbot** :
*[Retour à l'étape correspondante]*

## Commandes spéciales

À tout moment dans la conversation, l'utilisateur peut utiliser les commandes suivantes :

### Aide

**Entrée utilisateur** : "Aide", "Help", "?"

**Réponse du chatbot** :
```
📌 Aide - Commandes disponibles :

• "Aide" - Affiche ce message
• "Annuler" - Annule la déclaration en cours
• "Recommencer" - Redémarre la déclaration depuis le début
• "Retour" - Revient à l'étape précédente

Pour continuer votre déclaration, répondez simplement à la dernière question posée.
```

### Annuler

**Entrée utilisateur** : "Annuler", "Cancel", "Stop"

**Réponse du chatbot** :
```
Êtes-vous sûr de vouloir annuler cette déclaration d'incident ? (Oui/Non)
```

**Si "Oui"** :
```
Votre déclaration a été annulée. Si vous souhaitez déclarer un incident ultérieurement, scannez à nouveau le QR code du bâtiment.

Merci et bonne journée !
```

**Si "Non"** :
```
D'accord, continuons. Veuillez répondre à la dernière question.
```

### Recommencer

**Entrée utilisateur** : "Recommencer", "Restart", "Reset"

**Réponse du chatbot** :
```
Êtes-vous sûr de vouloir recommencer depuis le début ? (Oui/Non)
```

**Si "Oui"** :
*[Retour à l'étape 1 - Collecte de la zone]*

**Si "Non"** :
```
D'accord, continuons. Veuillez répondre à la dernière question.
```

### Retour

**Entrée utilisateur** : "Retour", "Back", "Previous"

**Réponse du chatbot** :
*[Retour à l'étape précédente]*

## Gestion des erreurs

### Réponse non reconnue

**Réponse du chatbot** :
```
Je n'ai pas compris votre réponse. Pourriez-vous reformuler ou utiliser l'une des options proposées ?

Pour obtenir de l'aide, tapez "Aide".
```

### Timeout (inactivité de 10 minutes)

**Réponse du chatbot** :
```
Êtes-vous toujours là ? Votre déclaration d'incident est en attente.

Pour continuer, veuillez répondre à la dernière question. Si vous souhaitez reprendre plus tard, vous pourrez retrouver cette conversation pendant 24 heures.
```

### Format email invalide

**Réponse du chatbot** :
```
L'adresse email que vous avez fournie semble incorrecte. Veuillez vérifier le format (exemple: nom@domaine.com) ou répondre "Non" si vous ne souhaitez pas fournir d'email.
```

## Diagramme d'état

```
┌─────────────┐
│  Initiation │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Zone     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Étage    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Catégorie  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Type     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Infos     │
│   Suppl.    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Email    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Récapitulatif│
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Confirmation │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Traitement  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Résultat  │
└─────────────┘
```

## Règles de validation

### Zone
- Doit contenir au moins 2 caractères
- Maximum 100 caractères

### Étage
- Doit contenir au moins 1 caractère
- Maximum 20 caractères
- Valeurs courantes acceptées : RDC, 1er, 2ème, etc.

### Catégorie
- Doit correspondre à l'une des catégories proposées
- Si "Autre" est sélectionné, une description est requise

### Type
- Doit correspondre à l'un des types proposés pour la catégorie
- Si "Autre" est sélectionné, une description est requise

### Email
- Format email standard (xxx@xxx.xxx)
- Facultatif

## Persistance de l'état

L'état de la conversation est persisté dans Redis avec une durée de vie (TTL) de 24 heures. Cela permet à l'utilisateur de reprendre une conversation interrompue dans ce délai.

Lorsqu'un utilisateur revient dans une conversation existante, le chatbot propose de reprendre là où il s'était arrêté :

```
Bonjour ! Je vois que vous avez une déclaration d'incident en cours pour le bâtiment situé au 789 Boulevard Haussmann.

Souhaitez-vous reprendre cette déclaration ? (Oui/Non)
```

**Si "Oui"** :
```
Parfait ! Voici où nous en étions :

[Dernière question posée]
```

**Si "Non"** :
```
D'accord. Souhaitez-vous commencer une nouvelle déclaration pour ce bâtiment ? (Oui/Non)
```
