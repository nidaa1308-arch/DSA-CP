# BHUMI-FUSE — AI & Spatial Land Record Harmonization

BHUMI-FUSE is an end-to-end geospatial harmonization and multi-source conflict resolution system for Smart India Hackathon (SIH PS-26013, NAKSHA Programme). It ingests authoritative legacy cadastral maps, drone orthomosaics, satellite imagery, GNSS survey points, and municipal layers to detect encroachments, boundary discrepancies, and land disputes through rigorous mathematical alignment and spatial intelligence.

---

## 📚 DSA Course Project Extension

This repository integrates **six advanced Data Structures and Algorithms (DSA)** directly into the core geospatial pipeline, extending the system's performance and topological integrity beyond traditional GIS tools:

```
Investigation / Multi-Source Upload
  ├── Cadastral Boundaries
  ├── Drone / Extracted Buildings
  ├── GNSS Ground Control Points  ──────► [ 1. KD-Tree: O(log n) Nearest-Neighbor Search ]
  ├── Municipal & Road Network   ──────► [ 5. A* Search: Field Verification Routing ]
  └── Map Viewport Rendering     ──────► [ 6. Quadtree: Hierarchical Viewport Partitioning ]
          │
          ▼
Harmonization & Registration Engine (Affine / TPS / RANSAC)
          │
          ▼
Topology & Boundary Validation   ──────► [ 2. Sweep-Line Algorithm: O((n+k) log n) Intersections ]
                                 ──────► [ 3. AVL Tree: O(log n) Self-Balancing Active State ]
                                 ──────► [ 4. Disjoint Set Union (DSU): α(n) Conflict Clustering ]
          │
          ▼
Discrepancy Ranking & Evidence Graph
```

---

## 🗂️ VS Code Project Structure

For presenting to course instructors or evaluators in VS Code, all DSA algorithms are cleanly encapsulated in standard, self-contained Python modules under `backend/app/dsa/`:

```
c:\Users\...\BhumiFuse\
├── DSA_COURSE_EXTENSION.md           # In-depth architectural & complexity analysis
├── README.md                          # Project & course documentation
├── backend/
│   ├── app/
│   │   ├── dsa/                       # ── CORE DSA IMPLEMENTATIONS ──
│   │   │   ├── __init__.py            # Clean exports of all DSA classes
│   │   │   ├── kd_tree.py             # 2D Spatial KD-Tree (GNSS nearest-neighbor search)
│   │   │   ├── avl_tree.py            # Self-Balancing AVL Tree (active sweep-line structure)
│   │   │   ├── sweep_line.py          # Sweep-Line Algorithm (parcel-boundary intersections)
│   │   │   ├── disjoint_set.py        # Disjoint Set Union (DSU with rank & path compression)
│   │   │   ├── astar.py               # A* Search Algorithm (field-verification route planner)
│   │   │   └── quadtree.py            # Spatial Quadtree (2D hierarchical region querying)
│   │   ├── db.py                      # Baseline SQLite R-Tree spatial index (retained)
│   │   ├── main.py                    # FastAPI server wiring DSA modules into harmonization
│   │   ├── study_areas.py             # Curated pilot area geometries
│   │   └── revenue_data.py            # Land revenue & RoR extract mappings
│   └── tests/
│       └── test_dsa.py                # Comprehensive pytest suite for all 6 DSA modules
└── frontend/
    └── src/
        ├── api/client.ts              # Frontend client exposing DSA endpoints
        ├── components/
        │   └── DemoMap.tsx            # MapLibre renderer with Quadtree viewport filtering
        └── utils/
            └── quadtree.ts            # Client-side TypeScript Quadtree implementation
```

---

## ⚡ DSA Complexity & Use-Case Matrix

