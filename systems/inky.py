
"""Inky: The cyan ghost whose target depends on Pac-Man and Blinky."""

from systems.ghost import Ghost
from systems.maze import ROWS


class Inky(Ghost):
    def __init__(self, spawn, speed=95.0):
        super().__init__(
            spawn=spawn,
            color=(0, 255, 255),
            speed=speed,
            name="Inky",
        )

        self.pacman_direction = (0, 1)
        self.blinky = None
        self.exiting_house = True

    def choose_direction(self, maze, target):
        # Use the normal targeting behaviour during Scatter mode.
        if self.mode == "scatter":
            return super().choose_direction(maze, target)

        # Fall back to direct targeting if Blinky is unavailable.
        if self.blinky is None:
            return super().choose_direction(maze, target)

        pacman_row, pacman_col = target
        dr, dc = self.pacman_direction

        # Find a pivot two tiles ahead of Pac-Man.
        # Coordinates are intentionally not clamped or wrapped.
        pivot_row = pacman_row + 2 * dr
        pivot_col = pacman_col + 2 * dc

        # Calculate the vector from Blinky to the pivot.
        blinky_row = self.blinky.row
        blinky_col = self.blinky.col

        # Extend that vector by the same distance beyond the pivot.
        target_row = 2 * pivot_row - blinky_row
        target_col = 2 * pivot_col - blinky_col

        self.target = (target_row, target_col)

        return super().choose_direction(maze, self.target)
