#!/usr/bin/env python3
"""
Script pour exécuter tous les tests de l'intégration WhatsApp et générer un rapport.

Ce script exécute les tests unitaires, les tests d'intégration, et vérifie les critères de succès
pour produire un rapport complet sur l'état de l'intégration WhatsApp.
"""

import os
import sys
import json
import time
import datetime
import subprocess
import argparse
import unittest
from typing import Dict, List, Any, Tuple

# Ajouter le répertoire parent au path pour pouvoir importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def run_unit_tests() -> Tuple[bool, Dict[str, Any]]:
    """
    Exécute les tests unitaires.
    
    Returns:
        Tuple[bool, Dict[str, Any]]: (Succès, Résultats)
    """
    print("\n=== EXÉCUTION DES TESTS UNITAIRES ===\n")
    
    # Découvrir et exécuter les tests unitaires
    loader = unittest.TestLoader()
    suite = loader.discover(os.path.dirname(os.path.abspath(__file__)), pattern="test_*.py")
    
    # Exécuter les tests
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Collecter les résultats
    success = result.wasSuccessful()
    results = {
        "total": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "success_rate": ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100 if result.testsRun > 0 else 0
    }
    
    return success, results


def run_e2e_tests(base_url: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Exécute les tests de bout en bout.
    
    Args:
        base_url: URL de base pour les tests
        
    Returns:
        Tuple[bool, Dict[str, Any]]: (Succès, Résultats)
    """
    print("\n=== EXÉCUTION DES TESTS DE BOUT EN BOUT ===\n")
    
    # Modifier le fichier de test pour utiliser l'URL fournie
    test_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_webhook_e2e.py")
    
    with open(test_file, "r") as f:
        content = f.read()
    
    # Remplacer l'URL de base
    content = content.replace('BASE_URL = "http://localhost:5000/api/webhook"', f'BASE_URL = "{base_url}/api/webhook"')
    
    # Sauvegarder temporairement
    temp_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_test_webhook_e2e.py")
    
    with open(temp_file, "w") as f:
        f.write(content)
    
    try:
        # Exécuter les tests
        result = subprocess.run([sys.executable, temp_file], capture_output=True, text=True)
        
        # Analyser les résultats
        success = result.returncode == 0
        
        # Extraire les statistiques de test
        import re
        
        match = re.search(r"Ran (\d+) tests? in [\d\.]+s", result.stdout)
        total_tests = int(match.group(1)) if match else 0
        
        failures_match = re.search(r"FAILED \(failures=(\d+)\)", result.stdout)
        failures = int(failures_match.group(1)) if failures_match else 0
        
        errors_match = re.search(r"FAILED \(errors=(\d+)\)", result.stdout)
        errors = int(errors_match.group(1)) if errors_match else 0
        
        results = {
            "total": total_tests,
            "failures": failures,
            "errors": errors,
            "success_rate": ((total_tests - failures - errors) / total_tests) * 100 if total_tests > 0 else 0,
            "output": result.stdout,
            "error_output": result.stderr
        }
        
        return success, results
    
    finally:
        # Supprimer le fichier temporaire
        if os.path.exists(temp_file):
            os.remove(temp_file)


def run_performance_tests(host: str, duration: int = 60, users: int = 100) -> Tuple[bool, Dict[str, Any]]:
    """
    Exécute les tests de performance avec Locust.
    
    Args:
        host: Hôte à tester
        duration: Durée du test en secondes
        users: Nombre d'utilisateurs simulés
        
    Returns:
        Tuple[bool, Dict[str, Any]]: (Succès, Résultats)
    """
    print(f"\n=== EXÉCUTION DES TESTS DE PERFORMANCE ({users} utilisateurs pendant {duration}s) ===\n")
    
    # Vérifier si Locust est installé
    try:
        subprocess.run(["locust", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Locust n'est pas installé. Installation en cours...")
        subprocess.run([sys.executable, "-m", "pip", "install", "locust"], check=True)
    
    # Chemin vers le fichier Locust
    locustfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locustfile.py")
    
    # Fichier de sortie CSV
    csv_prefix = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locust_results")
    
    # Exécuter Locust en mode headless
    cmd = [
        "locust",
        "-f", locustfile,
        "--host", host,
        "--headless",
        "--users", str(users),
        "--spawn-rate", "10",
        "--run-time", f"{duration}s",
        "--csv", csv_prefix
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Analyser les résultats
        success = result.returncode == 0
        
        # Lire les fichiers CSV générés
        stats_file = f"{csv_prefix}_stats.csv"
        stats = []
        
        if os.path.exists(stats_file):
            import csv
            with open(stats_file, "r") as f:
                reader = csv.DictReader(f)
                stats = list(reader)
        
        # Extraire les métriques clés
        response_times = [float(row.get("Median Response Time", 0)) for row in stats]
        requests_per_second = [float(row.get("Requests/s", 0)) for row in stats]
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        avg_rps = sum(requests_per_second) / len(requests_per_second) if requests_per_second else 0
        
        results = {
            "success": success,
            "average_response_time": avg_response_time,
            "average_requests_per_second": avg_rps,
            "users": users,
            "duration": duration,
            "stats": stats,
            "output": result.stdout,
            "error_output": result.stderr
        }
        
        return success, results
    
    except Exception as e:
        return False, {"error": str(e)}


def verify_success_criteria() -> Tuple[bool, Dict[str, Any]]:
    """
    Vérifie les critères de succès.
    
    Returns:
        Tuple[bool, Dict[str, Any]]: (Succès, Résultats)
    """
    print("\n=== VÉRIFICATION DES CRITÈRES DE SUCCÈS ===\n")
    
    # Chemin vers le script de vérification
    verify_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_success_criteria.py")
    
    # Fichier de sortie JSON
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "success_criteria_results.json")
    
    # Exécuter le script
    result = subprocess.run([sys.executable, verify_script, "--output", output_file], capture_output=True, text=True)
    
    # Analyser les résultats
    success = result.returncode == 0
    
    # Lire le fichier JSON généré
    results = {}
    
    if os.path.exists(output_file):
        with open(output_file, "r") as f:
            results = json.load(f)
    
    # Compter les critères satisfaits
    criteria_count = sum(1 for k in results.keys() if k != "metadata")
    pass_count = sum(1 for r in results.values() if isinstance(r, dict) and r.get("status") == "PASS")
    
    results["summary"] = {
        "total_criteria": criteria_count,
        "passed_criteria": pass_count,
        "success_rate": (pass_count / criteria_count) * 100 if criteria_count > 0 else 0
    }
    
    return success, results


def generate_report(unit_results: Dict[str, Any], e2e_results: Dict[str, Any],
                   performance_results: Dict[str, Any], criteria_results: Dict[str, Any]) -> str:
    """
    Génère un rapport HTML complet.
    
    Args:
        unit_results: Résultats des tests unitaires
        e2e_results: Résultats des tests de bout en bout
        performance_results: Résultats des tests de performance
        criteria_results: Résultats de la vérification des critères de succès
        
    Returns:
        str: Chemin vers le rapport HTML
    """
    print("\n=== GÉNÉRATION DU RAPPORT ===\n")
    
    # Chemin vers le rapport
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whatsapp_integration_report.html")
    
    # Créer le contenu HTML
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport d'intégration WhatsApp</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3 {{
            color: #333;
        }}
        .section {{
            margin-bottom: 30px;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }}
        .pass {{
            color: green;
        }}
        .fail {{
            color: red;
        }}
        .warning {{
            color: orange;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        th, td {{
            padding: 10px;
            border: 1px solid #ddd;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        .progress-bar {{
            height: 20px;
            background-color: #e0e0e0;
            border-radius: 10px;
            margin-bottom: 10px;
        }}
        .progress {{
            height: 100%;
            background-color: #4CAF50;
            border-radius: 10px;
            text-align: center;
            line-height: 20px;
            color: white;
        }}
        .summary {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
        }}
        .summary-box {{
            flex: 1;
            padding: 15px;
            margin: 0 10px;
            background-color: #f9f9f9;
            border-radius: 5px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <h1>Rapport d'intégration WhatsApp</h1>
    <p>Généré le {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</p>
    
    <div class="summary">
        <div class="summary-box">
            <h3>Tests unitaires</h3>
            <div class="progress-bar">
                <div class="progress" style="width: {unit_results.get('success_rate', 0)}%">
                    {unit_results.get('success_rate', 0):.1f}%
                </div>
            </div>
            <p>{unit_results.get('total', 0) - unit_results.get('failures', 0) - unit_results.get('errors', 0)}/{unit_results.get('total', 0)} tests réussis</p>
        </div>
        
        <div class="summary-box">
            <h3>Tests E2E</h3>
            <div class="progress-bar">
                <div class="progress" style="width: {e2e_results.get('success_rate', 0)}%">
                    {e2e_results.get('success_rate', 0):.1f}%
                </div>
            </div>
            <p>{e2e_results.get('total', 0) - e2e_results.get('failures', 0) - e2e_results.get('errors', 0)}/{e2e_results.get('total', 0)} tests réussis</p>
        </div>
        
        <div class="summary-box">
            <h3>Critères de succès</h3>
            <div class="progress-bar">
                <div class="progress" style="width: {criteria_results.get('summary', {}).get('success_rate', 0)}%">
                    {criteria_results.get('summary', {}).get('success_rate', 0):.1f}%
                </div>
            </div>
            <p>{criteria_results.get('summary', {}).get('passed_criteria', 0)}/{criteria_results.get('summary', {}).get('total_criteria', 0)} critères satisfaits</p>
        </div>
    </div>
    
    <div class="section">
        <h2>Tests unitaires</h2>
        <table>
            <tr>
                <th>Métrique</th>
                <th>Valeur</th>
            </tr>
            <tr>
                <td>Tests exécutés</td>
                <td>{unit_results.get('total', 0)}</td>
            </tr>
            <tr>
                <td>Tests réussis</td>
                <td>{unit_results.get('total', 0) - unit_results.get('failures', 0) - unit_results.get('errors', 0)}</td>
            </tr>
            <tr>
                <td>Échecs</td>
                <td>{unit_results.get('failures', 0)}</td>
            </tr>
            <tr>
                <td>Erreurs</td>
                <td>{unit_results.get('errors', 0)}</td>
            </tr>
            <tr>
                <td>Tests ignorés</td>
                <td>{unit_results.get('skipped', 0)}</td>
            </tr>
            <tr>
                <td>Taux de réussite</td>
                <td>{unit_results.get('success_rate', 0):.2f}%</td>
            </tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Tests de bout en bout</h2>
        <table>
            <tr>
                <th>Métrique</th>
                <th>Valeur</th>
            </tr>
            <tr>
                <td>Tests exécutés</td>
                <td>{e2e_results.get('total', 0)}</td>
            </tr>
            <tr>
                <td>Tests réussis</td>
                <td>{e2e_results.get('total', 0) - e2e_results.get('failures', 0) - e2e_results.get('errors', 0)}</td>
            </tr>
            <tr>
                <td>Échecs</td>
                <td>{e2e_results.get('failures', 0)}</td>
            </tr>
            <tr>
                <td>Erreurs</td>
                <td>{e2e_results.get('errors', 0)}</td>
            </tr>
            <tr>
                <td>Taux de réussite</td>
                <td>{e2e_results.get('success_rate', 0):.2f}%</td>
            </tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Tests de performance</h2>
        <table>
            <tr>
                <th>Métrique</th>
                <th>Valeur</th>
            </tr>
            <tr>
                <td>Utilisateurs simulés</td>
                <td>{performance_results.get('users', 0)}</td>
            </tr>
            <tr>
                <td>Durée du test</td>
                <td>{performance_results.get('duration', 0)} secondes</td>
            </tr>
            <tr>
                <td>Temps de réponse moyen</td>
                <td>{performance_results.get('average_response_time', 0):.2f} ms</td>
            </tr>
            <tr>
                <td>Requêtes par seconde</td>
                <td>{performance_results.get('average_requests_per_second', 0):.2f}</td>
            </tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Critères de succès</h2>
        <table>
            <tr>
                <th>Critère</th>
                <th>Statut</th>
                <th>Description</th>
            </tr>
"""
    
    # Ajouter chaque critère
    for criterion, result in criteria_results.items():
        if criterion != "metadata" and criterion != "summary" and isinstance(result, dict):
            status = result.get("status", "UNKNOWN")
            message = result.get("message", "")
            
            status_class = {
                "PASS": "pass",
                "FAIL": "fail",
                "INCONCLUSIVE": "warning",
                "ERROR": "fail",
                "UNKNOWN": "warning"
            }.get(status, "")
            
            html += f"""
            <tr>
                <td>{criterion}</td>
                <td class="{status_class}">{status}</td>
                <td>{message}</td>
            </tr>
            """
    
    html += """
        </table>
    </div>
    
    <div class="section">
        <h2>Conclusion</h2>
"""
    
    # Calculer le score global
    unit_score = unit_results.get('success_rate', 0)
    e2e_score = e2e_results.get('success_rate', 0)
    criteria_score = criteria_results.get('summary', {}).get('success_rate', 0)
    
    global_score = (unit_score + e2e_score + criteria_score) / 3
    
    if global_score >= 90:
        conclusion = "L'intégration WhatsApp est prête pour la production."
        conclusion_class = "pass"
    elif global_score >= 75:
        conclusion = "L'intégration WhatsApp est presque prête, mais nécessite quelques corrections."
        conclusion_class = "warning"
    else:
        conclusion = "L'intégration WhatsApp nécessite des corrections importantes avant d'être mise en production."
        conclusion_class = "fail"
    
    html += f"""
        <p class="{conclusion_class}"><strong>Score global: {global_score:.2f}%</strong></p>
        <p>{conclusion}</p>
        
        <h3>Recommandations</h3>
        <ul>
"""
    
    # Générer des recommandations basées sur les résultats
    if unit_results.get('failures', 0) > 0 or unit_results.get('errors', 0) > 0:
        html += "<li>Corriger les tests unitaires qui échouent.</li>"
    
    if e2e_results.get('failures', 0) > 0 or e2e_results.get('errors', 0) > 0:
        html += "<li>Résoudre les problèmes identifiés dans les tests de bout en bout.</li>"
    
    # Ajouter des recommandations pour chaque critère non satisfait
    for criterion, result in criteria_results.items():
        if criterion != "metadata" and criterion != "summary" and isinstance(result, dict):
            if result.get("status", "") == "FAIL":
                html += f"<li>Améliorer le critère {criterion}: {result.get('message', '')}</li>"
    
    html += """
        </ul>
    </div>
</body>
</html>
"""
    
    # Écrire le rapport dans un fichier
    with open(report_path, "w") as f:
        f.write(html)
    
    print(f"Rapport généré: {report_path}")
    
    return report_path


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(description="Exécution des tests d'intégration WhatsApp")
    parser.add_argument('--host', type=str, default='http://localhost:5000', help='URL de base pour les tests')
    parser.add_argument('--duration', type=int, default=60, help='Durée des tests de performance en secondes')
    parser.add_argument('--users', type=int, default=100, help='Nombre d\'utilisateurs simulés pour les tests de performance')
    parser.add_argument('--skip-unit', action='store_true', help='Ignorer les tests unitaires')
    parser.add_argument('--skip-e2e', action='store_true', help='Ignorer les tests de bout en bout')
    parser.add_argument('--skip-performance', action='store_true', help='Ignorer les tests de performance')
    parser.add_argument('--skip-criteria', action='store_true', help='Ignorer la vérification des critères de succès')
    args = parser.parse_args()
    
    # Résultats des tests
    unit_results = {"success_rate": 0}
    e2e_results = {"success_rate": 0}
    performance_results = {}
    criteria_results = {"summary": {"success_rate": 0}}
    
    # Exécuter les tests unitaires
    if not args.skip_unit:
        _, unit_results = run_unit_tests()
    else:
        print("\n=== TESTS UNITAIRES IGNORÉS ===\n")
    
    # Exécuter les tests de bout en bout
    if not args.skip_e2e:
        _, e2e_results = run_e2e_tests(args.host)
    else:
        print("\n=== TESTS DE BOUT EN BOUT IGNORÉS ===\n")
    
    # Exécuter les tests de performance
    if not args.skip_performance:
        _, performance_results = run_performance_tests(args.host, args.duration, args.users)
    else:
        print("\n=== TESTS DE PERFORMANCE IGNORÉS ===\n")
    
    # Vérifier les critères de succès
    if not args.skip_criteria:
        _, criteria_results = verify_success_criteria()
    else:
        print("\n=== VÉRIFICATION DES CRITÈRES DE SUCCÈS IGNORÉE ===\n")
    
    # Générer le rapport
    report_path = generate_report(unit_results, e2e_results, performance_results, criteria_results)
    
    print(f"\nRapport complet disponible à: {report_path}")


if __name__ == '__main__':
    main()
