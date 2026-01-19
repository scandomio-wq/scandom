#!/usr/bin/env python3
"""
Script de benchmark pour mesurer les performances de l'application QR Building Registry.

Ce script mesure les performances selon les critères de succès définis:
- SC-001: Enregistrement d'un immeuble en moins de 5 secondes
- SC-002: Empêcher 100% des doublons d'identifiants QR
- SC-003: Génération d'un QR code en moins de 2 secondes (95% des cas)
- SC-004: Recherche d'un immeuble par QR en moins de 1 seconde (95% des cas)
"""

import argparse
import json
import os
import random
import statistics
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Ajouter le répertoire parent au chemin de recherche des modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.db.building_dao import BuildingDAO
from src.models.building import Building
from src.qr.generator import QRCodeGenerator


def generate_random_building() -> Dict[str, Any]:
    """
    Génère des données aléatoires pour un bâtiment.
    
    Returns:
        Dictionnaire contenant les données du bâtiment.
    """
    streets = ["Rue de la Paix", "Avenue des Champs-Élysées", "Boulevard Haussmann", 
               "Rue de Rivoli", "Avenue Montaigne", "Rue du Faubourg Saint-Honoré"]
    cities = ["Paris", "Lyon", "Marseille", "Bordeaux", "Lille", "Strasbourg"]
    postal_codes = ["75000", "69000", "13000", "33000", "59000", "67000"]
    
    street = random.choice(streets)
    number = random.randint(1, 999)
    city = random.choice(cities)
    postal_code = random.choice(postal_codes)
    
    location = f"{number} {street}, {postal_code} {city}"
    
    # 80% de chance d'avoir un email
    if random.random() < 0.8:
        domains = ["example.com", "gestion.fr", "immobilier.org", "syndic.net"]
        email = f"contact{random.randint(1, 999)}@{random.choice(domains)}"
    else:
        email = None
    
    # 60% de chance d'avoir des notes
    if random.random() < 0.6:
        notes_options = [
            "Bâtiment rénové récemment.",
            "Accès sécurisé par badge.",
            "Immeuble avec ascenseur.",
            "Parties communes en bon état.",
            "Local à vélos disponible."
        ]
        notes = " ".join(random.sample(notes_options, random.randint(1, len(notes_options))))
    else:
        notes = None
    
    return {
        "LOCATION": location,
        "EMAIL_GESTIONNAIRE": email,
        "NOTES": notes
    }


def benchmark_create_building(num_tests: int = 100) -> Tuple[List[float], float, float, float]:
    """
    Benchmark pour la création d'immeubles (SC-001).
    
    Args:
        num_tests: Nombre de tests à effectuer.
    
    Returns:
        Tuple contenant la liste des temps d'exécution, le temps moyen, le temps médian et le 95e percentile.
    """
    print(f"\n=== Benchmark: Création d'immeubles (SC-001) ===")
    print(f"Exécution de {num_tests} tests...")
    
    dao = BuildingDAO()
    times = []
    
    for i in range(num_tests):
        # Générer des données aléatoires
        data = generate_random_building()
        building = Building.from_json(data)
        
        # Mesurer le temps de création
        start_time = time.time()
        dao.create_building(building)
        end_time = time.time()
        
        execution_time = end_time - start_time
        times.append(execution_time)
        
        if (i + 1) % 10 == 0:
            print(f"  Progression: {i + 1}/{num_tests}")
    
    # Calculer les statistiques
    avg_time = statistics.mean(times)
    median_time = statistics.median(times)
    percentile_95 = sorted(times)[int(num_tests * 0.95)]
    
    print(f"Temps moyen: {avg_time:.3f} secondes")
    print(f"Temps médian: {median_time:.3f} secondes")
    print(f"95e percentile: {percentile_95:.3f} secondes")
    print(f"Critère SC-001 (< 5 secondes): {'RÉUSSI' if percentile_95 < 5 else 'ÉCHEC'}")
    
    return times, avg_time, median_time, percentile_95


