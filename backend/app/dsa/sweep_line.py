"""
Bentley-Ottmann Style Sweep-Line Algorithm for Polygon Boundary Intersections.
Uses a balanced AVL Tree as the active sweep-line status structure and an event min-heap.
Distinguishes between:
  1. Proper Interior Crossings (Topological Collisions)
  2. Collinear Overlaps (Encroachments)
  3. Legitimate Shared Boundaries / Corner Touching (Valid Cadastral Adjacency)
"""

from __future__ import annotations
import heapq
import math
from dataclasses import dataclass, field
from typing import Any, Optional
from .avl_tree import AVLTree


EPSILON = 1e-9


@dataclass(order=True)
class Point:
    x: float
    y: float

    def __iter__(self):
        yield self.x
        yield self.y

    def dist_sq(self, o: Point) -> float:
        return (self.x - o.x) ** 2 + (self.y - o.y) ** 2


@dataclass
class Segment:
    id: int
    p1: Point
    p2: Point
    parcel_id: str
    edge_index: int

    @property
    def left(self) -> Point:
        if self.p1.x < self.p2.x - EPSILON:
            return self.p1
        elif self.p2.x < self.p1.x - EPSILON:
            return self.p2
        else:
            return self.p1 if self.p1.y <= self.p2.y else self.p2

    @property
    def right(self) -> Point:
        return self.p2 if self.left is self.p1 else self.p1

    @property
    def is_vertical(self) -> bool:
        return abs(self.p1.x - self.p2.x) < EPSILON

    def y_at(self, x: float) -> float:
        """Compute the y-coordinate along this segment at sweep position x."""
        if self.is_vertical:
            return min(self.p1.y, self.p2.y)
        dx = self.right.x - self.left.x
        if abs(dx) < EPSILON:
            return self.left.y
        t = (x - self.left.x) / dx
        # Clamp t to [0, 1] for numerical safety
        t = max(0.0, min(1.0, t))
        return self.left.y + t * (self.right.y - self.left.y)


def _orient(a: Point, b: Point, c: Point) -> float:
    """2D Cross product (b - a) x (c - a). Positive = CCW, Negative = CW, 0 = Collinear."""
    return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)


def _on_segment(p: Point, q: Point, r: Point) -> bool:
    """Check if point q lies on segment pr given p, q, r are collinear."""
    return (
        min(p.x, r.x) - EPSILON <= q.x <= max(p.x, r.x) + EPSILON and
        min(p.y, r.y) - EPSILON <= q.y <= max(p.y, r.y) + EPSILON
    )


