import pygame
import sys

###--- Initialize Pygame
pygame.init()

###--- Screen display size
WIDTH, HEIGHT = 600, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Click to Draw X") ###--- title bar

###--- Colors to be used in the game
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128,128,128)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

###--- Store click positions array for Left and Right Mouse Click
Lclick_positions = []
Rclick_possitions = []
# Main loop
running = True
while running:
    screen.fill(GRAY)

    ###--- Left clicks will be X on the screen
    for pos in Lclick_positions:
        x, y = pos
        ###---- pygame.draw.line(surface, color, start_pos, end_pos, width)

        pygame.draw.line(screen, WHITE, (x - 10, y - 10), (x + 10, y + 10), 2)
        pygame.draw.line(screen, WHITE, (x - 10, y + 10), (x + 10, y - 10), 2)
    ###--- Right click  will be 0
    for pos in Rclick_possitions:
        x, y = pos
        pygame.draw.circle(screen, RED, (x - 10, y - 10), 10, 2)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Detect mouse click
        mouse_pos = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                Lclick_positions.append(mouse_pos)
                print("Left click")
            elif event.button == 3:
                Rclick_possitions.append(mouse_pos)
                print("Right click")
            elif event.button == 2:
                print("Middle click")

        #if event.type == pygame.MOUSEBUTTONDOWN:
       #     mouse_pos = pygame.mouse.get_pos()
        #    click_positions.append(mouse_pos)

    pygame.display.flip()

# Quit Pygame
pygame.quit()
sys.exit()
