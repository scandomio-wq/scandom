-- Migration pour créer la table T_INCIDENT
-- Cette table stocke les incidents signalés pour les bâtiments

-- Création de la table T_INCIDENT
CREATE TABLE IF NOT EXISTS T_INCIDENT (
    ID SERIAL PRIMARY KEY,
    BUILDING_ID INTEGER NOT NULL REFERENCES T_BUILDING(ID),
    CREATION_DATE TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    REPORTER_PHONE VARCHAR(20),
    REPORTER_EMAIL VARCHAR(100),
    INCIDENT_INFORMATION JSONB NOT NULL,
    QR_CODE_NUMBER VARCHAR(50) NOT NULL UNIQUE
);

-- Création des index pour améliorer les performances
CREATE INDEX idx_incident_building_id ON T_INCIDENT(BUILDING_ID);
CREATE INDEX idx_incident_qr_code ON T_INCIDENT(QR_CODE_NUMBER);
CREATE INDEX idx_incident_creation_date ON T_INCIDENT(CREATION_DATE);

-- Commentaires pour la documentation
COMMENT ON TABLE T_INCIDENT IS 'Table des incidents signalés pour les bâtiments';
COMMENT ON COLUMN T_INCIDENT.ID IS 'Identifiant unique auto-incrémenté';
COMMENT ON COLUMN T_INCIDENT.BUILDING_ID IS 'Référence à l''ID du bâtiment concerné';
COMMENT ON COLUMN T_INCIDENT.CREATION_DATE IS 'Date et heure de création de l''incident';
COMMENT ON COLUMN T_INCIDENT.REPORTER_PHONE IS 'Numéro de téléphone du déclarant';
COMMENT ON COLUMN T_INCIDENT.REPORTER_EMAIL IS 'Email du déclarant';
COMMENT ON COLUMN T_INCIDENT.INCIDENT_INFORMATION IS 'Informations sur l''incident au format JSON';
COMMENT ON COLUMN T_INCIDENT.QR_CODE_NUMBER IS 'Identifiant unique utilisé dans le QR code';
