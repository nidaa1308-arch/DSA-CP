"""
Comprehensive Unit & Property-Based Test Suite for BHUMI-FUSE DSA Package.
Tests every algorithm against brute-force oracles and edge cases.
"""

import math
import random
import pytest
from app.dsa.kd_tree import KDTree
from app.dsa.avl_tree import AVLTree
from app.dsa.sweep_line import sweep_intersections, Segment, Point, compute_intersection
from app.dsa.disjoint_set import DisjointSet, conflict_zones
from app.dsa.astar import astar_search, plan_field_visit
from app.dsa.quadtree import QuadTree, Rect


# ── 1. KD-Tree Tests ─────────────────────────────────────────────────────────

def test_kdtree_against_brute_force():
    """Verify KDTree nearest, k-nearest, and radius query against brute-force oracle."""
    rng = random.Random(42)
    # Generate 150 random 2D points in metric space
    data = [((rng.uniform(0, 1000), rng.uniform(0, 1000)), f"pt_{i}") for i in range(150)]
    tree = KDTree(data)

    for _ in range(30):
        qx, qy = rng.uniform(0, 1000), rng.uniform(0, 1000)

        # 1. Test Nearest
        kd_nearest = tree.nearest((qx, qy))
        assert kd_nearest is not None

        bf_nearest_dist = float("inf")
        bf_nearest_pt = None
        for pt, payload in data:
            d = math.hypot(qx - pt[0], qy - pt[1])
            if d < bf_nearest_dist:
                bf_nearest_dist = d
                bf_nearest_pt = pt

        assert math.isclose(kd_nearest["distance"], bf_nearest_dist, rel_tol=1e-7)
        assert kd_nearest["point"] == bf_nearest_pt

        # 2. Test k-Nearest (k = 5)
        k = 5
        kd_knn = tree.k_nearest((qx, qy), k=k)
        assert len(kd_knn) == k

        bf_sorted = sorted(data, key=lambda item: math.hypot(qx - item[0][0], qy - item[0][1]))[:k]
        for i in range(k):
            expected_dist = math.hypot(qx - bf_sorted[i][0][0], qy - bf_sorted[i][0][1])
            assert math.isclose(kd_knn[i]["distance"], expected_dist, rel_tol=1e-7)

        # 3. Test Radius Query
        radius = 150.0
        kd_radius = tree.radius_query((qx, qy), radius_m=radius)
        bf_radius = [item for item in data if math.hypot(qx - item[0][0], qy - item[0][1]) <= radius]

        assert len(kd_radius) == len(bf_radius)
        kd_payloads = {r["payload"] for r in kd_radius}
        bf_payloads = {item[1] for item in bf_radius}
        assert kd_payloads == bf_payloads


def test_kdtree_edge_cases():
    empty_tree = KDTree([])
    assert empty_tree.nearest((0, 0)) is None
    assert empty_tree.k_nearest((0, 0), 3) == []
    assert empty_tree.radius_query((0, 0), 10) == []

    single_tree = KDTree([((10.0, 20.0), "solo")])
    res = single_tree.nearest((10.0, 25.0))
    assert res["payload"] == "solo"
    assert math.isclose(res["distance"], 5.0)


# ── 2. AVL Tree Tests ────────────────────────────────────────────────────────

def test_avl_tree_invariants_and_duplicate_keys():
    """Verify height balance invariant and deterministic duplicate key handling."""
    tree = AVLTree()
    rng = random.Random(1337)

    # Insert 100 elements with intentionally repeating keys
    keys = [rng.randint(1, 20) for _ in range(100)]
    for idx, k in enumerate(keys):
        tree.insert(float(k), f"val_{idx}")
        tree.assert_avl_invariants()

    assert len(tree) == 100
    inorder = tree.inorder()
    # Verify non-decreasing order
    for i in range(len(inorder) - 1):
        assert inorder[i][0] <= inorder[i + 1][0]


