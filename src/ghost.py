import pygame
import random
import math
import heapq
import os
from maze import MAP_DATA, MAP_WIDTH, MAP_HEIGHT, TILE_SIZE, screen

WALL = 1
WALKABLE = {0, 2, 3, 5, 6, 7, 8, 9}


def is_walkable(x: int, y: int) -> bool:
    return 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT and MAP_DATA[y][x] != WALL


def neighbors_with_tunnel(x: int, y: int):
    # Standard neighbors
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    for dx, dy in dirs:
        nx, ny = x + dx, y + dy
        # Tunnel wrap on row 9 across left/right edges
        if y == 9 and ny == 9 and (nx < 0 or nx >= MAP_WIDTH):
            if nx < 0:
                nx = MAP_WIDTH - 1
            elif nx >= MAP_WIDTH:
                nx = 0
        if is_walkable(nx, ny):
            yield nx, ny


def is_corner_or_junction(x: int, y: int) -> bool:
    if not is_walkable(x, y):
        return False
    nbs = list(neighbors_with_tunnel(x, y))
    n = len(nbs)
    if n != 2:
        return n > 0  # dead-end (1) or junction (>=3) are nodes
    # n == 2: corner or straight?
    (x1, y1), (x2, y2) = nbs
    # Straight if aligned horizontally or vertically
    straight = (y1 == y == y2) or (x1 == x == x2)
    return not straight  # corner if not straight


def build_graph():
    nodes = set()
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            if is_corner_or_junction(x, y):
                nodes.add((x, y))
    # Ensure tunnel endpoints are nodes (helps with wrapping)
    if is_walkable(0, 9):
        nodes.add((0, 9))
    if is_walkable(MAP_WIDTH - 1, 9):
        nodes.add((MAP_WIDTH - 1, 9))

    # Build adjacency by ray-casting from each node in 4 directions until next node
    adj = {n: [] for n in nodes}

    def raycast_from(x, y, dx, dy):
        cx, cy = x, y
        dist = 0
        while True:
            nx, ny = cx + dx, cy + dy
            # Tunnel wrap on row 9 across edges
            if ny == 9 and (nx < 0 or nx >= MAP_WIDTH):
                if nx < 0:
                    nx = MAP_WIDTH - 1
                elif nx >= MAP_WIDTH:
                    nx = 0
            if not is_walkable(nx, ny):
                return None
            dist += 1
            cx, cy = nx, ny
            if (cx, cy) in nodes:
                return (cx, cy, dist)

    for (x, y) in nodes:
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            hit = raycast_from(x, y, dx, dy)
            if hit is not None:
                nx, ny, w = hit
                # Store undirected edge (we'll add both directions)
                if (nx, ny) in adj:
                    adj[(x, y)].append(((nx, ny), w))

    # Make edges symmetric (some directions may not be found from the other node if blocked)
    for u in list(adj.keys()):
        for v, w in adj[u]:
            if u not in [n for n, _ in adj.get(v, [])]:
                adj.setdefault(v, []).append((u, w))

    return nodes, adj


def nearest_node_from_tile(tile, nodes):
    """Return the nearest graph node by BFS expanding along walkable tiles."""
    tx, ty = tile
    if (tx, ty) in nodes:
        return (tx, ty)
    # BFS until we hit a node
    from collections import deque
    dq = deque()
    dq.append((tx, ty))
    seen = { (tx, ty) }
    while dq:
        x, y = dq.popleft()
        for nx, ny in neighbors_with_tunnel(x, y):
            if (nx, ny) in seen:
                continue
            if (nx, ny) in nodes:
                return (nx, ny)
            seen.add((nx, ny))
            dq.append((nx, ny))
    # Fallback: pick any node (should not happen on valid maps)
    return next(iter(nodes))


