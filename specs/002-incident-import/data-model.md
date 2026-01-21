# Modèle de données pour l'import d'incidents

## Table T_INCIDENT

| Colonne | Type | Description | Contraintes |
|---------|------|-------------|------------|
| ID | SERIAL | Identifiant unique auto-incrémenté | PRIMARY KEY |
| BUILDING_ID | INTEGER | Référence à l'ID du bâtiment concerné | NOT NULL, FOREIGN KEY |
| CREATION_DATE | TIMESTAMP | Date et heure de création de l'incident | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| REPORTER_PHONE | VARCHAR(20) | Numéro de téléphone du déclarant | NULL |
| REPORTER_EMAIL | VARCHAR(100) | Email du déclarant | NULL |
| INCIDENT_INFORMATION | JSONB | Informations sur l'incident au format JSON | NOT NULL |
| QR_CODE_NUMBER | VARCHAR(50) | Identifiant unique utilisé dans le QR code | NOT NULL, UNIQUE |

## Structure du JSON INCIDENT_INFORMATION

```json
{
  "zone": "string",       // Obligatoire - Zone du bâtiment concernée par l'incident
  "etage": "string",      // Obligatoire - Étage où se situe l'incident
  "categorie": "string",  // Obligatoire - Catégorie de l'incident (ex: Plomberie, Électricité)
  "type": "string",       // Obligatoire - Type spécifique d'incident
  "informations_supplementaires": "string"  // Facultatif - Détails additionnels
}
```

## Contraintes et validations

1. Le champ `BUILDING_ID` doit référencer un bâtiment existant dans la table `T_BUILDING`.
2. Le champ `QR_CODE_NUMBER` doit être unique et commencer par le préfixe "IN" suivi de chiffres.
3. Le champ `INCIDENT_INFORMATION` doit contenir au minimum les champs obligatoires: zone, etage, categorie et type.
4. Si `REPORTER_EMAIL` est fourni, il doit respecter le format d'une adresse email valide.

## Relations

- Un incident est lié à un et un seul bâtiment (relation N:1 avec T_BUILDING).
- Un bâtiment peut avoir zéro, un ou plusieurs incidents associés.

## Indexation

Pour optimiser les performances des requêtes fréquentes, les index suivants sont créés:

1. Index sur `BUILDING_ID` pour accélérer la recherche des incidents par bâtiment.
2. Index sur `QR_CODE_NUMBER` pour accélérer la recherche par identifiant QR.
3. Index sur `CREATION_DATE` pour accélérer le tri et la recherche par date.
