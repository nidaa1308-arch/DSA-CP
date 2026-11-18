# BHUMI-FUSE: Target Architecture & Redesign Specification

**Target Standard:** SIH PS-26013 (NAKSHA Programme) & Advanced DSA Course Evaluation  
**System Type:** Production-Grade Decision Support System (DSS) for Land Record Harmonization

---

## 1. Architectural Principles

1. **Deterministic & Genuine Computation:** Zero fabricated metrics, zero simulated fallbacks, zero synthetic calibration branches. If data is missing or insufficient, return typed HTTP 4xx/5xx errors.
2. **Investigation-Scoped Isolation:** All data, spatial indexes, upload artifacts, and review decisions are strictly scoped by `investigation_id`. No shared module-level global state.
3. **Dual Database Tier:** 
   - **Production:** PostgreSQL 16 + PostGIS 3.4 via SQLAlchemy 2 + asyncpg / psycopg3.
   - **Local / Test:** SQLite (with SpatiaLite / pure-Python spatial fallbacks) for zero-dependency pytest execution.
4. **Decoupled Layered Architecture:** Clear separation between API routes, domain services, ingestion parsers, data structures, and core security/config.
5. **Calm, Accessible Government UI:** Adheres to GIGW 3.0 and WCAG 2.1 AA. Single 5-step guided workflow, large typography, high contrast, multilingual (English, Hindi, Marathi), and zero unpinned dependencies.

---

## 2. Target File Tree

