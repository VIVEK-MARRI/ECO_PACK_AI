import sqlite3

conn = sqlite3.connect('ecopackai.db')
c = conn.cursor()

c.execute('''
CREATE TABLE product_categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT,
    fragility_level TEXT,
    requires_cushioning BOOLEAN,
    moisture_sensitive BOOLEAN,
    temperature_sensitive BOOLEAN,
    typical_weight_kg REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

categories = [
    ('Electronics', 'high', True, True, True, 2.0),
    ('Clothing/Apparel', 'low', False, True, False, 1.0),
    ('Groceries/Food', 'medium', True, True, True, 5.0),
    ('Cosmetics', 'high', True, True, True, 0.5),
    ('Pharmaceuticals', 'high', True, True, True, 0.2),
    ('Books/Media', 'low', False, True, False, 1.0),
    ('Home Goods', 'medium', True, False, False, 3.0),
    ('Furniture', 'medium', True, False, False, 20.0),
    ('Toys', 'medium', True, False, False, 1.5),
    ('Jewelry', 'high', True, True, False, 0.1),
    ('Sporting Goods', 'low', False, False, False, 5.0),
    ('Pet Supplies', 'low', False, False, False, 3.0),
    ('Automotive Parts', 'low', True, False, False, 10.0),
]

c.executemany('''
INSERT INTO product_categories (category_name, fragility_level, requires_cushioning, moisture_sensitive, temperature_sensitive, typical_weight_kg)
VALUES (?, ?, ?, ?, ?, ?)
''', categories)

c.execute('''
CREATE TABLE recommendations (
    recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT,
    product_weight_kg REAL,
    fragility_level TEXT,
    budget_limit REAL,
    current_material_name TEXT,
    recommended_material_name TEXT,
    recommended_material_type TEXT,
    suitability_score REAL,
    predicted_cost_inr REAL,
    predicted_co2_kg REAL,
    eco_score REAL,
    co2_savings_kg REAL,
    cost_savings_inr REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()
print("SQLite database ecopackai.db created successfully.")
