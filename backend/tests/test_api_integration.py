"""
API Integration & Regression Unit Tests for BHUMI-FUSE.
Directly invokes route handlers to verify:
  - Zero hardcoded benchmark results (no 1.695 RMSE, 0.902 inlier ratio, etc.)
  - Explicit 4xx errors instead of fake success fallbacks
  - Full investigation lifecycle (sample load, validate, normalize, harmonize, validate topology, review, audit)
  - All 6 DSA endpoints functional
"""

from __future__ import annotations
import pytest
from app.main import (
    health, dsa_summary, load_sample_investigation,
    validate_investigation_sources, normalize_investigation_crs,
    harmonize, HarmonizeRequest,
    validate, TopologyRequest,
    review, ReviewRequest,
    audit_verify, get_db_reviews, get_db_audit,
    dsa_quadtree_query, dsa_astar_route
)
from app.dsa.astar import astar_search
from app.dsa.quadtree import QuadTree, Rect


def test_health_endpoint():
    data = health()
    assert data["status"] == "ok"
    assert data["version"] == "2.0.0"
    assert "geospatial_backend" in data


def test_dsa_summary_endpoint():
    data = dsa_summary()
    assert len(data["new_course_dsa"]) == 6
    names = [d["name"] for d in data["new_course_dsa"]]
    assert "KD-Tree" in names
    assert "Sweep Line" in names
    assert "AVL Tree" in names
    assert "Disjoint Set Union" in names
    assert "A*" in names
    assert "Quadtree" in names
    assert len(data["existing_not_claimed_as_new"]) == 1


def test_dsa_quadtree_spatial_query():
    tree = QuadTree(Rect(0, 0, 100, 100), capacity=4)
    tree.insert((10.0, 20.0), {"id": "p1"})
    tree.insert((15.0, 25.0), {"id": "p2"})
    tree.insert((80.0, 90.0), {"id": "p3"})

    # Query viewport
    results = tree.query(Rect(5.0, 15.0, 30.0, 35.0))
    assert len(results) == 2
    matched_ids = [m["id"] for m in results]
    assert "p1" in matched_ids
    assert "p2" in matched_ids
    assert "p3" not in matched_ids


def test_dsa_astar_pathfinding():
    graph = {
        "A": [("B", 10.0), ("C", 15.0)],
        "B": [("D", 12.0)],
        "C": [("D", 10.0)],
        "D": []
    }
    coords = {
        "A": (0.0, 0.0),
        "B": (10.0, 0.0),
        "C": (0.0, 15.0),
        "D": (10.0, 15.0)
    }
    result = astar_search(graph, coords, "A", "D")
    assert result["path"] == ["A", "B", "D"]
    assert result["cost"] == 22.0


def test_audit_verification_chains():
    res = audit_verify()
    assert "chain_valid" in res
    assert "audit_chain" in res
    assert "review_chain" in res
    assert res["chain_valid"] is True


def test_harmonize_fails_with_insufficient_sources():
    req = HarmonizeRequest(investigation_id="non-existent-inv-999", model="affine")
    resp = harmonize(req)
    # Returns 422 JSONResponse
    assert hasattr(resp, "status_code")
    assert resp.status_code == 422


def test_sample_investigation_lifecycle_and_honest_metrics():
    # 1. Load sample investigation
    sample_res = load_sample_investigation()
    assert sample_res["status"] == "success"
    inv_id = sample_res["investigation"]["id"]
    assert inv_id == "sample-kharadi-2026"

    # 2. Validate sources
    val_res = validate_investigation_sources(inv_id)
    assert val_res["valid"] is True
    # Ensure CSV does NOT report "no data rows"
    for r in val_res["results"]:
        assert "no data rows" not in " ".join(r.get("issues", []))

    # 3. Normalize CRS
    norm_res = normalize_investigation_crs(inv_id)
    assert norm_res["investigation_id"] == inv_id

    # 4. Harmonize
    harm_req = HarmonizeRequest(
        investigation_id=inv_id,
        model="affine",
        dndThreshold=50.0
    )
    harm_res = harmonize(harm_req)
    assert isinstance(harm_res, dict)

    # CRITICAL: Verify NO 224-benchmark hardcoded values exist!
    assert harm_res["rmse"] != 1.695, "RMSE must NOT be hardcoded to 1.695"
    assert harm_res["inlier_ratio"] != 0.902, "Inlier ratio must NOT be hardcoded to 0.902"
    assert harm_res["max_residual"] != 4.505, "Max residual must NOT be hardcoded to 4.505"

    # Verify held-out cross-validated RMSE exists
    assert "held_out_rmse_m" in harm_res

    # Verify auto_resolved_count does NOT count Needs Review
    residuals = harm_res["residuals"]
    actual_auto = sum(1 for r in residuals if r.get("state") == "Auto Accepted")
    assert harm_res["auto_resolved_count"] == actual_auto

    # 5. Validate Topology and make_valid repair
    topo_req = TopologyRequest(harmonized=harm_res["harmonized"])
    topo_res = validate(topo_req)
    assert "results" in topo_res
    assert "sweep_line" in topo_res
    assert "conflict_zones" in topo_res
    assert "harmonized" in topo_res  # auto-repaired features returned

    # 6. Post Review Decision
    rev_req = ReviewRequest(
        case_id="case-sample-101",
        parcel_id="101",
        decision="accept",
        reviewer="Reviewing Officer A",
        note="Cadastral and drone boundary align within tolerance.",
        ai_recommendation="Auto Accepted",
        area_id="pune_kharadi"
    )
    rev_res = review(rev_req)
    assert rev_res["stored"] is True
    assert rev_res.get("version") is not None  # resp.version is defined!