def benchmark_duplicate_prevention(num_tests: int = 100) -> float:
    """
    Benchmark pour la prévention des doublons d'identifiants QR (SC-002).
    
    Args:
        num_tests: Nombre de tests à effectuer.
    
    Returns:
        Pourcentage de succès dans la prévention des doublons.
    """
    print(f"\n=== Benchmark: Prévention des doublons d'identifiants QR (SC-002) ===")
    print(f"Exécution de {num_tests} tests...")
    
    dao = BuildingDAO()
    success_count = 0
    
    # Créer un premier bâtiment
    building = Building.from_json(generate_random_building())
    building = dao.create_building(building)
    qr_code_number = building.qr_code_number
    
    for i in range(num_tests):
        # Créer un nouveau bâtiment avec le même QR_CODE_NUMBER
        new_building = Building.from_json(generate_random_building())
        new_building.qr_code_number = qr_code_number
        
        try:
            # Tenter de créer un bâtiment avec un QR_CODE_NUMBER en doublon
            dao.create_building(new_building)
            # Si on arrive ici, le doublon n'a pas été détecté
            success_count -= 1
        except Exception:
            # Le doublon a été détecté et empêché
            success_count += 1
        
        if (i + 1) % 10 == 0:
            print(f"  Progression: {i + 1}/{num_tests}")
    
    success_rate = (success_count / num_tests) * 100
    print(f"Taux de succès: {success_rate:.2f}%")
    print(f"Critère SC-002 (100% de prévention): {'RÉUSSI' if success_rate == 100 else 'ÉCHEC'}")
    
    return success_rate


def benchmark_generate_qr(num_tests: int = 100) -> Tuple[List[float], float, float, float]:
    """
    Benchmark pour la génération de QR codes (SC-003).
    
    Args:
        num_tests: Nombre de tests à effectuer.
    
    Returns:
        Tuple contenant la liste des temps d'exécution, le temps moyen, le temps médian et le 95e percentile.
    """
    print(f"\n=== Benchmark: Génération de QR codes (SC-003) ===")
    print(f"Exécution de {num_tests} tests...")
    
    # Créer un dossier temporaire pour les tests
    temp_dir = os.path.join(os.path.dirname(__file__), "temp_qr")
    os.makedirs(temp_dir, exist_ok=True)
    
    generator = QRCodeGenerator()
    times = []
    
    for i in range(num_tests):
        # Générer un identifiant QR aléatoire
        qr_code_number = f"QR{random.randint(1000000000, 9999999999)}"
        
        # Mesurer le temps de génération
        start_time = time.time()
        generator.generate_qr_code(qr_code_number, temp_dir)
        end_time = time.time()
        
        execution_time = end_time - start_time
        times.append(execution_time)
        
        if (i + 1) % 10 == 0:
            print(f"  Progression: {i + 1}/{num_tests}")
    
    # Nettoyer les fichiers temporaires
    for file in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, file))
    os.rmdir(temp_dir)
    
    # Calculer les statistiques
    avg_time = statistics.mean(times)
    median_time = statistics.median(times)
    percentile_95 = sorted(times)[int(num_tests * 0.95)]
    
    print(f"Temps moyen: {avg_time:.3f} secondes")
    print(f"Temps médian: {median_time:.3f} secondes")
    print(f"95e percentile: {percentile_95:.3f} secondes")
    print(f"Critère SC-003 (< 2 secondes): {'RÉUSSI' if percentile_95 < 2 else 'ÉCHEC'}")
    
    return times, avg_time, median_time, percentile_95


def benchmark_find_building(num_tests: int = 100) -> Tuple[List[float], float, float, float]:
    """
    Benchmark pour la recherche d'immeubles par QR code (SC-004).
    
    Args:
        num_tests: Nombre de tests à effectuer.
    
    Returns:
        Tuple contenant la liste des temps d'exécution, le temps moyen, le temps médian et le 95e percentile.
    """
    print(f"\n=== Benchmark: Recherche d'immeubles par QR code (SC-004) ===")
    print(f"Préparation des données de test...")
    
    dao = BuildingDAO()
    buildings = []
    
    # Créer des bâtiments pour le test
    for _ in range(min(num_tests, 20)):  # Limiter le nombre de bâtiments à créer
        building = Building.from_json(generate_random_building())
        buildings.append(dao.create_building(building))
    
    print(f"Exécution de {num_tests} tests...")
    times = []
    
    for i in range(num_tests):
        # Sélectionner un bâtiment aléatoire
        building = random.choice(buildings)
        
        # Mesurer le temps de recherche
        start_time = time.time()
        dao.get_building_by_qr_code(building.qr_code_number)
        end_time = time.time()
        
        execution_time = end_time - start_time
        times.append(execution_time)
        
        if (i + 1) % 10 == 0:
            print(f"  Progression: {i + 1}/{num_tests}")
    
    # Calculer les statistiques
    avg_time = statistics.mean(times)
    median_time = statistics.median(times)
    percentile_95 = sorted(times)[int(num_tests * 0.95)]
    
    print(f"Temps moyen: {avg_time:.3f} secondes")
    print(f"Temps médian: {median_time:.3f} secondes")
    print(f"95e percentile: {percentile_95:.3f} secondes")
    print(f"Critère SC-004 (< 1 seconde): {'RÉUSSI' if percentile_95 < 1 else 'ÉCHEC'}")
    
    return times, avg_time, median_time, percentile_95


