# Guide d'installation et configuration de Redis

Ce guide explique comment installer et configurer Redis pour l'intégration WhatsApp, afin de gérer la persistance des états de conversation et les files d'attente Celery.

## Installation de Redis

### Sur Ubuntu/Debian

```bash
# Mettre à jour les paquets
sudo apt update

# Installer Redis
sudo apt install redis-server

# Vérifier que Redis est en cours d'exécution
sudo systemctl status redis-server
```

### Sur CentOS/RHEL

```bash
# Installer EPEL repository
sudo yum install epel-release

# Installer Redis
sudo yum install redis

# Démarrer Redis
sudo systemctl start redis

# Activer Redis au démarrage
sudo systemctl enable redis
```

### Sur macOS

```bash
# Avec Homebrew
brew install redis

# Démarrer Redis
brew services start redis
```

## Configuration de Redis

1. Copiez le fichier de configuration fourni dans le répertoire approprié :

```bash
sudo cp /home/jeremy/Documents/Projet/scandom/config/whatsapp/redis.conf /etc/redis/redis.conf
```

2. Redémarrez le service Redis :

```bash
sudo systemctl restart redis-server
```

## Vérification de l'installation

1. Connectez-vous à Redis CLI :

```bash
redis-cli
```

2. Testez la connexion :

```
> PING
PONG
```

3. Testez la persistance :

```
> SET test "Hello Redis"
OK
> GET test
"Hello Redis"
```

## Configuration pour Celery

Redis est maintenant configuré pour être utilisé comme broker et backend pour Celery. Les paramètres de connexion sont définis dans le fichier de configuration `/home/jeremy/Documents/Projet/scandom/config/whatsapp/config.ini`.

## Persistance des états de conversation

Redis est configuré pour sauvegarder périodiquement les données sur disque avec les paramètres suivants :
- Toutes les 15 minutes si au moins 1 clé a changé
- Toutes les 5 minutes si au moins 10 clés ont changé
- Toutes les 60 secondes si au moins 10000 clés ont changé

## Politique d'expiration

Les états de conversation seront automatiquement supprimés après 24 heures (86400 secondes) d'inactivité, conformément aux exigences du projet.

## Sécurité

Par défaut, Redis n'est accessible que depuis localhost (127.0.0.1). Si vous devez permettre l'accès depuis d'autres serveurs :

1. Modifiez la directive `bind` dans le fichier de configuration
2. Définissez un mot de passe avec la directive `requirepass`
3. Assurez-vous que votre pare-feu est correctement configuré

## Surveillance

Pour surveiller Redis en temps réel :

```bash
redis-cli info | grep used_memory
redis-cli --stat
redis-cli monitor  # Attention : peut affecter les performances en production
```
