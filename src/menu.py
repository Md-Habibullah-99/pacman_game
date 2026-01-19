# menu.py
import pygame
import json
import sys
import os

from paths import resource_path

# --- Constants ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
DARK_BLUE = (0, 0, 180)
LIGHT_BLUE = (173, 216, 230)
DARK_GREEN = (0, 180, 0)
DARK_RED = (180, 0, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)

# Initialize Fonts
pygame.font.init()
try:
    FONT = pygame.font.Font(None, 32)
    SMALL_FONT = pygame.font.Font(None, 24)
    TITLE_FONT = pygame.font.Font(None, 48)
    BIG_FONT = pygame.font.Font(None, 64)
except:
    FONT = pygame.font.SysFont("arial", 32)
    SMALL_FONT = pygame.font.SysFont("arial", 24)
    TITLE_FONT = pygame.font.SysFont("arial", 48)
    BIG_FONT = pygame.font.SysFont("arial", 64)

# --- UI Classes ---

class InputBox:
    def __init__(self, x, y, w, h, text='', is_password=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = GRAY
        self.text = text
        self.is_password = is_password
        self.txt_surface = FONT.render(self._get_display_text(), True, BLACK)
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0

    def _get_display_text(self):
        if self.is_password:
            return '*' * len(self.text)
        return self.text

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect
            if self.rect.collidepoint(event.pos):
                self.active = True
                self.color = BLUE
            else:
                self.active = False
                self.color = GRAY
            return None
        
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    return self.text
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif event.key not in [pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_TAB]:
                    self.text += event.unicode
                
                self.txt_surface = FONT.render(self._get_display_text(), True, BLACK)
                return None
        return None

    def update(self):
        # Update cursor blink
        if self.active:
            current_time = pygame.time.get_ticks()
            if current_time - self.cursor_timer > 500:  # Blink every 500ms
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = current_time

    def draw(self, screen):
        # Draw the background
        pygame.draw.rect(screen, WHITE, self.rect, border_radius=5)
        pygame.draw.rect(screen, self.color, self.rect, 2, border_radius=5)
        
        # Draw the text
        text_x = self.rect.x + 10
        text_y = self.rect.y + (self.rect.height - self.txt_surface.get_height()) // 2
        screen.blit(self.txt_surface, (text_x, text_y))
        
        # Draw cursor if active and visible
        if self.active and self.cursor_visible:
            cursor_x = text_x + self.txt_surface.get_width() + 2
            pygame.draw.line(screen, BLACK, (cursor_x, text_y), 
                            (cursor_x, text_y + self.txt_surface.get_height()), 2)

    def clear(self):
        """Clear the input box"""
        self.text = ""
        self.txt_surface = FONT.render(self._get_display_text(), True, BLACK)

class Button:
    def __init__(self, x, y, w, h, text, color=GRAY, text_color=WHITE):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.txt_surface = FONT.render(text, True, text_color)
        self.is_hovered = False

    def draw(self, screen):
        # Draw button with hover effect
        current_color = self.color
        if self.is_hovered:
            # Lighten color on hover
            current_color = tuple(min(c + 30, 255) for c in self.color)
        
        pygame.draw.rect(screen, current_color, self.rect, border_radius=8)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=8)
        
        text_rect = self.txt_surface.get_rect(center=self.rect.center)
        screen.blit(self.txt_surface, text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)
    
    def update_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)

# --- Main Menu Class ---

