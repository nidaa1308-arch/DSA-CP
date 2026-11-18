# BHUMI-FUSE: Full System Audit & Defect Catalog (Phase 0)

**Date:** 2026-11-18  
**Audit Standard:** Smart India Hackathon PS-26013 & Advanced Data Structures & Algorithms Course Project  
**Target:** Production-Grade Revenue & Urban Development Department Compliance (NAKSHA Programme)

---

## Executive Summary

A comprehensive architectural and source-code audit was conducted across the entire repository (backend API, geometric algorithms, database persistence, DSA extensions, frontend SPA, deployment manifests, and data assets).

**Verdict:** **All 15 defect clusters identified in the redesign specification are CONFIRMED.** 

While the system contains powerful conceptual foundations (classical geometric registration, OpenCV edge extraction, MapLibre rendering, and spatial algorithms), the current implementation contains critical shortcuts, hardcoded calibration branches, non-deterministic RNG seeds, race conditions, and UI fallbacks that would fail a government audit or rigorous academic evaluation.

Below is the exhaustive catalog of confirmed defects, architectural deficiencies, dead files, and contract mismatches with exact file and function names.

---

## Detailed Defect Findings

### 1. Hardcoded "224-Parcel Benchmark" in `/harmonize`
* **Status:** **CONFIRMED**
* **File & Function:** `backend/app/main.py` -> `harmonize()` (lines 1299–1677)
* **Evidence:**
  * Line 1299: `is_benchmark_224 = abs(len(all_src_m) - 224) <= 2`
  * Line 1317: `ransac_result["inlier_ratio"] = 0.902` (overwriting computed RANSAC inlier ratio with constant `0.902`).
  * Line 1429: `post_dist_m = 4.505 if corr_idx == 0 else round(2.6 + (29 - corr_idx) * (1.9 / 29.0), 3)` (synthetically forces exact 30 Critical, 50 Needs Review, 60 Low Priority, and 84 Resolved distribution).
  * Line 1550: `"ambiguous_match": True if (is_benchmark_224 and corr_idx < 22) else corr["ambiguous_match"]` (synthetically forces exactly 22 Do-Not-Decide cases).
  * Lines 1675–1677: `rmse = 1.695; max_post_residual = 4.505` (overwriting actual computed RMSE and maximum residual).
* **Impact:** Any investigation with ~224 parcels completely ignores the uploaded spatial coordinates and outputs pre-fabricated numbers. Must be removed completely.

---

### 2. Silent Fake-Success Fallbacks & Hardcoded Defaults
* **Status:** **CONFIRMED**
* **Files & Functions:**
  * `backend/app/main.py` -> `upload_municipal_vector()` (lines 710–752): If geopandas fails, silently defaults feature count to 1 and returns success.
  * `backend/app/main.py` -> `upload_drone_geotiff()` (lines 753–769): Silently falls back to `"EPSG:32643"` and synthetic bounding boxes without checking raster transform validity.
  * `backend/app/main.py` -> `upload_dsm_json()` (lines 2288–2290): `mean_elev = 562.0`, `max_elev = 580.0`, `min_elev = 545.0` hardcoded when elevation array is missing or empty.
  * `backend/app/main.py` -> `cv_extract()`: Hardcodes confidence fallback `0.85` or arbitrary scalar multipliers (`compactness * 0.9 + 0.1`).
  * `frontend/src/components/ReportsExportView.tsx` (lines 114, 170): Line 114 hardcodes `"- Hash Chain State : VERIFIED INTACT (100% Tamper-Evident SHA-256)"` in text export without querying audit verification; line 170 synthesizes a placeholder row with status `"verified"`.
* **Impact:** System masks corrupt or missing files as valid operations instead of returning typed HTTP 4xx errors with actionable diagnostics.

---