def compute_intersection(s1: Segment, s2: Segment) -> Optional[tuple[str, Optional[Point]]]:
    """
    Evaluates geometric interaction between two segments.
    Returns:
      - None if no intersection
      - ('proper', Point) if segments cross at an interior point
      - ('shared_boundary', None) if segments are identical or shared adjacent cadastral edges
      - ('overlap', None) if segments partially overlap collinearly
      - ('touch', Point) if segments only touch at an endpoint
    """
    if s1.parcel_id == s2.parcel_id:
        return None  # Ignore internal edges of same parcel

    p1, q1 = s1.left, s1.right
    p2, q2 = s2.left, s2.right

    # Check for identical / shared boundary between adjacent parcels
    if (p1.dist_sq(p2) < EPSILON and q1.dist_sq(q2) < EPSILON) or \
       (p1.dist_sq(q2) < EPSILON and q1.dist_sq(p2) < EPSILON):
        return ("shared_boundary", None)

    # Check endpoint touches
    is_touch = (
        p1.dist_sq(p2) < EPSILON or p1.dist_sq(q2) < EPSILON or
        q1.dist_sq(p2) < EPSILON or q1.dist_sq(q2) < EPSILON
    )

    o1 = _orient(p1, q1, p2)
    o2 = _orient(p1, q1, q2)
    o3 = _orient(p2, q2, p1)
    o4 = _orient(p2, q2, q1)

    # General crossing case
    if ((o1 > EPSILON and o2 < -EPSILON) or (o1 < -EPSILON and o2 > EPSILON)) and \
       ((o3 > EPSILON and o4 < -EPSILON) or (o3 < -EPSILON and o4 > EPSILON)):
        # Compute exact line-line intersection point
        d = (q1.x - p1.x) * (q2.y - p2.y) - (q1.y - p1.y) * (q2.x - p2.x)
        if abs(d) < EPSILON:
            return None
        t = ((p2.x - p1.x) * (q2.y - p2.y) - (p2.y - p1.y) * (q2.x - p2.x)) / d
        ix = p1.x + t * (q1.x - p1.x)
        iy = p1.y + t * (q1.y - p1.y)
        return ("proper", Point(ix, iy))

    # Collinear overlap case
    if abs(o1) < EPSILON and abs(o2) < EPSILON and abs(o3) < EPSILON and abs(o4) < EPSILON:
        # Collinear: check if their bounding intervals overlap
        overlap_x = max(min(p1.x, q1.x), min(p2.x, q2.x)) <= min(max(p1.x, q1.x), max(p2.x, q2.x)) - EPSILON
        overlap_y = max(min(p1.y, q1.y), min(p2.y, q2.y)) <= min(max(p1.y, q1.y), max(p2.y, q2.y)) - EPSILON
        if overlap_x or overlap_y:
            return ("overlap", None)

    # Endpoint touching
    if is_touch:
        return ("touch", None)

    return None


@dataclass(order=True)
class Event:
    x: float
    event_type: int  # 0: intersection, 1: left (start), 2: right (end)
    y: float
    segment_primary: Any = field(compare=False)
    segment_secondary: Optional[Any] = field(default=None, compare=False)


def polygon_segments(features: list[dict[str, Any]]) -> list[Segment]:
    """Extract validated Segment objects from a list of GeoJSON polygon features."""
    segments: list[Segment] = []
    seg_id = 0

    for i, feat in enumerate(features):
        pid = str(feat.get("properties", {}).get("parcel_id", f"p_{i}"))
        geom = feat.get("geometry") or {}
        gtype = geom.get("type", "")
        coords = geom.get("coordinates") or []
        if not coords:
            continue

        rings = []
        if gtype == "Polygon":
            rings = [coords[0]] if coords and isinstance(coords[0], list) else []
        elif gtype == "MultiPolygon":
            for poly in coords:
                if poly and isinstance(poly, list):
                    rings.append(poly[0])

        for ring in rings:
            if not ring or len(ring) < 3:
                continue
            n = len(ring)
            # Iterate through boundary edges
            for j in range(n - 1):
                pt_a = Point(float(ring[j][0]), float(ring[j][1]))
                pt_b = Point(float(ring[j + 1][0]), float(ring[j + 1][1]))
                if pt_a.dist_sq(pt_b) > 1e-14:  # Skip zero-length duplicate vertices
                    segments.append(Segment(
                        id=seg_id,
                        p1=pt_a,
                        p2=pt_b,
                        parcel_id=pid,
                        edge_index=j
                    ))
                    seg_id += 1

    return segments