class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.screen_width, self.screen_height = screen.get_size()
        self.state = "MAIN"  # States: MAIN, LOGIN, SIGNUP, DASHBOARD, HIGHSCORE, IN_GAME_MENU, GAME_OVER
        self.username = ""
        self.current_score = 0
        self.message = ""
        self.message_color = GREEN
        self.message_time = 0
        
        # Determine paths to JSON files
        # Use a writable user data directory so scores persist even in frozen builds
        xdg_data_home = os.environ.get("XDG_DATA_HOME")
        default_data_root = os.path.join(os.path.expanduser("~"), ".local", "share")
        data_root = os.path.expanduser(xdg_data_home) if xdg_data_home else default_data_root
        data_dir = os.path.join(data_root, "pacman_game")

        # Create data directory if it doesn't exist
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir, exist_ok=True)
                print(f"Created data directory: {data_dir}")
            except Exception as e:
                print(f"Error creating data directory: {e}")

        self.user_file = os.path.join(data_dir, "user.json")
        self.score_file = os.path.join(data_dir, "score.json")

        # Paths to bundled default data (read-only)
        self.default_user_file = resource_path("src", "data", "user.json")
        self.default_score_file = resource_path("src", "data", "score.json")
        
        print(f"User file: {self.user_file}")
        print(f"Score file: {self.score_file}")
        
        self.users = self.load_json(self.user_file, self.default_user_file)
        self.scores = self.load_json(self.score_file, self.default_score_file)
        
        print(f"Loaded {len(self.users)} users")
        print(f"Loaded {len(self.scores)} scores")
        
        self.inputs = []
        self.buttons = []
        
        # Initialize UI elements
        self.init_ui()

    def load_json(self, filepath, default_path=None):
        """Load JSON data from file, seeding from a bundled default if present."""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    return data
            else:
                seed_data = {}
                if default_path and os.path.exists(default_path):
                    try:
                        with open(default_path, 'r') as default_f:
                            seed_data = json.load(default_f)
                    except Exception as e:
                        print(f"Failed to read default data from {default_path}: {e}")
                print(f"File {filepath} doesn't exist, creating from defaults")
                with open(filepath, 'w') as f:
                    json.dump(seed_data, f)
                return seed_data
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return {}

    def save_json(self, filepath, data):
        """Save JSON data to file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving {filepath}: {e}")
            return False

    def show_message(self, msg, color=GREEN, duration=3000):
        """Show a temporary message"""
        self.message = msg
        self.message_color = color
        self.message_time = pygame.time.get_ticks() + duration

    def clear_message(self):
        """Clear the current message"""
        self.message = ""
        self.message_time = 0

    def update_messages(self):
        """Update message timer"""
        if self.message and pygame.time.get_ticks() > self.message_time:
            self.clear_message()

    def init_ui(self):
        """Initialize UI elements based on current state"""
        self.screen_width, self.screen_height = self.screen.get_size()
        self.inputs = []
        self.buttons = []
        
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        
        if self.state == "MAIN":
            # Main Menu - buttons placed with good spacing
            start_y = center_y - 40
            self.buttons.append(Button(center_x - 100, start_y, 200, 50, "Login", BLUE))
            self.buttons.append(Button(center_x - 100, start_y + 70, 200, 50, "Sign Up", GREEN))
            self.buttons.append(Button(center_x - 100, start_y + 140, 200, 50, "Exit", RED))
        
        elif self.state == "LOGIN":
            # Login Screen - properly spaced input boxes
            start_y = center_y - 100
            # Username input with good spacing
            self.inputs.append(InputBox(center_x - 150, start_y, 300, 40, ""))
            # Password input - placed 80px below username
            self.inputs.append(InputBox(center_x - 150, start_y + 80, 300, 40, "", is_password=True))
            
            # Buttons placed further down
            self.buttons.append(Button(center_x - 100, start_y + 170, 200, 50, "Login", BLUE))
            self.buttons.append(Button(center_x - 100, start_y + 240, 200, 50, "Back", GRAY))
        
        elif self.state == "SIGNUP":
            # Signup Screen - same spacing as login
            start_y = center_y - 100
            self.inputs.append(InputBox(center_x - 150, start_y, 300, 40, ""))
            self.inputs.append(InputBox(center_x - 150, start_y + 80, 300, 40, "", is_password=True))
            
            self.buttons.append(Button(center_x - 100, start_y + 170, 200, 50, "Sign Up", GREEN))
            self.buttons.append(Button(center_x - 100, start_y + 240, 200, 50, "Back", GRAY))
        
        elif self.state == "DASHBOARD":
            # Dashboard - username at top, buttons centered below
            start_y = center_y - 40
            self.buttons.append(Button(center_x - 100, start_y, 200, 50, "New Game", GREEN))
            self.buttons.append(Button(center_x - 100, start_y + 70, 200, 50, "High Score", BLUE))
            self.buttons.append(Button(center_x - 100, start_y + 140, 200, 50, "Logout", RED))
        
        elif self.state == "HIGHSCORE":
            # High Score Screen - ONLY BACK BUTTON
            self.buttons.append(Button(center_x - 100, self.screen_height - 100, 200, 50, "Back", GRAY))
        
        elif self.state == "IN_GAME_MENU":
            # In-game Pause Menu
            center_y = self.screen_height // 2
            self.buttons.append(Button(center_x - 100, center_y - 90, 200, 50, "Continue", GREEN))
            self.buttons.append(Button(center_x - 100, center_y - 30, 200, 50, "New Game", BLUE))
            self.buttons.append(Button(center_x - 100, center_y + 30, 200, 50, "High Score", PURPLE))
            self.buttons.append(Button(center_x - 100, center_y + 90, 200, 50, "Logout", RED))
        
        elif self.state == "GAME_OVER":
            # Game Over Screen
            center_y = self.screen_height // 2
            self.buttons.append(Button(center_x - 100, center_y - 20, 200, 50, "New Game", GREEN))
            self.buttons.append(Button(center_x - 100, center_y + 50, 200, 50, "High Score", BLUE))
            self.buttons.append(Button(center_x - 100, center_y + 120, 200, 50, "Logout", RED))

    def draw_text(self, text, y, color=WHITE, font=FONT, center=True, x_offset=0):
        """Helper function to draw text on screen"""
        surf = font.render(text, True, color)
        if center:
            rect = surf.get_rect(center=(self.screen_width // 2 + x_offset, y))
            self.screen.blit(surf, rect)
        else:
            self.screen.blit(surf, (20 + x_offset, y))

    def show_highscore_screen(self):
        """Display high score screen with proper spacing"""
        self.screen.fill(BLACK)
        
        # Title
        self.draw_text("HIGH SCORES", 60, YELLOW, TITLE_FONT)
        
        # Draw scores with proper spacing - leave room at bottom for button
        y_pos = 130
        
        # Sort scores by value (descending) - higher score gets higher position
        sorted_scores = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_scores:
            self.draw_text("No scores yet! Play a game!", 200, WHITE, FONT)
        else:
            # Draw column headers
            self.draw_text("Rank", y_pos, ORANGE, SMALL_FONT, center=True, x_offset=-150)
            self.draw_text("Player", y_pos, ORANGE, SMALL_FONT, center=True, x_offset=-50)
            self.draw_text("Score", y_pos, ORANGE, SMALL_FONT, center=True, x_offset=100)
            
            y_pos += 40
            
            # Draw a separator line
            pygame.draw.line(self.screen, GRAY, 
                           (self.screen_width // 2 - 200, y_pos - 10),
                           (self.screen_width // 2 + 200, y_pos - 10), 2)
            
            # Draw top 10 scores, but leave room for the back button
            max_scores_to_show = min(10, len(sorted_scores))
            for idx in range(max_scores_to_show):
                if y_pos > self.screen_height - 150:  # Leave room for button
                    break
                    
                username, score = sorted_scores[idx]
                
                # Highlight current user's score
                if username == self.username:
                    # Draw background highlight for current user
                    highlight_rect = pygame.Rect(
                        self.screen_width // 2 - 200, y_pos - 15,
                        400, 35
                    )
                    pygame.draw.rect(self.screen, DARK_BLUE, highlight_rect, border_radius=5)
                
                # Rank with different colors for top 3
                if idx == 0:  # 1st place
                    rank_color = YELLOW
                    rank_text = "1st 🥇"
                elif idx == 1:  # 2nd place
                    rank_color = LIGHT_BLUE
                    rank_text = "2nd 🥈"
                elif idx == 2:  # 3rd place
                    rank_color = ORANGE
                    rank_text = "3rd 🥉"
                else:
                    rank_color = WHITE
                    rank_text = f"{idx + 1}th"
                
                # Draw rank
                self.draw_text(rank_text, y_pos, rank_color, FONT, center=True, x_offset=-150)
                
                # Draw username (current user in different color)
                username_color = YELLOW if username == self.username else WHITE
                # Truncate long usernames
                display_username = username[:15] + "..." if len(username) > 15 else username
                self.draw_text(display_username, y_pos, username_color, FONT, center=True, x_offset=-50)
                
                # Draw score with formatting
                score_text = f"{score:,}"  # Add commas for thousands
                score_color = GREEN if username == self.username else WHITE
                self.draw_text(score_text, y_pos, score_color, FONT, center=True, x_offset=100)
                
                y_pos += 40
        
        # Draw only the back button (no other buttons)
        for btn in self.buttons:
            btn.draw(self.screen)
        
        pygame.display.flip()

    def handle_login(self):
        """Handle login attempt"""
        if len(self.inputs) >= 2:
            username = self.inputs[0].text.strip()
            password = self.inputs[1].text
            
            if not username or not password:
                self.show_message("Please enter username and password", RED)
                return False
            
            if username in self.users:
                if self.users[username] == password:
                    self.username = username
                    self.state = "DASHBOARD"
                    self.show_message(f"Welcome back, {username}!", GREEN)
                    self.init_ui()
                    return True
                else:
                    self.show_message("Incorrect password", RED)
                    return False
            else:
                self.show_message("Username not found", RED)
                return False
        return False

    def handle_signup(self):
        """Handle signup attempt"""
        if len(self.inputs) >= 2:
            username = self.inputs[0].text.strip()
            password = self.inputs[1].text
            
            if not username or not password:
                self.show_message("Please enter username and password", RED)
                return False
            
            if len(username) < 3:
                self.show_message("Username must be at least 3 characters", RED)
                return False
            
            if len(password) < 4:
                self.show_message("Password must be at least 4 characters", RED)
                return False
            
            if username in self.users:
                self.show_message("Username already exists", RED)
                return False
            
            # Add new user
            self.users[username] = password
            if self.save_json(self.user_file, self.users):
                # Show success message and clear inputs
                self.show_message("Account created successfully! Please login.", GREEN)
                
                # Clear input boxes
                for input_box in self.inputs:
                    input_box.clear()
                
                # Switch to login screen
                self.state = "LOGIN"
                self.init_ui()
                return True
            else:
                self.show_message("Error saving user data", RED)
                return False
        return False

    def run(self):
        """Run the main menu loop"""
        self.state = "MAIN"
        self.init_ui()
        
        clock = pygame.time.Clock()
        running = True
        
        while running:
            dt = clock.tick(60)  # Cap at 60 FPS
            
            # Update message timer
            self.update_messages()
            
            # Update input boxes
            for box in self.inputs:
                box.update()
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                # Handle input boxes
                for box in self.inputs:
                    box.handle_event(event)
                
                # Handle mouse clicks
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Update hover state for buttons
                    for btn in self.buttons:
                        btn.update_hover(mouse_pos)
                        if btn.is_clicked(mouse_pos):
                            # Handle button clicks
                            if btn.text == "Exit":
                                pygame.quit()
                                sys.exit()
                            
                            elif btn.text == "Login":
                                if self.state == "MAIN":
                                    self.state = "LOGIN"
                                    self.init_ui()
                                elif self.state == "LOGIN":
                                    self.handle_login()
                            
                            elif btn.text == "Sign Up":
                                if self.state == "MAIN":
                                    self.state = "SIGNUP"
                                    self.init_ui()
                                elif self.state == "SIGNUP":
                                    self.handle_signup()
                            
                            elif btn.text == "Back":
                                # From HIGHSCORE, go back to DASHBOARD
                                if self.state == "HIGHSCORE":
                                    self.state = "DASHBOARD"
                                    self.init_ui()
                                elif self.state in ["LOGIN", "SIGNUP"]:
                                    self.state = "MAIN"
                                    self.init_ui()
                            
                            elif btn.text == "New Game":
                                if self.state == "DASHBOARD":
                                    return "START_GAME"
                                elif self.state == "GAME_OVER":
                                    return "NEW_GAME"
                            
                            elif btn.text == "High Score":
                                if self.state == "DASHBOARD":
                                    self.state = "HIGHSCORE"
                                    self.scores = self.load_json(self.score_file)
                                    self.init_ui()
                                elif self.state == "GAME_OVER":
                                    # Show high score and then return to game over screen
                                    self.show_highscore_screen()
                                    # Wait for click to return
                                    waiting = True
                                    while waiting:
                                        for e in pygame.event.get():
                                            if e.type == pygame.QUIT:
                                                pygame.quit()
                                                sys.exit()
                                            if e.type == pygame.MOUSEBUTTONDOWN:
                                                waiting = False
                                            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                                                waiting = False
                                    self.state = "GAME_OVER"
                                    self.init_ui()
                            
                            elif btn.text == "Logout":
                                if self.state == "DASHBOARD":
                                    self.username = ""
                                    self.state = "MAIN"
                                    self.init_ui()
                                    return "LOGOUT"
                                elif self.state == "GAME_OVER":
                                    return "LOGOUT"
            
            # Draw everything based on state
            self.screen.fill(BLACK)
            
            # Update hover state for buttons
            mouse_pos = pygame.mouse.get_pos()
            for btn in self.buttons:
                btn.update_hover(mouse_pos)
            
            if self.state == "MAIN":
                # Draw title
                self.draw_text("PAC-MAN", 100, YELLOW, BIG_FONT)
                self.draw_text("Main Menu", 180, BLUE, TITLE_FONT)
                
                # Draw buttons
                for btn in self.buttons:
                    btn.draw(self.screen)
                
                # Draw message at bottom
                if self.message:
                    self.draw_text(self.message, self.screen_height - 50, self.message_color, SMALL_FONT)
            
            elif self.state == "LOGIN":
                # Draw title
                self.draw_text("LOGIN", 80, BLUE, TITLE_FONT)
                
                # Draw labels above input boxes
                if self.inputs:
                    # Username label
                    username_y = self.inputs[0].rect.y - 30
                    self.draw_text("Username:", username_y, WHITE, SMALL_FONT)
                    
                    # Password label
                    password_y = self.inputs[1].rect.y - 30
                    self.draw_text("Password:", password_y, WHITE, SMALL_FONT)
                
                # Draw input boxes
                for box in self.inputs:
                    box.draw(self.screen)
                
                # Draw buttons
                for btn in self.buttons:
                    btn.draw(self.screen)
                
                # Draw message
                if self.message:
                    self.draw_text(self.message, self.screen_height - 50, self.message_color, SMALL_FONT)
            
            elif self.state == "SIGNUP":
                # Draw title
                self.draw_text("SIGN UP", 80, GREEN, TITLE_FONT)
                
                # Draw labels above input boxes
                if self.inputs:
                    username_y = self.inputs[0].rect.y - 30
                    self.draw_text("Username:", username_y, WHITE, SMALL_FONT)
                    
                    password_y = self.inputs[1].rect.y - 30
                    self.draw_text("Password:", password_y, WHITE, SMALL_FONT)
                
                # Draw input boxes
                for box in self.inputs:
                    box.draw(self.screen)
                
                # Draw buttons
                for btn in self.buttons:
                    btn.draw(self.screen)
                
                # Draw message
                if self.message:
                    self.draw_text(self.message, self.screen_height - 50, self.message_color, SMALL_FONT)
            
            elif self.state == "DASHBOARD":
                # Draw welcome message at the top (not overlapping buttons)
                self.draw_text(f"Welcome, {self.username}!", 100, GREEN, TITLE_FONT)
                self.draw_text("Dashboard", 180, BLUE, FONT)
                
                # Draw buttons (positioned below the text)
                for btn in self.buttons:
                    btn.draw(self.screen)
                
                # Draw message at bottom
                if self.message:
                    self.draw_text(self.message, self.screen_height - 50, self.message_color, SMALL_FONT)
            
            elif self.state == "HIGHSCORE":
                # Show highscore screen (handles its own drawing)
                self.show_highscore_screen()
                continue  # Skip the rest of the drawing loop
            
            elif self.state == "GAME_OVER":
                # Draw game over screen
                self.draw_text("GAME OVER", 100, RED, TITLE_FONT)
                self.draw_text(f"Final Score: {self.current_score}", 180, YELLOW, FONT)
                self.draw_text(f"Player: {self.username}", 220, WHITE, SMALL_FONT)
                
                # Draw buttons
                for btn in self.buttons:
                    btn.draw(self.screen)
                
                # Draw message at bottom
                if self.message:
                    self.draw_text(self.message, self.screen_height - 50, self.message_color, SMALL_FONT)
            
            pygame.display.flip()

    def show_in_game_menu(self, current_score):
        """Show in-game pause menu, returns action"""
        self.current_score = current_score
        self.state = "IN_GAME_MENU"
        self.init_ui()
        
        clock = pygame.time.Clock()
        
        while True:
            dt = clock.tick(60)
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "CONTINUE"
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Handle button clicks
                    for btn in self.buttons:
                        if btn.is_clicked(mouse_pos):
                            if btn.text == "Continue":
                                return "CONTINUE"
                            elif btn.text == "New Game":
                                return "NEW_GAME"
                            elif btn.text == "High Score":
                                # Show high scores with back button
                                self.show_pause_highscore_screen()
                                # After returning from highscore, re-init the pause menu
                                self.init_ui()
                                continue
                            elif btn.text == "Logout":
                                return "LOGOUT"
            
            # Draw semi-transparent overlay
            overlay = pygame.Surface(self.screen.get_size())
            overlay.set_alpha(180)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            
            # Update hover state
            mouse_pos = pygame.mouse.get_pos()
            for btn in self.buttons:
                btn.update_hover(mouse_pos)
            
            # Draw menu title and info
            center_x = self.screen_width // 2
            center_y = self.screen_height // 2
            
            # Draw text above the buttons
            self.draw_text("PAUSED", center_y - 180, YELLOW, TITLE_FONT)
            self.draw_text(f"Score: {self.current_score}", center_y - 120, GREEN, FONT)
            self.draw_text(f"Player: {self.username}", center_y - 80, WHITE, SMALL_FONT)
            
            # Draw buttons (already positioned in init_ui)
            for btn in self.buttons:
                btn.draw(self.screen)
            
            pygame.display.flip()

    def show_game_over_menu(self, final_score):
        """Show game over menu with buttons, returns action"""
        self.current_score = final_score
        self.state = "GAME_OVER"
        self.init_ui()
        
        # Update the score
        score_updated = self.update_score(final_score)
        if score_updated:
            self.show_message("New High Score!", GREEN)
        
        clock = pygame.time.Clock()
        
        while True:
            dt = clock.tick(60)
            
            # Update message timer
            self.update_messages()
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Handle button clicks
                    for btn in self.buttons:
                        if btn.is_clicked(mouse_pos):
                            if btn.text == "New Game":
                                return "NEW_GAME"
                            elif btn.text == "High Score":
                                # Show high scores with proper back button handling
                                self.state = "HIGHSCORE"
                                self.scores = self.load_json(self.score_file)
                                self.init_ui()
                                
                                # Run highscore screen loop
                                while True:
                                    for e in pygame.event.get():
                                        if e.type == pygame.QUIT:
                                            pygame.quit()
                                            sys.exit()
                                        if e.type == pygame.MOUSEBUTTONDOWN:
                                            mouse_pos = pygame.mouse.get_pos()
                                            for b in self.buttons:
                                                if b.is_clicked(mouse_pos) and b.text == "Back":
                                                    # Return to game over menu
                                                    self.state = "GAME_OVER"
                                                    self.init_ui()
                                                    break
                                            # Check if we need to break out of the highscore loop
                                            if self.state != "HIGHSCORE":
                                                break
                                        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                                            # Allow ESC to go back as well
                                            self.state = "GAME_OVER"
                                            self.init_ui()
                                            break
                                    # Check if we need to break out of the highscore loop
                                    if self.state != "HIGHSCORE":
                                        break
                                    
                                    # Draw highscore screen
                                    self.screen.fill(BLACK)
                                    self.show_highscore_screen()
                                    pygame.display.flip()
                                
                                # After returning from highscore, continue with game over menu
                                break
                            elif btn.text == "Logout":
                                return "LOGOUT"
            
            # Draw everything
            self.screen.fill(BLACK)
            
            # Update hover state for buttons
            mouse_pos = pygame.mouse.get_pos()
            for btn in self.buttons:
                btn.update_hover(mouse_pos)
            
            # Draw game over screen
            self.draw_text("GAME OVER", 100, RED, TITLE_FONT)
            self.draw_text(f"Final Score: {self.current_score}", 180, YELLOW, FONT)
            self.draw_text(f"Player: {self.username}", 220, WHITE, SMALL_FONT)
            
            # Draw message if score was updated
            if score_updated:
                self.draw_text("🎉 New High Score! 🎉", 260, GREEN, SMALL_FONT)
            
            # Draw buttons
            for btn in self.buttons:
                btn.draw(self.screen)
            
            # Draw message at bottom
            if self.message:
                self.draw_text(self.message, self.screen_height - 50, self.message_color, SMALL_FONT)
            
            pygame.display.flip()

    def show_pause_highscore_screen(self):
        """Show high score screen from pause menu with back button"""
        # Save current state
        prev_state = self.state
        
        # Set to highscore state and initialize UI
        self.state = "HIGHSCORE"
        self.init_ui()
        
        clock = pygame.time.Clock()
        
        while True:
            dt = clock.tick(60)
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Check for back button click
                    for btn in self.buttons:
                        if btn.is_clicked(mouse_pos) and btn.text == "Back":
                            return
            
            # Draw high scores
            self.screen.fill(BLACK)
            self.show_highscore_screen()

    def update_score(self, score):
        """Update the score for current user - higher scores get higher position"""
        if self.username and score > 0:
            current_best = self.scores.get(self.username, 0)
            if score > current_best:
                self.scores[self.username] = score
                self.save_json(self.score_file, self.scores)
                return True
        return False