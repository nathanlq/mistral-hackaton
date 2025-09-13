-- Initialisation de la base de données Carbon Calculator

CREATE TABLE IF NOT EXISTS carbon_calculations (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    calculation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    energy_kwh DECIMAL(10,4),
    carbon_kg_co2 DECIMAL(10,4),
    metrics JSONB,
    optimizations JSONB
);

CREATE TABLE IF NOT EXISTS electricity_mix (
    region VARCHAR(10) PRIMARY KEY,
    carbon_intensity_g_co2_kwh INTEGER NOT NULL,
    renewable_percent DECIMAL(5,2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO electricity_mix (region, carbon_intensity_g_co2_kwh, renewable_percent) VALUES
('EU', 296, 32.3),
('US', 386, 20.1),
('FR', 57, 19.1),
('DE', 311, 46.2),
('UK', 202, 43.1)
ON CONFLICT (region) DO NOTHING;