### 3. Investigation Fallback to Demo Data
* **Status:** **CONFIRMED**
* **File & Function:** `backend/app/main.py` -> `harmonize()` (lines 1182–1195)
* **Evidence:**
  * Lines 1182–1195: When no custom layers or investigation DB sources exist, `harmonize()` falls back to `STUDY_AREAS[req.area_id]` (`"pune_kharadi"`).
  * The HTTP 422 `INSUFFICIENT_SOURCES` validation check is rendered unreachable for any request supplying default `area_id`.
* **Impact:** If an officer runs harmonization on an empty new investigation, the system silently harmonizes the pre-packaged Pune Kharadi demo data rather than failing loudly.

---

### 4. Flawed DSA Implementations: `AVLTree` & `sweep_intersections`
* **Status:** **CONFIRMED**
* **Files & Functions:**
  * `backend/app/dsa/avl_tree.py` -> `AVLTree`:
    * Has **no `delete()` method**.
    * Rebalance rotations in `insert()` check `if key < node.left.key` without the tie-breaker `id(value)`, causing improper rotations and loss of height balance on duplicate keys.
    * Uses Python's transient memory address `id(value)` as a comparison tie-breaker, which is non-deterministic.
  * `backend/app/dsa/sweep_line.py` -> `sweep_intersections()` & `_intersects()`:
    * In `sweep_intersections()`: Calls `tree.rebuild([(_y_at(s, x), s) for s in active])` on **every single event**, destroying and reconstructing the tree from scratch rather than performing $O(\log n)$ incremental insertions and deletions.
    * In `_intersects()`: `(o1 == 0 or o2 == 0 or o1 * o2 < 0) and ...` evaluates collinear touching edges and shared boundary segments between adjacent parcels as intersections. In cadastral maps, adjacent parcels *must* share boundaries; reporting valid shared boundaries as collisions creates hundreds of false-positive conflicts.
    * No intersection event queue: Misses intersections between non-adjacent segments that only become adjacent after intermediate segment swaps.
* **Impact:** The sweep-line algorithm is algorithmic theater in its current state ($O(E^2 \log E)$ due to full rebuilds per event) and corrupts topological validation.

---

### 5. Incomplete Topology Correction in `/validate`
* **Status:** **CONFIRMED**
* **File & Function:** `backend/app/main.py` -> `validate()` (lines 1690–1705)
* **Evidence:**
  * Line 1695: Computes `corrected_ring = list(mapping(repaired)["coordinates"][0])`.
  * The variable `corrected_ring` is completely discarded. The returned results only return `"validity": "Auto-corrected via buffer(0)"` but never return or persist the repaired polygon coordinates!
  * `poly.buffer(0)` can silently swallow polygon area or collapse multi-part geometries without warning or threshold checks.
* **Impact:** The user is told the polygon was "auto-corrected", but the exported geometry remains identical to the invalid original.

---

### 6. Fragile Ingestion Parsers (MultiPolygon, Nulls, BOM, CSVs)
* **Status:** **CONFIRMED**
* **File & Function:** `backend/app/main.py` -> `_parse_uploaded_file()`, `build_correspondence_set()`, `harmonize()`
* **Evidence:**
  * `ring = feat["geometry"]["coordinates"][0]`: Crashes with `TypeError: 'NoneType' object is not subscriptable` when geometry is null or empty.
  * MultiPolygon geometry coordinates are nested 4 levels deep (`[[[[x, y], ...]]]]`). Accessing `coordinates[0]` returns a list of rings, crashing `poly_centroid` and distance functions.
  * UTF-8 BOM headers (`\ufeff`) in CSVs cause dictionary keys to be read as `"\ufefflatitude"` instead of `"latitude"`, resulting in `float(row.get("latitude") or 0) == 0.0` (placing GNSS points at 0°N, 0°E in the Atlantic Ocean).
* **Impact:** Real-world government datasets with standard UTF-8 BOMs or MultiPolygons trigger unhandled HTTP 500 exceptions.

---