```text
BhumiFuse/
├── docs/
│   ├── AUDIT.md                      # Comprehensive defect audit findings
│   ├── ARCHITECTURE.md               # Target system design & specifications
│   └── USER_GUIDE.md                 # Plain-language officer manual
├── data/
│   └── samples/                      # Curated real-world pilot datasets for demonstration
│       ├── cadastral_sample.geojson
│       ├── drone_footprints.geojson
│       ├── gnss_points.csv
│       ├── elevation_dsm.csv
│       └── revenue_7_12.csv
├── docker-compose.yml                 # PostGIS + FastAPI Backend + React Web
├── Dockerfile                         # Production multi-stage Docker build
├── Procfile                           # Cloud container process specification
├── railway.json                       # Railway deployment configuration
├── run.py                             # Resilient server entrypoint
├── README.md                          # Master project documentation
│
├── backend/
│   ├── requirements.txt               # Pinned production Python dependencies
│   ├── requirements-dev.txt           # Test & linting dependencies (pytest, hypothesis, ruff)
│   ├── tests/                         # Full automated test suite
│   │   ├── conftest.py                # Fixtures & mock PostGIS/SQLite test database
│   │   ├── test_dsa_kdtree.py         # KD-Tree unit & property tests vs brute-force
│   │   ├── test_dsa_sweepline.py      # Bentley-Ottmann sweep-line tests (shared edges vs overlaps)
│   │   ├── test_dsa_avltree.py        # AVL Tree height invariant & duplicate key tests
│   │   ├── test_dsa_disjoint_set.py   # DSU path compression & zone aggregation tests
│   │   ├── test_dsa_astar.py          # A* pathfinding & heuristic admissibility tests
│   │   ├── test_dsa_quadtree.py       # Quadtree spatial partitioning & window tests
│   │   ├── test_ingest.py             # Parsers: GeoJSON, SHP, GPKG, GeoTIFF, BOM-CSV
│   │   ├── test_harmonization.py      # Registration: RANSAC, TPS, Affine, Held-Out RMSE
│   │   ├── test_topology.py           # Validations, make_valid area conservation
│   │   └── test_audit_integrity.py   # Cryptographic SHA-256 chain verification
│   └── app/
│       ├── __init__.py
│       ├── main.py                    # FastAPI application initialization & middleware
│       ├── core/
│       │   ├── config.py              # Validated Pydantic Settings (DATABASE_URL, CORS, limits)
│       │   ├── security.py            # JWT token validation, role-based access control (RBAC)
│       │   └── errors.py              # Standardized API error hierarchy & exception handlers
│       ├── models/
│       │   ├── database.py            # SQLAlchemy 2 declarative models (Investigation, Source, Audit, Decision)
│       │   └── schemas.py             # Pydantic v2 request/response schemas
│       ├── dsa/                       # ── ADVANCED COMPUTATIONAL GEOMETRY PACKAGE ──
│       │   ├── __init__.py
│       │   ├── kd_tree.py             # 2D KD-Tree: k-NN and radius queries in metric space
│       │   ├── avl_tree.py            # Balanced AVL Tree with insert, delete, and moving keys
│       │   ├── sweep_line.py          # Bentley-Ottmann sweep with intersection queue & shared-edge filter
│       │   ├── disjoint_set.py        # DSU with rank & path compression + cluster analytics
│       │   ├── astar.py               # A* graph router with explored node diagnostics
│       │   └── quadtree.py            # 2D Spatial Quadtree with bounding-box window queries
│       ├── ingest/                    # ── ROBUST MULTI-FORMAT INGESTION PARSERS ──
│       │   ├── __init__.py
│       │   ├── base.py                # Abstract parser interface & CRS normalizer
│       │   ├── vector.py              # GeoJSON, Shapefile (zip), GeoPackage parser (MultiPolygon safe)
│       │   ├── raster.py              # GeoTIFF/COG raster parser (Rasterio/GDAL headers & bounds)
│       │   ├── tabular.py             # BOM-safe CSV parser with delimiter sniffing & header matching
│       │   └── elevation.py           # DSM/DTM point grid & raster elevation parser
│       ├── services/                  # ── CORE DOMAIN BUSINESS SERVICES ──
│       │   ├── __init__.py
│       │   ├── correspondence.py      # Global 1-to-1 bipartite assignment (Hungarian / greedy resolver)
│       │   ├── registration.py        # Metric RANSAC + regularized TPS + Affine + Held-Out RMSE
│       │   ├── topology.py            # Shapely make_valid repair with area preservation checks
│       │   ├── evidence_graph.py      # Bipartite physical-to-legal spatial evidence network
│       │   └── audit_service.py       # Serialized transaction hash-chain logger & verifier
│       └── api/                       # ── REST API CONTROLLERS ──
│           ├── __init__.py
│           ├── auth.py                # Authentication, login, officer identity
│           ├── investigations.py      # CRUD for investigations & lifecycle states
│           ├── ingest.py              # File upload endpoints per data type
│           ├── harmonize.py           # Registration, correspondence, and residual calculation
│           ├── topology.py            # Topological verification, Sweep-Line & DSU zones
│           ├── audit.py               # Review decision submission & chain verification
│           └── dsa.py                 # Direct evaluation endpoints for all 6 DSA concepts
│
└── frontend/                          # ── STREAMLINED ACCESSIBLE SPA (React 19 + Vite) ──
    ├── index.html                     # Standard HTML5 document with viewport & SEO meta
    ├── package.json                   # Strictly pinned dependencies
    ├── vite.config.ts                 # Code-split bundler config (manual chunking)
    ├── tailwind.config.js             # High-contrast GIGW 3.0 theme palette
    └── src/
        ├── main.tsx                   # App root & providers
        ├── i18n/                      # Externalized string dictionary (en, hi, mr)
        │   ├── en.json
        │   ├── hi.json
        │   └── mr.json
        ├── api/                       # Typed client mapping 1-to-1 with backend OpenAPI
        │   └── client.ts
        ├── utils/
        │   └── quadtree.ts            # Client-side Quadtree for map viewport culling
        ├── components/
        │   ├── common/                # Accessible primitives (Button, Modal, Toast, Badge)
        │   ├── layout/                # Header, Progress Stepper, Help Drawer
        │   └── map/                   # Lazy-loaded MapLibre component with Quadtree indexing
        └── views/                     # ── 5-STEP GUIDED OFFICER WORKFLOW ──
            ├── CaseListView.tsx       # Step 0: Investigation Dashboard & "New Case"
            ├── Step1_CreateCase.tsx   # Step 1: Metadata, Administrative Ward, Projected CRS
            ├── Step2_UploadData.tsx   # Step 2: Drag-and-drop multi-source upload & validation
            ├── Step3_AlignData.tsx    # Step 3: Before/After slider, registration & held-out error
            ├── Step4_ReviewParcels.tsx# Step 4: Split-screen discrepancy triage & action panel
            ├── Step5_FieldReport.tsx  # Step 5: DSU conflict clusters, A* route & PDF export
            └── AuditVerifyView.tsx    # Independent cryptographic chain validator
```

---

## 3. Data Structures & Algorithms (DSA) Specifications

### 1. 2D Spatial KD-Tree (`app/dsa/kd_tree.py`)
* **Metric Coordinate Support:** Built in projected coordinate space (UTM metres), eliminating latitude-dependent longitudinal distortion.
* **Operations:**
  * `insert(point, payload)`: Balanced $O(n \log n)$ construction by alternating split axes ($x$ at depth even, $y$ at depth odd) using median selection.
  * `nearest(query_point)`: Average $O(\log n)$ branch-and-bound nearest neighbour search with hypersphere boundary pruning.
  * `k_nearest(query_point, k)`: Returns $k$ closest neighbours maintained via a max-heap of capacity $k$.
  * `radius_query(query_point, radius)`: Returns all control points within metric distance $r$.
