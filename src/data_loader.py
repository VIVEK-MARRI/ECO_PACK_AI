import hashlib
import os

import pandas as pd
from sqlalchemy import create_engine

df = pd.read_csv("data/processed/ecopackai_feature_engineered.csv")
print("Loaded dataset shape:", df.shape)

db_password = os.getenv("ECOPACKAI_DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD") or "admin"
engine = create_engine(
    f"postgresql+psycopg2://postgres:{db_password}@localhost:5432/ecopackai"
)


def make_material_id(material_type: str) -> str:
    base = "".join(ch for ch in material_type.upper() if ch.isalnum())
    base = base[:8] if base else "MAT"
    digest = hashlib.md5(material_type.encode("utf-8")).hexdigest()[:6]
    return f"MAT_{base}_{digest}"[:20]

materials_df = df[
    [
        "material_type",
        "strength",
        "weight_capacity",
        "cost_per_unit",
        "biodegradability_score",
        "recyclability_percentage",
    ]
].drop_duplicates(subset=["material_type"])

materials_df = materials_df.copy()
materials_df["material_id"] = materials_df["material_type"].apply(make_material_id)
materials_df = materials_df[
    [
        "material_id",
        "material_type",
        "strength",
        "weight_capacity",
        "cost_per_unit",
        "biodegradability_score",
        "recyclability_percentage",
    ]
]

materials_db = pd.read_sql(
    "SELECT material_id, material_type FROM materials",
    engine
)

if not materials_db.empty:
    materials_df = materials_df[
        ~materials_df["material_type"].isin(materials_db["material_type"])
    ]

if not materials_df.empty:
    materials_df.to_sql(
        "materials",
        engine,
        if_exists="append",
        index=False
    )

print("Materials table populated")
df["fragility_level"] = df["fragility_level"].astype(str)

products_df = df[
    [
        "product_category",
        "fragility_level",
        "shipping_type",
    ]
].drop_duplicates(
    subset=["product_category", "fragility_level", "shipping_type"]
)

products_db = pd.read_sql(
    "SELECT product_id, product_category, fragility_level, shipping_type FROM products",
    engine
)

if not products_db.empty:
    products_df = products_df.merge(
        products_db[
            ["product_category", "fragility_level", "shipping_type"]
        ],
        on=["product_category", "fragility_level", "shipping_type"],
        how="left",
        indicator=True
    )
    products_df = products_df[products_df["_merge"] == "left_only"].drop(columns=["_merge"])

if not products_df.empty:
    products_df.to_sql(
        "products",
        engine,
        if_exists="append",
        index=False
    )

print("Products table populated")

materials_db = pd.read_sql(
    "SELECT material_id, material_type FROM materials",
    engine
)

products_db = pd.read_sql(
    "SELECT product_id, product_category, fragility_level, shipping_type FROM products",
    engine
)

df_scores = df.merge(
    materials_db,
    on="material_type",
    how="left"
)

df_scores = df_scores.merge(
    products_db,
    on=["product_category", "fragility_level", "shipping_type"],
    how="left"
)

scores_df = df_scores[
    [
        "material_id",
        "product_id",
        "material_suitability_score",
        "co2_impact_index",
        "cost_efficiency_index",
    ]
]

scores_db = pd.read_sql(
    "SELECT material_id, product_id FROM material_product_scores",
    engine
)

if not scores_db.empty:
    scores_df = scores_df.merge(
        scores_db,
        on=["material_id", "product_id"],
        how="left",
        indicator=True
    )
    scores_df = scores_df[scores_df["_merge"] == "left_only"].drop(columns=["_merge"])

if not scores_df.empty:
    scores_df.to_sql(
        "material_product_scores",
        engine,
        if_exists="append",
        index=False
    )

print("Material–product scores populated")
print("Total score rows inserted:", len(scores_df))