### 7. Correspondence Scoring Flaw & Lack of 1-to-1 Assignment
* **Status:** **CONFIRMED**
* **File & Function:** `backend/app/main.py` -> `build_correspondence_set()` (lines 345–365)
* **Evidence:**
  * Computes: `combined = 0.40 * centroid_score + 0.35 * area_ratio + 0.25 * iou`
  * A cadastral land parcel is typically 500–2,000 $m^2$, while a building footprint inside it is 80–150 $m^2$. The `area_ratio` ($80/1000 = 0.08$) and pre-alignment IoU ($\approx 0$) drag the combined score below `0.45`, marking every legitimate parcel as an "ambiguous match" (`Do Not Decide`).
  * Correspondence matching is purely greedy per cadastral parcel: multiple parcels can claim the exact same drone building footprint without solving a global 1-to-1 bipartite assignment (Hungarian / Munkres algorithm).
  * Ambiguous and low-scoring matches are still passed into the RANSAC registration pool.
* **Impact:** Registration is contaminated by poor initial correspondences, skewing transformation matrices.

---

### 8. In-Sample RMSE, Flawed TPS, & Distorted Metrics
* **Status:** **CONFIRMED**
* **File & Function:** `backend/app/main.py` -> `solve_tps_2d()`, `harmonize()`
* **Evidence:**
  * `solve_tps_2d()` operates directly in raw geographic degrees ($\sim 0.0001^\circ$). At degree scale, $r^2 \log(r)$ produces near-zero numbers that make the $(n+3) \times (n+3)$ linear system ill-conditioned.
  * No regularization parameter ($\lambda \cdot I$) is applied along the diagonal, causing extreme spline over-fitting or singular matrices.
  * RMSE is calculated purely in-sample on the same control points used to estimate the transformation parameters.
  * `auto_resolved_count = len(matched_residuals) - dnd_count` (counts all "Needs Review" parcels as "auto-resolved").
* **Impact:** Over-optimistic error reporting that violates geospatial surveying standards (held-out RMSE is required).

---

### 9. GNSS "Disagreement" Measures Distance, Not Displacement
* **Status:** **CONFIRMED**
* **File & Function:** `backend/app/main.py` -> `harmonize()` (lines 1450–1475)
* **Evidence:**
  * When a GNSS point is matched to a parcel, `gnss_dist_m` records the distance from the parcel centroid to the GNSS observation point.
  * The system reports this spatial separation as "GNSS disagreement".
* **Impact:** If a GNSS control monument is located 40 metres away along the parcel boundary, the system flags a 40m "discrepancy" even if the physical boundary is accurate to 2 cm.

---

### 10. Pseudo-Reprojection in `/normalize-crs`
* **Status:** **CONFIRMED**
* **File & Function:** `backend/app/main.py` -> `normalize_investigation_crs()` (lines 980–1035)
* **Evidence:**
  * For non-GeoJSON formats (Shapefile, GPKG, CSV), no coordinate reprojection is performed, yet the endpoint reports: `"Reprojected to UTM Zone 43N"`.
  * For GeoJSON, it writes to a custom field `coordinates_utm` while leaving standard GeoJSON `coordinates` unchanged.
  * It only iterates over `type == "Polygon"`, dropping MultiPolygons, Points, and LineStrings.
* **Impact:** Downstream computations continue using the unprojected coordinates while reporting successful metric normalization.

---

### 11. Non-Deterministic Seeds & Synthetic Revenue Bias
* **Status:** **CONFIRMED**
* **File & Function:** `backend/app/revenue_data.py` (line 27)
* **Evidence:**
  * Line 27: `rng.seed(pid_num * 17 + hash(area_id) % 997)`
  * Python's `hash()` function uses randomized per-process seeds (`PYTHONHASHSEED`). The exact same dataset generates completely different revenue records, mutation histories, and dispute flags upon server restart.
* **Impact:** Test assertions and audit trails cannot be deterministically reproduced across worker processes.

---

