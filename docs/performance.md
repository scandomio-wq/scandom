# Guide de test de performance - QR Building Registry

Ce document décrit la procédure de test de performance pour l'application QR Building Registry, basée sur les critères de succès définis dans la spécification.

## Critères de succès

L'application doit respecter les critères de performance suivants :

1. **SC-001**: Un opérateur peut enregistrer un immeuble et obtenir un identifiant QR unique en moins de 5 secondes (hors latence d'infrastructure).
2. **SC-002**: Le système empêche 100% des doublons d'identifiants QR au moment de l'enregistrement.
3. **SC-003**: La génération d'un artefact QR pour un immeuble existant se termine en moins de 2 secondes dans 95% des cas sur un poste standard.
4. **SC-004**: Pour un identifiant QR valide, la recherche de l'immeuble associé retourne un résultat (ou une erreur) en moins de 1 seconde dans 95% des cas.

## Outil de benchmark

L'application inclut un script de benchmark (`scripts/benchmarks/perf_test.py`) qui permet de mesurer les performances selon ces critères.

### Prérequis

- Base de données PostgreSQL configurée et accessible
- Environnement Python avec toutes les dépendances installées
- Droits d'écriture dans le dossier `scripts/benchmarks/results/`

### Exécution du benchmark

Pour exécuter tous les tests de performance avec les paramètres par défaut :

```bash
python scripts/benchmarks/perf_test.py
```

### Options disponibles

```
usage: perf_test.py [-h] [--num-tests NUM_TESTS] [--output OUTPUT] [--skip-create] [--skip-duplicate] [--skip-generate] [--skip-find]

Benchmark pour l'application QR Building Registry.

options:
  -h, --help            affiche ce message d'aide et quitte
  --num-tests NUM_TESTS
                        Nombre de tests à effectuer pour chaque benchmark (défaut: 100)
  --output OUTPUT       Chemin du fichier de sortie pour les résultats (défaut: auto-généré)
  --skip-create         Ignorer le benchmark de création d'immeubles
  --skip-duplicate      Ignorer le benchmark de prévention des doublons
  --skip-generate       Ignorer le benchmark de génération de QR codes
  --skip-find           Ignorer le benchmark de recherche d'immeubles
```

### Exemples d'utilisation

Exécuter le benchmark avec 500 tests par critère :
```bash
python scripts/benchmarks/perf_test.py --num-tests 500
```

Exécuter uniquement les benchmarks de création et de recherche :
```bash
python scripts/benchmarks/perf_test.py --skip-duplicate --skip-generate
```

Sauvegarder les résultats dans un fichier spécifique :
```bash
python scripts/benchmarks/perf_test.py --output /path/to/results.json
```

## Interprétation des résultats

Le script génère un rapport détaillé avec les métriques suivantes pour chaque critère :

- **Temps moyen** : Moyenne des temps d'exécution
- **Temps médian** : Médiane des temps d'exécution
- **95e percentile** : Valeur en dessous de laquelle se trouvent 95% des temps d'exécution
- **Taux de succès** : Pourcentage de tests réussis (pour SC-002)
- **Statut** : RÉUSSI ou ÉCHEC selon le critère correspondant

### Exemple de rapport

```
=== Benchmark: Création d'immeubles (SC-001) ===
Temps moyen: 0.123 secondes
Temps médian: 0.118 secondes
95e percentile: 0.156 secondes
Critère SC-001 (< 5 secondes): RÉUSSI

=== Benchmark: Prévention des doublons d'identifiants QR (SC-002) ===
Taux de succès: 100.00%
Critère SC-002 (100% de prévention): RÉUSSI

=== Benchmark: Génération de QR codes (SC-003) ===
Temps moyen: 0.045 secondes
Temps médian: 0.042 secondes
95e percentile: 0.068 secondes
Critère SC-003 (< 2 secondes): RÉUSSI

=== Benchmark: Recherche d'immeubles par QR code (SC-004) ===
Temps moyen: 0.015 secondes
Temps médian: 0.012 secondes
95e percentile: 0.025 secondes
Critère SC-004 (< 1 seconde): RÉUSSI

=== Résumé des résultats ===
create_building: RÉUSSI
duplicate_prevention: RÉUSSI
generate_qr: RÉUSSI
find_building: RÉUSSI

Résultat global: RÉUSSI
```

## Historique des résultats

Les résultats des benchmarks sont sauvegardés au format JSON dans le dossier `scripts/benchmarks/results/` avec un horodatage, ce qui permet de suivre l'évolution des performances au fil du temps.

## Optimisation des performances

Si les critères de performance ne sont pas atteints, voici quelques pistes d'optimisation :

### SC-001: Création d'immeubles
- Optimiser les requêtes SQL d'insertion
- Réduire le nombre de validations ou les optimiser
- Utiliser des transactions groupées pour plusieurs opérations

### SC-002: Prévention des doublons
- Vérifier les index sur la colonne QR_CODE_NUMBER
- Optimiser l'algorithme de génération des identifiants QR

### SC-003: Génération de QR codes
- Réduire la résolution des QR codes si nécessaire
- Optimiser les opérations d'écriture sur le disque
- Utiliser un cache pour les QR codes fréquemment générés

### SC-004: Recherche d'immeubles
- Vérifier les index sur la colonne QR_CODE_NUMBER
- Optimiser les requêtes SQL de recherche
- Mettre en cache les résultats de recherche fréquents

## Environnement de référence

Les critères de performance sont définis pour un "poste standard", qui correspond aux spécifications suivantes :

- Processeur: Intel Core i5 (8e génération ou équivalent)
- RAM: 8 Go
- Disque: SSD
- Système d'exploitation: Linux/macOS/Windows
- PostgreSQL: Version 12 ou supérieure
- Python: Version 3.8 ou supérieure

Les performances peuvent varier selon l'environnement d'exécution. Il est recommandé d'exécuter les benchmarks dans un environnement similaire à l'environnement de production pour obtenir des résultats représentatifs.
