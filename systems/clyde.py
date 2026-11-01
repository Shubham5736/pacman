
"""Clyde: The orange ghost who chases Pac-Man but retreats when close."""

from systems.ghost import Ghost
from systems.maze import ROWS


class Clyde(Ghost):
    def __init__(self, spawn, speed=95.0):
        super().__init__(
            spawn=spawn,
            color=(255, 165, 0),
            speed=speed,
            name="Clyde",
        )

        self.scatter_target = (ROWS - 1, 0)
        self.chase_distance = 8
        self.exiting_house = True

    def choose_direction(self, maze, target):

        # Scatter mode: return to the bottom-left corner.
        if self.mode == "scatter":
            self.target = self.scatter_target
            return super().choose_direction(maze, self.scatter_target)

        pacman_row, pacman_col = target

        # Calculate squared Euclidean distance.
        row_distance = self.row - pacman_row
        col_distance = self.col - pacman_col

        distance_squared = (
            row_distance ** 2 + col_distance ** 2
        )

        # Chase when far away; retreat when close.
        if distance_squared > self.chase_distance ** 2:
            self.target = target
        else:
            self.target = self.scatter_target

        return super().choose_direction(maze, self.target)
