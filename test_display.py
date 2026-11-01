import pygame

pygame.init()

screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Pac-Man - Environment Test")

screen.fill((0, 0, 0))
pygame.display.flip()

print("PASS: Pygame window initialized.")
print("Window size:", screen.get_size())
print("Close the window to finish the test.")

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()
print("PASS: Pygame shut down cleanly.")
