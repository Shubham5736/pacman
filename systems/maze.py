
"""Maze generation, validation, and rendering for Pac-Man."""

import pygame

from config import BLUE, YELLOW

# Tile types
WALL = "#"
PELLET = "."
POWER_PELLET = "o"
GATE = "="
EMPTY = " "

# Maze dimensions
ROWS = 31
COLS = 28
TILE_SIZE = 20

# Rendering colors
BACKGROUND_COLOR = (0, 0, 0)
WALL_COLOR = (0, 100, 255)
PELLET_COLOR = (255, 255, 255)
POWER_COLOR = (255, 255, 255)
GATE_COLOR = (255, 160, 190)
PLAYER_COLOR = (255, 255, 0)
GHOST_COLOR = (255, 0, 120)

MAZE_LAYOUT = [
    "############################",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#o####.#####.##.#####.####o#",
    "#.####.#####.##.#####.####.#",
    "#............  ............#",
    "#.####.##.########.##.####.#",
    "#.####.##.########.##.####.#",
    "#......##....##....##......#",
    "######.##### ## #####.######",
    "     #.##### ## #####.#     ",
    "     #.##          ##.#     ",
    "     #.## ###==### ##.#     ",
    "######.## #      # ##.######",
    "      .   #      #   .      ",
    "######.## #      # ##.######",
    "     #.## ######## ##.#     ",
    "     #.##          ##.#     ",
    "     #.## ######## ##.#     ",
    "######.## ######## ##.######",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#.####.#####.##.#####.####.#",
    "#o..##................##..o#",
    "###.##.##.########.##.##.###",
    "###.##.##.########.##.##.###",
    "#......##....##....##......#",
    "#.##########.##.##########.#",
    "#.##########.##.##########.#",
    "#..........................#",
    "############################",
] 

