import pygame
import json
import os
import sys
from maze import screen, SCREEN_WIDTH, SCREEN_HEIGHT, draw_smooth_map

class MenuSystem:
    def __init__(self):
        self.current_state = "login"  # login, signup, main_menu, playing, paused, game_over, highscore
        self.current_user = None
        self.selected_level = 1
        self.high_scores = self.load_high_scores()
        self.users = self.load_users()
        self.current_score = 0
        self.music_enabled = True
        self.sound_enabled = True
        self.game_paused = False  # Track if game is paused
        self.game_over_score_saved = False  # Track if score saved on game over
        self.game_start_sound_played = False  # Track if game start sound played
        
        # Load settings first
        self.load_settings()
        
        # Input fields for login/signup
        self.username_input = ""
        self.password_input = ""
        self.active_field = "username"  # username or password
        self.login_focus = 0  # 0: username, 1: password, 2: Login, 3: Sign Up, 4: Exit
        self.signup_focus = 0  # 0: username, 1: password, 2: Register
        self.error_message = ""
        self.success_message = ""
        self.cursor_animation = 0  # For cursor jumping animation
        
        # Colors
        self.title_color = (255, 255, 0)  # Yellow
        self.menu_color = (255, 255, 255)  # White
        self.selected_color = (0, 255, 255)  # Cyan
        self.input_color = (200, 200, 255)  # Light blue
        self.error_color = (255, 100, 100)  # Red
        self.success_color = (100, 255, 100)  # Green
        
        # Fonts
        self.title_font = None
        self.menu_font = None
        self.input_font = None
        self.score_font = None
        self._init_fonts()
        
        # Menu positions - FIXED: Only one "New Game" option
        self.login_items = ["Login", "Sign Up", "Exit"]
        self.game_over_items = ["Play Again", "Main Menu", "Highscore", "Logout"]
        
        # Selection indexes
        self.login_selection = 0
        self.main_selection = 0
        self.game_over_selection = 0
        self.pause_selection = 0  # Separate selection for pause menu
        
        # Load sounds using your actual sound files
        self.sounds = {}
        self._load_sounds()
        
        # Initialize data files
        self._init_data_files()
        
        # Load music but don't start it yet
        self._load_music()
        
        # Saved game state
        self.saved_game = None
        
    def _init_fonts(self):
        """Initialize fonts for the menu"""
        try:
            if not pygame.font.get_init():
                pygame.font.init()
            
            # Try to load custom font
            font_path = os.path.normpath(
                os.path.join(os.path.dirname(__file__), "fonts", "CascadiaCode-VariableFont_wght.ttf")
            )
            
            if os.path.exists(font_path):
                self.title_font = pygame.font.Font(font_path, 72)
                self.menu_font = pygame.font.Font(font_path, 36)
                self.input_font = pygame.font.Font(font_path, 32)
                self.score_font = pygame.font.Font(font_path, 24)
                self.small_font = pygame.font.Font(font_path, 20)  # For error messages
            else:
                # Fallback to system fonts
                self.title_font = pygame.font.SysFont("arial", 72, bold=True)
                self.menu_font = pygame.font.SysFont("arial", 36)
                self.input_font = pygame.font.SysFont("arial", 32)
                self.score_font = pygame.font.SysFont("arial", 24)
                self.small_font = pygame.font.SysFont("arial", 20)
                
        except Exception as e:
            print(f"Failed to load fonts: {e}")
            # Last resort - create default fonts
            self.title_font = pygame.font.Font(None, 72)
            self.menu_font = pygame.font.Font(None, 36)
            self.input_font = pygame.font.Font(None, 32)
            self.score_font = pygame.font.Font(None, 24)
            self.small_font = pygame.font.Font(None, 20)
    
    def _init_data_files(self):
        """Initialize required data files if they don't exist"""
        data_dir = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "data")
        )
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Create user.json if it doesn't exist
        user_file = os.path.join(data_dir, "user.json")
        if not os.path.exists(user_file):
            with open(user_file, 'w') as f:
                json.dump([], f, indent=2)
    
    def _load_sounds(self):
        """Load sound effects using your actual sound files"""
        try:
            sound_dir = os.path.normpath(
                os.path.join(os.path.dirname(__file__), "..", "assets", "sounds")
            )
            
            if os.path.exists(sound_dir):
                # Initialize pygame mixer if not already
                if pygame.mixer.get_init() is None:
                    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                
                # Map our sound names to your actual files
                sound_files = {
                    "menu_select": "mouse-click-153941.mp3",
                    "menu_confirm": "pacman_beginning.wav",
                    "game_start": "pacman_beginning.wav",
                    "game_over": "pacman_death.wav",
                    "eat_pellet": "pacman_chomp.wav",
                    "eat_power": "pacman_eatfruit.wav",
                    "eat_ghost": "pacman_eatghost.wav"
                }
                
                for key, filename in sound_files.items():
                    filepath = os.path.join(sound_dir, filename)
                    if os.path.exists(filepath):
                        try:
                            self.sounds[key] = pygame.mixer.Sound(filepath)
                            self.sounds[key].set_volume(0.5)
                        except Exception as e:
                            print(f"Could not load sound {filename}: {e}")
                    else:
                        print(f"Sound file not found: {filepath}")
                        
        except Exception as e:
            print(f"Could not load sounds: {e}")
    
    def _load_music(self):
        """Load background music"""
        try:
            music_dir = os.path.normpath(
                os.path.join(os.path.dirname(__file__), "..", "assets", "music")
            )
            
            if os.path.exists(music_dir):
                music_file = os.path.join(music_dir, "pacman_intermission.wav")
                if os.path.exists(music_file):
                    try:
                        pygame.mixer.music.load(music_file)
                        pygame.mixer.music.set_volume(0.3)
                    except Exception as e:
                        print(f"Could not load music: {e}")
                else:
                    print(f"Music file not found: {music_file}")
                    
        except Exception as e:
            print(f"Could not load music: {e}")
    
    def play_sound(self, sound_name):
        """Play a sound effect if enabled"""
        if self.sound_enabled and sound_name in self.sounds:
            try:
                # Stop any previous instance of this sound to avoid overlap
                self.sounds[sound_name].stop()
                self.sounds[sound_name].play()
            except:
                pass
    
    def start_music(self):
        """Start background music if not already playing and music is enabled"""
        if self.music_enabled and not pygame.mixer.music.get_busy():
            try:
                pygame.mixer.music.play(-1)  # Loop indefinitely
            except:
                pass
    
    def stop_music(self):
        """Stop background music"""
        try:
            pygame.mixer.music.stop()
        except:
            pass
    
    def update_music_for_state(self):
        """Update music based on current state and music_enabled flag"""
        if self.music_enabled and self.current_state in ["login", "signup", "main_menu", "paused"]:
            self.start_music()
        else:
            self.stop_music()
    
    def toggle_music(self):
        """Toggle music on/off"""
        self.music_enabled = not self.music_enabled
        if self.music_enabled:
            self.update_music_for_state()
        else:
            self.stop_music()
        self.save_settings()
        # Update main menu items text
        self.get_main_menu_items()
    
    def toggle_sound(self):
        """Toggle sound on/off"""
        self.sound_enabled = not self.sound_enabled
        self.save_settings()
        # Update main menu items text
        self.get_main_menu_items()
    
    def get_main_menu_items(self):
        """Get the main menu items based on current state"""
        items = []
        
        # Always show New Game
        items.append("New Game")
        
        # Show Continue only if there's a saved game for current user
        if self.saved_game and self.saved_game.get("user") == self.current_user:
            items.insert(0, "Continue")
        
        # Add settings and other options
        items.append(f"Music: {'ON' if self.music_enabled else 'OFF'}")
        items.append(f"Sound: {'ON' if self.sound_enabled else 'OFF'}")
        items.append("Highscore")
        items.append("Logout")
        
        return items
    
    def load_users(self):
        """Load users from JSON file"""
        users_file = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "data", "user.json")
        )
        
        try:
            if os.path.exists(users_file):
                with open(users_file, 'r') as f:
                    return json.load(f)
            else:
                return []
        except Exception as e:
            print(f"Error loading users: {e}")
            return []
    
    def save_users(self):
        """Save users to JSON file"""
        users_file = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "data", "user.json")
        )
        
        try:
            with open(users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            print(f"Error saving users: {e}")
    
    def load_high_scores(self):
        """Load high scores from JSON file"""
        scores_file = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "data", "score.json")
        )
        
        try:
            if os.path.exists(scores_file):
                with open(scores_file, 'r') as f:
                    scores = json.load(f)
                    # Ensure scores is a list
                    if isinstance(scores, dict):
                        # Convert old format to new format
                        new_scores = []
                        for level_str, entries in scores.items():
                            if isinstance(entries, list):
                                for entry in entries:
                                    entry["level"] = int(level_str)
                                    new_scores.append(entry)
                        return new_scores
                    return scores
            else:
                return []
        except Exception as e:
            print(f"Error loading scores: {e}")
            return []
    
    def save_high_scores(self):
        """Save high scores to JSON file"""
        scores_file = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "data", "score.json")
        )
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(scores_file), exist_ok=True)
            
            with open(scores_file, 'w') as f:
                json.dump(self.high_scores, f, indent=2)
        except Exception as e:
            print(f"Error saving scores: {e}")
    
    def load_settings(self):
        """Load user settings"""
        settings_file = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "data", "settings.json")
        )
        
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    self.music_enabled = settings.get("music_enabled", True)
                    self.sound_enabled = settings.get("sound_enabled", True)
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save user settings"""
        settings_file = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "data", "settings.json")
        )
        
        try:
            settings = {
                "music_enabled": self.music_enabled,
                "sound_enabled": self.sound_enabled
            }
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def save_game_state(self, pacman, level, ghosts):
        """Save current game state for continue option"""
        if not self.current_user:
            return
        
        try:
            self.saved_game = {
                "user": self.current_user,
                "level": level.level if hasattr(level, 'level') else 1,
                "score": pacman.pallet_count if hasattr(pacman, 'pallet_count') else 0,
                "lives": level.lives if hasattr(level, 'lives') else 3,
                "selected_level": self.selected_level
            }
        except:
            self.saved_game = None
    
    def load_game_state(self):
        """Load saved game state"""
        return self.saved_game
    
    def clear_saved_game(self):
        """Clear saved game state"""
        self.saved_game = None
    
    def check_username_exists(self, username):
        """Check if username already exists"""
        for user in self.users:
            if user["username"] == username:
                return True
        return False
    
    def register_user(self, username, password):
        """Register a new user"""
        # Check if username already exists
        if self.check_username_exists(username):
            return False, "Username already exists"
        
        # Add new user
        new_user = {
            "username": username,
            "password": password
        }
        self.users.append(new_user)
        self.save_users()
        return True, "Registration successful!"
    
    def login_user(self, username, password):
        """Login existing user"""
        for user in self.users:
            if user["username"] == username and user["password"] == password:
                self.current_user = username
                self.load_settings()
                return True, "Login successful!"
        return False, "Invalid username or password"
    
    def logout(self):
        """Logout current user"""
        self.current_user = None
        self.current_state = "login"
        self.stop_music()
        self.clear_saved_game()
        self.reset_inputs()
        self.game_over_score_saved = False
    
    def reset_inputs(self):
        """Reset input fields"""
        self.username_input = ""
        self.password_input = ""
        self.active_field = "username"
        self.error_message = ""
        self.success_message = ""
    
    def update_score(self, score, level):
        """Update user's high score if current score is higher"""
        if not self.current_user:
            return
        
        # Convert level to int for consistency
        level_int = int(level)
        
        # Find existing score for this user and level
        user_found = False
        for i, entry in enumerate(self.high_scores):
            if entry["user"] == self.current_user and entry["level"] == level_int:
                user_found = True
                if score > entry["score"]:
                    self.high_scores[i]["score"] = score
                    self.high_scores[i]["date"] = self.get_current_date()
                break
        
        # If user doesn't have a score for this level, add new entry
        if not user_found:
            new_entry = {
                "user": self.current_user,
                "score": score,
                "level": level_int,
                "date": self.get_current_date()
            }
            self.high_scores.append(new_entry)
        
        # Sort scores by level and then by score (descending)
        self.high_scores.sort(key=lambda x: (x["level"], -x["score"]))
        self.save_high_scores()
        return True
    
    def get_current_date(self):
        """Get current date as string (simple version)"""
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d")
    
    def get_high_scores_by_level(self, level):
        """Get high scores for a specific level"""
        level_int = int(level)
        level_scores = []
        for entry in self.high_scores:
            if entry["level"] == level_int:
                level_scores.append(entry)
        
        # Sort by score descending
        level_scores.sort(key=lambda x: x["score"], reverse=True)
        return level_scores[:10]  # Top 10 scores
    
    def handle_input(self, event):
        """Handle input events for all menus"""
        if event.type == pygame.KEYDOWN:
            
            if self.current_state == "login":
                return self.handle_login_input(event)
                
            elif self.current_state == "signup":
                return self.handle_signup_input(event)
                
            elif self.current_state == "main_menu":
                return self.handle_main_menu_input(event)
                
            elif self.current_state == "playing":
                if event.key == pygame.K_ESCAPE:
                    # Pause the game
                    self.game_paused = True
                    self.current_state = "paused"
                    self.update_music_for_state()
                    self.play_sound("menu_select")
                    return False  # Don't reset game, just pause
                    
            elif self.current_state == "paused":
                return self.handle_pause_input(event)
                
            elif self.current_state == "game_over":
                return self.handle_game_over_input(event)
                
            elif self.current_state == "highscore":
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                    if self.current_user:
                        self.current_state = "main_menu"
                    else:
                        self.current_state = "login"
                    self.play_sound("menu_select")
        
        return False  # No state change that requires game reset
    
    def handle_login_input(self, event):
        """Handle input on login screen"""
        if event.key == pygame.K_TAB:
            # Switch between all interactive elements: username -> password -> Login -> Sign Up -> Exit -> username
            self.login_focus = (self.login_focus + 1) % 5
            if self.login_focus < 2:
                self.active_field = "username" if self.login_focus == 0 else "password"
            self.play_sound("menu_select")
            
        elif event.key == pygame.K_UP:
            # Navigate upward through all elements
            self.login_focus = (self.login_focus - 1) % 5
            if self.login_focus < 2:
                self.active_field = "username" if self.login_focus == 0 else "password"
            self.play_sound("menu_select")
            
        elif event.key == pygame.K_DOWN:
            # Navigate downward through all elements
            self.login_focus = (self.login_focus + 1) % 5
            if self.login_focus < 2:
                self.active_field = "username" if self.login_focus == 0 else "password"
            self.play_sound("menu_select")
            
        elif event.key == pygame.K_RETURN:
            # Handle selection based on which element is focused
            if self.login_focus == 2:
                # Login button
                success, message = self.login_user(self.username_input, self.password_input)
                if success:
                    self.current_state = "main_menu"
                    self.success_message = message
                    self.play_sound("menu_confirm")
                    self.update_music_for_state()
                else:
                    self.error_message = message
                    self.play_sound("menu_select")
                    
            elif self.login_focus == 3:
                # Sign Up button
                self.current_state = "signup"
                self.reset_inputs()
                self.signup_focus = 0
                self.update_music_for_state()
                self.play_sound("menu_confirm")
                
            elif self.login_focus == 4:
                # Exit button
                pygame.quit()
                sys.exit()
            else:
                # Username or password field - just focus it for input
                self.active_field = "username" if self.login_focus == 0 else "password"
            
        elif event.key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit()
            
        elif event.key == pygame.K_BACKSPACE:
            # Only allow backspace in input fields
            if self.login_focus == 0 or self.login_focus == 1:
                if self.login_focus == 0:
                    self.username_input = self.username_input[:-1]
                else:
                    self.password_input = self.password_input[:-1]
                # Clear error message when user types
                self.error_message = ""
                self.success_message = ""
                
        elif event.unicode and (event.unicode.isalnum() or event.unicode in ['_', '-', '.']):
            # Handle text input - only in input fields
            if self.login_focus == 0:
                if len(self.username_input) < 15:
                    self.username_input += event.unicode
                # Clear error message when user types
                self.error_message = ""
                self.success_message = ""
            elif self.login_focus == 1:
                if len(self.password_input) < 15:
                    self.password_input += event.unicode
                # Clear error message when user types
                self.error_message = ""
                self.success_message = ""
        
        return False
    
    def handle_signup_input(self, event):
        """Handle input on signup screen"""
        if event.key == pygame.K_TAB:
            # Switch between username, password, and register button
            self.signup_focus = (self.signup_focus + 1) % 3
            if self.signup_focus < 2:
                self.active_field = "username" if self.signup_focus == 0 else "password"
            self.play_sound("menu_select")
            
        elif event.key == pygame.K_UP:
            # Navigate upward
            self.signup_focus = (self.signup_focus - 1) % 3
            if self.signup_focus < 2:
                self.active_field = "username" if self.signup_focus == 0 else "password"
            self.play_sound("menu_select")
            
        elif event.key == pygame.K_DOWN:
            # Navigate downward
            self.signup_focus = (self.signup_focus + 1) % 3
            if self.signup_focus < 2:
                self.active_field = "username" if self.signup_focus == 0 else "password"
            self.play_sound("menu_select")
            
        elif event.key == pygame.K_RETURN:
            if self.signup_focus == 2:
                # Try to register
                if len(self.username_input) < 3:
                    self.error_message = "Username must be at least 3 characters"
                    self.play_sound("menu_select")
                elif len(self.password_input) < 3:
                    self.error_message = "Password must be at least 3 characters"
                    self.play_sound("menu_select")
                else:
                    # Check if username already exists
                    if self.check_username_exists(self.username_input):
                        self.error_message = "Username already exists"
                        self.play_sound("menu_select")
                    else:
                        success, message = self.register_user(self.username_input, self.password_input)
                        if success:
                            self.success_message = message
                            # Auto login after successful registration
                            self.login_user(self.username_input, self.password_input)
                            self.current_state = "main_menu"
                            self.update_music_for_state()
                            self.play_sound("menu_confirm")
                            return True
                        else:
                            self.error_message = message
                            self.play_sound("menu_select")
            else:
                # Focus on input field
                self.active_field = "username" if self.signup_focus == 0 else "password"
                
        elif event.key == pygame.K_ESCAPE:
            self.current_state = "login"
            self.reset_inputs()
            self.login_focus = 0
            self.update_music_for_state()
            self.play_sound("menu_select")
            
        elif event.key == pygame.K_BACKSPACE:
            # Only allow backspace in input fields
            if self.signup_focus == 0 or self.signup_focus == 1:
                if self.signup_focus == 0:
                    self.username_input = self.username_input[:-1]
                else:
                    self.password_input = self.password_input[:-1]
                # Clear error message when user types
                self.error_message = ""
                self.success_message = ""
                
        elif event.unicode and (event.unicode.isalnum() or event.unicode in ['_', '-', '.']):
            # Handle text input - only in input fields
            if self.signup_focus == 0:
                if len(self.username_input) < 15:
                    self.username_input += event.unicode
                # Clear error message when user types
                self.error_message = ""
                self.success_message = ""
            elif self.signup_focus == 1:
                if len(self.password_input) < 15:
                    self.password_input += event.unicode
                # Clear error message when user types
                self.error_message = ""
                self.success_message = ""
        
        return False
    
    def handle_main_menu_input(self, event):
        """Handle input on main menu"""
        main_items = self.get_main_menu_items()
        
        if event.key == pygame.K_UP:
            self.main_selection = (self.main_selection - 1) % len(main_items)
            self.play_sound("menu_select")
            
        elif event.key == pygame.K_DOWN:
            self.main_selection = (self.main_selection + 1) % len(main_items)
            self.play_sound("menu_select")
            
        elif event.key == pygame.K_RETURN:
            self.play_sound("menu_confirm")
            return self.handle_main_menu_selection()
            
        elif event.key == pygame.K_ESCAPE:
            self.logout()
            self.play_sound("menu_select")
        
        return False
    
    def handle_pause_input(self, event):
        """Handle input on pause screen"""
        pause_items = ["Resume", "New Game", "Main Menu", "Logout"]
        
        if event.key == pygame.K_UP:
            self.pause_selection = (self.pause_selection - 1) % len(pause_items)
            self.play_sound("menu_select")
            
        elif event.key == pygame.K_DOWN:
            self.pause_selection = (self.pause_selection + 1) % len(pause_items)
            self.play_sound("menu_select")
            
        elif event.key == pygame.K_RETURN:
            self.play_sound("menu_confirm")
            return self.handle_pause_selection()
            
        elif event.key == pygame.K_ESCAPE:
            # Resume game when ESC is pressed in pause menu
            self.current_state = "playing"
            self.game_paused = False
            self.update_music_for_state()
            self.play_sound("menu_select")
        
        return False
    
    def handle_game_over_input(self, event):
        """Handle input on game over screen"""
        if event.key == pygame.K_UP:
            self.game_over_selection = (self.game_over_selection - 1) % len(self.game_over_items)
            self.play_sound("menu_select")
            
        elif event.key == pygame.K_DOWN:
            self.game_over_selection = (self.game_over_selection + 1) % len(self.game_over_items)
            self.play_sound("menu_select")
            
        elif event.key == pygame.K_RETURN:
            self.play_sound("menu_confirm")
            return self.handle_game_over_selection()
            
        elif event.key == pygame.K_ESCAPE:
            self.current_state = "main_menu"
            self.game_over_score_saved = False
            self.update_music_for_state()
            self.play_sound("menu_select")
        
        return False
    
    def handle_main_menu_selection(self):
        """Handle selection in main menu"""
        main_items = self.get_main_menu_items()
        selection = main_items[self.main_selection]
        
        if selection == "Continue":
            self.current_state = "playing"
            self.game_paused = False
            self.game_start_sound_played = False  # Reset for new game session
            # Don't play game_start here - it will be played once in main game loop
            return True  # Signal to reset game with continue
            
        elif selection == "New Game":
            self.current_state = "playing"
            self.game_paused = False
            self.clear_saved_game()
            self.game_start_sound_played = False  # Reset for new game session
            # Don't play game_start here - it will be played once in main game loop
            return True  # Signal to reset game with new game
            
        elif selection.startswith("Music:"):
            self.toggle_music()
            return False
            
        elif selection.startswith("Sound:"):
            self.toggle_sound()
            return False
            
        elif selection == "Highscore":
            self.current_state = "highscore"
            return False
            
        elif selection == "Logout":
            self.logout()
            return False
            
        return False
    
    def handle_pause_selection(self):
        """Handle selection in pause menu"""
        if self.pause_selection == 0:  # Resume
            self.current_state = "playing"
            self.game_paused = False
            self.update_music_for_state()
            self.pause_selection = 0  # Reset for next pause
            return False
            
        elif self.pause_selection == 1:  # New Game
            self.current_state = "playing"
            self.game_paused = False
            self.clear_saved_game()
            self.update_music_for_state()
            self.pause_selection = 0  # Reset for next pause
            return True
            
        elif self.pause_selection == 2:  # Main Menu
            self.current_state = "main_menu"
            self.game_paused = False
            self.clear_saved_game()  # Clear saved game when going to main menu
            self.update_music_for_state()
            self.pause_selection = 0  # Reset for next pause
            return False
            
        elif self.pause_selection == 3:  # Logout
            self.logout()
            self.pause_selection = 0  # Reset for next pause
            return False
            
        return False
    
    def handle_game_over_selection(self):
        """Handle selection in game over menu"""
        selection = self.game_over_items[self.game_over_selection]
        
        if selection == "Play Again":
            self.current_state = "playing"
            self.game_paused = False
            self.game_over_score_saved = False
            self.update_music_for_state()
            self.play_sound("game_start")
            return True
            
        elif selection == "Main Menu":
            self.current_state = "main_menu"
            self.game_paused = False
            self.game_over_score_saved = False
            self.update_music_for_state()
            return False
            
        elif selection == "Highscore":
            self.current_state = "highscore"
            self.game_paused = False
            self.game_over_score_saved = False
            self.update_music_for_state()
            return False
            
        elif selection == "Logout":
            self.logout()
            self.game_over_score_saved = False
            return False
            
        return False
    
    def draw(self, current_score=0):
        """Draw the current menu/game state"""
        self.current_score = current_score
        
        # Update cursor animation
        self.cursor_animation = (self.cursor_animation + 1) % 20
        
        if self.current_state == "login":
            self.draw_login_screen()
        elif self.current_state == "signup":
            self.draw_signup_screen()
        elif self.current_state == "main_menu":
            self.draw_main_menu()
        elif self.current_state == "paused":
            self.draw_pause_screen()
        elif self.current_state == "game_over":
            self.draw_game_over_screen()
        elif self.current_state == "highscore":
            self.draw_highscore_screen()
        # For "playing" state, nothing is drawn (game draws itself)
    
    def draw_login_screen(self):
        """Draw the login screen"""
        # Draw maze background
        draw_smooth_map()
        
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # Title
        title = self.title_font.render("PAC-MAN LOGIN", True, self.title_color)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 6))
        screen.blit(title, title_rect)
        
        # Username field
        username_label = self.menu_font.render("Username:", True, self.menu_color)
        username_label_rect = username_label.get_rect(midright=(SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 3))
        screen.blit(username_label, username_label_rect)
        
        # Username input box
        username_box = pygame.Rect(SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT // 3 - 25, 300, 50)
        # Highlight with animated cursor if focused
        box_color = self.selected_color if self.login_focus == 0 else self.menu_color
        pygame.draw.rect(screen, box_color, username_box, 3 if self.login_focus == 0 else 2)
        
        username_text = self.input_font.render(self.username_input, True, self.menu_color)
        username_text_rect = username_text.get_rect(midleft=(username_box.left + 10, username_box.centery))
        screen.blit(username_text, username_text_rect)
        
        # Draw cursor animation if username is focused
        if self.login_focus == 0 and self.cursor_animation < 10:
            cursor_rect = pygame.Rect(username_text_rect.right + 5, username_box.centery - 15, 2, 30)
            pygame.draw.rect(screen, self.selected_color, cursor_rect)
        
        # Password field
        password_label = self.menu_font.render("Password:", True, self.menu_color)
        password_label_rect = password_label.get_rect(midright=(SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 2))
        screen.blit(password_label, password_label_rect)
        
        # Password input box
        password_box = pygame.Rect(SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT // 2 - 25, 300, 50)
        # Highlight with animated cursor if focused
        box_color = self.selected_color if self.login_focus == 1 else self.menu_color
        pygame.draw.rect(screen, box_color, password_box, 3 if self.login_focus == 1 else 2)
        
        # Show password as asterisks
        password_display = "*" * len(self.password_input)
        password_text = self.input_font.render(password_display, True, self.menu_color)
        password_text_rect = password_text.get_rect(midleft=(password_box.left + 10, password_box.centery))
        screen.blit(password_text, password_text_rect)
        
        # Draw cursor animation if password is focused
        if self.login_focus == 1 and self.cursor_animation < 10:
            cursor_rect = pygame.Rect(password_text_rect.right + 5, password_box.centery - 15, 2, 30)
            pygame.draw.rect(screen, self.selected_color, cursor_rect)
        
        # Error/Success message
        if self.error_message:
            error_text = self.small_font.render(self.error_message, True, self.error_color)
            error_rect = error_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70))
            screen.blit(error_text, error_rect)
        
        if self.success_message:
            success_text = self.small_font.render(self.success_message, True, self.success_color)
            success_rect = success_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70))
            screen.blit(success_text, success_rect)
        
        # Menu items
        menu_items = ["Login", "Sign Up", "Exit"]
        for i, item in enumerate(menu_items):
            focus_index = i + 2  # Menu items start at focus index 2
            color = self.selected_color if self.login_focus == focus_index else self.menu_color
            text = self.menu_font.render(item, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120 + i * 60))
            screen.blit(text, text_rect)
            
            # Draw animated arrow for selected item
            if self.login_focus == focus_index:
                if self.cursor_animation < 10:
                    arrow = self.menu_font.render(">", True, self.selected_color)
                    screen.blit(arrow, (text_rect.left - 50, text_rect.top))
                    arrow = self.menu_font.render("<", True, self.selected_color)
                    screen.blit(arrow, (text_rect.right + 30, text_rect.top))
        
        # Instructions
        inst1 = self.score_font.render("UP/DOWN: Navigate, TAB: Switch, ENTER: Select", True, (200, 200, 200))
        inst1_rect = inst1.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
        screen.blit(inst1, inst1_rect)
        
        inst2 = self.score_font.render("ESC: Exit game", True, (200, 200, 200))
        inst2_rect = inst2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
        screen.blit(inst2, inst2_rect)
    
    def draw_signup_screen(self):
        """Draw the signup screen"""
        # Draw maze background
        draw_smooth_map()
        
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # Title
        title = self.title_font.render("SIGN UP", True, self.title_color)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 6))
        screen.blit(title, title_rect)
        
        # Username field
        username_label = self.menu_font.render("Username:", True, self.menu_color)
        username_label_rect = username_label.get_rect(midright=(SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 3))
        screen.blit(username_label, username_label_rect)
        
        # Username input box
        username_box = pygame.Rect(SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT // 3 - 25, 300, 50)
        # Highlight with animated cursor if focused
        box_color = self.selected_color if self.signup_focus == 0 else self.menu_color
        pygame.draw.rect(screen, box_color, username_box, 3 if self.signup_focus == 0 else 2)
        
        username_text = self.input_font.render(self.username_input, True, self.menu_color)
        username_text_rect = username_text.get_rect(midleft=(username_box.left + 10, username_box.centery))
        screen.blit(username_text, username_text_rect)
        
        # Draw cursor animation if username is focused
        if self.signup_focus == 0 and self.cursor_animation < 10:
            cursor_rect = pygame.Rect(username_text_rect.right + 5, username_box.centery - 15, 2, 30)
            pygame.draw.rect(screen, self.selected_color, cursor_rect)
        
        # Username error message (shown below username box)
        username_error_y = username_box.bottom + 5
        if self.signup_focus == 0 and self.check_username_exists(self.username_input) and len(self.username_input) > 0:
            error_text = self.small_font.render("Username already exists", True, self.error_color)
            error_rect = error_text.get_rect(midleft=(username_box.left, username_error_y))
            screen.blit(error_text, error_rect)
        
        # Password field
        password_label = self.menu_font.render("Password:", True, self.menu_color)
        password_label_rect = password_label.get_rect(midright=(SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 2))
        screen.blit(password_label, password_label_rect)
        
        # Password input box
        password_box = pygame.Rect(SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT // 2 - 25, 300, 50)
        # Highlight with animated cursor if focused
        box_color = self.selected_color if self.signup_focus == 1 else self.menu_color
        pygame.draw.rect(screen, box_color, password_box, 3 if self.signup_focus == 1 else 2)
        
        # Show password as asterisks
        password_display = "*" * len(self.password_input)
        password_text = self.input_font.render(password_display, True, self.menu_color)
        password_text_rect = password_text.get_rect(midleft=(password_box.left + 10, password_box.centery))
        screen.blit(password_text, password_text_rect)
        
        # Draw cursor animation if password is focused
        if self.signup_focus == 1 and self.cursor_animation < 10:
            cursor_rect = pygame.Rect(password_text_rect.right + 5, password_box.centery - 15, 2, 30)
            pygame.draw.rect(screen, self.selected_color, cursor_rect)
        
        # General Error/Success message (for registration errors)
        if self.error_message and not (self.signup_focus == 0 and "already exists" in self.error_message):
            error_text = self.small_font.render(self.error_message, True, self.error_color)
            error_rect = error_text.get_rect(center=(SCREEN_WIDTH // 2, password_box.bottom + 40))
            screen.blit(error_text, error_rect)
        
        if self.success_message:
            success_text = self.small_font.render(self.success_message, True, self.success_color)
            success_rect = success_text.get_rect(center=(SCREEN_WIDTH // 2, password_box.bottom + 40))
            screen.blit(success_text, success_rect)
        
        # Register button
        register_text_str = "Register"
        color = self.selected_color if self.signup_focus == 2 else self.menu_color
        register_text = self.menu_font.render(register_text_str, True, color)
        register_rect = register_text.get_rect(center=(SCREEN_WIDTH // 2, password_box.bottom + 80))
        screen.blit(register_text, register_rect)
        
        # Draw animated arrows for register button if focused
        if self.signup_focus == 2:
            if self.cursor_animation < 10:
                arrow = self.menu_font.render(">", True, self.selected_color)
                screen.blit(arrow, (register_rect.left - 50, register_rect.top))
                arrow = self.menu_font.render("<", True, self.selected_color)
                screen.blit(arrow, (register_rect.right + 30, register_rect.top))
        
        # Instructions
        inst1 = self.score_font.render("UP/DOWN: Navigate, ENTER: Select, ESC: Back to Login", True, (200, 200, 200))
        inst1_rect = inst1.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
        screen.blit(inst1, inst1_rect)
        
        inst2 = self.score_font.render("Username/Password must be at least 3 characters", True, (200, 200, 200))
        inst2_rect = inst2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
        screen.blit(inst2, inst2_rect)
    
    def draw_main_menu(self):
        """Draw the main menu"""
        # Draw maze background
        draw_smooth_map()
        
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # Title
        title = self.title_font.render("PAC-MAN", True, self.title_color)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 6))
        screen.blit(title, title_rect)
        
        # Welcome message
        if self.current_user:
            welcome_text = self.menu_font.render(f"Welcome, {self.current_user}!", True, (100, 255, 100))
            welcome_rect = welcome_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
            screen.blit(welcome_text, welcome_rect)
        
        # Menu items (dynamically generated)
        main_items = self.get_main_menu_items()
        for i, item in enumerate(main_items):
            color = self.selected_color if i == self.main_selection else self.menu_color
            text = self.menu_font.render(item, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3 + i * 60))
            screen.blit(text, text_rect)
            
            # Draw arrow for selected item
            if i == self.main_selection:
                arrow = self.menu_font.render(">", True, self.selected_color)
                screen.blit(arrow, (text_rect.left - 40, text_rect.top))
                arrow = self.menu_font.render("<", True, self.selected_color)
                screen.blit(arrow, (text_rect.right + 20, text_rect.top))
        
        # Instructions
        inst1 = self.score_font.render("UP/DOWN: Navigate, ENTER: Select", True, (200, 200, 200))
        inst1_rect = inst1.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
        screen.blit(inst1, inst1_rect)
        
        inst2 = self.score_font.render("ESC: Logout", True, (200, 200, 200))
        inst2_rect = inst2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
        screen.blit(inst2, inst2_rect)
    
    def draw_pause_screen(self):
        """Draw the pause screen"""
        # Dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # Title
        title = self.title_font.render("GAME PAUSED", True, self.title_color)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        screen.blit(title, title_rect)
        
        # Current user
        if self.current_user:
            user_text = self.menu_font.render(f"Player: {self.current_user}", True, (100, 255, 100))
            user_rect = user_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4 + 70))
            screen.blit(user_text, user_rect)
        
        # Current score
        score_text = self.menu_font.render(f"Score: {self.current_score}", True, (255, 255, 0))
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4 + 120))
        screen.blit(score_text, score_rect)
        
        # Pause menu items
        pause_items = ["Resume", "New Game", "Main Menu", "Logout"]
        for i, item in enumerate(pause_items):
            color = self.selected_color if i == self.pause_selection else self.menu_color
            text = self.menu_font.render(item, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + i * 60))
            screen.blit(text, text_rect)
            
            # Draw arrow for selected item
            if i == self.pause_selection:
                arrow = self.menu_font.render(">", True, self.selected_color)
                screen.blit(arrow, (text_rect.left - 40, text_rect.top))
                arrow = self.menu_font.render("<", True, self.selected_color)
                screen.blit(arrow, (text_rect.right + 20, text_rect.top))
        
        # Instructions
        inst = self.score_font.render("ESC: Resume Game", True, (200, 200, 200))
        inst_rect = inst.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
        screen.blit(inst, inst_rect)
    
    def draw_game_over_screen(self):
        """Draw game over screen"""
        # Dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        
        # Game Over text
        title = self.title_font.render("GAME OVER", True, (255, 50, 50))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        screen.blit(title, title_rect)
        
        # Final score
        score_text = self.menu_font.render(f"Final Score: {self.current_score}", True, (255, 255, 0))
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3 + 50))
        screen.blit(score_text, score_rect)
        
        # Update and save score (only once when game over state is first entered)
        if not self.game_over_score_saved and self.current_user:
            self.update_score(self.current_score, self.selected_level)
            self.game_over_score_saved = True
            
        if self.game_over_score_saved:
            saved_text = self.score_font.render("Score saved!", True, (100, 255, 100))
            saved_rect = saved_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3 + 100))
            screen.blit(saved_text, saved_rect)
        
        # Menu items
        for i, item in enumerate(self.game_over_items):
            color = self.selected_color if i == self.game_over_selection else self.menu_color
            text = self.menu_font.render(item, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + i * 60))
            screen.blit(text, text_rect)
            
            # Draw arrow for selected item
            if i == self.game_over_selection:
                arrow = self.menu_font.render(">", True, self.selected_color)
                screen.blit(arrow, (text_rect.left - 40, text_rect.top))
                arrow = self.menu_font.render("<", True, self.selected_color)
                screen.blit(arrow, (text_rect.right + 20, text_rect.top))
        
        # Instructions
        inst = self.score_font.render("ESC: Main Menu", True, (200, 200, 200))
        inst_rect = inst.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
        screen.blit(inst, inst_rect)
    
    def draw_highscore_screen(self):
        """Draw highscore screen"""
        # Draw maze background
        draw_smooth_map()
        
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # Title
        title = self.title_font.render("HIGH SCORES", True, self.title_color)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 8))
        screen.blit(title, title_rect)
        
        # Get scores for current level
        level_scores = self.get_high_scores_by_level(self.selected_level)
        
        # Level indicator
        level_text = self.menu_font.render(f"Level {self.selected_level}", True, (100, 255, 255))
        level_rect = level_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 5))
        screen.blit(level_text, level_rect)
        
        # Column headers
        rank_header = self.score_font.render("Rank", True, self.selected_color)
        name_header = self.score_font.render("Player", True, self.selected_color)
        score_header = self.score_font.render("Score", True, self.selected_color)
        
        header_y = SCREEN_HEIGHT // 4
        rank_header_rect = rank_header.get_rect(center=(SCREEN_WIDTH // 4, header_y))
        name_header_rect = name_header.get_rect(center=(SCREEN_WIDTH // 2, header_y))
        score_header_rect = score_header.get_rect(center=(3 * SCREEN_WIDTH // 4, header_y))
        
        screen.blit(rank_header, rank_header_rect)
        screen.blit(name_header, name_header_rect)
        screen.blit(score_header, score_header_rect)
        
        # Draw scores
        if level_scores:
            for i, entry in enumerate(level_scores[:10]):  # Top 10
                rank = i + 1
                user = entry["user"]
                score = entry["score"]
                
                # Highlight current user's score
                color = (255, 255, 100) if user == self.current_user else self.menu_color
                
                rank_text = self.score_font.render(f"{rank}.", True, color)
                name_text = self.score_font.render(user, True, color)
                score_text = self.score_font.render(str(score), True, color)
                
                y_pos = header_y + 40 + i * 35
                
                rank_rect = rank_text.get_rect(center=(SCREEN_WIDTH // 4, y_pos))
                name_rect = name_text.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
                score_rect = score_text.get_rect(center=(3 * SCREEN_WIDTH // 4, y_pos))
                
                screen.blit(rank_text, rank_rect)
                screen.blit(name_text, name_rect)
                screen.blit(score_text, score_rect)
        else:
            # No scores yet
            no_scores = self.menu_font.render("No scores yet for this level!", True, self.menu_color)
            no_scores_rect = no_scores.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(no_scores, no_scores_rect)
        
        # Instructions
        inst = self.score_font.render("Press ESC or ENTER to go back", True, (200, 200, 200))
        inst_rect = inst.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
        screen.blit(inst, inst_rect)
    
    def is_game_paused(self):
        """Check if game is currently paused"""
        return self.game_paused or self.current_state != "playing"