def dijkstra(adj, start, goal):
    """Return list of nodes from start to goal inclusive."""
    if start == goal:
        return [start]
    dist = {start: 0}
    prev = {}
    pq = [(0, start)]
    while pq:
        d, u = heapq.heappop(pq)
        if u == goal:
            break
        if d != dist.get(u, math.inf):
            continue
        for v, w in adj.get(u, []):
            nd = d + w
            if nd < dist.get(v, math.inf):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))
    if goal not in prev and goal != start:
        return [start]
    # Reconstruct
    path = [goal]
    cur = goal
    while cur != start:
        cur = prev[cur]
        path.append(cur)
    path.reverse()
    return path


class Ghost:
    def __init__(self, color=(255, 0, 0), pacman=None, speed=2, spawn_values=None, sprite_variant: str = "red", behavior: str = "blinky", partner=None):
        self.color = color
        self.pacman = pacman
        self.speed = speed
        self.normal_speed = speed
        self.return_speed = 5
        self.radius = TILE_SIZE // 2 - 2
        self.image = None
        self.scatter_image = None
        self.scatter_active = False
        self.returning_to_base = False
        self._scatter_until_ms = None
        # Additional config for variants
        self.spawn_values = set(spawn_values) if spawn_values is not None else {5}
        self.sprite_variant = sprite_variant
        self.behavior = behavior  # 'blinky' for aggressive chase by default
        self._last_pac_tile = None  # track pacman tile to trigger re-path
        # Optional partner ghost reference (used by Inky behavior)
        self.partner = partner
        # Clyde home corner cache
        self.home_corner_node = None
        # Tunnel wrap cooldown to avoid rapid re-wrap flicker
        self._wrap_cooldown_until = 0
        # Movement idle guard
        self._last_move_ms = pygame.time.get_ticks()

        # Build graph once
        self.nodes, self.adj = build_graph()

        # Load ghost sprite for the selected variant if available
        try:
            sprite_filename = f"Ghost-{self.sprite_variant}.png"
            sprite_path = os.path.normpath(
                os.path.join(os.path.dirname(__file__), "..", "assets", "sprites", sprite_filename)
            )
            img = pygame.image.load(sprite_path).convert_alpha()
            # Scale to a tile size with a tiny padding so it fits corridors
            size = max(1, TILE_SIZE - 2)
            self.image = pygame.transform.smoothscale(img, (size, size))
            scatter_path = os.path.normpath(
                os.path.join(os.path.dirname(__file__), "..", "assets", "sprites", "scater_mode.png")
            )
            s_img = pygame.image.load(scatter_path).convert_alpha()
            self.scatter_image = pygame.transform.smoothscale(s_img, (size, size))
        except Exception as e:
            # Fallback: keep drawing a circle if sprite fails to load
            print("Failed to load ghost sprite:", e)

        # Choose a spawn among configured spawn values
        spawn_tiles = []
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                if MAP_DATA[y][x] in self.spawn_values:
                    spawn_tiles.append((x, y))
        if not spawn_tiles:
            # Fallback: center of map
            spawn = (MAP_WIDTH // 2, MAP_HEIGHT // 2)
        else:
            spawn = random.choice(spawn_tiles)
        self.spawn_tile = spawn

        # Build a return graph that includes the spawn tile as a node
        self.nodes_return, self.adj_return = self._build_return_graph()

        self.px = spawn[0] * TILE_SIZE + TILE_SIZE // 2
        self.py = spawn[1] * TILE_SIZE + TILE_SIZE // 2

        self.dx = 0
        self.dy = 0

        # Path state: list of node tiles; we move from one to next
        self.current_target_node = None
        self.path_nodes = []
        # Track last safe walkable tile to recover from overshoot
        self.last_safe_tile = self.spawn_tile
        # If spawn tile is not a node, plan an initial step toward nearest node
        self._plan_move_from_non_node()

        # Ensure an initial movement direction is chosen even if spawn is a node
        if self.dx == 0 and self.dy == 0:
            stx, sty = self.spawn_tile
            if (stx, sty) in self.nodes:
                # Compute an initial path toward the chase target and take the first step
                target_node = self._select_chase_target_node()
                path = dijkstra(self.adj, (stx, sty), target_node)
                if len(path) >= 2:
                    self.current_target_node = path[1]
                    self.choose_next_direction_to(self.current_target_node)
                else:
                    # Fallback: step toward raw target tile
                    step = self._next_tile_towards((stx, sty), self._select_target_tile())
                    if step is not None:
                        self.choose_next_direction_to(step)
                    else:
                        # Final fallback: pick any walkable neighbor toward target
                        self._choose_any_walkable_direction(self._select_target_tile())
            else:
                # Spawn isn't a node and planning failed; pick any walkable neighbor
                self._choose_any_walkable_direction(self._select_target_tile())

    def enter_scatter_mode(self):
        # Activate scatter for 5–8 seconds
        self.scatter_active = True
        self.returning_to_base = False
        now = pygame.time.get_ticks()
        duration_ms = random.randint(5000, 8000)
        self._scatter_until_ms = now + duration_ms

    def take_down_and_return_to_base(self):
        # Triggered when Pacman and ghost collide during scatter
        # Keep scatter visuals while returning to base
        self.scatter_active = True
        self.returning_to_base = True
        # Increase speed while returning
        self.speed = self.return_speed
        # Ensure motion toward the graph
        self._plan_move_from_non_node()

    def reset_to_spawn(self):
        self.px = self.spawn_tile[0] * TILE_SIZE + TILE_SIZE // 2
        self.py = self.spawn_tile[1] * TILE_SIZE + TILE_SIZE // 2
        self.dx, self.dy = 0, 0
        self.current_target_node = None
        self.path_nodes = []
        # Restore normal chase speed and visuals
        self.speed = self.normal_speed
        self.scatter_active = False
        self._plan_move_from_non_node()
        self.last_safe_tile = self.spawn_tile

    def on_map_changed(self):
        """Rebuild pathfinding graph and spawn for a new maze layout."""
        # Rebuild nodes/graph for current MAP_DATA
        self.nodes, self.adj = build_graph()
        # Recompute spawn tile from current MAP_DATA using configured spawn_values
        spawn_tiles = []
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                if MAP_DATA[y][x] in self.spawn_values:
                    spawn_tiles.append((x, y))
        if spawn_tiles:
            self.spawn_tile = random.choice(spawn_tiles)
        else:
            self.spawn_tile = (MAP_WIDTH // 2, MAP_HEIGHT // 2)
        # Rebuild return graph and reset
        self.nodes_return, self.adj_return = self._build_return_graph()
        self.reset_to_spawn()

    def current_tile(self):
        return int(self.px // TILE_SIZE), int(self.py // TILE_SIZE)

    def at_tile_center(self):
        cx = (self.px % TILE_SIZE)
        cy = (self.py % TILE_SIZE)
        center = TILE_SIZE // 2
        return abs(cx - center) <= 1 and abs(cy - center) <= 1

    def snap_to_center(self):
        tx, ty = self.current_tile()
        self.px = tx * TILE_SIZE + TILE_SIZE // 2
        self.py = ty * TILE_SIZE + TILE_SIZE // 2

    def _align_to_axis_center(self):
        """Gently align orthogonal axis to tile center to avoid visual jumps."""
        tx, ty = self.current_tile()
        center = TILE_SIZE // 2
        corr = max(0.4, min(1.0, self.speed * 0.5))
        if self.dx != 0 and self.dy == 0:
            desired = ty * TILE_SIZE + center
            diff = desired - self.py
            if abs(diff) <= 1:
                self.py = desired
            else:
                self.py += math.copysign(min(abs(diff), corr), diff)
        elif self.dy != 0 and self.dx == 0:
            desired = tx * TILE_SIZE + center
            diff = desired - self.px
            if abs(diff) <= 1:
                self.px = desired
            else:
                self.px += math.copysign(min(abs(diff), corr), diff)

    def _next_tile_to_nearest_node(self, start_tile):
        # BFS over walkable tiles to find nearest graph node and return next step from start
        from collections import deque
        sx, sy = start_tile
        if (sx, sy) in self.nodes:
            return None
        dq = deque()
        dq.append((sx, sy))
        parent = { (sx, sy): None }
        seen = { (sx, sy) }
        while dq:
            x, y = dq.popleft()
            for nx, ny in neighbors_with_tunnel(x, y):
                if (nx, ny) in seen:
                    continue
                parent[(nx, ny)] = (x, y)
                if (nx, ny) in self.nodes:
                    # reconstruct path from start to this node
                    path = [(nx, ny)]
                    cur = (nx, ny)
                    while parent[cur] is not None:
                        cur = parent[cur]
                        path.append(cur)
                    path.reverse()
                    if len(path) >= 2:
                        return path[1]  # first step from start
                    else:
                        return None
                seen.add((nx, ny))
                dq.append((nx, ny))
        return None

    def _plan_move_from_non_node(self):
        tx, ty = self.current_tile()
        if (tx, ty) not in self.nodes:
            next_step = self._next_tile_to_nearest_node((tx, ty))
            if next_step is not None:
                self.choose_next_direction_to(next_step)

    def _next_tile_towards(self, start_tile, target_tile):
        """BFS over walkable tiles; return immediate next step toward target."""
        sx, sy = start_tile
        tx, ty = target_tile
        if (sx, sy) == (tx, ty):
            return None
        from collections import deque
        dq = deque()
        dq.append((sx, sy))
        parent = { (sx, sy): None }
        seen = { (sx, sy) }
        while dq:
            x, y = dq.popleft()
            for nx, ny in neighbors_with_tunnel(x, y):
                if (nx, ny) in seen:
                    continue
                parent[(nx, ny)] = (x, y)
                if (nx, ny) == (tx, ty):
                    # reconstruct path and return first step
                    path = [(nx, ny)]
                    cur = (nx, ny)
                    while parent[cur] is not None:
                        cur = parent[cur]
                        path.append(cur)
                    path.reverse()
                    if len(path) >= 2:
                        return path[1]
                    return None
                seen.add((nx, ny))
                dq.append((nx, ny))
        return None

    def _build_return_graph(self):
        # Copy base nodes/adj and insert spawn tile as an explicit node with edges
        nodes = set(self.nodes)
        adj = {u: list(vs) for u, vs in self.adj.items()}
        nodes.add(self.spawn_tile)

        def raycast_from(x, y, dx, dy):
            cx, cy = x, y
            dist = 0
            while True:
                nx, ny = cx + dx, cy + dy
                if ny == 9 and (nx < 0 or nx >= MAP_WIDTH):
                    if nx < 0:
                        nx = MAP_WIDTH - 1
                    elif nx >= MAP_WIDTH:
                        nx = 0
                if not is_walkable(nx, ny):
                    return None
                dist += 1
                cx, cy = nx, ny
                if (cx, cy) in nodes:
                    return (cx, cy, dist)

        adj.setdefault(self.spawn_tile, [])
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            hit = raycast_from(self.spawn_tile[0], self.spawn_tile[1], dx, dy)
            if hit is not None:
                nx, ny, w = hit
                if (nx, ny) in nodes:
                    adj[self.spawn_tile].append(((nx, ny), w))
                    adj.setdefault((nx, ny), []).append((self.spawn_tile, w))

        return nodes, adj

    def handle_tunnel(self):
        tx, ty = self.current_tile()
        if ty != 9:
            return
        now = pygame.time.get_ticks()
        if now < self._wrap_cooldown_until:
            return
        pixel_in_tile = self.px % TILE_SIZE
        if tx == 0 and self.dx < 0:
            if pixel_in_tile < TILE_SIZE // 2:
                self.px = (MAP_WIDTH - 1) * TILE_SIZE + TILE_SIZE // 2
                self._wrap_cooldown_until = now + 60
        elif tx == MAP_WIDTH - 1 and self.dx > 0:
            if pixel_in_tile > TILE_SIZE // 2:
                self.px = TILE_SIZE // 2
                self._wrap_cooldown_until = now + 60

    def choose_next_direction_to(self, next_node):
        x, y = self.current_tile()
        nx, ny = next_node
        # Edge should be straight (same row or same column), except tunnel wrap
        if y == ny:
            # Horizontal move; decide direction considering wrap
            if x == 0 and nx == MAP_WIDTH - 1:
                self.dx, self.dy = -1, 0
            elif x == MAP_WIDTH - 1 and nx == 0:
                self.dx, self.dy = 1, 0
            else:
                self.dx = 1 if nx > x else -1
                self.dy = 0
        elif x == nx:
            self.dx, self.dy = 0, (1 if ny > y else -1)
        else:
            # Unexpected; fallback to greedy step
            self.dx = 1 if nx > x else (-1 if nx < x else 0)
            self.dy = 1 if ny > y else (-1 if ny < y else 0)

    def recompute_path_if_needed(self):
        # Only recompute when at node (turn or junction), per requirement
        tx, ty = self.current_tile()
        if (tx, ty) not in self.nodes:
            return
        # Determine target based on mode
        if self.returning_to_base:
            target_node = self.spawn_tile
        else:
            target_node = self._select_chase_target_node()
        start_node = (tx, ty)
        if self.returning_to_base:
            path = dijkstra(self.adj_return, start_node, target_node)
        else:
            path = dijkstra(self.adj, start_node, target_node)
        self.path_nodes = path
        # Set the immediate next node as the target (skip start)
        if len(path) >= 2:
            self.current_target_node = path[1]
            self.choose_next_direction_to(self.current_target_node)
        else:
            # Fallback when already at target node: take a step toward raw target tile
            self.current_target_node = None
            raw_target_tile = self._select_target_tile() if not self.returning_to_base else self.spawn_tile
            step = self._next_tile_towards((tx, ty), raw_target_tile)
            if step is not None:
                self.choose_next_direction_to(step)
            else:
                # Secondary fallback: move toward nearest node of raw target
                target_node2 = nearest_node_from_tile(raw_target_tile, self.nodes)
                step2 = self._next_tile_towards((tx, ty), target_node2)
                if step2 is not None:
                    self.choose_next_direction_to(step2)
                else:
                    # As a final fallback, pick any walkable neighbor toward target
                    self._choose_any_walkable_direction(raw_target_tile)

    def _select_chase_target_node(self):
        # Hook for per-ghost behavior. Default is Blinky's aggressive chase.
        if self.pacman is not None:
            p_tile = (int(self.pacman.px // TILE_SIZE), int(self.pacman.py // TILE_SIZE))
        else:
            p_tile = (MAP_WIDTH // 2, MAP_HEIGHT // 2)
        if self.behavior == "pinky":
            # Ambusher: aim 4 tiles ahead of Pacman's facing direction
            dx = getattr(self.pacman, 'dx', 0)
            dy = getattr(self.pacman, 'dy', 0)
            tx = p_tile[0] + 4 * dx
            ty = p_tile[1] + 4 * dy
            # Clamp within bounds; nearest_node will handle walls
            tx = max(0, min(MAP_WIDTH - 1, tx))
            ty = max(0, min(MAP_HEIGHT - 1, ty))
            return nearest_node_from_tile((tx, ty), self.nodes)
        if self.behavior == "inky" and self.partner is not None:
            # Flanker: compute a point 2 tiles ahead of Pacman, then vector from Blinky to that point and double it
            dx = getattr(self.pacman, 'dx', 0)
            dy = getattr(self.pacman, 'dy', 0)
            ahead_x = p_tile[0] + 2 * dx
            ahead_y = p_tile[1] + 2 * dy
            ahead_x = max(0, min(MAP_WIDTH - 1, ahead_x))
            ahead_y = max(0, min(MAP_HEIGHT - 1, ahead_y))
            b_tx, b_ty = self.partner.current_tile()
            target_x = 2 * ahead_x - b_tx
            target_y = 2 * ahead_y - b_ty
            target_x = max(0, min(MAP_WIDTH - 1, target_x))
            target_y = max(0, min(MAP_HEIGHT - 1, target_y))
            return nearest_node_from_tile((target_x, target_y), self.nodes)
        if self.behavior == "clyde":
            # Coward: if distance to Pacman <= threshold, retreat to home corner; else chase like blinky
            tx, ty = self.current_tile()
            px, py = p_tile
            dx = tx - px
            dy = ty - py
            # Use Euclidean tile distance; threshold per prompt (6 tiles)
            dist = math.sqrt(dx * dx + dy * dy)
            if dist <= 6:
                # Retreat to home corner node
                target_node = self._get_clyde_home_corner_node()
                return target_node
            # Otherwise chase
            return nearest_node_from_tile(p_tile, self.nodes)
        # For 'blinky' and default, aim at Pacman's current tile (nearest node)
        return nearest_node_from_tile(p_tile, self.nodes)

    def set_partner(self, ghost):
        self.partner = ghost

    def _get_clyde_home_corner_node(self):
        # Determine a home corner for Clyde (bottom-left typical). Cache it.
        if self.home_corner_node is not None:
            return self.home_corner_node
        # Pick a corner tile near bottom-left inside the maze bounds
        corner_tile = (1, max(0, MAP_HEIGHT - 2))
        self.home_corner_node = nearest_node_from_tile(corner_tile, self.nodes)
        return self.home_corner_node

    # ------- Target tile helpers to avoid freeze and ensure grid alignment -------
    def _get_pac_tile_or_center(self):
        if self.pacman is not None:
            return (int(self.pacman.px // TILE_SIZE), int(self.pacman.py // TILE_SIZE))
        return (MAP_WIDTH // 2, MAP_HEIGHT // 2)

    def _compute_pinky_target_tile(self, p_tile):
        dx = getattr(self.pacman, 'dx', 0)
        dy = getattr(self.pacman, 'dy', 0)
        tx = p_tile[0] + 4 * dx
        ty = p_tile[1] + 4 * dy
        tx = max(0, min(MAP_WIDTH - 1, tx))
        ty = max(0, min(MAP_HEIGHT - 1, ty))
        return (tx, ty)

    def _compute_inky_target_tile(self, p_tile):
        dx = getattr(self.pacman, 'dx', 0)
        dy = getattr(self.pacman, 'dy', 0)
        ahead_x = p_tile[0] + 2 * dx
        ahead_y = p_tile[1] + 2 * dy
        ahead_x = max(0, min(MAP_WIDTH - 1, ahead_x))
        ahead_y = max(0, min(MAP_HEIGHT - 1, ahead_y))
        b_tx, b_ty = self.partner.current_tile() if self.partner is not None else (ahead_x, ahead_y)
        target_x = 2 * ahead_x - b_tx
        target_y = 2 * ahead_y - b_ty
        target_x = max(0, min(MAP_WIDTH - 1, target_x))
        target_y = max(0, min(MAP_HEIGHT - 1, target_y))
        return (target_x, target_y)

    def _select_target_tile(self):
        # Return raw target tile (not necessarily a node) for step fallback
        p_tile = self._get_pac_tile_or_center()
        if self.returning_to_base:
            return self.spawn_tile
        if self.behavior == "pinky":
            return self._compute_pinky_target_tile(p_tile)
        if self.behavior == "inky":
            return self._compute_inky_target_tile(p_tile)
        if self.behavior == "clyde":
            tx, ty = self.current_tile()
            px, py = p_tile
            dx = tx - px
            dy = ty - py
            dist = math.sqrt(dx * dx + dy * dy)
            if dist <= 6:
                return (1, max(0, MAP_HEIGHT - 2))
            return p_tile
        # blinky/default
        return p_tile

    def _choose_any_walkable_direction(self, target_tile=None):
        """Pick a simple walkable direction, preferably reducing distance to target."""
        tx, ty = self.current_tile()
        best = None
        best_score = float('inf')
        for nx, ny in neighbors_with_tunnel(tx, ty):
            # Manhattan distance to target
            if target_tile is not None:
                score = abs(nx - target_tile[0]) + abs(ny - target_tile[1])
            else:
                score = 0
            if score < best_score:
                best_score = score
                best = (nx, ny)
        if best is not None:
            self.choose_next_direction_to(best)
        else:
            self.dx, self.dy = 0, 0

    def update(self):
        # Mouth/animation not needed for ghost; update path decisions at nodes
        # Aggressive re-path for Blinky when Pacman moves tiles
        if not self.returning_to_base and not self.scatter_active and self.pacman is not None:
            cur_p_tile = (int(self.pacman.px // TILE_SIZE), int(self.pacman.py // TILE_SIZE))
            if cur_p_tile != self._last_pac_tile:
                self._last_pac_tile = cur_p_tile
                # If at a node, recompute immediately for responsiveness
                tx_tmp, ty_tmp = self.current_tile()
                if (tx_tmp, ty_tmp) in self.nodes:
                    self.recompute_path_if_needed()
        # If not moving and not centered, try to step toward nearest node
        if self.dx == 0 and self.dy == 0 and not self.at_tile_center():
            tx0, ty0 = self.current_tile()
            ns0 = self._next_tile_to_nearest_node((tx0, ty0))
            if ns0 is not None:
                self.choose_next_direction_to(ns0)
            else:
                self._choose_any_walkable_direction(self._select_target_tile())
        if self.at_tile_center():
            self.snap_to_center()
            tx, ty = self.current_tile()
            # Update last safe tile if walkable
            if is_walkable(tx, ty):
                self.last_safe_tile = (tx, ty)
            # Arrived at current target node?
            if self.current_target_node is not None and (tx, ty) == self.current_target_node:
                # Reached this node; plan toward next or recompute toward Pacman again
                self.recompute_path_if_needed()
            else:
                # At center; if current tile is a node, recompute toward Pacman
                if (tx, ty) in self.nodes:
                    self.recompute_path_if_needed()
                else:
                    # Ensure we have a direction to reach a node if stuck
                    if self.dx == 0 and self.dy == 0:
                        next_step = self._next_tile_to_nearest_node((tx, ty))
                        if next_step is not None:
                            self.choose_next_direction_to(next_step)

        # Move along current direction if walkable; else stop
        next_px = self.px + self.dx * self.speed
        next_py = self.py + self.dy * self.speed
        # Predict next tile
        next_tx = int(next_px // TILE_SIZE)
        next_ty = int(next_py // TILE_SIZE)
        # Allow movement inside the same tile even if the next tile is wall; only block when crossing boundary
        cur_tx, cur_ty = self.current_tile()
        crossing_tile_boundary = (next_tx != cur_tx) or (next_ty != cur_ty)
        if not crossing_tile_boundary or is_walkable(next_tx, next_ty):
            self.px = next_px
            self.py = next_py
            # mark movement time
            try:
                self._last_move_ms = pygame.time.get_ticks()
            except Exception:
                pass
            # Keep movement visually aligned to corridor centers
            self._align_to_axis_center()
        else:
            # Blocked by wall when attempting to leave current tile
            # Snap to center of current tile and choose a new direction
            self.px = cur_tx * TILE_SIZE + TILE_SIZE // 2
            self.py = cur_ty * TILE_SIZE + TILE_SIZE // 2
            self.dx = 0
            self.dy = 0
            if self.returning_to_base:
                ns = self._next_tile_towards((cur_tx, cur_ty), self.spawn_tile)
                if ns is not None:
                    self.choose_next_direction_to(ns)
            else:
                if (cur_tx, cur_ty) in self.nodes:
                    self.recompute_path_if_needed()
                else:
                    ns = self._next_tile_to_nearest_node((cur_tx, cur_ty))
                    if ns is not None:
                        self.choose_next_direction_to(ns)
            # After recalculating direction, keep axis aligned
            self._align_to_axis_center()
        # Handle tunnel wrapping like Pacman
        self.handle_tunnel()
        # Maintain axis alignment after wrapping
        self._align_to_axis_center()

        # Idle freeze guard: if no movement for 300ms, pick any walkable direction toward target
        try:
            now2 = pygame.time.get_ticks()
            if now2 - self._last_move_ms > 300:
                self._choose_any_walkable_direction(self._select_target_tile())
                self._last_move_ms = now2
        except Exception:
            pass

        # Guard: if we ended up inside a wall tile (due to speed/overshoot), snap back
        ctx, cty = self.current_tile()
        if not is_walkable(ctx, cty):
            sx, sy = self.last_safe_tile
            self.px = sx * TILE_SIZE + TILE_SIZE // 2
            self.py = sy * TILE_SIZE + TILE_SIZE // 2
            self.dx = 0
            self.dy = 0
            # Plan next step depending on mode
            if self.returning_to_base:
                # Use return graph from nearest node toward spawn
                tx, ty = self.current_tile()
                if (tx, ty) in self.nodes_return:
                    self.recompute_path_if_needed()
                else:
                    ns = self._next_tile_to_nearest_node((tx, ty))
                    if ns is not None:
                        self.choose_next_direction_to(ns)
            else:
                # Normal chase: toward nearest node to Pacman
                tx, ty = self.current_tile()
                if (tx, ty) in self.nodes:
                    self.recompute_path_if_needed()
                else:
                    ns = self._next_tile_to_nearest_node((tx, ty))
                    if ns is not None:
                        self.choose_next_direction_to(ns)

        # Auto-exit scatter when time expires (unless returning to base)
        if self.scatter_active and not self.returning_to_base:
            if self._scatter_until_ms is not None and pygame.time.get_ticks() >= self._scatter_until_ms:
                self.scatter_active = False
                self._scatter_until_ms = None

        # Finish return-to-base when reaching spawn center
        if self.returning_to_base:
            if self.at_tile_center() and self.current_tile() == self.spawn_tile:
                self.reset_to_spawn()
                self.returning_to_base = False

    def draw(self):
        cx, cy = int(self.px), int(self.py)
        if self.scatter_active and self.scatter_image is not None:
            rect = self.scatter_image.get_rect(center=(cx, cy))
            screen.blit(self.scatter_image, rect)
        elif self.image is not None:
            rect = self.image.get_rect(center=(cx, cy))
            screen.blit(self.image, rect)
        else:
            body_color = self.color
            pygame.draw.circle(screen, body_color, (cx, cy), self.radius)
            # Eyes
            eye_offset_x = self.radius // 2
            eye_offset_y = -self.radius // 3
            eye_radius = max(2, self.radius // 4)
            pygame.draw.circle(screen, (255, 255, 255), (cx - eye_offset_x, cy + eye_offset_y), eye_radius)
            pygame.draw.circle(screen, (255, 255, 255), (cx + eye_offset_x, cy + eye_offset_y), eye_radius)
            pupil_radius = max(1, eye_radius // 2)
            pygame.draw.circle(screen, (0, 0, 255), (cx - eye_offset_x + 1, cy + eye_offset_y), pupil_radius)
            pygame.draw.circle(screen, (0, 0, 255), (cx + eye_offset_x + 1, cy + eye_offset_y), pupil_radius)
