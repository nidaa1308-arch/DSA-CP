"""
Global 1-to-1 Bipartite Correspondence Assignment Engine.
Matches Cadastral Parcels to Drone Building Footprints using:
  1. Centroid Distance (normalized by parcel radius)
  2. Containment Ratio (area of building inside parcel / total building area)
  3. Shape Similarity
Solves optimal global assignment using the Hungarian Algorithm (linear_sum_assignment)
to avoid greedy assignment conflicts.
"""

from __future__ import annotations
import math
from typing import Any, Optional
import numpy as np
from shapely.geometry import shape, Polygon


def _extract_shapely_poly(feat: dict[str, Any]) -> Optional[Polygon]:
    geom = feat.get("geometry")
    if not geom:
        return None
    try:
        s = shape(geom)
        if s.is_valid and not s.is_empty and s.geom_type in ("Polygon", "MultiPolygon"):
            return s
        repaired = s.buffer(0)
        return repaired if repaired.is_valid and not repaired.is_empty else None
    except Exception:
        return None


class CorrespondenceService:
    @staticmethod
    def match_parcels_to_footprints(
        cad_features: list[dict[str, Any]],
        drone_features: list[dict[str, Any]],
        search_radius_m: float = 120.0,
        ambiguity_cost_threshold: float = 0.65,
    ) -> list[dict[str, Any]]:
        """
        Global bipartite matching using the Hungarian Algorithm.
        Cost function:
          C = 0.50 * (distance / radius) + 0.35 * (1 - containment) + 0.15 * shape_diff
        """
        n_cad = len(cad_features)
        n_drone = len(drone_features)

        if n_cad == 0 or n_drone == 0:
            return []

        cad_polys = [_extract_shapely_poly(f) for f in cad_features]
        drone_polys = [_extract_shapely_poly(f) for f in drone_features]

        cad_centroids = [p.centroid if p else None for p in cad_polys]
        drone_centroids = [p.centroid if p else None for p in drone_polys]

        # Construct Cost Matrix (n_cad x n_drone)
        LARGE_COST = 1e6
        cost_matrix = np.full((n_cad, n_drone), LARGE_COST, dtype=float)

        for i in range(n_cad):
            p_cad = cad_polys[i]
            c_cad = cad_centroids[i]
            if not p_cad or not c_cad:
                continue

            for j in range(n_drone):
                p_drone = drone_polys[j]
                c_drone = drone_centroids[j]
                if not p_drone or not c_drone:
                    continue

                # Euclidean distance in projected coordinate space
                dist = c_cad.distance(c_drone)
                if dist > search_radius_m:
                    continue

                dist_term = min(1.0, dist / search_radius_m)

                # Containment term: how much of the building is inside the parcel
                try:
                    inter_area = p_cad.intersection(p_drone).area
                    containment = inter_area / p_drone.area if p_drone.area > 0 else 0.0
                except Exception:
                    containment = 0.0
                containment_term = max(0.0, min(1.0, 1.0 - containment))

                # Shape similarity term: perimeter-to-area aspect ratio
                cad_aspect = (p_cad.length ** 2) / (p_cad.area * 4 * math.pi) if p_cad.area > 0 else 1.0
                drone_aspect = (p_drone.length ** 2) / (p_drone.area * 4 * math.pi) if p_drone.area > 0 else 1.0
                shape_diff = min(1.0, abs(cad_aspect - drone_aspect) / max(cad_aspect, drone_aspect, 1.0))

                cost = 0.50 * dist_term + 0.35 * containment_term + 0.15 * shape_diff
                cost_matrix[i, j] = cost

        # Solve optimal 1-to-1 assignment via scipy or greedy fallback
        cad_ind = []
        drone_ind = []
        try:
            from scipy.optimize import linear_sum_assignment
            cad_ind, drone_ind = linear_sum_assignment(cost_matrix)
        except Exception:
            # Greedy bipartite fallback with conflict resolution
            used_drone = set()
            # Sort all possible pairings by cost
            candidates = []
            for i in range(n_cad):
                for j in range(n_drone):
                    if cost_matrix[i, j] < LARGE_COST:
                        candidates.append((cost_matrix[i, j], i, j))
            candidates.sort(key=lambda x: x[0])
            matched_cad = set()
            for cost, i, j in candidates:
                if i not in matched_cad and j not in used_drone:
                    matched_cad.add(i)
                    used_drone.add(j)
                    cad_ind.append(i)
                    drone_ind.append(j)

        # Build correspondence output
        results: list[dict[str, Any]] = []
        assigned_map = dict(zip(cad_ind, drone_ind))

        for i, cad_feat in enumerate(cad_features):
            cad_id = str(cad_feat.get("properties", {}).get("parcel_id", f"P{101 + i}"))
            j = assigned_map.get(i)

            if j is not None and cost_matrix[i, j] < LARGE_COST:
                cost = float(cost_matrix[i, j])
                drone_feat = drone_features[j]
                drone_id = str(drone_feat.get("properties", {}).get("id", f"B{101 + j}"))
                c_cad = cad_centroids[i]
                c_drone = drone_centroids[j]
                dist = c_cad.distance(c_drone) if c_cad and c_drone else 0.0

                is_ambiguous = cost > ambiguity_cost_threshold

                results.append({
                    "cad_idx": i,
                    "drone_idx": j,
                    "parcel_id": cad_id,
                    "building_id": drone_id,
                    "cost": round(cost, 4),
                    "confidence": round(max(0.1, 1.0 - cost), 3),
                    "centroid_dist_m": round(dist, 2),
                    "ambiguous_match": is_ambiguous,
                    "eligible_for_registration": not is_ambiguous,
                    "cad_centroid": (c_cad.x, c_cad.y) if c_cad else None,
                    "drone_centroid": (c_drone.x, c_drone.y) if c_drone else None,
                })
            else:
                # Unmatched parcel
                results.append({
                    "cad_idx": i,
                    "drone_idx": None,
                    "parcel_id": cad_id,
                    "building_id": None,
                    "cost": 1.0,
                    "confidence": 0.0,
                    "centroid_dist_m": None,
                    "ambiguous_match": True,
                    "eligible_for_registration": False,
                    "cad_centroid": None,
                    "drone_centroid": None,
                })

        return results
