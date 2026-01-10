import pygame
import os
from maze import TILE_SIZE, screen, MAP_DATA, reset_maze

class LevelSystem:
	def __init__(self, initial_lives: int = 3):
		self.lives = initial_lives
		self.game_over = False
		self.level = 1
		self.life_icon = None
		try:
			sprite_path = os.path.normpath(
				os.path.join(os.path.dirname(__file__), "..", "assets", "sprites", "pacman.png")
			)
			img = pygame.image.load(sprite_path).convert_alpha()
			size = max(16, TILE_SIZE - 6)
			self.life_icon = pygame.transform.smoothscale(img, (size, size))
		except Exception as e:
			print("Failed to load life icon:", e)

	def draw_lives(self):
		if self.life_icon is None or self.lives <= 0:
			return
		spacing = self.life_icon.get_width() + 6
		screen_w = screen.get_width()
		for i in range(self.lives):
			rect = self.life_icon.get_rect()
			rect.topright = (screen_w - i * spacing, 0)
			screen.blit(self.life_icon, rect)

	def check_level_completion(self, pacman, ghosts):
		"""If all pellets are eaten, advance level, reset maze, and speed up ghosts."""
		if self.game_over:
			return
		# Detect remaining pellets (2 or 3) in the current MAP_DATA
		remaining = 0
		for row in MAP_DATA:
			for v in row:
				if v == 2 or v == 3:
					remaining += 1
		if remaining == 0:
			# Advance level
			self.level += 1
			# Reset maze to original pellet layout
			reset_maze()
			# Reset Pacman position but keep score and lives
			pacman.reset_position()
			# Increase ghost speed by 0.2 and reset them to spawn
			for g in ghosts:
				if hasattr(g, 'normal_speed'):
					g.normal_speed = g.normal_speed + 0.2
					g.speed = g.normal_speed
				if hasattr(g, 'reset_to_spawn'):
					g.reset_to_spawn()

	def check_collision_and_reset(self, pacman, ghost):
		dx = pacman.px - ghost.px
		dy = pacman.py - ghost.py
		dist_sq = dx * dx + dy * dy
		pr = getattr(pacman, 'radius', TILE_SIZE // 2)
		gr = getattr(ghost, 'radius', TILE_SIZE // 2)
		threshold = (pr + gr) * 0.8
		if dist_sq <= threshold * threshold:
			# First: if ghost is already returning to base, ignore collisions
			if getattr(ghost, 'returning_to_base', False):
				return
			# Next: if ghost is in scatter, take it down once and start return
			if getattr(ghost, 'scatter_active', False):
				if hasattr(ghost, 'take_down_and_return_to_base'):
					ghost.take_down_and_return_to_base()
				return
			# Normal collision: lose life and reset
			if self.lives > 0:
				self.lives -= 1
			# If lives dropped to zero, trigger game over and DO NOT reset positions
			if self.lives <= 0:
				self.game_over = True
				return
			# Otherwise, reset positions for next life
			pacman.reset_position()
			if hasattr(ghost, 'reset_to_spawn'):
				ghost.reset_to_spawn()

	def get_lives(self) -> int:
		return self.lives

	def is_game_over(self) -> bool:
		return self.game_over

	def draw_game_over(self):
		# Draw a big centered "GAME OVER" overlay
		if not self.game_over:
			return
		# Semi-transparent dark overlay
		overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
		overlay.fill((0, 0, 0, 160))
		screen.blit(overlay, (0, 0))
		# Title font
		try:
			if not pygame.font.get_init():
				pygame.font.init()
			font = pygame.font.Font("src/fonts/CascadiaCode-VariableFont_wght.ttf", 72)
		except Exception:
			font = pygame.font.SysFont(None, 72)
		# Render text
		title = font.render("GAME OVER", True, (255, 80, 80))
		tr = title.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 - 20))
		screen.blit(title, tr)
		# Subtext
		try:
			sub_font = pygame.font.Font("src/fonts/CascadiaCode-VariableFont_wght.ttf", 28)
		except Exception:
			sub_font = pygame.font.SysFont(None, 28)
		sub = sub_font.render("No lives left", True, (255, 255, 255))
		sr = sub.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 32))
		screen.blit(sub, sr)