class Maze:
    """Stores and draws the Pac-Man maze."""

    def __init__(self):
        self.grid = [list(row) for row in MAZE_LAYOUT]

        # Coordinates are (row, column).
        self.player_spawn = (23, 13)
        self.ghost_spawn = (14, 13)
        self.blinky_spawn = (11,13)
        self.pinky_spawn = (14,12)
        self.inky_spawn = (14,14)
        self.clyde_spawn = (14,15)
        self.validate()
        self.power_pellet_collected = False
        self.pellets_eaten = 0

    

    def in_bounds(self, row, col):
        """Return whether a grid coordinate is valid."""
        return 0 <= row < ROWS and 0 <= col < COLS

    def is_wall(self, row, col):
        """Treat out-of-bounds positions as walls."""
        if not self.in_bounds(row, col):
            return True

        return self.grid[row][col] == WALL

    def is_walkable(self, row, col):
        """Check whether the tile can be traversed."""
        return not self.is_wall(row, col)

    def is_player_walkable(self, row,col):
        """Check whether Pac-Man can enter a tile"""
        if not self.in_bounds(row,col):
            return False
        return self.grid[row][col] not in (WALL,GATE)
    
    def count_pellets(self):
        """Count all remaining pellets."""
        return sum(
            tile == PELLET
            for row in self.grid
            for tile in row
        )

    def count_power_pellets(self):
        return sum(
            tile == POWER_PELLET
            for row in self.grid
            for tile in row
        )

    def collect_pellets(self, row, col):
        """Remove a collectible and return its score"""

        if not self.in_bounds(row, col):
            return 0

        tile = self.grid[row][col]
        if tile == PELLET:
            self.grid[row][col]= EMPTY
            self.pellets_eaten += 1
            return 10
        if tile == POWER_PELLET:
            self.grid[row][col] = EMPTY
            self.power_pellet_collected = True
            self.pellets_eaten += 1
            return 50
        return 0
        
    def count_walls(self):
        """Count all wall tiles."""
        return sum(
            tile == WALL
            for row in self.grid
            for tile in row
        )

    def validate(self):
        """Check maze dimensions, tiles, and spawn locations."""
        #1. Check dimensions
        if len(self.grid)!= ROWS:
            raise ValueError(f"Maze must have {ROWS} rows")
        
        for index, row in enumerate(self.grid):
            if len(row)!= COLS:
                raise ValueError(f"Maze row{index+1} must have {COLS} columns;")

        #2. Check valid tile symbols
        valid_tiles ={WALL, PELLET, POWER_PELLET, GATE, EMPTY}

        for row_index, row in enumerate(self.grid):
            for col_index, tile in enumerate(row):
                if tile not in valid_tiles:
                    raise ValueError(f"Invalid tile {tile!r} at"
                    f"row {row_index}, column {col_index}.")
        
        #3. Check the outer border
        if any(tile!=WALL for tile in self.grid[0]):
            raise ValueError("The top maze border must contain only walls ")
        
        if any(tile!=WALL for tile in self.grid[-1]):
            raise ValueError("The bottom maze border must contain only walls ")

        #Allow open side edges only in the designated tunnel row
        tunnel_rows = { 10,11,12,13,14,15,16,17,18}
        for row_index, row in enumerate(self.grid):
            if row[0] !=WALL or row[-1]!=WALL:
                if row_index not in tunnel_rows:
                    raise ValueError(
                        f"Left and right borders must be walls at row"
                        f"{row_index} unless that row is a tunnel"
                    )
        
        #4. Check spawn positions
        for name, spawn in(
            ("Player", self.player_spawn),
            ("Ghost", self.ghost_spawn),
        ):
            row,col =spawn

            if not(0 <= row<ROWS and 0 <= col <COLS):
                raise ValueError (f"{name} spawn {spawn} is out of bound")
            
            if self.grid[row][col] in (WALL,GATE):
                raise ValueError(f"{name} spawn {spawn} is inside a wall or gate.")

        #5. count collectibles
        ordinary_count = self.count_pellets()
        power_count = self.count_power_pellets()

        if power_count != 4:
            raise ValueError(
                f"Expected 4 power pellets; found {power_count}."
            )
        if ordinary_count!=240:
            raise ValueError(f"Expected 240 ordinary pellets; found{ordinary_count}")
        # 6. Check reachability from Pac-Man's spawn.
        start_row, start_col = self.player_spawn
        visited = {(start_row, start_col)}
        queue = [(start_row, start_col)]

        while queue:
            row, col = queue.pop(0)

            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                next_row = row + dr
                next_col = col + dc
                position = (next_row, next_col)

                if position in visited:
                    continue

                if not self.in_bounds(next_row, next_col):
                    continue

                if self.grid[next_row][next_col] in (WALL, GATE):
                    continue

                visited.add(position)
                queue.append(position)

        unreachable_pellets = []

        for row in range(ROWS):
            for col in range(COLS):
                if self.grid[row][col] in (PELLET, POWER_PELLET):
                    if (row, col) not in visited:
                        unreachable_pellets.append((row, col))

        if unreachable_pellets:
            raise ValueError(
                f"Found {len(unreachable_pellets)} unreachable "
                f"collectibles. First locations: "
                f"{unreachable_pellets[:10]}"
            )

       



    def draw(self, screen, area):
        """Draw visible walls, pellets, and spawn markers."""

        maze_width = COLS * TILE_SIZE
        maze_height = ROWS * TILE_SIZE

        # Center the maze inside the board.
        origin_x = area.centerx - maze_width // 2
        origin_y = area.centery - maze_height // 2

        # Draw a solid black maze background.
        pygame.draw.rect(
            screen,
            BACKGROUND_COLOR,
            (
                origin_x,
                origin_y,
                maze_width,
                maze_height,
            ),
        )

        # Render each grid tile.
        for row in range(ROWS):
            for col in range(COLS):
                x = origin_x + col * TILE_SIZE
                y = origin_y + row * TILE_SIZE

                tile = self.grid[row][col]

                if tile == WALL:
                    pygame.draw.rect(
                        screen,
                        WALL_COLOR,
                        (
                            x,
                            y,
                            TILE_SIZE - 1,
                            TILE_SIZE - 1,
                        ),
                        border_radius=3,
                    )

                elif tile == PELLET:
                    pygame.draw.circle(
                        screen,
                        PELLET_COLOR,
                        (
                            x + TILE_SIZE // 2,
                            y + TILE_SIZE // 2,
                        ),
                        2,
                    )

                elif tile == POWER_PELLET:
                    pygame.draw.circle(
                        screen,
                        POWER_COLOR,
                        (x+ TILE_SIZE //2, y+ TILE_SIZE //2),
                        6,
                    )
                elif tile == GATE:
                    pygame.draw.line(
                        screen,
                        GATE_COLOR,
                        (x, y+TILE_SIZE //2),
                        (x+TILE_SIZE-1, y+TILE_SIZE //2),
                        3,
                    )

        
      
