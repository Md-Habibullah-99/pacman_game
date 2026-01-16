import pygame
from sys import exit
from maze import draw_smooth_map, MAP_DATA, reset_maze
from pacman import Pacman
from ghost import Ghost
from lavel_system import LevelSystem
from menu import MenuSystem

# Config variables
GHOST_SPEED = 1.1
INITIAL_LIVES = 8

# Initialize pygame
pygame.init()
clock = pygame.time.Clock()

# Create Menu System
menu = MenuSystem()

# Game objects (will be initialized when game starts)
pacman = None
ghosts = []
level = None

# Sound control variables
pellet_sound_cooldown = 0
POWER_PELLET_SOUND_COOLDOWN = 30  # frames between power pellet sounds

def load_maze(level_num):
    """Load a specific maze level from JSON"""
    import json
    import os
    
    maze_file_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "data", "maze.json")
    )
    
    try:
        with open(maze_file_path, "r", encoding="utf-8") as f:
            maze_data = json.load(f)
        
        level_key = str(level_num)
        if level_key in maze_data:
            # Update MAP_DATA in maze module
            from maze import MAP_DATA, ORIGINAL_MAP_DATA
            
            # Get the map for the selected level
            map01 = maze_data[level_key]["map"]
            new_map_data = [[int(j) for j in i] for i in map01]
            
            # Replace the current map data
            for y in range(len(MAP_DATA)):
                for x in range(len(MAP_DATA[0])):
                    MAP_DATA[y][x] = new_map_data[y][x]
            
            # Also update the original data for reset functionality
            for y in range(len(ORIGINAL_MAP_DATA)):
                ORIGINAL_MAP_DATA[y] = new_map_data[y].copy()
            
            return True
        else:
            print(f"Level {level_num} not found in maze.json")
            return False
            
    except Exception as e:
        print(f"Error loading maze: {e}")
        return False

def reset_game(continue_game=False):
    """Reset the game with current level selection"""
    global pacman, ghosts, level, pellet_sound_cooldown
    
    # Reset sound cooldown
    pellet_sound_cooldown = 0
    
    # Load the selected maze
    if not load_maze(menu.selected_level):
        # Fallback to level 1 if selected level doesn't exist
        menu.selected_level = 1
        load_maze(1)
    
    # Create Pacman
    pacman = Pacman()
    
    # Create Ghosts
    red_ghost = Ghost(color=(255, 0, 0), pacman=pacman, speed=GHOST_SPEED, spawn_values={5}, sprite_variant="red", behavior="blinky", sound_callback=menu.play_sound)
    blue_ghost = Ghost(color=(0, 0, 255), pacman=pacman, speed=GHOST_SPEED, spawn_values={6}, sprite_variant="blue", behavior="inky", partner=red_ghost, sound_callback=menu.play_sound)
    orenge_ghost = Ghost(color=(255, 165, 0), pacman=pacman, speed=GHOST_SPEED, spawn_values={7}, sprite_variant="orenge", behavior="clyde", sound_callback=menu.play_sound)
    pink_ghost = Ghost(color=(255, 105, 180), pacman=pacman, speed=GHOST_SPEED, spawn_values={8}, sprite_variant="pink", behavior="pinky", sound_callback=menu.play_sound)
    
    ghosts = [red_ghost, blue_ghost, orenge_ghost, pink_ghost]
    
    # Level/Lives system
    level = LevelSystem(initial_lives=INITIAL_LIVES)
    
    # If continuing, load saved game state
    if continue_game:
        saved_state = menu.load_game_state()
        if saved_state and saved_state.get("user") == menu.current_user:
            level.level = saved_state.get("level", 1)
            level.lives = saved_state.get("lives", INITIAL_LIVES)
            pacman.pallet_count = saved_state.get("score", 0)
            menu.selected_level = saved_state.get("selected_level", 1)
            # Reload maze with saved level
            load_maze(menu.selected_level)

