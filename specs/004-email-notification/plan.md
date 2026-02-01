# Implementation Plan: Email Notification for Incidents

**Branch**: `004-email-notification` | **Date**: 2026-01-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-email-notification/spec.md`

## Summary

Implémenter un système de notification par email pour informer les gestionnaires de bâtiments lors de la création d'incidents. Le système utilise SMTP configurable, envoie des emails HTML de manière asynchrone via Celery, et conserve un historique des notifications dans PostgreSQL.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Flask, Celery, smtplib (stdlib), Jinja2 (templates HTML)  
**Storage**: PostgreSQL (table `email_notifications`)  
**Testing**: pytest  
**Target Platform**: Linux server  
**Project Type**: Single project (extension du backend existant)  
**Performance Goals**: 100 envois/minute, <30s latence d'envoi  
**Constraints**: Envoi asynchrone obligatoire, pas de pièces jointes  
**Scale/Scope**: ~100 emails/jour estimé

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Statut | Commentaire |
|----------|--------|-------------|
| PostgreSQL comme source de vérité | ✅ PASS | Table `email_notifications` dans PostgreSQL |
| CLI-first | ✅ PASS | Non applicable (fonctionnalité automatique) |
| QR codes uniques, stables et traçables | ✅ PASS | Utilise le QR code de l'incident existant |
| Sécurité et confidentialité par défaut | ✅ PASS | Pas de données sensibles dans les emails au-delà des infos incident |
| Simplicité avant tout | ✅ PASS | Utilise smtplib standard + Celery existant |
| Tests unitaires (80% couverture) | ✅ PASS | Tests email module validés (3 tests passent) |
| Performance (<5s création incident) | ✅ PASS | Envoi asynchrone ne bloque pas la création |
| Validation des données | ✅ PASS | Validation email destinataire |
| Traçabilité | ✅ PASS | Historique avec horodatage dans `email_notifications` |
| Immutabilité des données critiques | ✅ PASS | Non applicable |
| Compatibilité ascendante | ✅ PASS | Nouvelle fonctionnalité, pas de breaking change |
| Documentation systématique | ✅ PASS | README et quickstart mis à jour |

**Résultat**: ✅ PASS - Aucune violation majeure

## Project Structure

### Documentation (this feature)

```text
specs/004-email-notification/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── email/                    # Nouveau module email
│   ├── __init__.py
│   ├── config.py             # Configuration SMTP
│   ├── sender.py             # Service d'envoi d'email
│   ├── templates/            # Templates HTML Jinja2
│   │   └── incident_created.html
│   └── tasks.py              # Tâches Celery asynchrones
├── whatsapp/                 # Module existant (intégration)
│   └── conversation_manager.py  # Appel du service email après création incident

config/
└── email/
    └── config.ini            # Configuration SMTP

migrations/
└── 006_create_email_notifications.sql  # Table email_notifications

tests/
└── email/
    ├── test_sender.py
    └── test_tasks.py
```

**Structure Decision**: Extension du projet existant avec un nouveau module `src/email/` suivant la même architecture que `src/whatsapp/`.

## Complexity Tracking

Aucune violation de la constitution nécessitant justification.
