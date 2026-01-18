# main.py
import pygame
import sys
import os
from maze import draw_smooth_map, screen, SCREEN_WIDTH, SCREEN_HEIGHT, reset_maze
from pacman import Pacman
from ghost import Ghost
from lavel_system import LevelSystem
from menu import Menu

# Config variables
GHOST_SPEED = 1.1
INITIAL_LIVES = 8

# Global menu instance
menu = None

def run_game():
    """Main game loop"""
    # Create game objects
    pacman = Pacman()
    
    # Create Ghosts
    red_ghost = Ghost(color=(255, 0, 0), pacman=pacman, speed=GHOST_SPEED, 
                     spawn_values={5}, sprite_variant="red", behavior="blinky")
    blue_ghost = Ghost(color=(0, 0, 255), pacman=pacman, speed=GHOST_SPEED, 
                      spawn_values={6}, sprite_variant="blue", behavior="inky", partner=red_ghost)
    orenge_ghost = Ghost(color=(255, 165, 0), pacman=pacman, speed=GHOST_SPEED, 
                        spawn_values={7}, sprite_variant="orenge", behavior="clyde")
    pink_ghost = Ghost(color=(255, 105, 180), pacman=pacman, speed=GHOST_SPEED, 
                      spawn_values={8}, sprite_variant="pink", behavior="pinky")
    
    ghosts = [red_ghost, blue_ghost, orenge_ghost, pink_ghost]
    
    # Level/Lives system
    level = LevelSystem(initial_lives=INITIAL_LIVES)
    
    # Game loop
    clock = pygame.time.Clock()
    game_running = True
    
    while game_running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            # Handle ESC key for pause menu
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    action = menu.show_in_game_menu(pacman.pallet_count)
                    if action == "CONTINUE":
                        continue
                    elif action == "NEW_GAME":
                        # Start a new game immediately
                        reset_maze()
                        return "NEW_GAME"  # This tells main to start a new game
                    elif action == "LOGOUT":
                        return "LOGOUT"
            
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
            
            # After movement/collisions, check level completion and handle restart/speed-up
            level.check_level_completion(pacman, ghosts)
        
        # Draw everything
        draw_smooth_map()
        pacman.draw()
        for g in ghosts:
            g.draw()
        level.draw_lives()
        level.draw_level_title()
        
        # If game over, draw overlay message on top
        if level.is_game_over():
            level.draw_game_over()
            pygame.display.flip()
            # Show game over menu
            action = menu.show_game_over_menu(pacman.pallet_count)
            if action == "NEW_GAME":
                return "NEW_GAME"
            elif action == "LOGOUT":
                return "LOGOUT"
            # If user clicked High Score in game over menu, it's handled within the menu
        
        # Update display
        pygame.display.flip()
        
        # Limit frame rate to 60 FPS
        clock.tick(60)

def main():
    """Main application loop"""
    global menu
    
    # Initialize pygame
    pygame.init()
    
    # Initialize menu with current screen
    menu = Menu(screen)
    
    while True:
        # Show menu and get action
        action = menu.run()
        
        if action == "START_GAME" or action == "NEW_GAME":
            print("Starting new game...")
            # Reset maze before starting new game
            reset_maze()
            # Start the game
            while True:
                game_result = run_game()
                
                if game_result == "LOGOUT":
                    # User logged out from in-game menu
                    print("User logged out from game")
                    menu.username = ""
                    menu.state = "MAIN"
                    break
                elif game_result == "NEW_GAME":
                    # User wants new game from pause menu or game over
                    print("Starting new game")
                    reset_maze()
                    continue  # Continue with new game
        
        elif action == "LOGOUT":
            print("User logged out from menu")
            menu.username = ""
            menu.state = "MAIN"

if __name__ == "__main__":
    main()