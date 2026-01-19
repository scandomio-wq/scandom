-- Migration: 001_create_building_table.sql
-- Description: Création de la table T_BUILDING pour stocker les informations des immeubles

-- Création de la table T_BUILDING
CREATE TABLE IF NOT EXISTS T_BUILDING (
    ID SERIAL PRIMARY KEY,
    CREATION_DATE TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LOCATION VARCHAR(255) NOT NULL,
    EMAIL_GESTIONNAIRE VARCHAR(100),
    NOTES TEXT,
    QR_CODE_NUMBER VARCHAR(50) NOT NULL
);

-- Ajout de la contrainte d'unicité sur QR_CODE_NUMBER
ALTER TABLE T_BUILDING ADD CONSTRAINT uq_building_qr_code_number UNIQUE (QR_CODE_NUMBER);

-- Création d'un index pour la recherche rapide par QR_CODE_NUMBER
CREATE INDEX IF NOT EXISTS idx_qr_code_number ON T_BUILDING(QR_CODE_NUMBER);

-- Commentaires sur les colonnes
COMMENT ON TABLE T_BUILDING IS 'Table stockant les informations des immeubles';
COMMENT ON COLUMN T_BUILDING.ID IS 'Identifiant unique auto-incrémenté';
COMMENT ON COLUMN T_BUILDING.CREATION_DATE IS 'Date et heure de création de l''enregistrement';
COMMENT ON COLUMN T_BUILDING.LOCATION IS 'Adresse ou emplacement de l''immeuble';
COMMENT ON COLUMN T_BUILDING.EMAIL_GESTIONNAIRE IS 'Email du gestionnaire de l''immeuble';
COMMENT ON COLUMN T_BUILDING.NOTES IS 'Notes ou informations supplémentaires';
COMMENT ON COLUMN T_BUILDING.QR_CODE_NUMBER IS 'Identifiant unique utilisé dans le QR code';