def test_avl_tree_true_deletion():
    """Verify O(log n) delete with rebalancing and height invariants."""
    tree = AVLTree()
    items = [(float(x), f"id_{x}") for x in range(1, 40)]
    for k, v in items:
        tree.insert(k, v)

    tree.assert_avl_invariants()
    assert len(tree) == 39

    # Delete 15 items in random order
    to_delete = random.sample(items, 15)
    for k, v in to_delete:
        deleted = tree.delete(k, v)
        assert deleted is True
        tree.assert_avl_invariants()

    assert len(tree) == 24
    # Ensure deleted items are no longer in inorder traversal
    remaining_keys_vals = set(tree.inorder())
    for k, v in to_delete:
        assert (k, v) not in remaining_keys_vals

    # Test predecessor and successor lookups
    inorder = tree.inorder()
    for i in range(len(inorder)):
        k, v = inorder[i]
        pred = tree.predecessor(k, v)
        succ = tree.successor(k, v)
        if i > 0:
            assert pred == inorder[i - 1][1]
        else:
            assert pred is None
        if i < len(inorder) - 1:
            assert succ == inorder[i + 1][1]
        else:
            assert succ is None


# ── 3. Sweep-Line Algorithm Tests ────────────────────────────────────────────

def test_sweep_line_detects_proper_crossings():
    """Two overlapping polygons crossing in an X shape."""
    features = [
        {
            "properties": {"parcel_id": "P1"},
            "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]}
        },
        {
            "properties": {"parcel_id": "P2"},
            "geometry": {"type": "Polygon", "coordinates": [[[5, -5], [15, -5], [15, 5], [5, 5], [5, -5]]]}
        }
    ]
    res = sweep_intersections(features)
    assert res["intersection_pairs"] == 1
    assert res["intersections"][0] == {"parcel_a": "P1", "parcel_b": "P2"}


def test_sweep_line_ignores_valid_shared_cadastral_boundaries():
    """
    CRITICAL SIH TEST:
    A 2x2 grid of 4 adjacent cadastral parcels that touch along common boundary edges.
    Must NOT report shared boundaries as conflicts!
    """
    grid_features = [
        # Parcel (0,0) -> [0, 10] x [0, 10]
        {
            "properties": {"parcel_id": "101"},
            "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]}
        },
        # Parcel (1,0) -> [10, 20] x [0, 10] (shares edge x=10 with 101)
        {
            "properties": {"parcel_id": "102"},
            "geometry": {"type": "Polygon", "coordinates": [[[10, 0], [20, 0], [20, 10], [10, 10], [10, 0]]]}
        },
        # Parcel (0,1) -> [0, 10] x [10, 20] (shares edge y=10 with 101)
        {
            "properties": {"parcel_id": "103"},
            "geometry": {"type": "Polygon", "coordinates": [[[0, 10], [10, 10], [10, 20], [0, 20], [0, 10]]]}
        },
        # Parcel (1,1) -> [10, 20] x [10, 20] (shares edge with 102 & 103)
        {
            "properties": {"parcel_id": "104"},
            "geometry": {"type": "Polygon", "coordinates": [[[10, 10], [20, 10], [20, 20], [10, 20], [10, 10]]]}
        },
    ]

    res = sweep_intersections(grid_features)
    # Zero conflicts should be reported!
    assert res["intersection_pairs"] == 0
    # Legitimate shared boundaries should be detected and cataloged
    assert res["shared_boundary_pairs"] >= 4


# ── 4. Disjoint Set Union Tests ──────────────────────────────────────────────

def test_dsu_union_by_rank_and_path_compression():
    dsu = DisjointSet(["A", "B", "C", "D", "E"])
    assert not dsu.connected("A", "B")

    dsu.union("A", "B")
    dsu.union("B", "C")
    assert dsu.connected("A", "C")
    assert not dsu.connected("A", "D")

    dsu.union("D", "E")
    assert dsu.connected("D", "E")
    assert len(dsu.groups()) == 2

    dsu.union("C", "E")
    assert dsu.connected("A", "E")
    assert len(dsu.groups()) == 1


