#!/bin/bash
# Script d'initialisation de la base de données PostgreSQL pour QR Building Registry

# Charger les variables d'environnement depuis le fichier de configuration
if [ -f "../config/db_config.ini" ]; then
    DB_HOST=$(grep -A 5 '\[postgresql\]' ../config/db_config.ini | grep 'host' | cut -d'=' -f2 | tr -d ' ')
    DB_PORT=$(grep -A 5 '\[postgresql\]' ../config/db_config.ini | grep 'port' | cut -d'=' -f2 | tr -d ' ')
    DB_NAME=$(grep -A 5 '\[postgresql\]' ../config/db_config.ini | grep 'database' | cut -d'=' -f2 | tr -d ' ')
    DB_USER=$(grep -A 5 '\[postgresql\]' ../config/db_config.ini | grep 'user' | cut -d'=' -f2 | tr -d ' ')
    DB_PASSWORD=$(grep -A 5 '\[postgresql\]' ../config/db_config.ini | grep 'password' | cut -d'=' -f2 | tr -d ' ')
else
    echo "Erreur: Fichier de configuration non trouvé."
    echo "Veuillez copier config/db_config.ini.example vers config/db_config.ini et configurer les paramètres."
    exit 1
fi

# Vérifier si la base de données existe déjà
echo "Vérification de l'existence de la base de données $DB_NAME..."
if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo "La base de données $DB_NAME existe déjà."
else
    echo "Création de la base de données $DB_NAME..."
    PGPASSWORD="$DB_PASSWORD" createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"
    if [ $? -ne 0 ]; then
        echo "Erreur: Impossible de créer la base de données."
        exit 1
    fi
    echo "Base de données $DB_NAME créée avec succès."
fi

# Exécuter le script de création de la table T_BUILDING
echo "Création de la table T_BUILDING..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f 001_create_building_table.sql

if [ $? -ne 0 ]; then
    echo "Erreur: Impossible de créer la table T_BUILDING."
    exit 1
fi

echo "Table T_BUILDING créée avec succès."
echo "Initialisation de la base de données terminée."
