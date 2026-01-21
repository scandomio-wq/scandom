# Codes d'erreur - QR Building Registry

Ce document liste tous les codes d'erreur et messages associés pour l'application QR Building Registry.

## Codes d'erreur généraux

| Code | Description | Cause possible | Action recommandée |
|------|-------------|----------------|-------------------|
| 1 | Erreur générale | Erreur non spécifique | Consulter les logs pour plus de détails |

## Codes d'erreur pour l'importation de bâtiments (`import_building.py`)

| Code | Description | Cause possible | Action recommandée |
|------|-------------|----------------|-------------------|
| 2 | Fichier JSON introuvable ou invalide | Le fichier n'existe pas ou n'est pas accessible | Vérifier le chemin du fichier et les permissions |
| 3 | Données invalides (validation échouée) | Le format des données ne correspond pas au schéma attendu | Vérifier le contenu du fichier JSON selon le format requis |
| 4 | Erreur de base de données | Problème de connexion ou d'opération sur la base de données | Vérifier la configuration de la base de données et son état |
| 5 | Erreur de génération du QR code | Problème lors de la création du QR code | Vérifier les permissions du dossier de sortie |

## Codes d'erreur pour la génération de QR codes (`generate_qr.py`)

| Code | Description | Cause possible | Action recommandée |
|------|-------------|----------------|-------------------|
| 1 | Erreur générale | Erreur non spécifique | Consulter les logs pour plus de détails |
| 2 | Bâtiment introuvable | L'ID ou le QR_CODE_NUMBER fourni ne correspond à aucun bâtiment | Vérifier l'identifiant fourni |
| 3 | Arguments invalides | Ni --id ni --qr fournis, ou format invalide | Fournir soit --id soit --qr avec une valeur valide |
| 4 | Erreur de génération du QR code | Problème lors de la création du QR code | Vérifier les permissions du dossier de sortie |
| 5 | Erreur d'écriture du fichier | Impossible d'écrire le fichier QR code | Vérifier les permissions du dossier de sortie |

## Codes d'erreur pour la recherche de bâtiments (`find_building.py`)

| Code | Description | Cause possible | Action recommandée |
|------|-------------|----------------|-------------------|
| 1 | Erreur générale | Erreur non spécifique | Consulter les logs pour plus de détails |
| 2 | Bâtiment introuvable | Le QR_CODE_NUMBER fourni ne correspond à aucun bâtiment | Vérifier l'identifiant QR fourni |
| 3 | Format de sortie invalide | Le format spécifié n'est pas pris en charge | Utiliser 'json' ou 'text' comme format |
| 4 | Erreur de base de données | Problème de connexion ou d'opération sur la base de données | Vérifier la configuration de la base de données et son état |

## Codes d'erreur pour l'importation d'incidents (`import_incident.py`)

| Code | Description | Cause possible | Action recommandée |
|------|-------------|----------------|-------------------|
| 1 | Erreur générale | Erreur non spécifique | Consulter les logs pour plus de détails |
| 2 | Fichier JSON introuvable ou invalide | Le fichier n'existe pas ou n'est pas accessible | Vérifier le chemin du fichier et les permissions |
| 3 | Bâtiment associé introuvable | Le BUILDING_ID fourni ne correspond à aucun bâtiment | Vérifier l'ID du bâtiment |
| 4 | Données invalides (validation échouée) | Le format des données ne correspond pas au schéma attendu | Vérifier le contenu du fichier JSON selon le format requis |
| 5 | Erreur de base de données | Problème de connexion ou d'opération sur la base de données | Vérifier la configuration de la base de données et son état |
| 10 | Erreur inattendue | Erreur système non anticipée | Consulter les logs pour plus de détails |

## Codes d'erreur pour la génération de QR codes d'incidents (`generate_incident_qr.py`)

| Code | Description | Cause possible | Action recommandée |
|------|-------------|----------------|-------------------|
| 1 | Erreur générale | Erreur non spécifique | Consulter les logs pour plus de détails |
| 2 | Incident introuvable | L'ID ou le QR_CODE_NUMBER fourni ne correspond à aucun incident | Vérifier l'identifiant fourni |
| 3 | Arguments invalides | Ni --id ni --qr fournis, ou format invalide | Fournir soit --id soit --qr avec une valeur valide |
| 4 | Erreur de génération du QR code | Problème lors de la création du QR code | Vérifier les permissions du dossier de sortie |
| 10 | Erreur inattendue | Erreur système non anticipée | Consulter les logs pour plus de détails |

## Codes d'erreur pour la recherche d'incidents (`find_incident.py`)

| Code | Description | Cause possible | Action recommandée |
|------|-------------|----------------|-------------------|
| 1 | Erreur générale | Erreur non spécifique | Consulter les logs pour plus de détails |
| 2 | Incident introuvable | Le QR_CODE_NUMBER fourni ne correspond à aucun incident | Vérifier l'identifiant QR fourni |
| 3 | Format de sortie invalide | Le format spécifié n'est pas pris en charge | Utiliser 'json' ou 'text' comme format |
| 10 | Erreur inattendue | Erreur système non anticipée | Consulter les logs pour plus de détails |

