"""
Advanced Computational Geometry & Data Structures Layer for BHUMI-FUSE.
"""

from .kd_tree import KDTree, KDNode
from .avl_tree import AVLTree, AVLNode
from .sweep_line import sweep_intersections, compute_intersection, Segment, Point
from .disjoint_set import DisjointSet, conflict_zones
from .astar import astar_search, plan_field_visit
from .quadtree import QuadTree, Rect

__all__ = [
    "KDTree",
    "KDNode",
    "AVLTree",
    "AVLNode",
    "sweep_intersections",
    "compute_intersection",
    "Segment",
    "Point",
    "DisjointSet",
    "conflict_zones",
    "astar_search",
    "plan_field_visit",
    "QuadTree",
    "Rect",
]