| # | Data Structure / Algorithm | File Location | Core Operation | Theoretical Complexity | Real-World Application in BhumiFuse |
|---|---|---|---|---|---|
| **1** | **2D Spatial KD-Tree** | `backend/app/dsa/kd_tree.py` | Nearest-Neighbor Search | Average $O(\log n)$, Worst $O(n)$ | Replaces $O(n \cdot m)$ brute-force distance scans to find the closest GNSS control point for each parcel. |
| **2** | **Sweep-Line Algorithm** | `backend/app/dsa/sweep_line.py` | Segment Intersections | $O((n + k) \log n)$ vs $O(n^2)$ | Bentley-Ottmann style event sweep to detect overlapping parcel boundaries without comparing all pairs. |
| **3** | **AVL Tree** | `backend/app/dsa/avl_tree.py` | Insert / Delete / Search | Guaranteed $O(\log n)$ | Self-balancing binary search tree used as the active sweep-line status structure to maintain vertical segment order. |
| **4** | **Disjoint Set Union (DSU)** | `backend/app/dsa/disjoint_set.py` | `find()` & `union()` | Amortized $O(\alpha(n)) \approx O(1)$ | Groups pairwise intersecting parcels into connected conflict zones/dispute clusters using path compression & union by rank. |
| **5** | **A\* Search Algorithm** | `backend/app/dsa/astar.py` | Pathfinding | Heuristic-guided graph search | Computes the shortest travel path between survey stations for field ground-truthing teams over road networks. |
| **6** | **Spatial Quadtree** | `backend/app/dsa/quadtree.py`<br>`frontend/src/utils/quadtree.ts` | 2D Range / BBox Query | Sublinear average for spatial data | Partitions 2D geographic space so only parcels within the current map viewport are rendered, improving FPS. |
| *—* | *SQLite R-Tree* | `backend/app/db.py` | *Bounding-box filtering* | *$O(\log M)$* | *Existing baseline candidate filtering (retained, not counted as new DSA).* |

---

## 🧪 Verification & Running Tests

### 1. Run Backend DSA Unit Tests
In VS Code, open the terminal in the `backend/` directory:
```bash
cd backend
python -m pytest tests/test_dsa.py -v
```
**Expected output:**
```
tests/test_dsa.py::test_kdtree_nearest PASSED                            [ 16%]
tests/test_dsa.py::test_avl_sorted PASSED                                [ 33%]
tests/test_dsa.py::test_dsu_groups PASSED                                [ 50%]
tests/test_dsa.py::test_astar PASSED                                     [ 66%]
tests/test_dsa.py::test_quadtree PASSED                                  [ 83%]
tests/test_dsa.py::test_sweep_line_detects_cross_parcel_intersection PASSED [100%]

============================== 6 passed in 0.04s ==============================
```

### 2. Verify Frontend Production Build
In the `frontend/` directory:
```bash
cd frontend
npm run build
```
Compiles with 0 TypeScript errors and produces production bundles.

---

## 🌐 API Endpoints for DSA Verification

The backend exposes dedicated endpoints to test and inspect the DSA implementations directly:

* **`GET /dsa/summary`** — Returns a complete inventory of all DSA modules, their parameters, and time complexities.
* **`POST /dsa/astar-route`** — Runs A* pathfinding over a user-supplied road graph and coordinate set.
* **`POST /dsa/quadtree-query`** — Indexes a collection of spatial points into a Quadtree and returns only points matching a bounding box.
* **`POST /validate`** — Runs the **Sweep-Line + AVL Tree** boundary collision detector and returns **DSU** conflict clusters.
* **`POST /harmonize`** — Runs the geometric registration engine, leveraging the **KD-Tree** for fast GNSS control-point matching.

---

## 🚀 Running the Full Stack

### 1. Start Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Start Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
Web Application: [http://localhost:5173](http://localhost:5173)

---

## 👥 Guardrails & Ethics
* **Decision Support, Not Replacement:** The system assists land administrators; it never unilaterally alters legal title.
* **Preservation of Raw Evidence:** Original historical maps and modern drone rasters are preserved in their native CRS and coordinate systems.
* **Auditable Provenance:** Every algorithmic decision, residual score, and administrative review is cryptographically hashed and logged.
