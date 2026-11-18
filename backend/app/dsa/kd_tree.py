"""
2D Spatial KD-Tree Implementation.
Provides balanced spatial partitioning, nearest-neighbour, k-nearest, and radius queries
in metric (metres) coordinate space.
"""

from __future__ import annotations
import heapq
import math
from dataclasses import dataclass
from typing import Any, Iterable, Optional


@dataclass
class KDNode:
    point: tuple[float, float]
    payload: Any
    axis: int
    left: Optional[KDNode] = None
    right: Optional[KDNode] = None


class KDTree:
    """
    2D Balanced KD-Tree for spatial coordinate queries.
    Complexity:
      - Build: O(n log n)
      - Nearest Neighbour: Average O(log n), Worst O(n)
      - k-NN: Average O(k log n)
      - Radius Search: O(log n + m) where m is number of points in radius
    """

    def __init__(self, points_with_payloads: Iterable[tuple[tuple[float, float], Any]]):
        items = list(points_with_payloads)
        self.size = len(items)
        self.root = self._build(items, depth=0)

    def _build(self, items: list[tuple[tuple[float, float], Any]], depth: int) -> Optional[KDNode]:
        if not items:
            return None

        axis = depth % 2
        # Sort and select median element for guaranteed tree balance
        items.sort(key=lambda item: item[0][axis])
        median_idx = len(items) // 2
        pt, payload = items[median_idx]

        node = KDNode(point=pt, payload=payload, axis=axis)
        node.left = self._build(items[:median_idx], depth + 1)
        node.right = self._build(items[median_idx + 1:], depth + 1)
        return node

    # ── Nearest Neighbour ────────────────────────────────────────────────────

    def nearest(self, query_point: tuple[float, float]) -> Optional[dict[str, Any]]:
        """
        Find the single nearest point to query_point.
        Returns dict with point, payload, distance (metres), and search diagnostics.
        """
        if not self.root:
            return None

        best_node: Optional[KDNode] = None
        best_dist_sq = float("inf")
        nodes_visited = 0

        def _search(node: Optional[KDNode]):
            nonlocal best_node, best_dist_sq, nodes_visited
            if node is None:
                return

            nodes_visited += 1
            qx, qy = query_point
            nx, ny = node.point
            d_sq = (qx - nx) ** 2 + (qy - ny) ** 2

            if d_sq < best_dist_sq:
                best_dist_sq = d_sq
                best_node = node

            axis = node.axis
            diff = query_point[axis] - node.point[axis]
            first = node.left if diff < 0 else node.right
            second = node.right if diff < 0 else node.left

            _search(first)
            # Branch-and-bound prune: only explore second branch if hypersphere crosses splitting plane
            if diff * diff < best_dist_sq:
                _search(second)

        _search(self.root)

        if not best_node:
            return None

        return {
            "point": best_node.point,
            "payload": best_node.payload,
            "distance": math.sqrt(best_dist_sq),
            "nodes_visited": nodes_visited,
            "tree_size": self.size,
        }

    # ── k-Nearest Neighbours ─────────────────────────────────────────────────

    def k_nearest(self, query_point: tuple[float, float], k: int) -> list[dict[str, Any]]:
        """
        Find top k closest points to query_point.
        Maintains a max-heap of capacity k storing (-dist_sq, node).
        """
        if not self.root or k <= 0:
            return []

        # Max-heap stores (-dist_sq, unique_id, node)
        heap: list[tuple[float, int, KDNode]] = []
        uid = 0

        def _search(node: Optional[KDNode]):
            nonlocal uid
            if node is None:
                return

            qx, qy = query_point
            nx, ny = node.point
            d_sq = (qx - nx) ** 2 + (qy - ny) ** 2

            if len(heap) < k:
                heapq.heappush(heap, (-d_sq, uid, node))
                uid += 1
            elif d_sq < -heap[0][0]:
                heapq.heapreplace(heap, (-d_sq, uid, node))
                uid += 1

            axis = node.axis
            diff = query_point[axis] - node.point[axis]
            first = node.left if diff < 0 else node.right
            second = node.right if diff < 0 else node.left

            _search(first)
            # Only visit other branch if current max distance exceeds distance to splitting plane
            max_d_sq = -heap[0][0] if len(heap) >= k else float("inf")
            if diff * diff < max_d_sq:
                _search(second)

        _search(self.root)

        # Sort results from closest to farthest
        results = []
        for neg_d_sq, _, n in sorted(heap, key=lambda x: -x[0]):
            results.append({
                "point": n.point,
                "payload": n.payload,
                "distance": math.sqrt(-neg_d_sq),
            })
        return results

    # ── Radius Query ─────────────────────────────────────────────────────────

    def radius_query(self, query_point: tuple[float, float], radius_m: float) -> list[dict[str, Any]]:
        """
        Find all points within radius_m of query_point.
        """
        if not self.root or radius_m < 0:
            return []

        radius_sq = radius_m * radius_m
        results: list[dict[str, Any]] = []

        def _search(node: Optional[KDNode]):
            if node is None:
                return

            qx, qy = query_point
            nx, ny = node.point
            d_sq = (qx - nx) ** 2 + (qy - ny) ** 2

            if d_sq <= radius_sq:
                results.append({
                    "point": node.point,
                    "payload": node.payload,
                    "distance": math.sqrt(d_sq),
                })

            axis = node.axis
            diff = query_point[axis] - node.point[axis]
            first = node.left if diff < 0 else node.right
            second = node.right if diff < 0 else node.left

            _search(first)
            if diff * diff <= radius_sq:
                _search(second)

        _search(self.root)
        results.sort(key=lambda r: r["distance"])
        return results