def sweep_intersections(features: list[dict[str, Any]]) -> dict[str, Any]:
    """
    True Bentley-Ottmann style event sweep over polygon boundaries.
    Maintains an active-status AVL Tree with dynamic coordinate evaluation at x.
    """
    segments = polygon_segments(features)
    event_queue: list[Event] = []

    # Initialize event queue with segment start and end endpoints
    for seg in segments:
        heapq.heappush(event_queue, Event(x=seg.left.x, event_type=1, y=seg.left.y, segment_primary=seg))
        heapq.heappush(event_queue, Event(x=seg.right.x, event_type=2, y=seg.right.y, segment_primary=seg))

    current_x = -float("inf")

    # Comparator for AVL status tree ordering segments vertically at current_x
    def seg_comparator(k1: float, s1: Any, k2: float, s2: Any) -> int:
        y1 = s1.y_at(current_x) if isinstance(s1, Segment) else k1
        y2 = s2.y_at(current_x) if isinstance(s2, Segment) else k2
        if abs(y1 - y2) > 1e-9:
            return -1 if y1 < y2 else 1
        # Secondary order by segment slope to handle coincident vertices
        dx1 = s1.right.x - s1.left.x
        dx2 = s2.right.x - s2.left.x
        slope1 = (s1.right.y - s1.left.y) / dx1 if abs(dx1) > 1e-9 else float("inf")
        slope2 = (s2.right.y - s2.left.y) / dx2 if abs(dx2) > 1e-9 else float("inf")
        if abs(slope1 - slope2) > 1e-9:
            return -1 if slope1 < slope2 else 1
        # Final tie breaker by segment unique ID
        return -1 if s1.id < s2.id else (1 if s1.id > s2.id else 0)

    status_tree = AVLTree(key_comparator=seg_comparator)
    conflicts: set[tuple[str, str]] = set()
    shared_boundaries: set[tuple[str, str]] = set()
    tested_pairs: set[tuple[int, int]] = set()
    checks_count = 0

    def check_interaction(s1: Segment, s2: Segment):
        nonlocal checks_count
        if s1 is None or s2 is None or s1.id == s2.id:
            return
        pair_key = (min(s1.id, s2.id), max(s1.id, s2.id))
        if pair_key in tested_pairs:
            return
        tested_pairs.add(pair_key)
        checks_count += 1

        res = compute_intersection(s1, s2)
        if res is not None:
            itype, pt = res
            parcel_pair = tuple(sorted((s1.parcel_id, s2.parcel_id)))
            if itype in ("proper", "overlap"):
                conflicts.add(parcel_pair)
                # If crossing occurs to the right of current sweep position, push to event queue
                if pt and pt.x > current_x + EPSILON:
                    heapq.heappush(event_queue, Event(
                        x=pt.x,
                        event_type=0,
                        y=pt.y,
                        segment_primary=s1,
                        segment_secondary=s2
                    ))
            elif itype == "shared_boundary":
                shared_boundaries.add(parcel_pair)

    while event_queue:
        event = heapq.heappop(event_queue)
        current_x = event.x
        s = event.segment_primary

        if event.event_type == 1:
            # Segment start: Insert into active AVL status structure
            status_tree.insert(s.y_at(current_x), s)
            pred = status_tree.predecessor(s.y_at(current_x), s)
            succ = status_tree.successor(s.y_at(current_x), s)
            if pred:
                check_interaction(s, pred)
            if succ:
                check_interaction(s, succ)

        elif event.event_type == 2:
            # Segment end: Delete from active AVL status structure
            pred = status_tree.predecessor(s.y_at(current_x), s)
            succ = status_tree.successor(s.y_at(current_x), s)
            status_tree.delete(s.y_at(current_x), s)
            # Test adjacency between predecessor and successor segments
            if pred and succ:
                check_interaction(pred, succ)

        elif event.event_type == 0:
            # Intersection event: Swap status between two segments
            s1 = event.segment_primary
            s2 = event.segment_secondary
            if s1 and s2:
                pred = status_tree.predecessor(s1.y_at(current_x), s1)
                succ = status_tree.successor(s2.y_at(current_x), s2)
                if pred:
                    check_interaction(pred, s2)
                if succ:
                    check_interaction(s1, succ)

    return {
        "intersections": [{"parcel_a": a, "parcel_b": b} for a, b in sorted(conflicts)],
        "intersection_pairs": len(conflicts),
        "shared_boundaries": [{"parcel_a": a, "parcel_b": b} for a, b in sorted(shared_boundaries)],
        "shared_boundary_pairs": len(shared_boundaries),
        "segments_processed": len(segments),
        "pairwise_checks": checks_count,
        "algorithm": "Bentley-Ottmann Event Sweep",
        "active_structure": "Self-Balancing AVL Tree",
    }
