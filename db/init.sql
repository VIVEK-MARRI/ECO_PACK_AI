-- EcoPackAI database initialization script
-- Run in psql or a PostgreSQL client

-- Create database if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'ecopack') THEN
        CREATE DATABASE ecopack;
    END IF;
END $$;

-- Connect to the database (psql will honor this; other clients can switch DB manually)
\connect ecopack

-- Products created from API input
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(100) UNIQUE,
    category VARCHAR(50),
    weight FLOAT,
    strength FLOAT,
    biodegradability FLOAT,
    recyclability FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Recommendations history (API)
CREATE TABLE IF NOT EXISTS recommendations (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(100),
    material VARCHAR(50),
    cost_score FLOAT,
    co2_score FLOAT,
    eco_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Materials catalog (ETL)
CREATE TABLE IF NOT EXISTS materials (
    material_id VARCHAR(20) PRIMARY KEY,
    material_type VARCHAR(100),
    strength FLOAT,
    weight_capacity FLOAT,
    cost_per_unit FLOAT,
    biodegradability_score FLOAT,
    recyclability_percentage FLOAT
);

-- Product catalog for data-driven scoring (ETL)
CREATE TABLE IF NOT EXISTS products_catalog (
    product_id SERIAL PRIMARY KEY,
    product_category VARCHAR(100),
    fragility_level VARCHAR(20),
    shipping_type VARCHAR(50)
);

-- Suitability scores between materials and products (ETL)
CREATE TABLE IF NOT EXISTS material_product_scores (
    material_id VARCHAR(20),
    product_id INT,
    material_suitability_score FLOAT,
    co2_impact_index FLOAT,
    cost_efficiency_index FLOAT,
    PRIMARY KEY (material_id, product_id),
    FOREIGN KEY (material_id) REFERENCES materials(material_id),
    FOREIGN KEY (product_id) REFERENCES products_catalog(product_id)
);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_recommendations_product_id ON recommendations(product_id);
CREATE INDEX IF NOT EXISTS idx_material_scores_material_id ON material_product_scores(material_id);
CREATE INDEX IF NOT EXISTS idx_material_scores_product_id ON material_product_scores(product_id);