## Erreurs de validation

### Validation des données JSON

#### Bâtiments

| Message d'erreur | Cause | Action recommandée |
|------------------|-------|-------------------|
| "Le champ LOCATION est obligatoire." | Le champ LOCATION est manquant ou vide | Ajouter le champ LOCATION avec une valeur non vide |
| "Le champ LOCATION ne doit pas dépasser 255 caractères." | Le champ LOCATION est trop long | Réduire la longueur du champ LOCATION |
| "Le format de l'email du gestionnaire est invalide." | Format d'email incorrect | Corriger le format de l'email |
| "L'email du gestionnaire ne doit pas dépasser 100 caractères." | Email trop long | Réduire la longueur de l'email |
| "Le format de QR_CODE_NUMBER est invalide." | Format QR_CODE_NUMBER incorrect | Le format doit être "QR" suivi de chiffres |

#### Incidents

| Message d'erreur | Cause | Action recommandée |
|------------------|-------|-------------------|
| "Le champ BUILDING_ID est obligatoire." | Le champ BUILDING_ID est manquant | Ajouter le champ BUILDING_ID avec un ID valide |
| "Le champ INCIDENT_INFORMATION est obligatoire." | Le champ INCIDENT_INFORMATION est manquant | Ajouter le champ INCIDENT_INFORMATION avec les détails de l'incident |
| "Le champ zone est obligatoire." | Le champ zone est manquant dans INCIDENT_INFORMATION | Ajouter le champ zone dans INCIDENT_INFORMATION |
| "Le champ etage est obligatoire." | Le champ etage est manquant dans INCIDENT_INFORMATION | Ajouter le champ etage dans INCIDENT_INFORMATION |
| "Le champ categorie est obligatoire." | Le champ categorie est manquant dans INCIDENT_INFORMATION | Ajouter le champ categorie dans INCIDENT_INFORMATION |
| "Le champ type est obligatoire." | Le champ type est manquant dans INCIDENT_INFORMATION | Ajouter le champ type dans INCIDENT_INFORMATION |
| "Le format de l'email du déclarant est invalide." | Format d'email incorrect pour REPORTER_EMAIL | Corriger le format de l'email du déclarant |
| "Le format de QR_CODE_NUMBER est invalide." | Format QR_CODE_NUMBER incorrect | Le format doit être "IN" suivi de chiffres |

### Erreurs de base de données

| Message d'erreur | Cause | Action recommandée |
|------------------|-------|-------------------|
| "La modification des informations d'un bâtiment après création n'est pas autorisée." | Tentative de modification d'un bâtiment | Les bâtiments sont immuables après création |
| "La suppression d'un bâtiment n'est pas autorisée." | Tentative de suppression d'un bâtiment | Les bâtiments ne peuvent pas être supprimés |
| "Impossible de générer un QR_CODE_NUMBER unique." | Collision répétée d'identifiants QR | Problème système, contacter l'administrateur |
| "Le bâtiment avec l'ID spécifié n'existe pas." | Référence à un bâtiment inexistant | Vérifier l'ID du bâtiment fourni |

### Erreurs de génération de QR codes

| Message d'erreur | Cause | Action recommandée |
|------------------|-------|-------------------|
| "Le dossier de sortie n'existe pas." | Dossier de destination inexistant | Créer le dossier ou utiliser un dossier existant |
| "Pas de permission d'écriture dans le dossier." | Permissions insuffisantes | Vérifier les permissions du dossier |
| "Erreur lors de la génération du QR code." | Problème avec la bibliothèque QR | Vérifier les dépendances et l'installation |

## Journalisation des erreurs

Les erreurs sont journalisées dans les fichiers de log avec les niveaux suivants :

- **INFO**: Informations générales sur le fonctionnement normal
- **WARNING**: Avertissements qui ne bloquent pas l'exécution
- **ERROR**: Erreurs qui empêchent une opération spécifique
- **CRITICAL**: Erreurs critiques qui empêchent le fonctionnement de l'application

Les logs contiennent les informations suivantes :
- Horodatage
- Niveau de log
- Module source
- Message d'erreur
- Trace de la pile (pour les erreurs)

## Résolution des problèmes courants

### Problèmes de connexion à la base de données

1. Vérifier que PostgreSQL est en cours d'exécution
2. Vérifier les paramètres de connexion dans `config/db_config.ini`
3. Vérifier que l'utilisateur a les droits nécessaires sur la base de données

### Problèmes de génération de QR codes

1. Vérifier que le dossier `qr_codes/` existe et est accessible en écriture
2. Vérifier que les dépendances Python sont correctement installées
3. Vérifier que l'identifiant QR est au format correct :
   - Pour les bâtiments : commence par "QR" suivi de chiffres
   - Pour les incidents : commence par "IN" suivi de chiffres
