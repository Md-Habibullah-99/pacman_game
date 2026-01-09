import pygame
from sys import exit
from maze import draw_smooth_map
from pacman import Pacman
from ghost import Ghost
from lavel_system import LevelSystem

# Config variables
GHOST_SPEED = 1.1
INITIAL_LIVES = 3

# Initialize pygame
pygame.init()
clock = pygame.time.Clock()

# Create Pacman
pacman = Pacman()

# Create Ghosts (all follow same algorithm initially)
red_ghost = Ghost(color=(255, 0, 0), pacman=pacman, speed=GHOST_SPEED, spawn_values={5}, sprite_variant="red", behavior="blinky")
blue_ghost = Ghost(color=(0, 0, 255), pacman=pacman, speed=GHOST_SPEED, spawn_values={6}, sprite_variant="blue", behavior="inky", partner=red_ghost)
orenge_ghost = Ghost(color=(255, 165, 0), pacman=pacman, speed=GHOST_SPEED, spawn_values={7}, sprite_variant="orenge", behavior="clyde")
pink_ghost = Ghost(color=(255, 105, 180), pacman=pacman, speed=GHOST_SPEED, spawn_values={8}, sprite_variant="pink", behavior="pinky")

ghosts = [red_ghost, blue_ghost, orenge_ghost, pink_ghost]

# Level/Lives system
level = LevelSystem(initial_lives=INITIAL_LIVES)

# Main game loop
while True:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        
        # Handle Pacman input
        pacman.handle_input(event)
    
    # Only update gameplay if not game over
    if not level.is_game_over():
        # Update Pacman first
        pacman.update()
        # If Pacman ate a power pellet this frame, enter scatter BEFORE collisions
        if getattr(pacman, 'last_ate_power', False):
            for g in ghosts:
                if hasattr(g, 'enter_scatter_mode'):
                    g.enter_scatter_mode()
            pacman.last_ate_power = False
        # Then update ghosts and check collisions
        for g in ghosts:
            g.update()
        prev_lives = level.get_lives()
        for g in ghosts:
            level.check_collision_and_reset(pacman, g)
            if level.is_game_over():
                break
            if level.get_lives() < prev_lives:
                # life lost: reset all ghosts to spawn to avoid instant re-collision
                for gg in ghosts:
                    if hasattr(gg, 'reset_to_spawn'):
                        gg.reset_to_spawn()
                break
    
    # Draw everything
    draw_smooth_map()
    pacman.draw()
    for g in ghosts:
        g.draw()
    level.draw_lives()
    # If game over, draw overlay message on top
    level.draw_game_over()
    
    # Update display
    pygame.display.flip()
    
    # Limit frame rate to 60 FPS
    clock.tick(60)
