"""
A* Shortest Path Search Algorithm with Admissible Euclidean Distance Heuristic.
Supports field-verification routing over municipal street and adjacency graphs.
Handles nodes that appear only as edge targets and provides multi-stop field inspection planning.
"""

from __future__ import annotations
import heapq
import math
from typing import Any, Optional


def _euclidean_heuristic(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    """Admissible Euclidean distance: h(u, v) = sqrt((x1-x2)^2 + (y1-y2)^2)."""
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def astar_search(
    graph: dict[str, list[tuple[str, float]]],
    coords: dict[str, tuple[float, float]],
    start: str,
    goal: str,
) -> dict[str, Any]:
    """
    A* algorithm over a weighted graph with known geographic/metric coordinates.
    Returns:
      - 'found': bool
      - 'path': list of node IDs from start to goal
      - 'cost': total traversal path cost in graph units (metres)
      - 'nodes_explored': count of priority queue pop operations
    """
    start = str(start)
    goal = str(goal)

    # Collect all reachable nodes to handle target-only nodes gracefully
    all_nodes: set[str] = set(graph.keys())
    for neighbours in graph.values():
        for nbr, _ in neighbours:
            all_nodes.add(str(nbr))

    if start not in all_nodes or goal not in all_nodes:
        return {
            "found": False,
            "path": [],
            "cost": float("inf"),
            "nodes_explored": 0,
            "error": f"Start '{start}' or Goal '{goal}' not found in graph nodes.",
            "algorithm": "A*",
        }

    if start == goal:
        return {
            "found": True,
            "path": [start],
            "cost": 0.0,
            "nodes_explored": 0,
            "algorithm": "A*",
        }

    goal_coord = coords.get(goal)

    # Priority queue stores (f_score, tie_breaker, node_id)
    # f(n) = g(n) + h(n)
    pq: list[tuple[float, int, str]] = []
    tie_breaker = 0

    g_score: dict[str, float] = {start: 0.0}
    came_from: dict[str, str] = {}

    h_start = _euclidean_heuristic(coords[start], goal_coord) if (coords and start in coords and goal_coord) else 0.0
    heapq.heappush(pq, (h_start, tie_breaker, start))
    tie_breaker += 1

    nodes_explored = 0
    visited: set[str] = set()

    while pq:
        f, _, current = heapq.heappop(pq)
        nodes_explored += 1

        if current == goal:
            # Reconstruct optimal path
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return {
                "found": True,
                "path": path,
                "cost": round(g_score[goal], 2),
                "nodes_explored": nodes_explored,
                "algorithm": "A*",
                "heuristic": "Admissible Euclidean Distance",
            }

        if current in visited:
            continue
        visited.add(current)

        curr_g = g_score[current]
        # Inspect outbound edges
        for neighbor, weight in graph.get(current, []):
            neighbor = str(neighbor)
            tentative_g = curr_g + float(weight)

            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                h = _euclidean_heuristic(coords[neighbor], goal_coord) if (coords and neighbor in coords and goal_coord) else 0.0
                heapq.heappush(pq, (tentative_g + h, tie_breaker, neighbor))
                tie_breaker += 1

    return {
        "found": False,
        "path": [],
        "cost": float("inf"),
        "nodes_explored": nodes_explored,
        "error": "No connected path between start and goal.",
        "algorithm": "A*",
    }


def plan_field_visit(
    graph: dict[str, list[tuple[str, float]]],
    coords: dict[str, tuple[float, float]],
    depot_node: str,
    flagged_parcel_nodes: list[str],
) -> dict[str, Any]:
    """
    Officer Inspection Tour Planner:
    Connects a survey office depot node to multiple flagged dispute parcels using consecutive A* legs.
    """
    if not flagged_parcel_nodes:
        return {"legs": [], "total_distance_m": 0.0, "full_route": [depot_node]}

    full_route: list[str] = [depot_node]
    legs = []
    total_cost = 0.0
    curr = depot_node

    for target in flagged_parcel_nodes:
        result = astar_search(graph, coords, curr, target)
        if result["found"]:
            legs.append({
                "from": curr,
                "to": target,
                "distance_m": result["cost"],
                "path": result["path"],
            })
            total_cost += result["cost"]
            # Append path skipping duplicate junction
            full_route.extend(result["path"][1:])
            curr = target
        else:
            legs.append({
                "from": curr,
                "to": target,
                "distance_m": None,
                "path": [],
                "unreachable": True,
            })

    return {
        "total_distance_m": round(total_cost, 2),
        "stops_count": len(flagged_parcel_nodes),
        "legs": legs,
        "full_route": full_route,
    }
