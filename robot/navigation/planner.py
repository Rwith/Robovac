"""Path planning on the occupancy grid.

Two pieces:
  * a_star()         shortest path between two cells, avoiding obstacles.
  * coverage_path()  boustrophedon (back-and-forth) sweep that covers all free
                     cells of a region — the actual "vacuum the room" pattern.

Grids here are 2D numpy arrays where 0 = free, 1 = obstacle/unknown.
"""

from __future__ import annotations

import heapq

import numpy as np

Cell = tuple[int, int]


def a_star(grid: np.ndarray, start: Cell, goal: Cell) -> list[Cell]:
    """4-connected A* on a binary grid. Returns [] if no path."""
    h, w = grid.shape

    def neighbors(c: Cell):
        r, col = c
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, col + dc
            if 0 <= nr < h and 0 <= nc < w and grid[nr, nc] == 0:
                yield (nr, nc)

    def heuristic(c: Cell) -> int:
        return abs(c[0] - goal[0]) + abs(c[1] - goal[1])

    open_heap: list[tuple[int, Cell]] = [(0, start)]
    came_from: dict[Cell, Cell] = {}
    g = {start: 0}

    while open_heap:
        _, cur = heapq.heappop(open_heap)
        if cur == goal:
            path = [cur]
            while cur in came_from:
                cur = came_from[cur]
                path.append(cur)
            return path[::-1]
        for nxt in neighbors(cur):
            ng = g[cur] + 1
            if ng < g.get(nxt, 1 << 30):
                g[nxt] = ng
                came_from[nxt] = cur
                heapq.heappush(open_heap, (ng + heuristic(nxt), nxt))
    return []


def coverage_path(grid: np.ndarray, step: int = 1) -> list[Cell]:
    """Boustrophedon sweep over all free cells. Rows alternate direction."""
    h, w = grid.shape
    path: list[Cell] = []
    for r in range(0, h, step):
        cols = range(0, w, step) if (r // step) % 2 == 0 else range(w - 1, -1, -step)
        for c in cols:
            if grid[r, c] == 0:
                path.append((r, c))
    return path
