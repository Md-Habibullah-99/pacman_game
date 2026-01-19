# 🎮 Pacman Game

A classic Pac-Man game implementation in Python with intelligent ghost AI, level system, and engaging gameplay mechanics.

## 📋 Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Game Controls](#game-controls)
- [Game Features](#game-features)
- [Contributors](#contributors)

## ✨ Features

- **Classic Pacman Gameplay**: Navigate through mazes, eat pellets, and avoid ghosts
- **Intelligent Ghost AI**: Multiple ghost behaviors with different AI strategies
  - Blinky (Red) - Aggressive pursuit
  - Pinky (Pink) - Ambush tactics
  - Inky (Blue) - Unpredictable movement
  - Clyde (Orange) - Varied behavior
- **Level System**: Progressive difficulty with multiple maze levels
- **Lives & Scoring System**: Track lives and score throughout the game
- **Smooth Animations**: Sprite-based graphics with smooth character movement
- **Main Menu**: Interactive menu interface for game navigation
- **Custom Maze Levels**: Multiple maze configurations loaded from JSON

## 📁 Project Structure

```
pacman_game/
├── src/
│   ├── main.py              # Main game loop and entry point
│   ├── pacman.py            # Pacman player character logic
│   ├── ghost.py             # Ghost AI and behavior logic
│   ├── maze.py              # Maze rendering and collision detection
│   ├── menu.py              # Main menu interface
│   ├── lavel_system.py       # Level and lives management
│   ├── paths.py             # Pathfinding utilities
│   └── data/
│       ├── score.json       # Player scores
│       └── user.json        # User data
├── data/
│   └── maze.json            # Maze level definitions
├── assets/
│   └── sprites/             # Character and tile sprites
├── build/                   # Compiled builds (PyInstaller)
├── README.md                # This file
└── pacman.spec / pacman_win.spec  # PyInstaller specs
```

## 🚀 Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Setup Steps

1. Clone the repository:
```bash
git clone https://github.com/Md-Habibullah-99/pacman_game.git
cd pacman_game
```

2. Install required dependencies:
```bash
pip install pygame
```

3. Run the game:
```bash
python src/main.py
```

## 🎮 Usage

Simply run the main game file to start playing:

```bash
python src/main.py
```

The game will launch with a menu where you can start a new game or view options.

## ⌨️ Game Controls

| Key | Action |
|-----|--------|
| **Arrow Keys** | Move Pacman (Up, Down, Left, Right) |
| **ESC** | Open pause menu |
| **Space** | Select menu options / Resume game |

## 🎯 Game Features

### Gameplay Mechanics
- **Pellet Collection**: Eat all pellets to complete a level
- **Power Pellets**: Special pellets that temporarily make ghosts vulnerable
- **Ghost Behavior**: Each ghost has unique AI patterns and behaviors
- **Lives System**: Start with 8 lives, lose one when caught by a ghost
- **Level Progression**: Advance through increasingly difficult levels
- **Score Tracking**: Accumulate points for eating pellets and ghosts

### AI Behaviors
- **Blinky (Red Ghost)**: Direct pursuit of Pacman
- **Pinky (Pink Ghost)**: Targets a position ahead of Pacman
- **Inky (Blue Ghost)**: Complex behavior influenced by Blinky's position
- **Clyde (Orange Ghost)**: Alternates between pursuit and random movement

## 👥 Contributors

This project is developed collaboratively by:

### [Shahnur](https://github.com/shahnur07)
- GitHub: [@shahnur07](https://github.com/shahnur07)

### [Md Habibullah](https://github.com/Md-Habibullah-99)
- GitHub: [@Md-Habibullah-99](https://github.com/Md-Habibullah-99)

---

## 📄 License

This project is provided as-is for educational purposes.

## 🙏 Acknowledgments

- Inspired by the classic Pac-Man arcade game
- Built with Python and Pygame library
- Ghost AI algorithms based on classic Pac-Man ghost behavior patterns

---

**Enjoy the game! 🎮**
