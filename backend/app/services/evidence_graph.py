"""
Spatial Evidence Graph Service.
Constructs bipartite physical-to-legal spatial evidence networks for interactive cross-filtering.
"""

from __future__ import annotations
import math
from typing import Any


def _centroid(geom: dict) -> tuple[float, float]:
    coords = geom.get("coordinates", [])
    gtype = geom.get("type", "")
    if not coords:
        return 0.0, 0.0
    ring = coords[0] if (gtype in ("Polygon", "MultiPolygon") and isinstance(coords[0], list)) else coords
    valid_pts = [p for p in ring if isinstance(p, (list, tuple)) and len(p) >= 2]
    if not valid_pts:
        return 0.0, 0.0
    return sum(p[0] for p in valid_pts) / len(valid_pts), sum(p[1] for p in valid_pts) / len(valid_pts)


class EvidenceGraphService:
    @staticmethod
    def build_graph(
        cad_features: list[dict[str, Any]],
        drone_features: list[dict[str, Any]],
        gnss_points: list[dict[str, Any]],
        municipal_features: list[dict[str, Any]],
        residuals: list[dict[str, Any]],
    ) -> dict[str, Any]:
        nodes = []
        links = []
        node_ids = set()

        # 1. Cadastral Parcel Nodes
        residual_map = {str(r.get("parcel_id", "")): r for r in residuals}
        for i, cad in enumerate(cad_features):
            pid = str(cad.get("properties", {}).get("parcel_id", f"P{101 + i}"))
            nid = f"parcel-{pid}"
            res = residual_map.get(pid, {})
            nodes.append({
                "id": nid,
                "label": f"Parcel {pid}",
                "type": "cadastral",
                "type_label": "Cadastral Parcel",
                "source_type": "authoritative_cadastral",
                "residual_m": res.get("magnitude_m") or res.get("residual_m"),
                "status": res.get("status", "pending"),
            })
            node_ids.add(nid)

        # 2. Drone Footprint Nodes
        for j, drone in enumerate(drone_features[:len(cad_features)]):
            bid = str(drone.get("properties", {}).get("id", f"bldg-{101 + j}"))
            nid = f"bldg-{bid}"
            nodes.append({
                "id": nid,
                "label": f"Building {bid}",
                "type": "drone",
                "type_label": "Boundary Observation",
                "source_type": "physical_observation",
            })
            node_ids.add(nid)

            # Link to corresponding cadastral parcel
            if j < len(cad_features):
                cad_pid = str(cad_features[j].get("properties", {}).get("parcel_id", f"P{101 + j}"))
                cad_nid = f"parcel-{cad_pid}"
                if cad_nid in node_ids:
                    links.append({
                        "source": cad_nid,
                        "target": nid,
                        "relationship": "corresponds_to",
                        "relation": "corresponds_to",
                        "confidence": 0.85,
                    })

        # 3. GNSS Points
        for g_idx, gp in enumerate(gnss_points[:15]):
            gid = str(gp.get("point_id", f"gnss_{g_idx + 1}"))
            nid = f"gnss-{gid}"
            nodes.append({
                "id": nid,
                "label": f"GNSS {gid}",
                "type": "gnss",
                "type_label": "GNSS Control Point",
                "source_type": "ground_truth_control",
                "accuracy_m": gp.get("horizontal_accuracy_m", 0.05),
            })
            node_ids.add(nid)

        # 4. Municipal Features
        for m_idx, mf in enumerate(municipal_features[:20]):
            mid = str(mf.get("properties", {}).get("id", f"road_{m_idx + 1}"))
            nid = f"muni-{mid}"
            nodes.append({
                "id": nid,
                "label": f"Road {mid}",
                "type": "municipal",
                "type_label": "Municipal Feature",
                "source_type": "contextual_municipal",
            })
            node_ids.add(nid)

        return {
            "nodes": nodes,
            "links": links,
            "total_nodes": len(nodes),
            "total_links": len(links),
        }