def test_dsu_conflict_zones():
    parcels = [{"parcel_id": f"P{i}"} for i in range(1, 6)]
    # P1 overlaps P2; P2 overlaps P3 (Zone 1). P4 overlaps P5 (Zone 2)
    pairs = [("P1", "P2"), ("P2", "P3"), ("P4", "P5")]
    residuals = {"P1": 1.2, "P2": 3.8, "P3": 2.1, "P4": 0.8, "P5": 0.9}

    zones = conflict_zones(parcels, pairs, residuals_by_parcel=residuals)
    assert len(zones) == 2

    # Zone with P2 (max residual 3.8m) should be ranked first (CRITICAL)
    assert zones[0]["parcel_count"] == 3
    assert "P2" in zones[0]["parcels"]
    assert zones[0]["max_residual_m"] == 3.8
    assert zones[0]["severity"] == "CRITICAL"

    # Second zone should be NEEDS_REVIEW (residuals < 3.0m)
    assert zones[1]["parcel_count"] == 2
    assert zones[1]["severity"] == "NEEDS_REVIEW"


# ── 5. A* Search Algorithm Tests ─────────────────────────────────────────────

def test_astar_optimal_path_and_target_only_nodes():
    # Graph where "D" exists only as an edge target, not in top-level keys
    graph = {
        "Base": [("A", 10.0), ("B", 25.0)],
        "A": [("C", 15.0), ("Base", 10.0)],
        "B": [("D", 10.0), ("Base", 25.0)],
        "C": [("D", 5.0), ("A", 15.0)],
    }
    coords = {
        "Base": (0.0, 0.0),
        "A": (10.0, 0.0),
        "B": (0.0, 20.0),
        "C": (20.0, 5.0),
        "D": (25.0, 5.0),
    }

    # Shortest path: Base -> A (10) -> C (15) -> D (5) = 30.0
    res = astar_search(graph, coords, "Base", "D")
    assert res["found"] is True
    assert res["path"] == ["Base", "A", "C", "D"]
    assert math.isclose(res["cost"], 30.0)
    assert res["nodes_explored"] >= 3


def test_astar_field_visit_planning():
    graph = {
        "Survey_Office": [("P101", 100.0), ("P102", 300.0)],
        "P101": [("P102", 150.0), ("Survey_Office", 100.0)],
        "P102": [("P103", 200.0), ("P101", 150.0)],
        "P103": [("P102", 200.0)],
    }
    coords = {
        "Survey_Office": (0, 0),
        "P101": (100, 0),
        "P102": (200, 50),
        "P103": (350, 100),
    }

    plan = plan_field_visit(graph, coords, "Survey_Office", ["P101", "P103"])
    assert plan["stops_count"] == 2
    assert plan["total_distance_m"] == 450.0  # Office -> P101 (100) + P101 -> P102 -> P103 (350)
    assert plan["full_route"] == ["Survey_Office", "P101", "P102", "P103"]


# ── 6. Spatial Quadtree Tests ────────────────────────────────────────────────

def test_quadtree_10k_parcels_against_brute_force():
    """Stress-test Quadtree with 10,000 parcels and test viewport window queries."""
    bounds = Rect(min_x=0.0, min_y=0.0, max_x=10000.0, max_y=10000.0)
    qtree = QuadTree(bounds=bounds, capacity=16, max_depth=10)
    rng = random.Random(999)

    points = []
    for i in range(10000):
        pt = (rng.uniform(0, 10000), rng.uniform(0, 10000))
        pid = f"parcel_{i}"
        points.append((pt, pid))
        qtree.insert(pt, pid)

    stats = qtree.stats()
    assert stats["total_points"] == 10000
    assert stats["tree_nodes"] > 50

    # Viewport window query
    viewport = Rect(min_x=2000.0, min_y=2000.0, max_x=3000.0, max_y=3000.0)
    qt_results = set(qtree.query(viewport))

    # Compare with brute force
    bf_results = {pid for pt, pid in points if viewport.contains(pt)}
    assert qt_results == bf_results