def save_results(results: Dict[str, Any], output_file: str = None) -> None:
    """
    Sauvegarde les résultats des benchmarks dans un fichier JSON.
    
    Args:
        results: Résultats des benchmarks.
        output_file: Chemin du fichier de sortie. Si None, un nom par défaut est utilisé.
    """
    if output_file is None:
        # Créer le dossier results s'il n'existe pas
        results_dir = os.path.join(os.path.dirname(__file__), "results")
        os.makedirs(results_dir, exist_ok=True)
        
        # Générer un nom de fichier avec la date et l'heure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(results_dir, f"benchmark_{timestamp}.json")
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nRésultats sauvegardés dans {output_file}")


def parse_arguments():
    """
    Parse les arguments de la ligne de commande.
    
    Returns:
        Arguments parsés.
    """
    parser = argparse.ArgumentParser(description="Benchmark pour l'application QR Building Registry.")
    
    parser.add_argument(
        "--num-tests",
        type=int,
        default=100,
        help="Nombre de tests à effectuer pour chaque benchmark (défaut: 100)"
    )
    
    parser.add_argument(
        "--output",
        help="Chemin du fichier de sortie pour les résultats (défaut: auto-généré)"
    )
    
    parser.add_argument(
        "--skip-create",
        action="store_true",
        help="Ignorer le benchmark de création d'immeubles"
    )
    
    parser.add_argument(
        "--skip-duplicate",
        action="store_true",
        help="Ignorer le benchmark de prévention des doublons"
    )
    
    parser.add_argument(
        "--skip-generate",
        action="store_true",
        help="Ignorer le benchmark de génération de QR codes"
    )
    
    parser.add_argument(
        "--skip-find",
        action="store_true",
        help="Ignorer le benchmark de recherche d'immeubles"
    )
    
    return parser.parse_args()


def main():
    """Fonction principale."""
    args = parse_arguments()
    
    print("=== Benchmark QR Building Registry ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Nombre de tests par benchmark: {args.num_tests}")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "num_tests": args.num_tests,
        "benchmarks": {}
    }
    
    try:
        if not args.skip_create:
            times, avg, median, p95 = benchmark_create_building(args.num_tests)
            results["benchmarks"]["create_building"] = {
                "avg_time": avg,
                "median_time": median,
                "percentile_95": p95,
                "success": p95 < 5
            }
        
        if not args.skip_duplicate:
            success_rate = benchmark_duplicate_prevention(args.num_tests)
            results["benchmarks"]["duplicate_prevention"] = {
                "success_rate": success_rate,
                "success": success_rate == 100
            }
        
        if not args.skip_generate:
            times, avg, median, p95 = benchmark_generate_qr(args.num_tests)
            results["benchmarks"]["generate_qr"] = {
                "avg_time": avg,
                "median_time": median,
                "percentile_95": p95,
                "success": p95 < 2
            }
        
        if not args.skip_find:
            times, avg, median, p95 = benchmark_find_building(args.num_tests)
            results["benchmarks"]["find_building"] = {
                "avg_time": avg,
                "median_time": median,
                "percentile_95": p95,
                "success": p95 < 1
            }
        
        # Résumé des résultats
        print("\n=== Résumé des résultats ===")
        all_success = True
        
        for name, data in results["benchmarks"].items():
            status = "RÉUSSI" if data["success"] else "ÉCHEC"
            print(f"{name}: {status}")
            all_success = all_success and data["success"]
        
        print(f"\nRésultat global: {'RÉUSSI' if all_success else 'ÉCHEC'}")
        
        # Sauvegarder les résultats
        save_results(results, args.output)
        
    except Exception as e:
        print(f"Erreur lors de l'exécution des benchmarks: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
