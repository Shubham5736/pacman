"""Blinky: The red ghost that directly chases Pac-Man."""

from systems.ghost import Ghost

class Blinky(Ghost):
    """Ghost whose target is Pac-Man's current tile"""

    def __init__(self, spawn, speed=95.0):
        super().__init__(
            spawn=spawn,
            color=(255,0,0),
            speed=speed,
            name="Blinky"
        )

    def choose_direction(self, maze, target):
        return super().choose_direction(maze, target)