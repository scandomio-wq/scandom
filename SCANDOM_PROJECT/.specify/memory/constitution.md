# Constitution du Projet SCANDOM

## Principes fondamentaux

1. **PostgreSQL comme source de vérité** : La base de données PostgreSQL est l'autorité unique pour toutes les données du système.

2. **CLI-first** : Les opérations principales doivent être accessibles via une interface en ligne de commande claire et documentée.

3. **QR codes uniques, stables et traçables** : Chaque entité principale (bâtiment, incident) dispose d'identifiants QR uniques qui ne changent jamais une fois attribués.

4. **Sécurité et confidentialité par défaut** : Aucune donnée personnelle n'est encodée dans les QR codes, seulement des identifiants.

5. **Simplicité avant tout** : Préférer des solutions simples et maintenables plutôt que des architectures complexes.

## Périmètre technique minimum

### Entités principales

1. **T_BUILDING**
   - ID (PK)
   - CREATION_DATE
   - LOCATION (NOT NULL)
   - EMAIL_GESTIONNAIRE
   - NOTES
   - QR_CODE_NUMBER (UNIQUE)

2. **T_INCIDENT** (Nouvelle entité)
   - ID (PK)
   - CREATION_DATE
   - BUILDING_ID (FK → T_BUILDING.ID)
   - TYPE (NOT NULL)
   - DESCRIPTION
   - SEVERITY
   - STATUS
   - REPORTER_CONTACT
   - QR_CODE_NUMBER (UNIQUE)

### Fonctionnalités essentielles

1. **Gestion des bâtiments**
   - Création via JSON
   - Génération de QR code
   - Recherche par QR code

2. **Gestion des incidents**
   - Création via JSON
   - Association à un bâtiment existant
   - Génération de QR code d'incident
   - Recherche par QR code

## Portes qualité

1. **Tests unitaires** : Couverture minimale de 80% pour toutes les fonctionnalités critiques.

2. **Performance** : 
   - Création d'un incident en moins de 5 secondes
   - Recherche d'un incident par QR code en moins de 1 seconde

3. **Validation des données** : Toutes les entrées utilisateur doivent être validées selon des schémas définis.

4. **Traçabilité** : Chaque opération de création/modification doit être horodatée.

## Règles d'évolution

1. **Immutabilité des données critiques** : Une fois créés, les identifiants QR et les associations entre entités ne peuvent être modifiés.

2. **Compatibilité ascendante** : Les nouvelles fonctionnalités ne doivent pas casser les fonctionnalités existantes.

3. **Documentation systématique** : Toute nouvelle fonctionnalité doit être documentée dans README.md et les fichiers associés.

## Conventions

1. **Nommage des fichiers QR** : `[QR_CODE_NUMBER].png`

2. **Structure des dossiers QR** : Organisation par année/mois

3. **Format des identifiants QR** : Préfixe + chiffres (ex: QR1234567890 pour bâtiments, IN1234567890 pour incidents)