### 12. Concurrency Clashes, Global Tables, & Missing Review Verification
* **Status:** **CONFIRMED**
* **File & Function:** `backend/app/db.py`, `backend/app/main.py`
* **Evidence:**
  * Line 238: `cursor.execute("DELETE FROM parcel_rtree")` inside `index_features_rtree()` operates on a single global SQLite table. Concurrent harmonization runs wipe out each other's spatial indexes.
  * `verify_audit_chain()` only validates `audit_logs`; no function exists to verify the `review_decisions` hash chain.
  * `INSERT OR REPLACE INTO investigations` completely wipes out existing metadata if an investigation is updated with partial fields.
  * In-memory globals `AUDIT = []` and `VERSIONS = {}` in `main.py` leak memory and diverge from SQLite on restart.
  * Global CORS `allow_origins=["*"]`, zero authentication, and zero upload file-size limits.
* **Impact:** System is vulnerable to race conditions, denial-of-service via large payloads, and unauthorized access.

---

### 13. Frontend Contract Mismatches & Monolithic Bundle
* **Status:** **CONFIRMED**
* **Files & Functions:**
  * `frontend/src/components/ReportsExportView.tsx` (line 158): `fetch("/api/db/audit")` — endpoint does not exist on backend (returns 404).
  * `frontend/src/main.tsx` (line 282): Accesses `resp.version`, but backend `/review` returns `{"stored": true, "new_version": {"version": ...}}` — `resp.version` is always `undefined`.
  * `frontend/src/main.tsx` (line 276): Hardcodes `reviewer: "AO (Land Records Officer)"`.
  * `frontend/index.html`: Missing `<!DOCTYPE html>`, `<html>`, `<head>`, `<meta name="viewport">`, `<title>`.
  * `frontend/package.json`: Every single dependency is unpinned (`"latest"`), and `@tailwindcss/postcss ^4` conflicts with v3 `tailwind.config.js`.
  * Single monolithic bundle of **1.52 MB** because routes, MapLibre GL, and D3 force graph are not code-split.
* **Impact:** High frontend failure rate, broken audit export downloads, and slow mobile/tablet load times.

---

### 14. Deployment Failures & Dead Artifacts
* **Status:** **CONFIRMED**
* **Files & Functions:**
  * `api/index.py`: Uses `sys.path.insert(0, str(ROOT / "backend"))` where `ROOT` is `/api`, pointing to non-existent `/api/backend`.
  * `docker-compose.yml`: Launches a `postgis/postgis:16-3.4` container, but the backend code never connects to Postgres (defaults to SQLite `bhumi_fuse.db`).
  * 12+ Dead / Redundant files:
    * `BEGINNERS_GUIDE.md`, `BHUMI-FUSE_Beginners_Guide.docx`, `BHUMI-FUSE_Complete_Project_Guide.pdf`
    * `scripts/create_beginners_guide_docx.py`, `scripts/generate_complete_guide_pdf.py`
    * `scripts/mock_api_server.mjs`, `scripts/build_static_demo_data.py`, `scripts/fetch_real_layers.py`, `scripts/build_comprehensive_demo_data.py`, `scripts/run_etl_pipeline.py`, `scripts/generate_simulated_cadastral.py`
    * `frontend/src/demoData.ts` (150 KB static mock)
    * Redundant dataset copies in `datasets/` vs `frontend/public/datasets/`
* **Impact:** Cluttered repository, wasted bandwidth, and confusion during evaluation.

---

## Conclusion & Transition to Target Architecture

All identified defects stem from accumulated hackathon demo code that was layered over earlier mock implementations. To achieve production readiness:
1. Every hardcoded fallback, benchmark, and synthetic calibration must be eliminated.
2. The 6 DSA modules must be re-engineered into correct, fully tested computational geometry classes.
3. The backend must be restructured into clean service layers backed by PostgreSQL + PostGIS with SQLite fallback for unit tests.
4. The frontend must be streamlined into a calm, accessible 5-step government workflow adhering to GIGW 3.0 / WCAG 2.1 AA.
5. All dead files, generated binaries, and redundant scripts must be deleted.

Target design and architecture specifications are formalized in `docs/ARCHITECTURE.md`.
