"""
Topological Validation & Area-Preserving Geometry Repair Service.
Provides:
  - Shapely make_valid repair with area-conservation tracking
  - Bentley-Ottmann Sweep-Line boundary intersection detection
  - DSU Connected Conflict Zone clustering
  - Returns both original and repaired geometry coordinates
"""

from __future__ import annotations
from typing import Any, Optional
from shapely.geometry import shape, mapping, Polygon, MultiPolygon
from shapely.validation import explain_validity
from ..dsa.sweep_line import sweep_intersections
from ..dsa.disjoint_set import conflict_zones


class TopologyService:
    @staticmethod
    def validate_and_repair_parcels(
        harmonized_features: list[dict[str, Any]],
        area_delta_threshold_pct: float = 2.0,
    ) -> dict[str, Any]:
        """
        Validates polygon geometry rings.
        Performs make_valid repairs while tracking area preservation.
        Runs sweep_intersections to catch boundary collisions and DSU to cluster dispute zones.
        """
        results = []
        n_valid = 0
        n_auto_repaired = 0
        n_manual_required = 0

        for i, feat in enumerate(harmonized_features):
            pid = str(feat.get("properties", {}).get("parcel_id", f"P{101 + i}"))
            geom = feat.get("geometry")

            if not geom or not geom.get("coordinates"):
                results.append({
                    "parcel_id": pid,
                    "status": "FAIL",
                    "validity": "Empty or missing geometry",
                    "area_delta_pct": 0.0,
                    "auto_repaired": False,
                    "requires_officer_approval": True,
                    "original_coordinates": [],
                    "repaired_coordinates": [],
                })
                n_manual_required += 1
                continue

            orig_coords = geom.get("coordinates")
            poly_obj = None
            try:
                poly_obj = shape(geom)
            except Exception as e:
                poly_obj = None

            if poly_obj is None:
                results.append({
                    "parcel_id": pid,
                    "status": "FAIL",
                    "validity": "Unparseable GeoJSON geometry",
                    "area_delta_pct": 0.0,
                    "auto_repaired": False,
                    "requires_officer_approval": True,
                    "original_coordinates": orig_coords,
                    "repaired_coordinates": orig_coords,
                })
                n_manual_required += 1
                continue

            is_valid = poly_obj.is_valid
            reason = "Valid Geometry (ST_IsValid)" if is_valid else explain_validity(poly_obj)
            auto_repaired = False
            repaired_coords = orig_coords
            area_delta_pct = 0.0
            requires_approval = False

            if is_valid:
                n_valid += 1
            else:
                # Attempt shapely make_valid repair
                try:
                    from shapely import make_valid
                    repaired = make_valid(poly_obj)
                    if repaired.is_valid and not repaired.is_empty:
                        orig_area = poly_obj.area
                        rep_area = repaired.area
                        delta = abs(rep_area - orig_area)
                        area_delta_pct = round((delta / orig_area) * 100.0, 2) if orig_area > 0 else 0.0

                        auto_repaired = True
                        n_auto_repaired += 1
                        repaired_coords = mapping(repaired)["coordinates"]

                        if area_delta_pct > area_delta_threshold_pct:
                            requires_approval = True
                            reason = f"Repaired via make_valid, but area shifted by {area_delta_pct}% (Officer confirmation needed)"
                        else:
                            reason = f"Auto-repaired via make_valid (area delta: {area_delta_pct}%)"
                    else:
                        n_manual_required += 1
                except Exception:
                    # Fallback to buffer(0)
                    try:
                        repaired = poly_obj.buffer(0)
                        if repaired.is_valid and not repaired.is_empty:
                            orig_area = poly_obj.area
                            rep_area = repaired.area
                            delta = abs(rep_area - orig_area)
                            area_delta_pct = round((delta / orig_area) * 100.0, 2) if orig_area > 0 else 0.0
                            auto_repaired = True
                            n_auto_repaired += 1
                            repaired_coords = mapping(repaired)["coordinates"]
                            requires_approval = area_delta_pct > area_delta_threshold_pct
                            reason = f"Repaired via buffer(0) (area delta: {area_delta_pct}%)"
                        else:
                            n_manual_required += 1
                    except Exception as err:
                        reason = f"Topology error: {err}"
                        n_manual_required += 1

            results.append({
                "parcel_id": pid,
                "status": "PASS" if is_valid else ("REPAIRED" if auto_repaired else "FAIL"),
                "validity": reason,
                "area_delta_pct": area_delta_pct,
                "auto_repaired": auto_repaired,
                "requires_officer_approval": requires_approval,
                "original_coordinates": orig_coords,
                "repaired_coordinates": repaired_coords,
            })

        # Run Sweep-Line boundary intersection detection
        sweep_res = sweep_intersections(harmonized_features)
        intersections = sweep_res.get("intersections", [])

        # Cluster connected conflict pairs using DSU
        conflict_pairs = [(item["parcel_a"], item["parcel_b"]) for item in intersections]
        zones = conflict_zones(harmonized_features, conflict_pairs)

        return {
            "parcel_results": results,
            "total_parcels": len(harmonized_features),
            "n_valid": n_valid,
            "n_auto_repaired": n_auto_repaired,
            "n_manual_required": n_manual_required,
            "sweep_line_intersections": intersections,
            "intersection_pairs_count": len(intersections),
            "shared_boundaries_count": sweep_res.get("shared_boundary_pairs", 0),
            "dsu_conflict_zones": zones,
            "conflict_zones_count": len(zones),
            "dsa_algorithms_used": ["Bentley-Ottmann Sweep-Line", "Self-Balancing AVL Tree", "Disjoint Set Union (DSU)"],
        }
