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
        residual_map = {str(r.get("parcel_id", "")).replace("parcel-", ""): r for r in residuals}
        cad_centroids = []
        for i, cad in enumerate(cad_features):
            pid = str(cad.get("properties", {}).get("parcel_id", cad.get("properties", {}).get("id", f"{101 + i}"))).replace("parcel-", "")
            nid = f"parcel-{pid}"
            res = residual_map.get(pid, {})
            c = _centroid(cad.get("geometry", {}))
            cad_centroids.append((nid, c))
            nodes.append({
                "id": nid,
                "label": f"Parcel {pid}",
                "type": "cadastral",
                "type_label": "Cadastral Parcel",
                "source_type": "cadastral",
                "source": "Cadastral Map (1960)",
                "residual_m": res.get("magnitude_m") or res.get("residual_m"),
                "status": res.get("state", "Auto Accepted"),
                "dispute_type": res.get("dispute_type", "None"),
            })
            node_ids.add(nid)

        # 2. Drone Footprint Nodes (AI Boundary)
        for j, drone in enumerate(drone_features[:len(cad_features)]):
            bid = str(drone.get("properties", {}).get("id", drone.get("properties", {}).get("building_id", f"{101 + j}"))).replace("bldg-", "").replace("building-", "")
            nid = f"bldg-{bid}"
            nodes.append({
                "id": nid,
                "label": f"AI Boundary {bid}",
                "type": "drone",
                "type_label": "AI Boundary",
                "source_type": "drone",
                "source": "Drone Footprint (2024)",
            })
            node_ids.add(nid)

            # Link: matches (AI -> Cadastral)
            if j < len(cad_centroids):
                cad_nid = cad_centroids[j][0]
                if cad_nid in node_ids:
                    links.append({
                        "source": cad_nid,
                        "target": nid,
                        "relationship": "matches",
                        "relation": "matches",
                        "type": "matches",
                        "confidence": 0.88,
                    })

        # 3. GNSS Points
        for g_idx, gp in enumerate(gnss_points[:25]):
            gid = str(gp.get("point_id", gp.get("id", f"{g_idx + 1}")))
            nid = f"gnss-{gid}"
            nodes.append({
                "id": nid,
                "label": f"GNSS Point {gid}",
                "type": "gnss",
                "type_label": "GNSS Point",
                "source_type": "gnss",
                "source": "GNSS RTK Control (2024)",
                "accuracy_m": gp.get("horizontal_accuracy_m", 0.05),
            })
            node_ids.add(nid)

            # Link: supports (GNSS -> closest Cadastral Parcel)
            try:
                gx = float(gp.get("lon") or gp.get("longitude") or gp.get("x") or 0)
                gy = float(gp.get("lat") or gp.get("latitude") or gp.get("y") or 0)
            except Exception:
                gx, gy = 0.0, 0.0
            if cad_centroids and (gx != 0 or gy != 0):
                best_pid, best_dist = None, float("inf")
                for cnid, cpos in cad_centroids:
                    d = (cpos[0] - gx)**2 + (cpos[1] - gy)**2
                    if d < best_dist:
                        best_dist = d
                        best_pid = cnid
                if best_pid:
                    links.append({
                        "source": nid,
                        "target": best_pid,
                        "relationship": "supports",
                        "relation": "supports",
                        "type": "supports",
                        "confidence": 0.95,
                    })

        # 4. Municipal Features
        for m_idx, mf in enumerate(municipal_features[:30]):
            mid = str(mf.get("properties", {}).get("id", f"road_{m_idx + 1}"))
            nid = f"muni-{mid}"
            nodes.append({
                "id": nid,
                "label": f"Municipal Feature {mid}",
                "type": "municipal",
                "type_label": "Municipal Feature",
                "source_type": "municipal",
                "source": "Municipal GIS (2023)",
            })
            node_ids.add(nid)

            # Link: intersects (Road -> parcel)
            if cad_centroids and m_idx < len(cad_centroids):
                target_cad = cad_centroids[m_idx % len(cad_centroids)][0]
                links.append({
                    "source": nid,
                    "target": target_cad,
                    "relationship": "intersects",
                    "relation": "intersects",
                    "type": "intersects",
                })

        # 5. Adjacent To links between neighbouring cadastral parcels
        for i in range(min(len(cad_centroids), 60)):
            for j in range(i + 1, min(len(cad_centroids), 60)):
                c1 = cad_centroids[i][1]
                c2 = cad_centroids[j][1]
                if abs(c1[0] - c2[0]) < 0.0008 and abs(c1[1] - c2[1]) < 0.0008:
                    links.append({
                        "source": cad_centroids[i][0],
                        "target": cad_centroids[j][0],
                        "relationship": "adjacent_to",
                        "relation": "adjacent_to",
                        "type": "adjacent_to",
                    })

        return {
            "nodes": nodes,
            "links": links,
            "total_nodes": len(nodes),
            "total_links": len(links),
        }
