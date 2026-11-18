"""
Spatial Quadtree Implementation for 2D Viewport Partitioning and Range Querying.
Enables sublinear indexing of 10,000+ parcels for smooth map panning and server-side spatial window queries.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Rect:
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def contains(self, point: tuple[float, float]) -> bool:
        x, y = point
        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y

    def intersects(self, other: Rect) -> bool:
        return not (
            other.max_x < self.min_x or
            other.min_x > self.max_x or
            other.max_y < self.min_y or
            other.min_y > self.max_y
        )


class QuadTree:
    """
    2D Hierarchical Spatial Quadtree.
    Subdivides into North-West, North-East, South-West, South-East quadrants upon reaching capacity.
    """

    def __init__(self, bounds: Rect, capacity: int = 16, max_depth: int = 12, depth: int = 0):
        self.bounds = bounds
        self.capacity = max(1, capacity)
        self.max_depth = max_depth
        self.depth = depth

        self.points: list[tuple[tuple[float, float], Any]] = []
        self.divided = False

        self.nw: Optional[QuadTree] = None
        self.ne: Optional[QuadTree] = None
        self.sw: Optional[QuadTree] = None
        self.se: Optional[QuadTree] = None

    def _subdivide(self) -> None:
        bx, by = (self.bounds.min_x + self.bounds.max_x) / 2.0, (self.bounds.min_y + self.bounds.max_y) / 2.0
        d = self.depth + 1
        cap = self.capacity
        md = self.max_depth

        self.nw = QuadTree(Rect(self.bounds.min_x, by, bx, self.bounds.max_y), cap, md, d)
        self.ne = QuadTree(Rect(bx, by, self.bounds.max_x, self.bounds.max_y), cap, md, d)
        self.sw = QuadTree(Rect(self.bounds.min_x, self.bounds.min_y, bx, by), cap, md, d)
        self.se = QuadTree(Rect(bx, self.bounds.min_y, self.bounds.max_x, by), cap, md, d)
        self.divided = True

        # Re-distribute existing points into quadrants
        old_points = self.points
        self.points = []
        for pt, payload in old_points:
            self.insert(pt, payload)

    def insert(self, point: tuple[float, float], payload: Any) -> bool:
        """Insert a 2D point with arbitrary payload into the Quadtree."""
        if not self.bounds.contains(point):
            return False

        if not self.divided:
            if len(self.points) < self.capacity or self.depth >= self.max_depth:
                self.points.append((point, payload))
                return True
            self._subdivide()

        # Delegate insertion to quadrants
        assert self.nw and self.ne and self.sw and self.se
        if self.nw.insert(point, payload):
            return True
        if self.ne.insert(point, payload):
            return True
        if self.sw.insert(point, payload):
            return True
        if self.se.insert(point, payload):
            return True

        return False

    def query(self, search_rect: Rect) -> list[Any]:
        """Returns all payloads whose points lie within the search_rect bounding box."""
        found: list[Any] = []

        def _search(node: QuadTree):
            if not node.bounds.intersects(search_rect):
                return

            if not node.divided:
                for pt, payload in node.points:
                    if search_rect.contains(pt):
                        found.append(payload)
            else:
                assert node.nw and node.ne and node.sw and node.se
                _search(node.nw)
                _search(node.ne)
                _search(node.sw)
                _search(node.se)

        _search(self)
        return found

    def stats(self) -> dict[str, Any]:
        """Returns structural profiling statistics for the Quadtree."""
        total_points = 0
        nodes_count = 0
        max_seen_depth = self.depth

        def _walk(node: QuadTree):
            nonlocal total_points, nodes_count, max_seen_depth
            nodes_count += 1
            max_seen_depth = max(max_seen_depth, node.depth)
            if not node.divided:
                total_points += len(node.points)
            else:
                assert node.nw and node.ne and node.sw and node.se
                _walk(node.nw)
                _walk(node.ne)
                _walk(node.sw)
                _walk(node.se)

        _walk(self)
        return {
            "total_points": total_points,
            "tree_nodes": nodes_count,
            "max_depth": max_seen_depth,
            "capacity_per_node": self.capacity,
        }
