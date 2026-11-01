from collections import deque
import random

import pygame

from systems.maze import TILE_SIZE, ROWS, COLS, WALL, GATE


# ---------------------------------------------------------------------------
# Movement directions
# ---------------------------------------------------------------------------
UP = (-1, 0)
DOWN = (1, 0)
LEFT = (0, -1)
RIGHT = (0, 1)

DIRECTIONS = (UP, LEFT, DOWN, RIGHT)

FRIGHTENEC_COLOR = (0,0,225)
FLASH_COLOR = (255,255,255)
FLASH_START_TIME = 2.0
FLAST_INTERVAL_MS = 150

class Ghost:
    # -----------------------------------------------------------------------
    # 1. Initialization and state
    # -----------------------------------------------------------------------
    def __init__(self, spawn, color, speed=150.0, name="Ghost"):
        self.row, self.col = spawn
        self.spawn_row, self.spawn_col = spawn

        self.x = self.col * TILE_SIZE + TILE_SIZE / 2
        self.y = self.row * TILE_SIZE + TILE_SIZE / 2

        self.name = name
        self.normal_color = color
        self.color = color
        self.radius = TILE_SIZE // 2 - 2

        self.base_speed = float(speed)
        self.direction = LEFT
        self.target = spawn
        self.last_decision_tile = None
        self.speed = self.base_speed

        # Pending direction reversal
        self.reverse_pending = False

        # Lifecycle state
        self.alive = True
        self.eaten = False
        self.returning_home = False

        # Ghost-house state
        self.exiting_house = False
        self.has_left_house = False
        self.waiting_in_house = False
        self.exit_tiles = set()

        # Behavior mode
        self.game_mode = "scatter"
        self.mode = "chase"

    # -----------------------------------------------------------------------
    # 2. Grid and movement helpers
    # -----------------------------------------------------------------------
    def _tile_at(self, x, y):
        """Convert pixel coordinates into a maze row and column."""
        col = int(x // TILE_SIZE)
        row = int(y // TILE_SIZE)

        if col < 0:
            col = COLS - 1
        elif col >= COLS:
            col = 0

        return row, col

    def _at_tile_center(self):
        """Return True when the ghost is aligned with its current tile."""
        center_x = self.col * TILE_SIZE + TILE_SIZE / 2
        center_y = self.row * TILE_SIZE + TILE_SIZE / 2

        # Crossing detection lands ghosts exactly on tile centers,
        # so only a tiny tolerance is needed here.
        return (
            abs(self.x - center_x) <= 0.01
            and abs(self.y - center_y) <= 0.01
        )

    def _walkable(self, maze, row, col):
        """Check whether a ghost can move onto a tile."""

        if not (0 <= row < ROWS and 0 <= col < COLS):
            return False

        tile = maze.grid[row][col]

        if tile == WALL:
            return False

        # The gate is passable only when leaving or returning to the house.
        if tile == GATE:
            return self.returning_home or self.exiting_house

        return True

    def _can_move(self, maze, direction):
        """Check whether one of the four cardinal moves is legal."""
        if direction not in DIRECTIONS:
            return False

        dr, dc = direction
        next_row = self.row + dr
        next_col = (self.col + dc) % COLS

        return self._walkable(maze, next_row, next_col)

    # -----------------------------------------------------------------------
    # 3. Ghost-house exit navigation
    # -----------------------------------------------------------------------
    def _find_exit_tiles(self, maze):
        """Find walkable tiles immediately outside the ghost-house gate."""
        gates = [
            (row, col)
            for row in range(ROWS)
            for col in range(COLS)
            if maze.grid[row][col] == GATE
        ]

        if not gates:
            return set()

        gate_row = sum(row for row, _ in gates) / len(gates)

        if self.spawn_row > gate_row:
            exits = [(row - 1, col) for row, col in gates]
        else:
            exits = [(row + 1, col) for row, col in gates]

        return {
            (row, col)
            for row, col in exits
            if (
                0 <= row < ROWS
                and 0 <= col < COLS
                and maze.grid[row][col] not in (WALL, GATE)
            )
        }

    def _exit_direction(self, maze):
        """Use BFS to find the first move from the house toward its exit."""
        exits = self._find_exit_tiles(maze)

        if not exits:
            return None

        current = (self.row, self.col)

        if current in exits:
            self.exiting_house = False
            self.has_left_house = True
            self.exit_tiles = exits
            return None

        queue = deque([(current, None)])
        visited = {current}

        while queue:
            (row, col), first_direction = queue.popleft()

            if (row, col) in exits:
                self.exit_tiles = exits
                return first_direction

            for direction in DIRECTIONS:
                dr, dc = direction
                next_row = row + dr
                next_col = (col + dc) % COLS
                next_tile = (next_row, next_col)

                if next_tile in visited:
                    continue

                if not (0 <= next_row < ROWS):
                    continue

                tile = maze.grid[next_row][next_col]

                if tile == WALL:
                    continue

                if tile == GATE and self.has_left_house:
                    continue

                visited.add(next_tile)

                next_first_direction = (
                    direction
                    if first_direction is None
                    else first_direction
                )

                queue.append((next_tile, next_first_direction))

        return None

    # -----------------------------------------------------------------------
    # 4. Normal and frightened movement decisions
    # -----------------------------------------------------------------------
    def choose_direction(self, maze, target):
        """Choose a legal direction that moves toward the target tile."""
        self.target = target

        options = [
            direction
            for direction in DIRECTIONS
            if self._can_move(maze, direction)
        ]

        if not options:
            return (0, 0)

        reverse = (-self.direction[0], -self.direction[1])

        alternatives = [
            direction
            for direction in options
            if direction != reverse
        ]

        if alternatives:
            options = alternatives

        target_row, target_col = target

        def distance(direction):
            dr, dc = direction
            next_row = self.row + dr
            next_col = (self.col + dc)

            #preserve tunnel wrappinf for normal in-maze target
            #use direct columns for aoo maze targets
            if 0 <= target_col <COLS:
                next_col %=COLS

            return (
                (target_row - next_row) ** 2
                + (target_col - next_col) ** 2
            )

        return min(options, key=distance)

    def choose_frightened_direction(self, maze):
        """Choose a random legal direction while frightened."""

        options = [
            direction
            for direction in DIRECTIONS
            if self._can_move(maze, direction)
        ]

        # No legal movement is available.
        if not options:
            return (0, 0)

        reverse = (-self.direction[0], -self.direction[1])

        alternatives = [
            direction
            for direction in options
            if direction != reverse
        ]

        if alternatives:
            options = alternatives

        return random.choice(options)


    # -----------------------------------------------------------------------
    # 5. Speed management
    # -----------------------------------------------------------------------
    def update_speed(self):
        """Update speed according to the ghost's current state."""

        if self.returning_home:
            multiplier = 3.0

        elif self.mode == "frightened":
            multiplier = 0.5

        else:
            multiplier = 1.0

        self.speed = self.base_speed * multiplier

    # -----------------------------------------------------------------------
    # 6. Reversal management
    # -----------------------------------------------------------------------
    def request_reverse(self):
        """
        Request reversal at the next tile center.

        Returning ghosts and ghosts exiting the house are excluded.
        Repeated requests coalesce into one pending reversal.
        """
        if self.returning_home or self.exiting_house:
            return

        self.reverse_pending = True

    # -----------------------------------------------------------------------
    # 7. Mode and eaten-state management
    # -----------------------------------------------------------------------
    def set_mode(self, mode):
        """Set scatter/chase/frightened mode without interrupting recovery."""

        if mode not in ("frightened", "eaten"):
            self.game_mode = mode

        if self.returning_home:
            self.mode = "eaten"
            self.color = self.normal_color
            return

        if self.mode == mode:
            return

        self.mode = mode

        if mode == "frightened":
            self.color = (30, 60, 255)
        else:
            self.color = self.normal_color

        self.update_speed()

    def eat(self):
        """Begin the return-home process after Pac-Man eats this ghost."""
        if not self.alive or self.returning_home:
            return

        self.reverse_pending = False

        self.eaten = True
        self.returning_home = True
        self.exiting_house = False
        self.mode = "eaten"
        self.color = self.normal_color

        self.update_speed()

    # -----------------------------------------------------------------------
    # 8. Return-home pathfinding
    # -----------------------------------------------------------------------
    def return_home_direction(self, maze):
        """Use BFS to find the first move toward the original spawn tile."""
        start = (self.row, self.col)
        goal = (self.spawn_row, self.spawn_col)

        if start == goal:
            return (0, 0)

        queue = deque([(start, [])])
        visited = {start}

        while queue:
            current, path = queue.popleft()

            for direction in DIRECTIONS:
                dr, dc = direction
                next_row = current[0] + dr
                next_col = (current[1] + dc) % COLS
                next_tile = (next_row, next_col)

                if next_tile in visited:
                    continue

                if not (0 <= next_row < ROWS):
                    continue

                if maze.is_wall(next_row, next_col):
                    continue

                new_path = path + [direction]

                if next_tile == goal:
                    return new_path[0]

                visited.add(next_tile)
                queue.append((next_tile, new_path))

        return (0, 0)

    def _recover_at_home(self):
        """Restore a ghost after it reaches its spawn position."""
        self.returning_home = False
        self.eaten = False

        if self.name == "Blinky":
            self.exiting_house = False
            self.has_left_house = True

        else:
            self.exiting_house = True
            self.has_left_house = False

        self.mode = self.game_mode
        self.color = self.normal_color
        self.direction = (0, 0)

        self.reverse_pending = False
        self.update_speed()

    # -----------------------------------------------------------------------
    # 9. Tile-center decisions
    # -----------------------------------------------------------------------
    def _process_tile_center(self, maze, target):
        """Make the ghost's movement decision at a tile center."""

        current_tile = (self.row, self.col)

        # Decide only once per tile.
        if current_tile == self.last_decision_tile:
            return

        self.last_decision_tile = current_tile

        # Returning-home behaviour
        if self.returning_home:

            if (self.row, self.col) == (
                self.spawn_row,
                self.spawn_col
            ):
                self._recover_at_home()

            else:
                return_direction = self.return_home_direction(maze)

                self.direction = (
                    return_direction
                    if return_direction in DIRECTIONS
                    else (0, 0)
                )

        # Ghost-house exit behaviour
        elif self.exiting_house:

            exit_direction = self._exit_direction(maze)

            if exit_direction in DIRECTIONS:
                self.direction = exit_direction

            elif not self.exiting_house:
                self.direction = self.choose_direction(
                    maze, target
                )

            else:
                self.direction = (0, 0)

        # Normal/frightened behaviour
        else:

            reversed_successfully = False

            if self.reverse_pending:

                reverse_direction = (
                    -self.direction[0],
                    -self.direction[1]
                )

                self.reverse_pending = False

                if (
                    reverse_direction in DIRECTIONS
                    and self._can_move(maze, reverse_direction)
                ):
                    self.direction = reverse_direction
                    reversed_successfully = True

            if not reversed_successfully:

                if self.mode == "frightened":
                    new_direction = self.choose_frightened_direction(
                        maze
                    )

                else:
                    new_direction = self.choose_direction(
                        maze, target
                    )

                if new_direction in DIRECTIONS:
                    self.direction = new_direction

                else:
                    self.direction = (0, 0)

    # -----------------------------------------------------------------------
    # 10. Main movement update
    # -----------------------------------------------------------------------
    def update(self, dt, maze, target=None):
        """Update ghost movement with tile-center crossing detection."""

        if not self.alive or self.waiting_in_house:
            return

        self.update_speed()

        dt = min(max(dt, 0.0), 0.05)

        self.row, self.col = self._tile_at(self.x, self.y)
        self.row = max(0, min(ROWS - 1, self.row))
        self.col = max(0, min(COLS - 1, self.col))

        if target is None:
            target = (self.row, self.col)

        # A stopped ghost may decide again on the tile it is standing on.
        if self.direction == (0, 0):
            self.last_decision_tile = None

        half = TILE_SIZE / 2
        maze_width = COLS * TILE_SIZE
        epsilon = 0.000001

        # Handle a tile center the ghost is already standing on.
        # Requiring a NEW tile stops slow ghosts from being snapped back
        # to the same center every frame (the freeze bug).
        if (
            self._at_tile_center()
            and (self.row, self.col) != self.last_decision_tile
        ):
            self.x = self.col * TILE_SIZE + half
            self.y = self.row * TILE_SIZE + half

            self._process_tile_center(maze, target)

        remaining_distance = self.speed * dt

        # Safety limit so a logic error can never cause an endless loop.
        iterations = 0
        max_iterations = 16

        while remaining_distance > epsilon and iterations < max_iterations:
            iterations += 1

            if self.direction == (0, 0):
                break

            dr, dc = self.direction

            center_x = self.col * TILE_SIZE + half
            center_y = self.row * TILE_SIZE + half

            # Find the next tile center.
            if dc > 0:
                if self.x < center_x - epsilon:
                    next_center_x = center_x
                else:
                    next_center_x = center_x + TILE_SIZE

                next_center_y = center_y

            elif dc < 0:
                if self.x > center_x + epsilon:
                    next_center_x = center_x
                else:
                    next_center_x = center_x - TILE_SIZE

                next_center_y = center_y

            elif dr > 0:
                if self.y < center_y - epsilon:
                    next_center_y = center_y
                else:
                    next_center_y = center_y + TILE_SIZE

                next_center_x = center_x

            else:
                if self.y > center_y + epsilon:
                    next_center_y = center_y
                else:
                    next_center_y = center_y - TILE_SIZE

                next_center_x = center_x

            # Determine destination logical tile.
            next_row = self.row + dr
            next_col = (self.col + dc) % COLS

            # The current tile center may still be ahead.
            if dc > 0 and next_center_x == center_x:
                next_row, next_col = self.row, self.col

            elif dc < 0 and next_center_x == center_x:
                next_row, next_col = self.row, self.col

            elif dr > 0 and next_center_y == center_y:
                next_row, next_col = self.row, self.col

            elif dr < 0 and next_center_y == center_y:
                next_row, next_col = self.row, self.col

            # Validate the destination before moving.
            if not self._walkable(maze, next_row, next_col):

                # Stop before entering the blocked tile.
                self.direction = (0, 0)

                # Permit a fresh decision on this tile.
                self.last_decision_tile = None

                # Try another legal direction.
                self._process_tile_center(maze, target)

                if self.direction == (0, 0):
                    break

                # Continue with the newly selected direction.
                continue

            if dc != 0:
                distance_to_center = abs(next_center_x - self.x)
            else:
                distance_to_center = abs(next_center_y - self.y)

            # Not enough movement to reach the next center.
            if remaining_distance + epsilon < distance_to_center:

                self.x += dc * remaining_distance
                self.y += dr * remaining_distance

                # Tunnel wrapping.
                if self.x < 0:
                    self.x += maze_width

                elif self.x >= maze_width:
                    self.x -= maze_width

                remaining_distance = 0
                break

            # Move exactly to the next tile center.
            self.x = next_center_x
            self.y = next_center_y

            # Tunnel wrapping.
            if self.x < 0:
                self.x += maze_width

            elif self.x >= maze_width:
                self.x -= maze_width

            self.row = next_row
            self.col = next_col

            remaining_distance -= distance_to_center

            # Process AI decisions at this tile center.
            self._process_tile_center(maze, target)

        # Keep the logical tile in sync with the final pixel position.
        self.row, self.col = self._tile_at(self.x, self.y)
        self.row = max(0, min(ROWS - 1, self.row))
        self.col = max(0, min(COLS - 1, self.col))

    # -----------------------------------------------------------------------
    # 11. Rendering
    # -----------------------------------------------------------------------
    def get_display_color(self, frightened_timer):
        """Return the ghost color based on its current mode."""

        if self.mode == "frightened":

            if 0 < frightened_timer <= 2.0:
                flash_phase = (
                    pygame.time.get_ticks() // 150
                ) % 2

                return (
                    (255, 255, 255)
                    if flash_phase == 0
                    else (0, 0, 255)
                )

            return (0, 0, 255)

        return self.color
    
    def _draw_eyes(self, screen, center_x, center_y):
        """Draw the ghost's white eyes and blue pupils."""
        eye_y = center_y - 2

        for eye_x in (center_x - 3, center_x + 3):
            pygame.draw.circle(
                screen,
                (255, 255, 255),
                (eye_x, eye_y),
                3
            )

            pygame.draw.circle(
                screen,
                (0, 80, 255),
                (eye_x, eye_y),
                1
            )

    def draw(self, screen, area, frightened_timer =0.0):
        """Draw a normal ghost or only its eyes while it returns home."""

        if not self.alive:
            return

        center_x = area.x + int(round(self.x))
        center_y = area.y + int(round(self.y))
        radius = self.radius

        if self.returning_home:
            self._draw_eyes(screen, center_x, center_y)
            return

        body_color = self.get_display_color(frightened_timer)
        pygame.draw.circle(
            screen,
            body_color,
            (center_x, center_y - 2),
            radius
        )

        pygame.draw.rect(
            screen,
            body_color,
            (
                center_x - radius,
                center_y - 2,
                radius * 2,
                radius + 2
            )
        )

        for offset in (-radius // 2, 0, radius // 2):
            pygame.draw.circle(
                screen,
                body_color,
                (center_x + offset, center_y + radius - 2),
                max(2, radius // 3)
            )

        self._draw_eyes(screen, center_x, center_y)