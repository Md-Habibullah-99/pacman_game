import pygame
from sys import exit
from maze import draw_smooth_map
from pacman import Pacman

# Initialize pygame
pygame.init()
clock = pygame.time.Clock()

# Create Pacman
pacman = Pacman()

# Main game loop
while True:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        
        # Handle Pacman input
        pacman.handle_input(event)
    
    # Update Pacman position and physics
    pacman.update()
    
    # Draw everything
    draw_smooth_map()
    pacman.draw()
    
    # Update display
    pygame.display.flip()
    
    # Limit frame rate to 60 FPS
    clock.tick(60)