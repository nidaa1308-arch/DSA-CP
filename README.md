<div align="center">

# 🌍 BHUMI-FUSE (भूमि-फ्यूज)
### Intelligent Geospatial Harmonization, Cadastral Discrepancy Resolution & DSA Spatial Computing Engine

[![Python 3.11](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19.0-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![MapLibre GL](https://img.shields.io/badge/MapLibre_GL-3.6-blue?style=for-the-badge&logo=mapbox&logoColor=white)](https://maplibre.org/)
[![Live on Railway](https://img.shields.io/badge/Railway-Live_Backend-0B0D0E?style=for-the-badge&logo=railway&logoColor=white)](https://web-production-d5b3c14b.up.railway.app/health)
[![Vercel Ready](https://img.shields.io/badge/Vercel-Frontend_Ready-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com/)
[![Pytest](https://img.shields.io/badge/Pytest-6%20Passed-449C44?style=for-the-badge&logo=pytest&logoColor=white)](tests/test_dsa.py)

**Smart India Hackathon (SIH PS-26013 — NAKSHA Programme)**  
*Automated Multi-Source Cadastral Harmonization, Topological Dispute Grouping, and Land Record Intelligence*

[Live Backend API](https://web-production-d5b3c14b.up.railway.app) • [Interactive API Docs (Swagger)](https://web-production-d5b3c14b.up.railway.app/docs) • [DSA Technical Guide](DSA_COURSE_EXTENSION.md) • [DSA Health Summary](https://web-production-d5b3c14b.up.railway.app/dsa/summary)

</div>

---

## 📑 Table of Contents
1. [Executive Summary](#-executive-summary)
2. [The Problem Statement (SIH PS-26013)](#-the-problem-statement-sih-ps-26013)
3. [End-to-End System Architecture](#-end-to-end-system-architecture)
4. [Advanced DSA Course Extension](#-advanced-dsa-course-extension)
   - [DSA Inventory & Complexity Analysis](#dsa-inventory--complexity-analysis)
   - [Real-World GIS Bottleneck Solutions](#real-world-gis-bottleneck-solutions)
   - [Dedicated DSA Endpoints](#dedicated-dsa-endpoints)
5. [Key System Modules & Features](#-key-system-modules--features)
6. [VS Code Project Layout for Review](#-vs-code-project-layout-for-review)
7. [Getting Started & Local Development](#-getting-started--local-development)
8. [Testing & Verification Suite](#-testing--verification-suite)
9. [Cloud Deployment Guide](#-cloud-deployment-guide)
10. [Ethics & Administrative Guardrails](#-ethics--administrative-guardrails)

---

## 📌 Executive Summary

**BHUMI-FUSE** is a high-precision geospatial data harmonization, topological verification, and dispute resolution platform. Built to solve the systemic challenges of digitized land administration in India, it reconciles discrepancies between **decades-old historical cadastral maps** and **high-resolution modern physical observations** (UAV/drone orthomosaics, satellite imagery, GNSS survey points, and municipal rights-of-way).

By combining **mathematical coordinate transformation (RANSAC + Thin Plate Spline)** with **six core Data Structures and Algorithms (DSA)**, BHUMI-FUSE eliminates manual surveying bottlenecks, detects structural encroachments with sub-metre accuracy, and clusters land disputes for administrative adjudication.

---

## 🎯 The Problem Statement (SIH PS-26013)

Under the Government of India's **NAKSHA (National Geospatial Knowledge-Based Land Survey & Harmonization Action)** initiative, revenue authorities face severe impediments when digitizing legacy land records:

* **Non-Linear Historical Distortions:** Cadastral maps surveyed in the 1960s–1980s suffer from paper shrinkage, cloth stretching, local datum shifts, and subjective chain-survey measurements.
* **Modern Encroachments:** Physical boundary walls, modern building footprints, and municipal roadways frequently breach recorded boundary coordinates over time.
* **CRS Mismatches:** Heterogeneous datasets arrive in conflicting coordinate systems (local Cassini-Soldner, Polyconic, UTM WGS84, or raw geographic lat/lon).
* **Topological Collisions:** Automated vectorization often introduces sliver polygons, self-intersections, and boundary overlaps.
* **Administrative Burden:** Land registrars lack automated decision-support pipelines to separate minor fuzz (sub-centimetre surveying tolerances) from critical land disputes.

---

## 🏗️ End-to-End System Architecture

Every investigation executes through an authoritative, deterministic spatial pipeline without synthetic fallbacks or hardcoded constants:

```text
 ┌────────────────────────────────────────────────────────────────────────┐
 │                    1. MULTI-SOURCE INGESTION (9 SOURCES)               │
 │  • Cadastral (GeoJSON/GPKG)  • Drone Footprints (GeoJSON/SHP)          │
 │  • GNSS Points (CSV/RTK)     • DSM/DTM Elevation (CSV/GeoTIFF)         │
 │  • RoR Revenue Records (CSV) • Municipal Utilities & Roads (GeoJSON)   │
 │  • Orthomosaic (Cloud GeoTIFF) • Ground Truth Controls (GeoJSON)       │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │          2. CRS DETECTION & REPROJECTION (pyproj & Shapely)            │
 │  Detects native EPSG → Transforms to optimal investigation-metric CRS  │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │            3. GEOMETRIC REGISTRATION & EVIDENCE FUSION                 │
 │  • Candidate Spatial Filtering via SQLite R-Tree                       │
 │  • Balanced 2D KD-Tree: O(log n) Nearest-Neighbour GNSS Matching       │
 │  • RANSAC Inlier Estimation + Affine / Thin Plate Spline (TPS) Warping │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │           4. TOPOLOGICAL VERIFICATION & CONFLICT CLUSTERING            │
 │  • Sweep-Line Algorithm with Balanced AVL Tree Active Status           │
 │  • Disjoint Set Union (DSU) Connected Conflict Zone Partitioning       │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │         5. DISCREPANCY RANKING, EVIDENCE GRAPH & AUDIT TRAIL           │
 │  • 4-Tier Severity Scoring: Critical, Needs Review, Low Priority, Auto │
 │  • Spatial Evidence Graph (Cross-layer Node & Edge relationships)      │
 │  • A* Search Algorithm: Optimal Field Survey Verification Routing      │
 │  • Cryptographic SHA-256 Hash Chain Immutable Audit Trail              │
 └────────────────────────────────────────────────────────────────────────┘
```

---

## 🧠 Advanced DSA Course Extension

This project houses an integrated **Data Structures & Algorithms (DSA)** computing layer designed to tackle high-complexity computational geometry problems at production scale.

### DSA Inventory & Complexity Analysis

| # | Data Structure / Algorithm | Source Module | Core Operation | Theoretical Complexity | Production Function in BhumiFuse |
|:---:|---|---|---|:---:|---|
| **1** | **2D Spatial KD-Tree** | `backend/app/dsa/kd_tree.py` | Nearest Neighbour Search | Average $\mathcal{O}(\log n)$<br>Worst $\mathcal{O}(n)$ | Matches each parcel centroid to the closest high-precision GNSS/RTK base observation point without $O(n \cdot m)$ all-pair distance scans. |
| **2** | **Sweep-Line Algorithm** | `backend/app/dsa/sweep_line.py` | Segment Intersections | $\mathcal{O}((n + k) \log n)$ vs $\mathcal{O}(n^2)$ | Bentley-Ottmann inspired event sweep across horizontal coordinates to discover cross-parcel boundary overlap errors. |
| **3** | **AVL Tree** | `backend/app/dsa/avl_tree.py` | Insertion, Deletion, Search | Guaranteed $\mathcal{O}(\log n)$ | Self-balancing binary search tree used as the active sweep-line status structure, preventing degenerate $O(n)$ tree heights. |
| **4** | **Disjoint Set Union (DSU)** | `backend/app/dsa/disjoint_set.py` | `find()` & `union()` | Amortized $\mathcal{O}(\alpha(n)) \approx \mathcal{O}(1)$ | Groups pairwise intersecting parcels and contested land boundaries into connected multi-parcel conflict clusters. |
| **5** | **A\* Search Algorithm** | `backend/app/dsa/astar.py` | Shortest Path Planning | Heuristic-guided Graph Traversal | Optimizes travel routes for field survey teams inspecting flagged parcels across real municipal street graphs. |
| **6** | **Spatial Quadtree** | `backend/app/dsa/quadtree.py`<br>`frontend/src/utils/quadtree.ts` | 2D Bounding-Box Range Query | $\mathcal{O}(\log n)$ avg per viewport query | Hierarchically partitions the 2D map canvas so only parcels currently inside the user's viewport are rendered. |
| *—* | *SQLite R-Tree* | `backend/app/db.py` | *B-Tree Spatial Indexing* | *$\mathcal{O}(\log M)$* | *Pre-existing baseline spatial candidate indexing (retained, not counted as new DSA).* |

---

### Real-World GIS Bottleneck Solutions

```text
[Problem 1: Brute-Force GNSS Scanning]
Old Approach: For N parcels and M GNSS points, compute distance for every pair → O(N * M)
BhumiFuse DSA: Construct balanced 2D KD-Tree once in O(M log M) → Query each parcel in O(log M)

[Problem 2: Boundary Intersection Check]
Old Approach: Compare every boundary segment against all others → O(E^2) where E = total edges
BhumiFuse DSA: Sweep-Line with AVL Tree orders events and tests only active adjacent edges → O((E + K) log E)

[Problem 3: Multi-Parcel Dispute Cascades]
Old Approach: Ad-hoc recursive graph searches prone to stack overflows on large grids
BhumiFuse DSA: Disjoint Set Union with Path Compression & Union-by-Rank clusters dispute zones in O(α(P))
```

---

### Dedicated DSA Endpoints

All DSA modules are exposed via live REST endpoints for direct evaluation:

* **`GET /dsa/summary`** — Full inventory of all 6 course DSA modules, theoretical complexities, and GIS use cases.
* **`POST /dsa/astar-route`** — Executes A* shortest path search over a weighted node graph using Euclidean distance heuristics:
  ```json
  {
    "graph": { "Survey_Base": [["Station_A", 120.5], ["Station_B", 310.2]], "Station_A": [["Target_Parcel", 85.0]] },
    "coords": { "Survey_Base": [73.8567, 18.5204], "Station_A": [73.8572, 18.5210], "Station_B": [73.8580, 18.5215], "Target_Parcel": [73.8578, 18.5218] },
    "start": "Survey_Base",
    "goal": "Target_Parcel"
  }
  ```
* **`POST /dsa/quadtree-query`** — Indexes coordinates in a Quadtree and executes sublinear spatial viewport window queries.
* **`POST /validate`** — Evaluates topology using the **Sweep-Line + AVL Tree** collision detector and returns **DSU** conflict clusters.

---

## ⚙️ Key System Modules & Features

### 1. 9-Source Ingestion & Dynamic Discovery
Accepts and parses real geospatial artifacts:
* **Vector:** Cadastral boundaries (GeoJSON/GPKG/SHP), Building Footprints, Municipal Roadways & RoW, Underground Utilities.
* **Tabular / Sensor:** GNSS Ground Control Points (RTK Fixes, accuracy bounds, DOP metrics), DSM/DTM Elevation points, RoR (7/12 Extract, Khata/Khasra numbers, encumbrance & mutation logs).
* **Raster:** High-resolution Drone Orthomosaics (ORI) served as TMS/WMS tiles.

### 2. Multi-Model Geometric Harmonization
* **RANSAC (Random Sample Consensus):** Filters out physical structural modifications and false matches, guaranteeing only true historical survey corners guide alignment.
* **Thin Plate Spline (TPS):** Models non-linear paper warping and local topographical elevation shifts with minimum bending energy.
* **Affine Transformation:** Provides rigid 6-parameter baseline rotation, translation, and scale correction.

### 3. Calibrated Discrepancy & Decision Engine
Parcels are classified deterministically based on residual displacement vectors:
* 🔴 **Critical ($> 3.0\text{m}$):** Do-Not-Decide (DND) — Requires formal field inspection.
* 🟡 **Needs Review ($1.5\text{m} - 3.0\text{m}$):** Human surveyor verification required.
* 🟢 **Low Priority / Resolved ($< 1.5\text{m}$):** Auto-accepted within permissible digital survey tolerances.

### 4. Interactive Spatial Evidence Graph
A bipartite force-directed graph cross-links legal ownership nodes with physical observation nodes, showing:
* `derived_from`, `overlaps_with`, `intersects`, `adjacent_to` relationships.

### 5. Cryptographic Audit Trail
Every review action (Accept, Adjust, Reject, Escalate) generates an immutable, timestamped record anchored in a SHA-256 hash chain to prevent administrative tampering.

---

## 📂 VS Code Project Layout for Review

To navigate the codebase during technical presentations, open the workspace in VS Code:

```text
BhumiFuse/
├── DSA_COURSE_EXTENSION.md           # 📘 Detailed DSA course documentation
├── README.md                          # 📘 Master project documentation
├── run.py                             # 🚀 Resilient production application entrypoint
├── Procfile                           # ☁️ Cloud Procfile deployment configuration
├── railway.json                       # ☁️ Railway Nixpacks deployment specification
│
├── backend/                           # ── FASTAPI BACKEND ENGINE ──
│   ├── run.py                         # Secondary runner script
│   ├── requirements.txt               # Production Python dependencies
│   ├── test_live.py                   # Live end-to-end integration test runner
│   ├── app/
│   │   ├── main.py                    # API controllers, registration logic, endpoints
│   │   ├── db.py                      # SQLite database, schemas & R-Tree spatial index
│   │   ├── study_areas.py             # Pilot benchmark datasets (Kharadi, Hinjawadi, Wagholi)
│   │   ├── revenue_data.py            # Departmental RoR schema mappings
│   │   ├── attribute_mapping.py       # Crosswalk engine with Levenshtein fuzzy matching
│   │   └── dsa/                       # ── 🧠 CORE DSA PACKAGE ──
│   │       ├── __init__.py            # Module exports
│   │       ├── kd_tree.py             # 2D KD-Tree implementation
│   │       ├── avl_tree.py            # Balanced AVL Tree implementation
│   │       ├── sweep_line.py          # Sweep-Line intersection algorithm
│   │       ├── disjoint_set.py        # Disjoint Set Union (DSU) implementation
│   │       ├── astar.py               # A* shortest path search implementation
│   │       └── quadtree.py            # Spatial Quadtree implementation
│   └── tests/
│       └── test_dsa.py                # 🧪 Pytest unit tests for all DSA modules
│
└── frontend/                          # ── REACT + VITE + TAILWIND FRONTEND ──
    ├── package.json                   # Frontend dependencies
    ├── vite.config.ts                 # Vite bundler configuration
    ├── src/
    │   ├── main.tsx                   # Main React application controller & view router
    │   ├── styles.css                 # Custom Tailwind & geospatial theme stylesheets
    │   ├── api/
    │   │   └── client.ts              # Strongly typed API client with DSA integration
    │   ├── components/
    │   │   ├── DemoMap.tsx            # MapLibre GL map renderer + Quadtree viewport querying
    │   │   ├── EvidenceGraphView.tsx  # D3/SVG Force-directed spatial evidence graph
    │   │   ├── HarmonizationView.tsx  # Interactive alignment & residual vector visualizer
    │   │   ├── ConflictDashboardView.tsx # 4-tier discrepancy table & action center
    │   │   └── UploadIngestView.tsx   # 9-source file upload & CRS validation stepper
    │   └── utils/
    │       ├── geoEngine.ts           # Client-side spatial math & RANSAC fallback
    │       └── quadtree.ts            # Client-side TypeScript Quadtree
```

---

## 🚀 Getting Started & Local Development

### Prerequisites
* **Python 3.11+**
* **Node.js 20+** and **npm**
* *Optional:* GDAL / GEOS libraries (pre-configured for Windows & Linux)

### 1. Backend Setup
```bash
# Navigate to the backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the development server
python run.py
```
* **Backend Live:** `http://localhost:8000`
* **Swagger API Documentation:** `http://localhost:8000/docs`

### 2. Frontend Setup
In a new terminal:
```bash
# Navigate to the frontend directory
cd frontend

# Install packages
npm install

# Start Vite dev server
npm run dev
```
* **Frontend Web App:** `http://localhost:5173`

---

## 🧪 Testing & Verification Suite

### Running Backend DSA Unit Tests
To verify all 6 Data Structures & Algorithms, run `pytest`:
```bash
cd backend
python -m pytest tests/test_dsa.py -v
```

**Verified Test Output:**
```text
============================= test session starts =============================
platform win32 -- Python 3.11.4, pytest-9.1.1, pluggy-1.6.0
collected 6 items

tests/test_dsa.py::test_kdtree_nearest PASSED                            [ 16%]
tests/test_dsa.py::test_avl_sorted PASSED                                [ 33%]
tests/test_dsa.py::test_dsu_groups PASSED                                [ 50%]
tests/test_dsa.py::test_astar PASSED                                     [ 66%]
tests/test_dsa.py::test_quadtree PASSED                                  [ 83%]
tests/test_dsa.py::test_sweep_line_detects_cross_parcel_intersection PASSED [100%]

============================== 6 passed in 0.04s ==============================
```

### Running Full Pipeline Integration Tests
```bash
cd backend
python test_live.py
```
Validates affine registration, thin plate spline warping, ST_IsValid topological evaluation, and evidence graph construction across all pilot datasets.

### Running Frontend Production Build
```bash
cd frontend
npm run build
```
Executes TypeScript type-checking (`tsc`) and Vite production bundle generation with 0 errors.

---

## ☁️ Cloud Deployment Guide

The platform is architected for seamless cloud deployment:

### Backend on Railway
* **Live Deployment:** [https://web-production-d5b3c14b.up.railway.app](https://web-production-d5b3c14b.up.railway.app)
* **Configuration:** `railway.json` utilizes the Nixpacks builder with `python run.py` entrypoint.
* **Health Check Path:** `/health`

### Frontend on Vercel
1. Link your GitHub repository to Vercel.
2. Set Root Directory to `.` (or `frontend`).
3. Set Framework Preset to **Vite**.
4. Configure Environment Variable:
   * **Key:** `VITE_API_URL`
   * **Value:** `https://web-production-d5b3c14b.up.railway.app`
5. Deploy.

---

## 🛡️ Ethics & Administrative Guardrails

1. **Human-in-the-Loop Governance:** The system acts strictly as an administrative **Decision Support System (DSS)**. It never unilaterally modifies cadastral ownership records or alters legal property titles.
2. **Immutable Source Preservation:** Raw historical cadastral maps, drone imagery, and revenue extracts are cryptographically sealed in their original native formats and coordinates.
3. **Do-Not-Decide (DND) Safeguard:** Ambiguous parcels with high residual displacement or conflicting multi-party evidence automatically route to "Do Not Decide" status for formal on-site field enquiry.
4. **Transparent Explainability:** Every spatial alignment is accompanied by full mathematical provenance: post-alignment RMSE, residual displacement vectors, confidence intervals, and spatial evidence graphs.

---

<div align="center">
  <b>BHUMI-FUSE — Smart India Hackathon PS-26013</b><br>
  <i>Empowering Transparent, Verifiable, and Scientifically Harmonized Land Administration</i>
</div>
