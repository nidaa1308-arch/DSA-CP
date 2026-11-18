<div align="center">

# 🌐 BHUMI-FUSE (भूमि-फ्यूज)
### Production-Grade Geospatial Harmonization, Cadastral Discrepancy Resolution & DSA Spatial Computing Engine

[![Python 3.11](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19.0-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![MapLibre GL](https://img.shields.io/badge/MapLibre_GL-6.6-blue?style=for-the-badge&logo=mapbox&logoColor=white)](https://maplibre.org/)
[![Live on Railway](https://img.shields.io/badge/Railway-Live_Backend-0B0D0E?style=for-the-badge&logo=railway&logoColor=white)](https://web-production-d5b3c14b.up.railway.app/health)
[![Pytest](https://img.shields.io/badge/Pytest-18%20Passed-449C44?style=for-the-badge&logo=pytest&logoColor=white)](backend/tests/)
[![Docker Ready](https://img.shields.io/badge/Docker-PostGIS_Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](docker-compose.yml)

**Smart India Hackathon (SIH PS-26013 — NAKSHA Programme)**  
*Automated Multi-Source Cadastral Harmonization, Topological Dispute Grouping, and Land Record Intelligence*

[Live Backend API](https://web-production-d5b3c14b.up.railway.app) • [Interactive API Docs (Swagger)](https://web-production-d5b3c14b.up.railway.app/docs) • [DSA Technical Guide](DSA_COURSE_EXTENSION.md) • [DSA Health Summary](https://web-production-d5b3c14b.up.railway.app/dsa/summary)

</div>

---

## 📑 Table of Contents
1. [Executive Summary](#-executive-summary)
2. [The Problem Statement (SIH PS-26013)](#-the-problem-statement-sih-ps-26013)
3. [Zero-Fabrication & Honest Metrics Guarantee](#-zero-fabrication--honest-metrics-guarantee)
4. [End-to-End System Architecture](#-end-to-end-system-architecture)
5. [Core DSA Computational Geometry Engine](#-core-dsa-computational-geometry-engine)
   - [DSA Inventory & Complexity Analysis](#dsa-inventory--complexity-analysis)
   - [Real-World Computational Geometry Solutions](#real-world-computational-geometry-solutions)
   - [Dedicated DSA REST Endpoints](#dedicated-dsa-rest-endpoints)
6. [Mathematical Transformations & Modeling](#-mathematical-transformations--modeling)
7. [Project Directory Layout](#-project-directory-layout)
8. [Getting Started & Local Development](#-getting-started--local-development)
9. [Automated Verification & Test Suite](#-automated-verification--test-suite)
10. [Cloud Deployment & Docker](#-cloud-deployment--docker)
11. [Administrative Guardrails & Tamper-Evident Ledger](#-administrative-guardrails--tamper-evident-ledger)

---

## 📌 Executive Summary

**BHUMI-FUSE** is an enterprise-grade geospatial harmonization, topological verification, and land administration dispute-resolution platform. Designed for Indian state revenue and urban-development departments under the **NAKSHA (National Geospatial Knowledge-Based Land Survey & Harmonization Action)** initiative (SIH PS-26013), it provides a rigorous decision-support tool that bridges historical cadastral records with modern high-precision observations (UAV drone orthomosaics, RTK GNSS control points, LiDAR DSM/DTM elevation, and 7/12 RoR revenue registers).

The platform enforces **zero-fabrication honesty**: every number, confidence score, and boundary coordinate is mathematically derived from uploaded datasets. It assists administrative revenue officers and never makes autonomous legal adjudications.

---

## 🎯 The Problem Statement (SIH PS-26013)

Digitizing Indian land records involves major technical and historical hurdles:
* **Historical Non-Linear Distortion:** Cadastral maps surveyed decades ago suffer from paper shrinkage, cloth stretching, local datum shifts, and chain-survey errors.
* **Physical Encroachments:** Built structures, compound walls, and roads frequently deviate from paper boundaries.
* **Coordinate Reference System (CRS) Clashes:** Incoming layers use incompatible datums (local Cassini-Soldner, Polyconic, UTM WGS84, or geographic lat/long).
* **Topological Defects:** Vectorization often creates slivers, self-intersections, and boundary collisions.
* **Administrative Load:** Officers lack objective triage tools to differentiate permissible measurement tolerances from actionable land disputes.

---

## 🛡️ Zero-Fabrication & Honest Metrics Guarantee

Following an exhaustive architectural audit (`docs/AUDIT.md`):
1. **Zero Hardcoded Benchmarks:** No synthetic fixed outputs, no fixed inlier counts, no artificial RMSE numbers, and no hidden thresholds.
2. **Fail Loudly:** If a dataset is corrupt, missing required columns, or incomplete, typed HTTP 4xx/5xx errors are returned with actionable diagnostic messages.
3. **Dual RMSE Reporting:** In-sample training fit is strictly separated from out-of-sample (held-out 80/20 cross-validated) RMSE.
4. **Isolated Sample Data:** Realistic demonstration datasets live exclusively in `data/samples/` and load via the same strict ingestion pipeline as live user data.
5. **No Area Loss:** Topological repairs use `make_valid` with an area-conservation delta threshold ($\le 2\%$) rather than destructive zero-width buffering.

---

## 🏗️ End-to-End System Architecture

```text
 ┌────────────────────────────────────────────────────────────────────────┐
 │                    1. MULTI-SOURCE INGESTION LAYER                     │
 │  • Cadastral Boundaries (GeoJSON / Shapefile zip / GeoPackage)        │
 │  • Drone Building Footprints (GeoJSON / Shapefile zip)                │
 │  • GNSS Ground Control Points (BOM-safe CSV / RTK Fixed)               │
 │  • DSM / DTM Elevation Grid (CSV / GeoTIFF)                            │
 │  • RoR Revenue Records (7/12 Extract CSV: Khata/Khasra/Owner)          │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │               2. METRIC NORMALIZATION & REPROJECTION                   │
 │  • EPSG Detection (pyproj) → Project to Local Metric CRS (UTM 43N)     │
 │  • Bounding box calculation & schema attribute normalization           │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │            3. GEOMETRIC REGISTRATION & EVIDENCE FUSION                 │
 │  • Global 1-to-1 Bipartite Matching (Hungarian Algorithm / O(n³))     │
 │  • 2D Spatial KD-Tree: Metric Nearest-Neighbour GNSS Control Matching  │
 │  • RANSAC Inlier Consensus Filtering + Affine / Regularized TPS Warping│
 │  • 80/20 Train-Test Held-Out Cross-Validated RMSE Computation          │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │           4. TOPOLOGICAL VERIFICATION & CONFLICT CLUSTERING            │
 │  • Bentley-Ottmann Sweep-Line Algorithm with Balanced AVL Tree Status  │
 │  • Distinguishes Proper Crossings vs Valid Shared Cadastral Boundaries │
 │  • Disjoint Set Union (DSU) Connected Conflict Zone Partitioning       │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │         5. DISCREPANCY RANKING, EVIDENCE GRAPH & AUDIT TRAIL           │
 │  • Dynamic Severity Scoring: Critical, Needs Review, Low, Auto-Resolved│
 │  • Bipartite Spatial Evidence Graph (Physical-to-Legal Relationships)  │
 │  • A* Search: Multi-Stop Inspection Field Visit Route Planning         │
 │  • Dual SHA-256 Hash Chain Immutable Ledger (Audits & Review Decisions)│
 └────────────────────────────────────────────────────────────────────────┘
```

---

## 🧠 Core DSA Computational Geometry Engine

All six course algorithms are implemented in pure Python with unit tests verified against brute-force oracles:

### DSA Inventory & Complexity Analysis

| # | Data Structure / Algorithm | Source Module | Core Operation | Theoretical Complexity | Production Role in BHUMI-FUSE |
|:---:|---|---|---|:---:|---|
| **1** | **2D Spatial KD-Tree** | `backend/app/dsa/kd_tree.py` | `nearest()`, `k_nearest()`, `radius_query()` | Average $\mathcal{O}(\log n)$<br>Worst $\mathcal{O}(n)$ | Matches parcel centroids to high-precision GNSS/RTK base observation points in metric space. |
| **2** | **Sweep-Line Algorithm** | `backend/app/dsa/sweep_line.py` | Segment Intersections | $\mathcal{O}((n + k) \log n)$ vs $\mathcal{O}(n^2)$ | Bentley-Ottmann event sweep detecting boundary overlaps while correctly exempting valid shared cadastral edges. |
| **3** | **AVL Tree** | `backend/app/dsa/avl_tree.py` | `insert()`, `delete()`, `successor()`, `predecessor()` | Strict $\mathcal{O}(\log n)$ | Balanced binary search tree maintaining the active sweep-line status structure with height balance factor $\in \{-1, 0, 1\}$. |
| **4** | **Disjoint Set Union (DSU)** | `backend/app/dsa/disjoint_set.py` | `find()` & `union()` | Amortized $\mathcal{O}(\alpha(n)) \approx \mathcal{O}(1)$ | Two-pass path compression + union-by-rank clustering intersecting parcels into connected dispute zones with mean/max metrics. |
| **5** | **A\* Search Algorithm** | `backend/app/dsa/astar.py` | `astar_search()`, `plan_field_visit()` | Heuristic Graph Search $\mathcal{O}(b^d)$ | Optimizes inspection travel routes for revenue officers visiting flagged dispute parcels across municipal road networks. |
| **6** | **Spatial Quadtree** | `backend/app/dsa/quadtree.py`<br>`frontend/src/utils/quadtree.ts` | 2D Window Range Query | $\mathcal{O}(\log n)$ avg per viewport query | Hierarchical 2D space partitioning indexing parcel coordinate bounds for sub-millisecond map viewport rendering. |
| *—* | *SQLite R-Tree* | `backend/app/db.py` | *B-Tree Spatial Indexing* | *$\mathcal{O}(\log M)$* | *Retained baseline database spatial indexing (documented as pre-existing, not claimed as course contribution).* |

---

### Real-World Computational Geometry Solutions

* **Problem 1: All-Pairs GNSS Scanning**  
  *Old Approach:* $\mathcal{O}(N \cdot M)$ brute-force distance calculations between $N$ parcels and $M$ GNSS points.  
  *BHUMI-FUSE Solution:* 2D KD-Tree built once in $\mathcal{O}(M \log M)$; each parcel queries nearest GNSS in $\mathcal{O}(\log M)$.
* **Problem 2: Boundary Collision Detection**  
  *Old Approach:* $\mathcal{O}(E^2)$ brute-force comparison of all polygon edges.  
  *BHUMI-FUSE Solution:* Bentley-Ottmann Sweep-Line with an AVL Tree active status structure in $\mathcal{O}((E + K) \log E)$, correctly ignoring legitimate shared parcel boundaries.
* **Problem 3: Multi-Parcel Dispute Cascades**  
  *Old Approach:* Recursive graph searches prone to stack overflows on dense cadastral grids.  
  *BHUMI-FUSE Solution:* Disjoint Set Union with union-by-rank and iterative path compression partitions conflict zones in $\mathcal{O}(\alpha(P))$.

---

### Dedicated DSA REST Endpoints

* **`GET /dsa/summary`** — Returns the full inventory of all 6 DSA modules, theoretical complexities, and GIS use cases.
* **`POST /dsa/astar-route`** — Executes A* shortest path search over a weighted node graph using Euclidean distance heuristics.
* **`POST /dsa/quadtree-query`** — Indexes coordinates in a Quadtree and executes sublinear spatial viewport window queries.
* **`POST /validate`** — Evaluates topology using the **Sweep-Line + AVL Tree** collision detector and returns **DSU** conflict clusters.

---

## 📐 Mathematical Transformations & Modeling

### 1. RANSAC Inlier Estimation
Filters false correspondences caused by modern structural modifications:
$$r_i = \|\mathbf{T}(\mathbf{x}_i) - \mathbf{y}_i\| \le \tau_{\text{inlier}} \quad (\tau = 2.0\text{ m})$$

### 2. 6-Parameter Metric Affine Transformation
Provides rigid rotation, translation, and scale correction:
$$\begin{bmatrix} x' \\ y' \end{bmatrix} = \begin{bmatrix} a & b \\ c & d \end{bmatrix} \begin{bmatrix} x \\ y \end{bmatrix} + \begin{bmatrix} t_x \\ t_y \end{bmatrix}$$

### 3. Regularized Thin Plate Spline (TPS)
Models non-linear historical paper shrinkage with Tikhonov regularization $\lambda \mathbf{I}$:
$$f(\mathbf{x}) = \mathbf{A}\mathbf{x} + \mathbf{t} + \sum_{i=1}^n w_i U(\|\mathbf{x} - \mathbf{c}_i\|), \quad U(r) = r^2 \ln(r)$$

### 4. Held-Out Cross-Validation
Control points are split 80% train / 20% test:
$$\text{RMSE}_{\text{held-out}} = \sqrt{\frac{1}{|S_{\text{test}}|} \sum_{j \in S_{\text{test}}} \|\mathbf{T}_{\text{train}}(\mathbf{x}_j) - \mathbf{y}_j\|^2}$$

---

## 📂 Project Directory Layout

```text
BhumiFuse/
├── .github/workflows/ci.yml           # 🚀 GitHub Actions CI Pipeline (Backend + Frontend)
├── docs/
│   ├── AUDIT.md                       # 📋 Exhaustive Phase 0 defect audit & confirmation
│   └── ARCHITECTURE.md                # 🏛️ Target system architecture specification
├── data/samples/                      # 📁 Clean, isolated sample datasets
│   ├── cadastral_sample.geojson       # Historical cadastral boundary polygons
│   ├── drone_footprints.geojson       # Modern UAV building footprints
│   ├── gnss_points.csv                # High-accuracy RTK ground control points
│   └── revenue_7_12.csv               # Legal RoR ownership & encumbrance registers
├── scripts/
│   └── seed_sample_investigation.py   # Database seeder for sample investigation
├── run.py                             # ⚡ Resilient unified server entrypoint
├── Dockerfile                         # Production container image
├── docker-compose.yml                 # PostGIS + Backend API + Frontend services
│
├── backend/                           # ── FASTAPI BACKEND ENGINE ──
│   ├── requirements.txt               # Pinned Python dependencies
│   ├── app/
│   │   ├── main.py                    # FastAPI controllers, routes, and lifecycles
│   │   ├── db.py                      # SQLite database, dual hash chains & R-Tree
│   │   ├── core/                      # Configuration, error hierarchy, JWT auth
│   │   ├── models/                    # SQLAlchemy 2 models & Pydantic v2 schemas
│   │   ├── ingest/                    # Unified parsers (GeoJSON, SHP, GPKG, GeoTIFF, CSV)
│   │   ├── services/                  # Correspondence, Registration, Topology, Audit
│   │   └── dsa/                       # ── 🧠 ADVANCED DSA PACKAGE ──
│   │       ├── kd_tree.py             # 2D KD-Tree (metric nearest & radius queries)
│   │       ├── avl_tree.py            # Balanced AVL Tree with true deletion
│   │       ├── sweep_line.py          # Bentley-Ottmann sweep-line intersection detector
│   │       ├── disjoint_set.py        # DSU with union-by-rank & path compression
│   │       ├── astar.py               # A* shortest path & field inspection tour
│   │       └── quadtree.py            # Hierarchical 2D spatial Quadtree
│   └── tests/
│       ├── test_dsa.py                # Exhaustive DSA property tests vs oracles
│       └── test_api_integration.py    # Full API lifecycle & regression tests (18 passed)
│
└── frontend/                          # ── REACT + VITE + TAILWIND FRONTEND ──
    ├── package.json                   # Pinned frontend dependencies
    ├── vite.config.ts                 # Chunking configuration (< 250 kB entry)
    ├── index.html                     # HTML5 standards-compliant doctype/head/viewport
    └── src/
        ├── main.tsx                   # React root controller & view router
        ├── api/client.ts              # Strongly typed API client
        ├── components/                # 5-step guided workflow UI views
        └── utils/                     # Client-side geometry engine & Quadtree
```

---

## 🚀 Getting Started & Local Development

### Prerequisites
* **Python 3.11+**
* **Node.js 20+** and **npm**

### 1. Backend Setup
```bash
# Navigate to backend and setup virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Start backend server
python run.py
```
* **API Live:** `http://localhost:8000`
* **Swagger Documentation:** `http://localhost:8000/docs`

### 2. Frontend Setup
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
* **Web App:** `http://localhost:5173`

---

## 🧪 Automated Verification & Test Suite

The test suite validates both the computational geometry DSA package and the end-to-end API lifecycle:

```bash
# Set PYTHONPATH and execute pytest
$env:PYTHONPATH="backend"
python -m pytest backend/tests/ -v
```

### Test Results Summary:
```text
============================= test session starts =============================
collected 18 items

backend/tests/test_api_integration.py::test_health_endpoint PASSED       [  5%]
backend/tests/test_api_integration.py::test_dsa_summary_endpoint PASSED  [ 11%]
backend/tests/test_api_integration.py::test_dsa_quadtree_spatial_query PASSED [ 16%]
backend/tests/test_api_integration.py::test_dsa_astar_pathfinding PASSED [ 22%]
backend/tests/test_api_integration.py::test_audit_verification_chains PASSED [ 27%]
backend/tests/test_api_integration.py::test_harmonize_fails_with_insufficient_sources PASSED [ 33%]
backend/tests/test_api_integration.py::test_sample_investigation_lifecycle_and_honest_metrics PASSED [ 38%]
backend/tests/test_dsa.py::test_kdtree_against_brute_force PASSED        [ 44%]
backend/tests/test_dsa.py::test_kdtree_edge_cases PASSED                 [ 50%]
backend/tests/test_dsa.py::test_avl_tree_invariants_and_duplicate_keys PASSED [ 55%]
backend/tests/test_dsa.py::test_avl_tree_true_deletion PASSED            [ 61%]
backend/tests/test_dsa.py::test_sweep_line_detects_proper_crossings PASSED [ 66%]
backend/tests/test_dsa.py::test_sweep_line_ignores_valid_shared_cadastral_boundaries PASSED [ 72%]
backend/tests/test_dsa.py::test_dsu_union_by_rank_and_path_compression PASSED [ 77%]
backend/tests/test_dsa.py::test_dsu_conflict_zones PASSED                [ 83%]
backend/tests/test_dsa.py::test_astar_optimal_path_and_target_only_nodes PASSED [ 88%]
backend/tests/test_dsa.py::test_astar_field_visit_planning PASSED        [ 94%]
backend/tests/test_dsa.py::test_quadtree_10k_parcels_against_brute_force PASSED [100%]

======================== 18 passed, 1 warning in 1.71s ========================
```

---

## 🐳 Cloud Deployment & Docker

### Run with Docker Compose
```bash
docker-compose up --build
```
This spins up:
1. `db`: PostGIS 16-3.4 database on port 5432 with persistent volume `pgdata`.
2. `api`: FastAPI backend on port 8000.
3. `web`: React frontend on port 5173.

### Production Cloud Deployment
* **Backend:** Deployed on **Railway** with resilient port handling.
* **Frontend:** Configured for **Vercel** with optimized code-splitting chunks (< 250 kB initial bundle).

---

## ⚖️ Administrative Guardrails & Tamper-Evident Ledger

1. **Human-in-the-Loop:** BHUMI-FUSE acts as an assistive decision-support engine. All final boundary mutations require formal administrative sign-off by a designated revenue officer.
2. **Dual SHA-256 Hash Chain:**
   * Every audit log event is cryptographically linked to the previous entry:
     $$\text{Hash}_k = \text{SHA256}(\text{Hash}_{k-1} \parallel \text{JSON}(\text{Row}_k))$$
   * Review decisions maintain an independent versioned hash chain to guarantee court admissibility.
3. **Chain Verification:** Call `GET /audit/verify` at any time to verify cryptographic integrity across all recorded decisions.
