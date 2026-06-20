"""Path-planning tests — pure logic, no hardware needed."""

import numpy as np

from robot.navigation.planner import a_star, coverage_path


def test_a_star_straight_line():
    grid = np.zeros((5, 5), dtype=int)
    path = a_star(grid, (0, 0), (0, 4))
    assert path[0] == (0, 0)
    assert path[-1] == (0, 4)
    assert len(path) == 5


def test_a_star_routes_around_wall():
    grid = np.zeros((5, 5), dtype=int)
    grid[1:4, 2] = 1  # vertical wall with a gap at row 0 and row 4
    path = a_star(grid, (2, 0), (2, 4))
    assert path, "expected a path around the wall"
    assert all(grid[r, c] == 0 for r, c in path)


def test_a_star_no_path():
    grid = np.zeros((5, 5), dtype=int)
    grid[:, 2] = 1  # full wall, no gap
    assert a_star(grid, (0, 0), (0, 4)) == []


def test_coverage_visits_only_free_cells():
    grid = np.zeros((4, 4), dtype=int)
    grid[1, 1] = 1
    cells = coverage_path(grid)
    assert (1, 1) not in cells
    assert len(cells) == 15  # 16 cells minus the one obstacle


def test_coverage_rows_alternate_direction():
    grid = np.zeros((2, 3), dtype=int)
    cells = coverage_path(grid)
    # row 0 left->right, row 1 right->left
    assert cells[:3] == [(0, 0), (0, 1), (0, 2)]
    assert cells[3:] == [(1, 2), (1, 1), (1, 0)]
