def draw(self):
        self.screen.fill(BLACK)

        if not self.game_started:
            self.draw_start_screen()
            pygame.display.flip()
            return

        title = self.title_font.render("PAC-MAN", True, YELLOW)
        self.screen.blit(title, (BOARD_MARGIN , 20))

        level_text = self.hud_font.render(
            f"Level: {self.level}", True, WHITE
        )
        self.screen.blit(
            level_text,
            (WINDOWS_WIDTH // 2 - 50, 25),
        )

        score_text = self.hud_font.render(
            f"Score: {self.score}", True, WHITE
        )
        self.screen.blit(
            score_text,
            (WINDOWS_WIDTH - 220, 25),
        )

        lives_text = self.hud_font.render(
            f"Lives: {self.lives}", True, WHITE
        )
        self.screen.blit(lives_text, (WINDOWS_WIDTH -220 , 55))
        remaining = (
            self.maze.count_pellets()
            + self.maze.count_power_pellets()
        )
        remaining_text = self.info_font.render(
            f"Pellets: {remaining}", True, WHITE
        )
        self.screen.blit(
            remaining_text,
            (WINDOWS_WIDTH // 2 + 65, 29),
        )

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

        # Draw all three ghosts.
        self.blinky.draw(self.screen, board_rect)
        self.pinky.draw(self.screen, board_rect)
        self.inky.draw(self.screen, board_rect)

        pygame.draw.rect(
            self.screen,
            BLUE,
            board_rect,
            width=3,
            border_radius=12,
        )

        controls = self.info_font.render(
            "Move: Arrows/WASD | ESC: Quit",
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

    def run(self):
        try:
            while self.running:
                dt = self.clock.tick(FPS) / 1000.0

                self.handle_events()
                self.update(dt)
                self.draw()

        finally:
            pygame.quit()


  def draw_start_screen(self):
        self.screen.fill(BLACK)

        if self.game_over:
            heading_text = "GAME COMPLETE!"
            subtitle_text = "You collected every pellet!"
            button_label = "PLAY AGAIN"
        else:
            heading_text = "PAC-MAN"
            subtitle_text = "Ready for an adventure?"
            button_label = "START THE GAME"

        title = self.title_font.render(
            heading_text, True, YELLOW
        )
        title_rect = title.get_rect(
            center=(
                WINDOWS_WIDTH // 2,
                WINDOWS_HEIGHT // 2 - 100,
            )
        )
        self.screen.blit(title, title_rect)

        subtitle = self.info_font.render(
            subtitle_text, True, WHITE
        )
        subtitle_rect = subtitle.get_rect(
            center=(
                WINDOWS_WIDTH // 2,
                WINDOWS_HEIGHT // 2 - 35,
            )
        )
        self.screen.blit(subtitle, subtitle_rect)

        if self.game_over:
            final_score = self.hud_font.render(
                f"Final Score: {self.score}", True, WHITE
            )
            final_score_rect = final_score.get_rect(
                center=(
                    WINDOWS_WIDTH // 2,
                    WINDOWS_HEIGHT // 2 + 10,
                )
            )
            self.screen.blit(final_score, final_score_rect)

        pygame.draw.rect(
            self.screen,
            YELLOW,
            self.start_button_rect,
            border_radius=12,
        )

        button_text = self.button_font.render(
            button_label, True, BLACK
        )
        button_text_rect = button_text.get_rect(
            center=self.start_button_rect.center
        )
        self.screen.blit(button_text, button_text_rect)

        hint_text = (
            "Click to play again"
            if self.game_over
            else "Click the button to begin"
        )
        hint = self.info_font.render(hint_text, True, GRAY)
        hint_rect = hint.get_rect(
            center=(
                WINDOWS_WIDTH // 2,
                self.start_button_rect.bottom + 30,
            )
        )
        self.screen.blit(hint, hint_rect)