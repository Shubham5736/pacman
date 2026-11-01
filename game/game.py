"""Main game controller and Pygame loop."""

import pygame
import asyncio

from config import (
    WINDOWS_WIDTH,
    WINDOWS_HEIGHT,
    WINDOWS_TITLE,
    FPS,
    BLACK,
    BLUE,
    WHITE,
    DARK_BLUE,
    YELLOW,
    GRAY,
    HUD_HEIGHT,
    BOARD_MARGIN,
)

from systems.collision import check_ghost_collisions
from systems.maze import Maze, ROWS, COLS, TILE_SIZE
from systems.player import Player
from systems.blinky import Blinky
from systems.clyde import Clyde
from systems.pinky import Pinky
from systems.inky import Inky


maze_width = COLS * TILE_SIZE
maze_height = ROWS * TILE_SIZE


class Game:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode(
            (WINDOWS_WIDTH, WINDOWS_HEIGHT)
        )
        pygame.display.set_caption(WINDOWS_TITLE)

        self.clock = pygame.time.Clock()
        self.running = True

        self.title_font = pygame.font.Font(None, 42)
        self.hud_font = pygame.font.Font(None, 30)
        self.info_font = pygame.font.Font(None, 24)
        self.button_font = pygame.font.Font(None, 32)

        # Game Status
        self.score = 0
        self.level = 1
        self.lives = 3
        self.game_started = False
        self.game_over = False
        self.game_won = False

        self.maze = Maze()
        self.player = Player(self.maze.player_spawn)

        # Scatter / chase schedule
        self.mode_schedule = [
            ("scatter", 7),
            ("chase", 20),
            ("scatter", 7),
            ("chase", 20),
            ("scatter", 5),
            ("chase", 20),
            ("scatter", 5),
            ("chase", float("inf")),
        ]

        self.mode_index = 0
        self.current_mode = "scatter"
        self.mode_timer = 7.0

        # Frightened mode lasts six seconds.
        self.frightened_timer = 0.0
        self.ghost_eaten_combo =0

        #Ghost release process
        self.next_ghost_release =0
        self.no_dot_timer = 0.0
        self.last_pellets_eaten = self.maze.pellets_eaten
        self.create_ghosts()
        self.colliding_ghosts = []

        # Button dimensions
        self.start_button_rect = pygame.Rect(0, 0, 260, 64)
        self.start_button_rect.center = (
            WINDOWS_WIDTH // 2,
            WINDOWS_HEIGHT // 2 + 55,
        )

    def create_ghosts(self):
        """Create all ghosts at their designated spawn positions."""

        self.blinky = Blinky(self.maze.blinky_spawn)
        self.pinky = Pinky(self.maze.pinky_spawn)
        self.inky = Inky(self.maze.inky_spawn)
        self.clyde = Clyde(self.maze.clyde_spawn)

        # Inky needs Blinky's position to calculate his target.
        self.inky.blinky = self.blinky

        # Ghost house leaving methods
        #Pinky is allowed to leave immediately
        self.pinky.waiting_in_house = False
        self.pinky.exiting_house = True

        #Inky waits for 30 dots
        self.inky.waiting_in_house = self.next_ghost_release < 1
        self.inky.exiting_house = self.next_ghost_release >= 1

        #Clyde waits for 60 dots
        self.clyde.waiting_in_house = self.next_ghost_release < 2
        self.exiting_house = self.next_ghost_release >= 2

        #Release sequence
        self.ghost_release_queue= [(self.inky, 30), (self.clyde,60)]
        

        self.last_pellets_eaten = self.maze.pellets_eaten



        # Share Pac-Man's facing direction with Pinky and Inky.
        self.pinky.pacman_direction = self.player.facing
        self.inky.pacman_direction = self.player.facing

        # Set mode of each ghost.
        self.set_all_ghost_modes(self.current_mode)

    def update_ghost_release(self, dt):
        """Release ghosts according to dot counts and the no-dot timer."""

        if self.next_ghost_release >= len(self.ghost_release_queue):
            return

        current_count = self.maze.pellets_eaten
        if current_count > self.last_pellets_eaten:
            self.no_dot_timer = 0.0
        else:
            self.no_dot_timer += dt
        self.last_pellets_eaten = current_count

        ghost, required_dots = self.ghost_release_queue[self.next_ghost_release]

        if current_count >= required_dots or self.no_dot_timer >= 4.0:
            ghost.waiting_in_house = False
            ghost.exiting_house =True
            ghost.direction = (0,0)
            ghost.last_decision_tile = None

            self.next_ghost_release += 1
            self.no_dot_timer = 0.0
    
    def set_all_ghost_modes(self, mode):
        """Apply a behavior mode to all the ghosts."""
        self.blinky.set_mode(mode)
        self.pinky.set_mode(mode)
        self.inky.set_mode(mode)
        self.clyde.set_mode(mode)

    def request_all_ghosts_reverse(self):
        """Request reversal from all eligible ghosts."""
        ghosts = (
            self.blinky,
            self.pinky,
            self.inky,
            self.clyde,
        )

        for ghost in ghosts:
            ghost.request_reverse()

    def update_ghost_modes(self, dt):
        """Manage Scatter, Chase and Frightened mode timers."""

        # Frightened mode temporarily pauses the normal schedule.
        if self.frightened_timer > 0:
            self.frightened_timer -= dt

            if self.frightened_timer <= 0:
                self.frightened_timer = 0.0

                # Restore the previous global mode.
                # Do not request reversal when frightened mode ends.
                self.ghost_eaten_combo = 0
                self.set_all_ghost_modes(self.current_mode)

            return

        self.mode_timer -= dt

        if self.mode_timer <= 0:
            if self.mode_index < len(self.mode_schedule) - 1:
                self.mode_index += 1

            previous_mode = self.current_mode

            self.current_mode, duration = self.mode_schedule[self.mode_index]

            self.mode_timer = duration
            self.set_all_ghost_modes(self.current_mode)

            # Reverse only on an actual Scatter <-> Chase transition.
            if self.current_mode != previous_mode:
                self.request_all_ghosts_reverse()

    def activate_frightened_mode(self):
        """Activate frightened mode and request ghost reversal."""

        # Determine whether frightened mode is already active.
        frightened_already_active = self.frightened_timer > 0

        self.frightened_timer = 6.0
        self.set_all_ghost_modes("frightened")

        # Request reversal only when frightened mode starts.
        if not frightened_already_active:
            self.ghost_eaten_combo =0
            self.request_all_ghosts_reverse()

    def reset_game(self):
        """Reset the maze, player, ghosts, and score."""

        self.maze = Maze()
        self.player = Player(self.maze.player_spawn)
        self.lives = 3

        #Ghost release process for a new game
        self.next_ghost_release = 0
        self.no_dot_timer = 0.0
        self.last_pellets_eaten = self.maze.pellets_eaten
        
        # Reset mode of ghosts.
        self.mode_index = 0
        self.current_mode = "scatter"
        self.mode_timer = 7.0
        self.frightened_timer = 0.0

        self.create_ghosts()

        self.score = 0
        self.level = 1
        self.game_over = False
        self.game_won = False
        self.game_started = True

    def handle_events(self):
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    self.running = False

                elif self.game_started:

                    movement = {
                        pygame.K_UP: (-1, 0),
                        pygame.K_w: (-1, 0),
                        pygame.K_DOWN: (1, 0),
                        pygame.K_s: (1, 0),
                        pygame.K_LEFT: (0, -1),
                        pygame.K_a: (0, -1),
                        pygame.K_RIGHT: (0, 1),
                        pygame.K_d: (0, 1),
                    }

                    if event.key in movement:
                        row_change, col_change = movement[event.key]

                        self.player.request_direction(
                            row_change,
                            col_change,
                        )

            elif event.type == pygame.MOUSEBUTTONDOWN:

                if (
                    event.button == 1
                    and not self.game_started
                    and self.start_button_rect.collidepoint(event.pos)
                ):
                    if self.game_over:
                        self.reset_game()
                    else:
                        self.game_started = True

    def lose_life(self):
        """Handle Pac-Man losing one life."""
        self.lives -= 1

        if self.lives <= 0:
            self.lives = 0
            self.game_started = False
            self.game_over = True
            return

        # Keep the score.
        current_score = self.player.score

        # Reset Pac-Man position.
        self.player = Player(self.maze.player_spawn)
        self.player.score = current_score

        # Reset ghost modes and timers.
        self.mode_index = 0
        self.current_mode = "scatter"
        self.mode_timer = 7.0
        self.frightened_timer = 0.0

        # Reset inactivity timer, but preserve pellet/release progress.
        self.no_dot_timer = 0.0
        self.last_pellets_eaten = self.maze.pellets_eaten
        
        self.create_ghosts()
        self.colliding_ghosts = []

    def update(self, dt):
        """Update player, ghosts, collisions, and game state."""

        if not self.game_started:
            return

        # Update Pac-Man first.
        self.player.update(dt, self.maze)
        self.score = self.player.score
        self.update_ghost_release(dt)

        # Check whether Pac-Man collected a power pellet.
        if self.maze.power_pellet_collected:
            self.activate_frightened_mode()
            self.maze.power_pellet_collected = False

        # Update ghost behavior modes.
        self.update_ghost_modes(dt)

        target = (self.player.row, self.player.col)

        # Give Pinky and Inky Pac-Man's facing direction.
        self.pinky.pacman_direction = self.player.facing
        self.inky.pacman_direction = self.player.facing

        # Individual scatter targets.
        blinky_scatter = (-1, COLS)
        pinky_scatter = (-1, -1)
        inky_scatter = (ROWS , COLS)
        clyde_scatter = (ROWS, -1)

        if self.blinky.mode == "scatter":
            blinky_target = blinky_scatter
        else:
            blinky_target = target

        if self.pinky.mode == "scatter":
            pinky_target = pinky_scatter
        else:
            pinky_target = target

        if self.inky.mode == "scatter":
            inky_target = inky_scatter
        else:
            inky_target = target

        if self.clyde.mode == "scatter":
            clyde_target = clyde_scatter
        else:
            clyde_target = target

        # Update all four ghosts.
        self.blinky.update(dt, self.maze, blinky_target)
        self.pinky.update(dt, self.maze, pinky_target)
        self.inky.update(dt, self.maze, inky_target)
        self.clyde.update(dt, self.maze, clyde_target)

        # Check collisions with ghosts.
        ghosts = [self.blinky, self.pinky, self.inky, self.clyde]

        self.colliding_ghosts = check_ghost_collisions(
            self.player, ghosts
        )

        # Ignore ghosts that are already returning home.
        active_collisions = [
            ghost for ghost in self.colliding_ghosts
            if not ghost.returning_home
        ]

        if active_collisions:

            # Normal ghosts cause Pac-Man to lose a life.
            normal_collision = any(
                ghost.mode != "frightened"
                for ghost in active_collisions
            )

            if normal_collision:
                self.lose_life()
                return

            # Frightened ghosts can be eaten.
            else:
                for ghost in active_collisions:

                    # Avoid awarding points more than once.
                    if ghost.mode == "frightened":
                        ghost.eat()
                        #Calculate ghost-eating score
                        points = 200 * (2 ** min(self.ghost_eaten_combo,3))
                        self.player.score += points
                        self.ghost_eaten_combo +=1
                        #print(f"Ghost eaten ! +{points} points")

                self.score = self.player.score

            self.colliding_ghosts = []

        # Check whether all collectibles have been collected.
        remaining = (
            self.maze.count_pellets()
            + self.maze.count_power_pellets()
        )

        if remaining == 0:
            self.game_started = False
            self.game_over = True
            self.game_won = True

    def draw_start_screen(self):
        self.screen.fill(BLACK)

        # Game content.
        if not self.game_over:
            heading_text = "PAC-MAN"
            heading_color = YELLOW
            subtitle_text = "Ready for an adventure?"
            button_label = "START THE GAME"
            hint_text = "Click the button to begin"

        elif self.game_won:
            heading_text = "CONGRATULATIONS"
            heading_color = (0, 255, 100)
            subtitle_text = ""
            button_label = "PLAY AGAIN"
            hint_text = ""
        else:
            heading_text = "GAME OVER!!!!"
            heading_color = (255, 60, 60)
            subtitle_text = ""
            button_label = "TRY AGAIN"
            hint_text = ""

        # Main heading.
        title = self.title_font.render(heading_text, True, heading_color)
        title_rect = title.get_rect(
            center=(WINDOWS_WIDTH // 2, WINDOWS_HEIGHT // 2 - 155)
        )
        self.screen.blit(title, title_rect)

        # Subtitle.
        if subtitle_text:
            subtitle = self.info_font.render(subtitle_text, True, WHITE)
            subtitle_rect = subtitle.get_rect(
                center=(WINDOWS_WIDTH // 2, WINDOWS_HEIGHT // 2 - 85)
            )
            self.screen.blit(subtitle, subtitle_rect)

        # Display score.
        if self.game_over:
            score_label = self.hud_font.render("Final Score", True, WHITE)
            score_label_rect = score_label.get_rect(
                center=(WINDOWS_WIDTH // 2, WINDOWS_HEIGHT // 2 - 65)
            )
            self.screen.blit(score_label, score_label_rect)

            final_score = self.title_font.render(
                str(self.score), True, YELLOW
            )
            final_score_rect = final_score.get_rect(
                center=(WINDOWS_WIDTH // 2, WINDOWS_HEIGHT // 2 - 10)
            )
            self.screen.blit(final_score, final_score_rect)

        # Fixed-size button.
        pygame.draw.rect(
            self.screen,
            YELLOW,
            self.start_button_rect,
            border_radius=12,
        )
        button_text = self.button_font.render(button_label, True, BLACK)
        button_text_rect = button_text.get_rect(
            center=self.start_button_rect.center
        )
        self.screen.blit(button_text, button_text_rect)

        # Hint.
        if hint_text:
            hint = self.info_font.render(hint_text, True, GRAY)
            hint_rect = hint.get_rect(
                center=(WINDOWS_WIDTH // 2, self.start_button_rect.bottom + 30)
            )
            self.screen.blit(hint, hint_rect)

   
           
            

    def draw(self):
        self.screen.fill(BLACK)

        if not self.game_started:
            self.draw_start_screen()
            pygame.display.flip()
            return

        # HUD row 1: centered game title.
        title = self.title_font.render("PAC-MAN", True, YELLOW)
        title_rect = title.get_rect(center=(WINDOWS_WIDTH // 2, 22))
        self.screen.blit(title, title_rect)

        # HUD row 2: game information.
        hud_y = 55
        level_text = self.hud_font.render(
            f"Level: {self.level}", True, WHITE
        )
        level_rect = level_text.get_rect(midleft=(BOARD_MARGIN, hud_y))
        self.screen.blit(level_text, level_rect)

        # Score.
        score_text = self.hud_font.render(
            f"Score: {self.score}", True, WHITE
        )
        score_rect = score_text.get_rect(center=(WINDOWS_WIDTH // 2, hud_y))
        self.screen.blit(score_text, score_rect)

        # Lives.
        lives_text = self.hud_font.render(
            f"Lives: {self.lives}", True, WHITE
        )
        lives_rect = lives_text.get_rect(
            midright=(WINDOWS_WIDTH - BOARD_MARGIN, hud_y)
        )
        self.screen.blit(lives_text, lives_rect)

        board_rect = pygame.Rect(
            (WINDOWS_WIDTH - maze_width) // 2,
            HUD_HEIGHT,
            maze_width,
            maze_height,
        )

        pygame.draw.rect(
            self.screen,
            DARK_BLUE,
            board_rect,
            border_radius=12,
        )

        self.maze.draw(self.screen, board_rect)

        # Draw Pac-Man.
        self.player.draw(self.screen, board_rect)

        # Draw all four ghosts.
        self.blinky.draw(self.screen, board_rect,self.frightened_timer)
        self.pinky.draw(self.screen, board_rect,self.frightened_timer)
        self.inky.draw(self.screen, board_rect,self.frightened_timer)
        self.clyde.draw(self.screen, board_rect,self.frightened_timer)

      

        pygame.draw.rect(
            self.screen,
            BLUE,
            board_rect,
            width=3,
            border_radius=12,
        )

        controls = self.info_font.render(
            "Move: Arrows | ESC: Quit",
            True,
            GRAY,
        )
        controls_rect = controls.get_rect(
            center=(
                WINDOWS_WIDTH // 2,
                board_rect.bottom + 18,
            )
        )
        self.screen.blit(controls, controls_rect)

        pygame.display.flip()

    async def run(self):
        try:
            while self.running:
                dt = self.clock.tick(FPS) / 1000.0

                self.handle_events()
                self.update(dt)
                self.draw()

                await asyncio.sleep(0)

        finally:
            pygame.quit()