* **Application:** Resolves the closest GNSS base monument or ground control point for every cadastral boundary vertex without exhaustive $O(n \cdot m)$ scanning.

### 2. Bentley-Ottmann Sweep-Line Algorithm (`app/dsa/sweep_line.py`)
* **Intersection Event Queue:** Min-heap ordering segment left endpoints (insert), right endpoints (delete), and dynamic intersection points (swap).
* **Active Status Structure:** Backed by the incremental `AVLTree` ordered by $y$-coordinate at the current sweep line position $x$.
* **Topological Boundary Classification:**
  * *Proper Crossing:* Edges cross internally $\rightarrow$ Flagged as collision.
  * *Collinear Overlap:* Edges overlap on identical line $\rightarrow$ Flagged as encroachment dispute.
  * *Shared Boundary:* Adjacent parcels sharing legitimate identical vertices/edges $\rightarrow$ **Ignored** (normal cadastral adjacency).
* **Application:** Detects structural boundary violations and overlaps across thousands of parcel polygons in $O((n + k) \log n)$ time.

### 3. Self-Balancing AVL Tree (`app/dsa/avl_tree.py`)
* **Balance Invariant:** Guaranteed $|h(\text{left}) - h(\text{right})| \le 1$ at every node via single (LL, RR) and double (LR, RL) rotations.
* **Full Dictionary Operations:**
  * `insert(key, value)`: $O(\log n)$ insertion with deterministic secondary tie-breaking for duplicate keys.
  * `delete(key, value)`: True $O(\log n)$ node removal with full rebalancing along the parent path (no full tree rebuilds).
  * `find(key)` / `predecessor(node)` / `successor(node)`: $O(\log n)$ neighbour lookups for adjacent sweep segments.
* **Dynamic Coordinate Evaluation:** Compares segment vertical positions $y(x) = y_1 + \frac{x - x_1}{x_2 - x_1}(y_2 - y_1)$ dynamically at sweep position $x$.

### 4. Disjoint Set Union (DSU) (`app/dsa/disjoint_set.py`)
* **Asymptotics:** Amortized $\mathcal{O}(\alpha(n)) \approx \mathcal{O}(1)$ via path compression (flattening tree pointers on `find`) and union-by-rank.
* **Cluster Analytics:**
  * Aggregates connected conflict zones from intersecting parcel pairs.
  * Computes real cluster statistics: parcel member count, bounding box envelope, total disputed area, and mean/max residual displacement.
* **Application:** Converts isolated pairwise collisions into coherent land dispute zones for revenue court notices.

### 5. A\* Search Algorithm (`app/dsa/astar.py`)
* **Heuristic:** Admissible Euclidean straight-line distance $h(u, v) = \sqrt{(x_u - x_v)^2 + (y_u - y_v)^2}$, guaranteeing optimal path recovery.
* **Graph Structure:** Operates over directed or undirected road/access networks extracted from municipal GeoJSON layers.
* **Robustness:** Handles disconnected components, target-only nodes, and returns path coordinates, total traversal distance (metres), and explored node count.
* **Officer Feature ("Plan Field Visit"):** Computes the shortest inspection tour connecting the survey office to all Critical/Needs-Review parcels.

### 6. Spatial Quadtree (`app/dsa/quadtree.py` & `frontend/src/utils/quadtree.ts`)
* **Spatial Partitioning:** Recursively splits 2D geographic bounding boxes into North-West, North-East, South-West, South-East quadrants when capacity threshold is reached.
* **Range Search:** Prunes non-intersecting subtrees; returns all parcels intersecting the camera viewport in average $O(\log n)$ time.
* **Client-Side Optimization:** Enables the MapLibre canvas to fluidly pan and zoom across 10,000+ parcels at 60 FPS by rendering only visible features.

---

## 4. Ingestion & Pre-Processing Architecture

### Supported Formats & Real Parsers
1. **Cadastral & Buildings (Vector):** `pyogrio` / `shapely` parsing GeoJSON, Shapefile (.zip), and GeoPackage (.gpkg). Handles `Polygon` and `MultiPolygon` natively.
2. **GNSS Points (Tabular):** Python `csv` with UTF-8 BOM stripping (`utf-8-sig`) and delimiter sniffing (`csv.Sniffer`). Parses latitude, longitude, elevation, horizontal accuracy ($1\sigma$), and RTK fix status (`FIXED`, `FLOAT`, `SINGLE`).
3. **Elevation DSM/DTM:** GeoTIFF raster parsing via `rasterio` or tabular elevation point grids.
4. **Revenue Records (RoR / 7/12 Extract):** Ingests khata numbers, khasra/survey numbers, recorded area ($m^2$), owner of record, encumbrance flags, and mutation counts.

