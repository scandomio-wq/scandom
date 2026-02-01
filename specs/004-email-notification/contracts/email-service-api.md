# Email Service API Contract

**Feature**: 004-email-notification  
**Date**: 2026-01-30

## Service interne (Python)

Ce service est interne et n'expose pas d'API REST. Il est appelé directement depuis le code Python.

### Interface EmailService

```python
class EmailService:
    """Service d'envoi d'emails pour les notifications d'incidents."""
    
    def send_incident_notification(
        self,
        incident_id: int,
        incident_qr_code: str,
        building_address: str,
        manager_email: str,
        incident_data: dict
    ) -> bool:
        """
        Envoie une notification email au gestionnaire pour un incident créé.
        
        Args:
            incident_id: ID de l'incident en base
            incident_qr_code: Numéro QR de l'incident (ex: IN12345)
            building_address: Adresse du bâtiment
            manager_email: Email du gestionnaire destinataire
            incident_data: Données de l'incident (zone, étage, catégorie, description, photos)
        
        Returns:
            bool: True si l'email a été envoyé avec succès
        
        Raises:
            EmailConfigurationError: Configuration SMTP invalide
            EmailSendError: Erreur lors de l'envoi
        """
        pass
```

### Interface Celery Task

```python
@celery.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(SMTPException, ConnectionError),
    retry_backoff=True
)
def send_incident_email_task(
    self,
    incident_id: int,
    incident_qr_code: str,
    building_address: str,
    manager_email: str,
    incident_data: dict
) -> dict:
    """
    Tâche Celery asynchrone pour l'envoi d'email.
    
    Returns:
        dict: {
            "success": bool,
            "notification_id": int,
            "error": str | None
        }
    """
    pass
```

## Structures de données

### IncidentData (input)

```python
@dataclass
class IncidentData:
    zone: str              # Zone de l'incident
    floor: str             # Étage
    category: str          # Catégorie d'incident
    description: str       # Description libre
    photo_urls: list[str]  # URLs des photos (peut être vide)
    reporter_phone: str    # Téléphone du déclarant
    created_at: datetime   # Date de création
```

### EmailNotificationResult (output)

```python
@dataclass
class EmailNotificationResult:
    success: bool
    notification_id: int | None
    error_message: str | None
    sent_at: datetime | None
```

## Template HTML

### Variables disponibles

| Variable | Type | Description |
|----------|------|-------------|
| `incident_qr_code` | str | Numéro QR de l'incident |
| `building_address` | str | Adresse du bâtiment |
| `zone` | str | Zone concernée |
| `floor` | str | Étage |
| `category` | str | Catégorie d'incident |
| `description` | str | Description de l'incident |
| `photo_urls` | list[str] | Liste des URLs des photos |
| `reporter_phone` | str | Téléphone du déclarant |
| `created_at` | str | Date de création formatée |

### Exemple de rendu

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Incident {{ incident_qr_code }}</title>
</head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h1 style="color: #333;">L'incident n°{{ incident_qr_code }} a été créé</h1>
    
    <div style="background: #f5f5f5; padding: 15px; border-radius: 5px;">
        <h2>Détails de l'incident</h2>
        <p><strong>Bâtiment:</strong> {{ building_address }}</p>
        <p><strong>Zone:</strong> {{ zone }}</p>
        <p><strong>Étage:</strong> {{ floor }}</p>
        <p><strong>Catégorie:</strong> {{ category }}</p>
        <p><strong>Description:</strong> {{ description }}</p>
        <p><strong>Déclaré le:</strong> {{ created_at }}</p>
        <p><strong>Contact déclarant:</strong> {{ reporter_phone }}</p>
    </div>
    
    {% if photo_urls %}
    <div style="margin-top: 20px;">
        <h2>Photos</h2>
        <ul>
        {% for url in photo_urls %}
            <li><a href="{{ url }}">Photo {{ loop.index }}</a></li>
        {% endfor %}
        </ul>
    </div>
    {% endif %}
    
    <footer style="margin-top: 30px; color: #666; font-size: 12px;">
        <p>Ce message a été envoyé automatiquement par le système SCANDOM.</p>
    </footer>
</body>
</html>
```

## Codes d'erreur

| Code | Description | Action |
|------|-------------|--------|
| `EMAIL_CONFIG_ERROR` | Configuration SMTP manquante ou invalide | Vérifier les variables d'environnement |
| `EMAIL_SEND_ERROR` | Erreur lors de l'envoi SMTP | Retry automatique (max 3) |
| `EMAIL_INVALID_RECIPIENT` | Adresse email destinataire invalide | Log warning, pas de retry |
| `EMAIL_TEMPLATE_ERROR` | Erreur de rendu du template | Log error, pas de retry |
