"""
Disjoint Set Union (Union-Find) with Iterative Path Compression and Union-by-Rank.
Clusters connected conflict pairs and computes comprehensive dispute zone statistics.
"""

from __future__ import annotations
from typing import Any, Iterable, Optional


class DisjointSet:
    """
    Disjoint Set Union (DSU) supporting O(alpha(n)) amortized operations.
    Uses iterative find with two-pass path compression to prevent recursion depth limits.
    """

    def __init__(self, elements: Iterable[str] = ()):
        self.parent: dict[str, str] = {}
        self.rank: dict[str, int] = {}
        for elem in elements:
            self.add(elem)

    def add(self, x: str) -> None:
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0

    def find(self, x: str) -> str:
        """Iterative two-pass find with path compression."""
        self.add(x)
        # Pass 1: Find root
        root = x
        while self.parent[root] != root:
            root = self.parent[root]

        # Pass 2: Compress path directly to root
        curr = x
        while curr != root:
            nxt = self.parent[curr]
            self.parent[curr] = root
            curr = nxt

        return root

    def union(self, x: str, y: str) -> bool:
        """Union elements x and y by rank. Returns True if sets were merged, False if already in same set."""
        root_x = self.find(x)
        root_y = self.find(y)

        if root_x == root_y:
            return False

        # Union by rank heuristic
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1

        return True

    def connected(self, x: str, y: str) -> bool:
        return self.find(x) == self.find(y)

    def groups(self) -> dict[str, list[str]]:
        """Returns dictionary mapping root representative to member elements."""
        clusters: dict[str, list[str]] = {}
        for elem in self.parent:
            r = self.find(elem)
            clusters.setdefault(r, []).append(elem)
        return clusters


def conflict_zones(
    parcels: list[dict[str, Any]],
    conflict_pairs: list[tuple[str, str]],
    residuals_by_parcel: Optional[dict[str, float]] = None,
) -> list[dict[str, Any]]:
    """
    Partition conflicting parcels into connected dispute clusters.
    Calculates genuine cluster statistics: parcel member count, mean residual, max residual.
    """
    residuals_by_parcel = residuals_by_parcel or {}
    all_pids = [str(p.get("parcel_id", "")) for p in parcels if p.get("parcel_id")]

    dsu = DisjointSet(all_pids)

    # Union all pairs flagged with topological collision or spatial encroachment
    for p1, p2 in conflict_pairs:
        dsu.union(str(p1), str(p2))

    clusters = dsu.groups()
    zones: list[dict[str, Any]] = []
    zone_idx = 1

    for root, members in clusters.items():
        # Only report multi-parcel connected conflict zones
        if len(members) >= 2:
            member_residuals = [residuals_by_parcel.get(m) for m in members if residuals_by_parcel.get(m) is not None]
            valid_res = [r for r in member_residuals if r is not None]

            mean_res = round(sum(valid_res) / len(valid_res), 3) if valid_res else None
            max_res = round(max(valid_res), 3) if valid_res else None

            zones.append({
                "zone_id": f"zone-{zone_idx}",
                "root_parcel": root,
                "parcels": sorted(members),
                "parcel_count": len(members),
                "mean_residual_m": mean_res,
                "max_residual_m": max_res,
                "severity": "CRITICAL" if (max_res and max_res >= 3.0) else "NEEDS_REVIEW",
            })
            zone_idx += 1

    # Sort zones by severity (highest maximum displacement first)
    zones.sort(key=lambda z: (z["max_residual_m"] or 0), reverse=True)
    return zones
