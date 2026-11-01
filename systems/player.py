
import math
import pygame

from systems.maze import TILE_SIZE, ROWS, COLS


class Player:
    def __init__(self, spawn):
        self.row, self.col = spawn
        self.score = 0

        # Pixel position at the center of the spawn tile.
        self.x = self.col * TILE_SIZE + TILE_SIZE / 2
        self.y = self.row * TILE_SIZE + TILE_SIZE / 2

        # Directions: (row_change, col_change).
        self.direction = (0, 1)
        self.next_direction = (0, 1)

        #buffer turn input
        self.turn_buffer_timer = 0.0
        self.turn_buffer_duration = 0.20

        # Last direction faced, retained when stopped.
        self.facing = (0, 1)

        self.speed = 120.0

        # Mouth animation.
        self.animation_time = 0.0
        self.animation_speed = 10.0
        self.max_mouth_angle = 45.0
        self.mouth_angle = 0.0

        self.radius = TILE_SIZE // 2 - 2

    def request_direction(self, row_change, col_change):
        """Request a direction change."""
        requested = (row_change, col_change)

        if requested in (
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
        ):
            self.next_direction = requested
            self.turn_buffer_timer = self.turn_buffer_duration

    def _tile_at(self, x, y):
        """Convert pixel coordinates into a maze tile."""
        col = int(x // TILE_SIZE)
        row = int(y // TILE_SIZE)

        # Map horizontal positions across the tunnel edges.
        if col < 0:
            col = COLS - 1
        elif col >= COLS:
            col = 0

        return row, col

    def _is_wall_at(self, x, y, maze):
        """Check whether a pixel position lies in a wall or gate."""
        row, col = self._tile_at(x, y)

        if not (0 <= row < ROWS):
            return True

        return not maze.is_player_walkable(row, col)

    def _can_move(self, row_change, col_change, maze):
        """Check whether the next tile is walkable."""
        next_row = self.row + row_change
        next_col = self.col + col_change

        # Support horizontal tunnel connections.
        if col_change != 0:
            if next_col < 0:
                next_col = COLS - 1
            elif next_col >= COLS:
                next_col = 0

        if not (0 <= next_row < ROWS):
            return False

        return maze.is_player_walkable(next_row, next_col)

    def update(self, dt, maze):
        """Move smoothly with buffered turns, wall stopping, and tunnel wrapping."""

        dt = min(max(dt, 0.0), 0.05)
        distance = self.speed * dt

        #Expire buffered direction request
        if self.next_direction != self.direction:
            self.turn_buffer_timer -=dt
            
            if self.turn_buffer_timer <=0:
                self.next_direction = self.direction
                self.turn_buffer_timer = 0.0
        maze_width = COLS * TILE_SIZE
        alignment_tolerance = max(2.0, distance)

        # Synchronize logical tile coordinates.
        self.row, self.col = self._tile_at(self.x, self.y)

        tile_center_x = self.col * TILE_SIZE + TILE_SIZE / 2
        tile_center_y = self.row * TILE_SIZE + TILE_SIZE / 2

        requested_row, requested_col = self.next_direction

        aligned_x = abs(self.x - tile_center_x) <= alignment_tolerance
        aligned_y = abs(self.y - tile_center_y) <= alignment_tolerance

        can_attempt_turn = (
            (requested_row != 0 and aligned_x)
            or (requested_col != 0 and aligned_y)
        )

        # Attempt a requested turn when aligned.
        if can_attempt_turn and self.next_direction != self.direction:

            if self._can_move(requested_row, requested_col, maze):

                # Align with the tile centre before turning.
                if requested_row != 0:
                    self.x = tile_center_x
                else:
                    self.y = tile_center_y

                self.direction = self.next_direction
                self.facing = self.direction

            # Keep blocked requests buffered for the next tile.

        row_change, col_change = self.direction

        # Check whether the tile ahead is blocked.
        if (
            self.direction != (0, 0)
            and not self._can_move(row_change, col_change, maze)
        ):

            # Calculate distance to the current tile centre.
            if col_change != 0:
                distance_to_center = (
                    tile_center_x - self.x
                ) * col_change
            else:
                distance_to_center = (
                    tile_center_y - self.y
                ) * row_change

            if distance_to_center > 0:

                # Move towards the centre without overshooting.
                movement = min(distance, distance_to_center)

                self.x += col_change * movement
                self.y += row_change * movement

                if movement >= distance_to_center:
                    self.x = tile_center_x
                    self.y = tile_center_y
                    self.direction = (0, 0)

            else:
                # Stop without snapping backwards.
                self.direction = (0, 0)

        else:
            next_x = self.x + col_change * distance
            next_y = self.y + row_change * distance

            # Horizontal tunnel wrapping.
            if next_x < 0:

                if not maze.is_wall(self.row, COLS - 1):
                    self.x = next_x + maze_width
                else:
                    self.x = TILE_SIZE / 2
                    self.direction = (0, 0)
                    self.next_direction = (0, 0)

            elif next_x >= maze_width:

                if not maze.is_wall(self.row, 0):
                    self.x = next_x - maze_width
                else:
                    self.x = maze_width - TILE_SIZE / 2
                    self.direction = (0, 0)
                    self.next_direction = (0, 0)

            elif not self._is_wall_at(next_x, next_y, maze):
                self.x = next_x
                self.y = next_y

            else:
                # Safety collision: stop without snapping backwards.
                self.direction = (0, 0)

        # Update logical tile coordinates.
        self.row, self.col = self._tile_at(self.x, self.y)
        self.row = max(0, min(ROWS - 1, self.row))
        self.col = max(0, min(COLS - 1, self.col))

        # Collect pellets.
        points = maze.collect_pellets(self.row, self.col)

        if points:
            self.score += points

        # Animate Pac-Man's mouth.
        if self.direction != (0, 0):
            self.animation_time += dt * self.animation_speed

            self.mouth_angle = (
                abs(math.sin(self.animation_time * math.pi))
                * self.max_mouth_angle
            )
        else:
            self.mouth_angle = 0.0

    def draw(self, screen, area):
        """Draw Pac-Man with a smooth mouth and no black overlay."""
        center_x = area.x + int(round(self.x))
        center_y = area.y + int(round(self.y))
        radius = self.radius

        # Keep the last facing direction when stopped.
        facing_row, facing_col = self.facing
        facing_angle = math.atan2(-facing_row, facing_col)

        # A closed mouth is a complete circle.
        if self.mouth_angle <= 0.5 or self.direction == (0, 0):
            pygame.draw.circle(
                screen,
                (255, 255, 0),
                (center_x, center_y),
                radius,
            )
            return

        half_angle = math.radians(self.mouth_angle)

        # The mouth edges lie on either side of the facing direction.
        start_angle = facing_angle + half_angle

        # Trace the larger circular arc around Pac-Man's body.
        segments = 48
        points = [(center_x, center_y)]

        for index in range(segments + 1):
            fraction = index / segments

            angle = (
                start_angle
                + (2 * math.pi - 2 * half_angle) * fraction
            )

            px = center_x + radius * math.cos(angle)
            py = center_y - radius * math.sin(angle)

            points.append(
                (int(round(px)), int(round(py)))
            )

        pygame.draw.polygon(
            screen,
            (255, 255, 0),
            points,
        )