### Coordinate Reference System (CRS) Normalization
1. Reads source CRS from file metadata or vector projection header (`.prj`, GeoPackage SRS table).
2. If unprojected (e.g. WGS84 `EPSG:4326`), computes data centroid and selects appropriate metric UTM zone (e.g. UTM Zone 43N / `EPSG:32643` for Maharashtra).
3. Performs true coordinate transformation using `pyproj.Transformer(always_xy=True)` across all geometry rings and persists the reprojected coordinates.

---

## 5. Geometric Registration & Discrepancy Scoring

### 1. Global 1-to-1 Correspondence Matching
* Eliminates greedy duplicates by constructing a cost matrix between Cadastral Parcels and Physical Footprints:
  $$C_{ij} = w_d \cdot \frac{d(c_i, c_j)}{R} + w_a \cdot \left| 1 - \frac{\text{Area}_j}{\text{Area}_i \cdot \text{Ratio}_{\text{exp}}} \right| + w_c \cdot (1 - \text{Containment}(j \in i))$$
* Solves optimal bipartite matching via the Hungarian Algorithm (`scipy.optimize.linear_sum_assignment`).
* Ambiguous matches ($C_{ij} > \text{threshold}$) are isolated and never feed the transformation solver.

### 2. Multi-Model Transformation
* **RANSAC Estimator:** Randomly samples minimum point sets to estimate inlier consensus, rejecting structural modifications and outlier corners.
* **Affine Alignment:** Fits 6-parameter matrix (rotation, translation, non-uniform scaling, shear) in metric coordinates.
* **Regularized Thin Plate Spline (TPS):** Solves the $(n+3) \times (n+3)$ metric system with diagonal Tikhonov regularization $\lambda \cdot I$ ($\lambda = 0.01$), preventing numerical singularization.
* **Held-Out Cross-Validation:** Computes transformation parameters on $80\%$ of control points; reports true out-of-sample RMSE on remaining $20\%$ held-out points.

---

## 6. Cryptographic Audit Trail & Governance

```text
 ┌─────────────────────────────────────────────────────────────┐
 │                      TRANSACTION BLOCK                      │
 │                                                             │
 │  [Previous Row Hash] ──────────────────────────┐            │
 │                                                │            │
 │  [Record Data]                                 │            │
 │  • Record ID / Investigation ID                ▼            │
 │  • Officer ID & User Role              ┌───────────────┐    │
 │  • Timestamp (UTC ISO-8601)      ────► │ SHA-256 HASH  │    │
 │  • Action: ACCEPT / REJECT / ESCALATE  │   ALGORITHM   │    │
 │  • Input Data Cryptographic Hashes     └───────┬───────┘    │
 │  • Algorithm Parameters Snapshot               │            │
 │                                                ▼            │
 │                                       [Current Row Hash]    │
 └─────────────────────────────────────────────────────────────┘
```

1. **Serialized SQLite / PostGIS Transactions:** Written with `EXCLUSIVE` locks to prevent concurrency race conditions.
2. **Dual Chain Verification:** Dedicated verification routines for both `audit_logs` and `review_decisions`.
3. **Reproducibility Guarantee:** Any recorded decision can be re-run against historical parameters to prove algorithmic determinism in legal revenue courts.

---

## 7. Streamlined 5-Step Officer Workflow (Frontend)

```text
Step 1: Create Case  ──► Step 2: Upload Data  ──► Step 3: Align & Check  ──► Step 4: Review Parcels  ──► Step 5: Report & Export
 (Name, Ward, CRS)       (Cadastral, Drone,       (Before/After Slider,       (Triage Table, Map &         (PDF, CSV, DSU Zones,
                          GNSS, 7/12 Records)       Held-out RMSE, Params)      Action: Accept/Escalate)    A* Field Visit Route)
```

* **Calm Government Palette:** Slate Navy (`#0f172a`), Clean White (`#ffffff`), Neutral Gray (`#f8fafc`), with high-contrast accessibility tags for Critical (Red), Review (Amber), and Auto-Accepted (Green).
* **Multilingual i18n:** Built-in localization support for **English**, **Hindi (हिंदी)**, and **Marathi (मराठी)**.
* **Performance:** Code-split route loading via `React.lazy()` ensuring initial vendor bundle remains $< 250\text{ KB}$.
