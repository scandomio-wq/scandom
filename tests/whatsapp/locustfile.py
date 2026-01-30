"""
Tests de performance pour le webhook WhatsApp avec Locust.

Ce script simule une charge importante sur le webhook WhatsApp
pour vérifier sa capacité à gérer de nombreuses conversations simultanées.

Pour exécuter:
    locust -f locustfile.py --host=http://localhost:5000
"""

import json
import random
import time
from locust import HttpUser, task, between


class WhatsAppWebhookUser(HttpUser):
    """Utilisateur simulé pour les tests de charge du webhook WhatsApp."""
    
    # Temps d'attente entre les requêtes (1-3 secondes)
    wait_time = between(1, 3)
    
    def on_start(self):
        """Initialisation avant le début des tests."""
        # Générer un numéro de téléphone unique pour cet utilisateur
        self.phone_number = f"+336{random.randint(10000000, 99999999)}"
        
        # Étape actuelle de la conversation
        self.current_step = "welcome"
        
        # Compteur pour les SIDs uniques
        self.message_counter = 0
        
        # Données collectées
        self.collected_data = {}
    
    def _get_next_sid(self):
        """Génère un SID unique pour chaque message."""
        self.message_counter += 1
        return f"SM{self.message_counter:012d}"
    
    def _send_message(self, body):
        """
        Envoie un message simulé au webhook Twilio.
        
        Args:
            body: Corps du message
        """
        # Créer les données du formulaire Twilio
        data = {
            'MessageSid': self._get_next_sid(),
            'From': self.phone_number,
            'To': '+14155238886',  # Numéro Twilio
            'Body': body,
            'NumMedia': '0'
        }
        
        # Ajouter un en-tête X-Twilio-Signature simulé
        headers = {
            'X-Twilio-Signature': 'simulated_signature_for_testing'
        }
        
        # Envoyer la requête POST au webhook
        with self.client.post("/api/webhook/twilio", data=data, headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                # Vérifier que la réponse est au format TwiML
                if '<?xml version="1.0" encoding="UTF-8"?>' in response.text and '<Response>' in response.text:
                    response.success()
                    
                    # Avancer dans les étapes de la conversation
                    self._advance_conversation_step(response.text)
                else:
                    response.failure("La réponse n'est pas au format TwiML")
            else:
                response.failure(f"Échec de la requête: {response.status_code}")
    
    def _advance_conversation_step(self, response_text):
        """
        Avance dans les étapes de la conversation en fonction de la réponse.
        
        Args:
            response_text: Texte de la réponse TwiML
        """
        if "code QR du bâtiment" in response_text:
            self.current_step = "building_qr"
        elif "décrire" in response_text:
            self.current_step = "description"
        elif "zone du bâtiment" in response_text:
            self.current_step = "zone"
        elif "étage" in response_text:
            self.current_step = "etage"
        elif "priorité" in response_text:
            self.current_step = "priorite"
        elif "numéro de téléphone" in response_text:
            self.current_step = "reporter_phone"
        elif "adresse email" in response_text:
            self.current_step = "reporter_email"
        elif "résumé" in response_text:
            self.current_step = "confirmation"
        elif "succès" in response_text:
            self.current_step = "completed"
    
    def _get_response_for_step(self):
        """
        Génère une réponse appropriée pour l'étape actuelle.
        
        Returns:
            str: Réponse pour l'étape actuelle
        """
        if self.current_step == "welcome":
            return "Bonjour"
        elif self.current_step == "building_qr":
            building_qr = f"QR{random.randint(10000, 99999)}"
            self.collected_data["building_qr"] = building_qr
            return building_qr
        elif self.current_step == "description":
            descriptions = [
                "Fuite d'eau dans les toilettes",
                "Ampoule grillée dans le couloir",
                "Porte cassée",
                "Problème de chauffage",
                "Vitre brisée"
            ]
            description = random.choice(descriptions)
            self.collected_data["description"] = description
            return description
        elif self.current_step == "zone":
            zones = [
                "Hall d'entrée",
                "Toilettes hommes",
                "Toilettes femmes",
                "Couloir principal",
                "Salle de réunion"
            ]
            zone = random.choice(zones)
            self.collected_data["zone"] = zone
            return zone
        elif self.current_step == "etage":
            etages = ["RDC", "1er", "2ème", "3ème", "Sous-sol"]
            etage = random.choice(etages)
            self.collected_data["etage"] = etage
            return etage
        elif self.current_step == "priorite":
            priorites = ["haute", "moyenne", "basse"]
            priorite = random.choice(priorites)
            self.collected_data["priorite"] = priorite
            return priorite
        elif self.current_step == "reporter_phone":
            return self.phone_number
        elif self.current_step == "reporter_email":
            email = f"test{random.randint(1000, 9999)}@example.com"
            self.collected_data["reporter_email"] = email
            return email
        elif self.current_step == "confirmation":
            return "oui"
        else:
            return "Bonjour"  # Recommencer
    
    @task(1)
    def send_next_message(self):
        """Envoie le message approprié pour l'étape actuelle de la conversation."""
        # Si la conversation est terminée, recommencer
        if self.current_step == "completed":
            self.current_step = "welcome"
            self.collected_data = {}
        
        # Envoyer le message approprié pour l'étape actuelle
        message = self._get_response_for_step()
        self._send_message(message)
    
    @task(0.1)
    def send_help_command(self):
        """Envoie occasionnellement une commande d'aide."""
        self._send_message("aide")
    
    @task(0.05)
    def send_cancel_command(self):
        """Envoie rarement une commande d'annulation."""
        self._send_message("annuler")
        # Après annulation, recommencer
        self.current_step = "welcome"
        self.collected_data = {}
    
    @task(0.2)
    def send_invalid_input(self):
        """Envoie occasionnellement une entrée invalide."""
        invalid_inputs = {
            "building_qr": "INVALID",
            "description": "OK",
            "zone": "X",
            "etage": "",
            "priorite": "urgente",
            "reporter_phone": "0612345678",  # Format invalide
            "reporter_email": "invalid-email",
            "confirmation": "peut-être"
        }
        
        if self.current_step in invalid_inputs:
            self._send_message(invalid_inputs[self.current_step])


class StatusCallbackUser(HttpUser):
    """Utilisateur simulé pour les callbacks de statut de message."""
    
    # Temps d'attente entre les requêtes (5-10 secondes)
    wait_time = between(5, 10)
    
    def on_start(self):
        """Initialisation avant le début des tests."""
        # Compteur pour les SIDs uniques
        self.message_counter = 0
    
    def _get_next_sid(self):
        """Génère un SID unique pour chaque message."""
        self.message_counter += 1
        return f"SM{self.message_counter:012d}"
    
    @task
    def send_status_callback(self):
        """Envoie un callback de statut de message."""
        # Statuts possibles
        statuses = ["sent", "delivered", "read", "failed"]
        
        # Créer les données du formulaire
        data = {
            'MessageSid': self._get_next_sid(),
            'MessageStatus': random.choice(statuses),
            'To': f"+336{random.randint(10000000, 99999999)}",
            'From': '+14155238886'
        }
        
        # Ajouter un en-tête X-Twilio-Signature simulé
        headers = {
            'X-Twilio-Signature': 'simulated_signature_for_testing'
        }
        
        # Envoyer la requête POST au webhook de statut
        with self.client.post("/api/webhook/status", data=data, headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Échec de la requête: {response.status_code}")
