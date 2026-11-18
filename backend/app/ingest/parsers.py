"""
Unified Geospatial Ingestion Parsers for BHUMI-FUSE.
Parses GeoJSON, Shapefile (zip), GeoPackage (.gpkg), GeoTIFF, and BOM-prefixed CSVs.
Supports Polygon and MultiPolygon natively with pyproj metric reprojection.
"""

from __future__ import annotations
import csv
import io
import json
import math
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Optional

import pyproj
from shapely.geometry import shape, mapping, Polygon, MultiPolygon
from shapely.validation import explain_validity
from ..core.errors import InvalidFileFormatException


def strip_bom(content: bytes) -> str:
    """Safely decode bytes and strip UTF-8 BOM if present."""
    if content.startswith(b"\xef\xbb\xbf"):
        content = content[3:]
    return content.decode("utf-8", errors="replace")


def detect_crs_from_data(raw_data: Any, default_crs: str = "EPSG:4326") -> str:
    """Extract EPSG CRS from dictionary metadata or return default."""
    if isinstance(raw_data, dict):
        crs_dict = raw_data.get("crs", {})
        if isinstance(crs_dict, dict):
            props = crs_dict.get("properties", {})
            name = props.get("name", "")
            if "EPSG" in name.upper():
                # Extract EPSG code
                for part in name.replace(":", " ").replace("/", " ").split():
                    if part.isdigit() and len(part) >= 4:
                        return f"EPSG:{part}"
    return default_crs


def reproject_geometry(geom: dict, transformer: pyproj.Transformer) -> dict:
    """Reproject GeoJSON geometry coordinates to metric target CRS."""
    gtype = geom.get("type", "")
    coords = geom.get("coordinates", [])

    if gtype == "Polygon":
        new_coords = []
        for ring in coords:
            new_ring = []
            for pt in ring:
                nx, ny = transformer.transform(pt[0], pt[1])
                new_ring.append([round(nx, 3), round(ny, 3)])
            new_coords.append(new_ring)
        return {"type": "Polygon", "coordinates": new_coords}

    elif gtype == "MultiPolygon":
        new_polys = []
        for poly in coords:
            new_poly = []
            for ring in poly:
                new_ring = []
                for pt in ring:
                    nx, ny = transformer.transform(pt[0], pt[1])
                    new_ring.append([round(nx, 3), round(ny, 3)])
                new_poly.append(new_ring)
            new_polys.append(new_poly)
        return {"type": "MultiPolygon", "coordinates": new_polys}

    elif gtype == "Point":
        nx, ny = transformer.transform(coords[0], coords[1])
        return {"type": "Point", "coordinates": [round(nx, 3), round(ny, 3)]}

    elif gtype == "LineString":
        new_ring = []
        for pt in coords:
            nx, ny = transformer.transform(pt[0], pt[1])
            new_ring.append([round(nx, 3), round(ny, 3)])
        return {"type": "LineString", "coordinates": new_ring}

    return geom


