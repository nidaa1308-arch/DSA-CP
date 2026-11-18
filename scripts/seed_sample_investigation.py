"""
Seed Script for BHUMI-FUSE Sample Investigation.
Loads real sample datasets from data/samples/ through the database ingestion pipeline.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

# Add backend directory to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.db import (
    init_db, create_investigation, upsert_investigation_source, update_investigation_step
)

def seed_sample():
    print("Initializing database...")
    init_db()

    inv_id = "sample-kharadi-2026"
    title = "Sample Investigation: Pune Kharadi Revenue Sector"
    lead_officer = "District Revenue Officer (Sample Demonstration)"
    area_id = "pune_kharadi"

    print(f"Creating sample investigation: {inv_id}...")
    create_investigation(
        inv_id=inv_id,
        name="Sample Investigation: Pune Kharadi Revenue Sector",
        city_area="Kharadi, Pune",
        cadastral_year="1960",
        survey_year="2024",
        description="Authoritative cadastral boundary review vs drone orthomosaic survey with GNSS ground control.",
        parcels_count=224
    )

    samples_dir = ROOT / "data" / "samples"
    files = {
        "cadastral": ("cadastral_sample.geojson", "GeoJSON", "EPSG:4326"),
        "buildings": ("drone_footprints.geojson", "GeoJSON", "EPSG:4326"),
        "gnss": ("gnss_points.csv", "CSV", "EPSG:4326"),
        "revenue": ("revenue_7_12.csv", "CSV", "Attribute only"),
    }

    for key, (filename, fmt, crs) in files.items():
        fpath = samples_dir / filename
        if not fpath.exists():
            print(f"Warning: sample file {fpath} not found.")
            continue
        content = fpath.read_text(encoding="utf-8")
        features_cnt = 224 if key in ("cadastral", "buildings") else (10 if key == "gnss" else 20)
        upsert_investigation_source(
            inv_id=inv_id,
            source_key=key,
            filename=filename,
            file_format=fmt,
            original_crs=crs,
            target_crs="EPSG:32643" if key != "revenue" else "Attribute only",
            features_count=features_cnt,
            status="VALID",
            data_json=content
        )
        print(f"  + Loaded {key} source from {filename}")

    update_investigation_step(inv_id, 3)
    print(f"\nSuccessfully seeded sample investigation '{inv_id}'! Ready for harmonization.")

if __name__ == "__main__":
    seed_sample()
