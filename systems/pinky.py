
"""Pinky: the pink ghost that targets tiles ahead of Pac-Man."""

from systems.ghost import Ghost
from systems.maze import ROWS, COLS

class Pinky(Ghost):
    def __init__(self, spawn, speed=95.0):
        super().__init__(
            spawn=spawn,
            color=(255, 105, 180),
            speed=speed,
            name="Pinky",
        )
        self.pacman_direction = (0, 1)
        self.exiting_house = True

    def choose_direction(self, maze, target):

        if self.mode == "scatter":
            return super().choose_direction(maze, target)
        
        target_row, target_col = target
        dr, dc = self.pacman_direction

        
        ambush_target = (target_row + dr *4 , target_col + dc *4)

        self.target = ambush_target
        return super().choose_direction(maze, ambush_target)