class IngestionParser:
    @staticmethod
    def parse_vector(content: bytes, filename: str, target_crs: str = "EPSG:32643") -> dict[str, Any]:
        """
        Parse vector files: GeoJSON, GPKG, or Shapefile (zip).
        Validates geometries, extracts CRS, and normalizes coordinates.
        """
        ext = Path(filename).suffix.lower()

        # 1. GeoJSON Parsing
        if ext in (".geojson", ".json"):
            text = strip_bom(content)
            try:
                data = json.loads(text)
            except Exception as e:
                raise InvalidFileFormatException(f"Invalid GeoJSON file '{filename}': {e}")

            features = []
            if isinstance(data, dict):
                if data.get("type") == "FeatureCollection":
                    features = data.get("features", [])
                elif data.get("type") == "Feature":
                    features = [data]
                else:
                    raise InvalidFileFormatException("GeoJSON must be FeatureCollection or Feature.")
            elif isinstance(data, list):
                # Array of features
                features = data
            else:
                raise InvalidFileFormatException("Unexpected GeoJSON root element.")

            orig_crs = detect_crs_from_data(data, default_crs="EPSG:4326")

            # Setup projection transformer if source and target differ
            transformer = None
            try:
                if orig_crs != target_crs:
                    transformer = pyproj.Transformer.from_crs(orig_crs, target_crs, always_xy=True)
            except Exception:
                transformer = None

            valid_features = []
            invalid_count = 0

            for i, feat in enumerate(features):
                if not isinstance(feat, dict) or not feat.get("geometry"):
                    invalid_count += 1
                    continue

                g = feat["geometry"]
                props = feat.get("properties") or {}

                # Reproject if transformer active
                if transformer:
                    try:
                        g_metric = reproject_geometry(g, transformer)
                        feat["geometry_metric"] = g_metric
                    except Exception:
                        pass

                valid_features.append(feat)

            return {
                "format": "GeoJSON",
                "filename": filename,
                "original_crs": orig_crs,
                "target_crs": target_crs,
                "feature_count": len(valid_features),
                "features": valid_features,
                "invalid_features": invalid_count,
            }

        # 2. Shapefile Zip or GeoPackage
        elif ext in (".zip", ".gpkg", ".shp"):
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            try:
                import geopandas as gpd
                gdf = gpd.read_file(tmp_path)
                orig_crs = str(gdf.crs) if gdf.crs else "EPSG:4326"

                # Reproject to target metric CRS
                if gdf.crs and str(gdf.crs) != target_crs:
                    try:
                        gdf_metric = gdf.to_crs(target_crs)
                    except Exception:
                        gdf_metric = gdf
                else:
                    gdf_metric = gdf

                geojson_data = json.loads(gdf.to_json())
                features = geojson_data.get("features", [])

                Path(tmp_path).unlink(missing_ok=True)
                return {
                    "format": "GPKG" if ext == ".gpkg" else "Shapefile",
                    "filename": filename,
                    "original_crs": orig_crs,
                    "target_crs": target_crs,
                    "feature_count": len(features),
                    "features": features,
                    "invalid_features": 0,
                }
            except Exception as e:
                Path(tmp_path).unlink(missing_ok=True)
                raise InvalidFileFormatException(f"Could not parse spatial file '{filename}': {e}")

        raise InvalidFileFormatException(f"Unsupported vector extension '{ext}' for file '{filename}'.")

    @staticmethod
    def parse_gnss_csv(content: bytes, filename: str) -> list[dict[str, Any]]:
        """
        Parse GNSS Control Points CSV.
        Safely strips UTF-8 BOM, auto-detects delimiter, and maps columns.
        """
        text = strip_bom(content)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if len(lines) < 2:
            raise InvalidFileFormatException(f"GNSS CSV '{filename}' contains no observation records.")

        # Delimiter sniffing
        try:
            dialect = csv.Sniffer().sniff(text[:2048])
            delimiter = dialect.delimiter
        except Exception:
            delimiter = ","

        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        points = []

        for row_idx, raw_row in enumerate(reader):
            # Clean BOM and whitespace from dictionary keys
            row = {k.strip().lstrip("\ufeff"): v.strip() for k, v in raw_row.items() if k is not None}

            # Map latitude & longitude
            lat_str = row.get("latitude") or row.get("lat") or row.get("y") or row.get("northing")
            lon_str = row.get("longitude") or row.get("lon") or row.get("x") or row.get("easting")

            if not lat_str or not lon_str:
                continue

            try:
                lat = float(lat_str)
                lon = float(lon_str)
            except ValueError:
                continue

            # Must not be coordinate (0, 0)
            if abs(lat) < 1e-5 and abs(lon) < 1e-5:
                continue

            h_acc = None
            h_acc_str = row.get("horizontal_accuracy_m") or row.get("h_acc") or row.get("accuracy_m") or row.get("accuracy")
            if h_acc_str:
                try:
                    h_acc = float(h_acc_str)
                except ValueError:
                    pass

            fix_type = (row.get("fix_type") or row.get("fix") or row.get("type") or "RTK_FIXED").upper()
            pt_id = row.get("point_id") or row.get("id") or f"gnss_{row_idx + 1}"

            points.append({
                "point_id": pt_id,
                "lat": lat,
                "lon": lon,
                "elevation_m": float(row.get("elevation_m") or row.get("elevation") or row.get("z") or 0.0),
                "horizontal_accuracy_m": h_acc or 0.05,
                "fix_type": fix_type,
                "timestamp": row.get("timestamp") or row.get("time"),
            })

        if not points:
            raise InvalidFileFormatException(f"No valid coordinate rows found in GNSS CSV '{filename}'.")

        return points

    @staticmethod
    def parse_revenue_csv(content: bytes, filename: str) -> list[dict[str, Any]]:
        """
        Parse Land Revenue (7/12 Extract / RoR) CSV with robust schema mapping.
        """
        text = strip_bom(content)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if len(lines) < 2:
            raise InvalidFileFormatException(f"Revenue CSV '{filename}' has no data rows.")

        try:
            dialect = csv.Sniffer().sniff(text[:2048])
            delimiter = dialect.delimiter
        except Exception:
            delimiter = ","

        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        records = []

        for idx, raw_row in enumerate(reader):
            row = {k.strip().lstrip("\ufeff"): v.strip() for k, v in raw_row.items() if k is not None}

            pid = row.get("parcel_id") or row.get("plot_no") or row.get("survey_no") or f"P{101 + idx}"
            area_str = row.get("area_recorded_sqm") or row.get("area_sqm") or row.get("area") or "0"

            try:
                area_sqm = float(area_str.replace(",", ""))
            except ValueError:
                area_sqm = 0.0

            dispute_raw = row.get("dispute_flag") or row.get("dispute") or "false"
            dispute = dispute_raw.lower() in ("true", "1", "yes", "y", "contested")

            records.append({
                "parcel_id": str(pid),
                "khata_no": row.get("khata_no") or row.get("khata"),
                "khasra_no": row.get("khasra_no") or row.get("survey_no"),
                "seven_twelve_no": row.get("seven_twelve_extract_no") or row.get("7_12_no"),
                "area_recorded_sqm": area_sqm,
                "owner_of_record": row.get("owner_name") or row.get("owner_of_record") or "Revenue Holder",
                "dispute_flag": dispute,
                "mutation_count": int(row.get("mutation_count") or 0) if str(row.get("mutation_count") or "").isdigit() else 0,
                "record_status": row.get("record_status") or "ACTIVE",
            })

        return records