# Main game loop
while True:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        
        # Handle menu/game input
        needs_reset = menu.handle_input(event)
        
        if needs_reset:
            # Check if we're continuing a saved game
            continue_game = (menu.current_state == "playing" and 
                           menu.get_main_menu_items()[menu.main_selection] == "Continue")
            reset_game(continue_game=continue_game)
        elif menu.current_state == "playing":
            # Handle Pacman input and pause
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # Pause game - handled in menu.handle_input
                pass
            else:
                # Only handle Pacman input if game is not paused
                if pacman and level and not level.is_game_over() and not menu.game_paused:
                    pacman.handle_input(event)
    
    # Update sound cooldown
    if pellet_sound_cooldown > 0:
        pellet_sound_cooldown -= 1
    
    # Clear screen
    screen = draw_smooth_map()
    
    # Update and draw based on current state
    if menu.current_state == "playing" and pacman and level:
        # Play game start sound only once when game begins
        if not menu.game_start_sound_played:
            menu.play_sound("game_start")
            menu.game_start_sound_played = True
        
        # Only update gameplay if not game over and not paused
        if not level.is_game_over() and not menu.game_paused:
            # Save current pellet count to detect changes
            previous_pellet_count = pacman.pallet_count
            
            # Update Pacman first
            try:
                pacman.update()
            except Exception as e:
                print(f"Error updating Pacman: {e}")
                import traceback
                traceback.print_exc()
            
            # Check if Pacman ate pellets
            if pacman.pallet_count > previous_pellet_count:
                # Determine if it was a power pellet
                pellet_increase = pacman.pallet_count - previous_pellet_count
                
                if pellet_increase == 50:  # Power pellet
                    # Only play power pellet sound if cooldown is 0
                    if pellet_sound_cooldown == 0:
                        menu.play_sound("eat_power")
                        pellet_sound_cooldown = POWER_PELLET_SOUND_COOLDOWN
                    
                    # Set last_ate_power for ghost scatter mode
                    pacman.last_ate_power = True
                    
                    # Enter scatter mode for ghosts
                    for g in ghosts:
                        if hasattr(g, 'enter_scatter_mode'):
                            g.enter_scatter_mode()
                    pacman.last_ate_power = False
                else:  # Regular pellet
                    # Play pellet sound with cooldown
                    if pellet_sound_cooldown == 0:
                        menu.play_sound("eat_pellet")
                        pellet_sound_cooldown = 5  # Small cooldown for regular pellets
            
            # Then update ghosts and check collisions
            for g in ghosts:
                try:
                    g.update()
                except Exception as e:
                    print(f"Error updating ghost: {e}")
                    # Continue with other ghosts instead of crashing
                    continue
            
            prev_lives = level.get_lives()
            for g in ghosts:
                try:
                    level.check_collision_and_reset(pacman, g)
                except Exception as e:
                    print(f"Error checking collision with ghost: {e}")
                    # Continue with other ghosts instead of crashing
                    continue
                if level.is_game_over():
                    # Play game over sound
                    menu.play_sound("game_over")
                    menu.stop_music()
                    break
                if level.get_lives() < prev_lives:
                    # life lost: reset all ghosts to spawn to avoid instant re-collision
                    for gg in ghosts:
                        if hasattr(gg, 'reset_to_spawn'):
                            gg.reset_to_spawn()
                    # Play death sound
                    menu.play_sound("game_over")
                    break

            # After movement/collisions, check level completion and handle restart/speed-up
            level.check_level_completion(pacman, ghosts)
        
        # Draw game elements (always draw even when paused)
        pacman.draw()
        for g in ghosts:
            g.draw()
        level.draw_lives()
        # Draw level title at (120, 0)
        level.draw_level_title()
        
        # Check if game over
        if level.is_game_over():
            menu.current_state = "game_over"
            menu.game_paused = False
            menu.update_music_for_state()
        
        # Draw menu overlay if paused
        if menu.game_paused:
            menu.draw(pacman.pallet_count if pacman else 0)
        
        # Save game state for continue option
        if pacman and level and menu.current_user and not menu.game_paused:
            menu.save_game_state(pacman, level, ghosts)
    
    else:
        # Draw menu system
        menu.draw(pacman.pallet_count if pacman else 0)
    
    # Update display
    pygame.display.flip()
    
    # Limit frame rate to 60 FPS
    clock.tick(60)