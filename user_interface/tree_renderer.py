
from time import time

import pygame
import math
from user_interface.color_scheme import (
    BG_DEEP, BG_SURFACE, BORDER,
    AMBER, AMBER_DIM, TEXT_PRIMARY, TEXT_DIM,
    TEXT_SECONDARY, CRITICAL, GREEN_TERM,
    NODE_RADIUS, NODE_H_SPACING, NODE_V_SPACING,
    node_color, border_color,
)


# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

MIN_ZOOM   = 0.3
MAX_ZOOM   = 2.0
ZOOM_STEP  = 0.1
EDGE_WIDTH = 1


class TreeRenderer:
    """
    Handles layout computation and rendering of the AVL tree.

    Args:
        viewport_rect : pygame.Rect defining the drawable area on screen.
    """

    def __init__(self, viewport_rect: pygame.Rect):
        self.viewport   = viewport_rect
        self.zoom       = 1.0
        self.offset_x   = 0.0
        self.offset_y   = 40.0

        # Drag state
        self._dragging      = False
        self._drag_start    = (0, 0)
        self._offset_start  = (0, 0)

        # Computed node positions: code → (x, y) in tree space
        self._positions     = {}

        # Currently highlighted node code (from search)
        self._highlighted   = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def set_highlighted(self, code) -> None:
        """Highlights a node by its flight code (used after search)."""
        self._highlighted = code

    def clear_highlight(self) -> None:
        """Removes any active node highlight."""
        self._highlighted = None

    def get_node_screen_pos(self, code) -> tuple | None:
        """
        Returns the screen (sx, sy) of the node with the given code,
        or None if the node hasn't been laid out yet.
        Used by MainScreen to draw the traversal highlight halo.

        Args:
            code : Flight code of the target node.

        Returns:
            tuple | None: (sx, sy) in screen coordinates, or None.
        """
        tree_pos = self._positions.get(code)
        if tree_pos is None:
            return None
        sx, sy = self._tree_to_screen(tree_pos)
        return int(sx), int(sy)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Processes zoom and scroll input events."""
        if not self.viewport.collidepoint(pygame.mouse.get_pos()):
            return
        if event.type == pygame.MOUSEWHEEL:
            self._handle_zoom(event.y)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._dragging     = True
            self._drag_start   = event.pos
            self._offset_start = (self.offset_x, self.offset_y)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = False
        elif event.type == pygame.MOUSEMOTION and self._dragging:
            self._handle_drag(event.pos)

    def draw(self, surface: pygame.Surface, root, stress_mode: bool = False) -> None:
        """
        Renders the full tree onto the given surface within the viewport.
        
        Args:
            surface     : Main pygame surface.
            root        : Root FlightNode of the AVL tree (or None).
            stress_mode : If True, renders degraded style (red edges, reddish nodes, warning).
                          Default False maintains full compatibility with MainScreen.
        """
        # Clip drawing to the viewport area
        surface.set_clip(self.viewport)
        pygame.draw.rect(surface, BG_DEEP, self.viewport)

        if root is None:
            self._draw_empty(surface)
            surface.set_clip(None)
            return

        # Compute layout positions (unchanged)
        self._positions = {}
        self._compute_positions(root, 0, 0, _subtree_width(root))

        # Draw edges and nodes with stress support
        if stress_mode:
            self._draw_edges_stress(surface, root)
            self._draw_nodes_stress(surface, root)
            self._draw_stress_overlay(surface)
        else:
            self._draw_edges(surface, root)      # método original
            self._draw_nodes(surface, root)      # método original

        surface.set_clip(None)

    def get_node_at(self, screen_pos: tuple, root):
        """
        Returns the FlightNode under the given screen position, or None.
        Used for click-to-select behavior.

        Args:
            screen_pos : (x, y) in screen coordinates.
            root       : Root FlightNode.

        Returns:
            FlightNode | None
        """
        if root is None or not self._positions:
            return None
        for node in _all_nodes(root):
            sx, sy = self._tree_to_screen(self._positions[node.code])
            dist = math.hypot(screen_pos[0] - sx, screen_pos[1] - sy)
            if dist <= NODE_RADIUS * self.zoom:
                return node
        return None

    def center_on_root(self, root) -> None:
        """Resets zoom and centers the view on the root node."""
        self.zoom     = 1.0
        self.offset_x = 0.0
        self.offset_y = 40.0

    # ------------------------------------------------------------------
    # Layout computation
    # ------------------------------------------------------------------

    def _compute_positions(self, node, depth: int, left_bound: float, width: float) -> None:
        """
        Recursively computes (x, y) positions for every node in tree space.
        Uses a simple centered layout based on subtree widths.

        Args:
            node       : Current FlightNode.
            depth      : Depth level of this node (root = 0).
            left_bound : Left boundary of this subtree's horizontal space.
            width      : Total horizontal space allocated to this subtree.
        """
        if node is None:
            return

        x = left_bound + width / 2
        y = depth * NODE_V_SPACING
        self._positions[node.code] = (x, y)

        left_width  = _subtree_width(node.getLeftChild())
        right_width = _subtree_width(node.getRightChild())

        self._compute_positions(node.getLeftChild(),  depth + 1, left_bound, left_width)
        self._compute_positions(node.getRightChild(), depth + 1, left_bound + left_width, right_width)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw_empty(self, surface: pygame.Surface) -> None:
        """Renders a placeholder when the tree has no data."""
        cx = self.viewport.centerx
        cy = self.viewport.centery
        msg1 = "// ÁRBOL VACÍO"
        msg2 = "Carga un archivo JSON para comenzar"
        s1 = _font_cache("label_md").render(msg1, True, AMBER_DIM) if False else None
        # Inline rendering without font cache for simplicity
        font_lg = pygame.font.SysFont("Courier New", 14, bold=True)
        font_sm = pygame.font.SysFont("Courier New", 12)
        t1 = font_lg.render(msg1, True, AMBER_DIM)
        t2 = font_sm.render(msg2, True, TEXT_DIM)
        surface.blit(t1, t1.get_rect(centerx=cx, centery=cy - 14))
        surface.blit(t2, t2.get_rect(centerx=cx, centery=cy + 10))

    def _draw_edges(self, surface: pygame.Surface, node) -> None:
        """Recursively draws lines connecting each node to its children."""
        if node is None:
            return
        sx, sy = self._tree_to_screen(self._positions[node.code])

        for child in (node.getLeftChild(), node.getRightChild()):
            if child is not None:
                cx, cy = self._tree_to_screen(self._positions[child.code])
                pygame.draw.line(surface, BORDER, (int(sx), int(sy)), (int(cx), int(cy)), EDGE_WIDTH)
                self._draw_edges(surface, child)

    def _draw_nodes(self, surface: pygame.Surface, node) -> None:
        """Recursively draws all nodes as hexagons with labels."""
        if node is None:
            return
        sx, sy = self._tree_to_screen(self._positions[node.code])
        self._draw_single_node(surface, node, int(sx), int(sy))
        self._draw_nodes(surface, node.getLeftChild())
        self._draw_nodes(surface, node.getRightChild())

    def _draw_single_node(self, surface, node, sx: int, sy: int) -> None:
        """
        Draws one hexagon node with its code and balance factor labels.

        Args:
            surface : Target surface.
            node    : FlightNode to render.
            sx, sy  : Screen coordinates for the node center.
        """
        r = int(NODE_RADIUS * self.zoom)
        if r < 4:
            return

        fill   = node_color(node)
        stroke = border_color(node)

        # Highlight override
        if self._highlighted is not None and node.code == self._highlighted:
            fill   = GREEN_TERM
            stroke = (180, 255, 100)
    
        # Draw hexagon
        pts = _hex_points(sx, sy, r)
        pygame.draw.polygon(surface, _darken(fill, 0.15), pts)
        pygame.draw.polygon(surface, stroke, pts, max(1, int(1.5 * self.zoom)))

        # Labels — only draw if zoom is large enough to read
        if r >= 10:
            font_size = max(8, int(11 * self.zoom))
            font = pygame.font.SysFont("Courier New", font_size, bold=True)
            code_surf = font.render(str(node.code), True, TEXT_PRIMARY)
            surface.blit(code_surf, code_surf.get_rect(centerx=sx, centery=sy))

        if r >= 16:
            bf_size = max(7, int(9 * self.zoom))
            bf_font = pygame.font.SysFont("Courier New", bf_size)
            bf_col  = CRITICAL if abs(node.balance_factor) > 1 else TEXT_DIM
            bf_surf = bf_font.render(f"bf:{node.balance_factor}", True, bf_col)
            surface.blit(bf_surf, bf_surf.get_rect(centerx=sx, top=sy + r + 2))

    # ------------------------------------------------------------------
    # Coordinate transforms
    # ------------------------------------------------------------------

    def _tree_to_screen(self, pos: tuple) -> tuple:
        """
        Converts a tree-space position to screen coordinates
        applying zoom and scroll offset.

        Args:
            pos : (x, y) in tree space.

        Returns:
            tuple: (sx, sy) in screen coordinates.
        """
        tx, ty = pos
        sx = self.viewport.centerx + (tx + self.offset_x) * self.zoom
        sy = self.viewport.top     + (ty + self.offset_y) * self.zoom
        return sx, sy

    # ------------------------------------------------------------------
    # Input handlers
    # ------------------------------------------------------------------

    def _handle_zoom(self, direction: int) -> None:
        """Zooms in or out centered on the mouse position."""
        self.zoom = max(MIN_ZOOM, min(MAX_ZOOM, self.zoom + direction * ZOOM_STEP))

    def _handle_drag(self, pos: tuple) -> None:
        """Updates scroll offset while dragging."""
        dx = (pos[0] - self._drag_start[0]) / self.zoom
        dy = (pos[1] - self._drag_start[1]) / self.zoom
        self.offset_x = self._offset_start[0] + dx
        self.offset_y = self._offset_start[1] + dy

# ------------------------------------------------------------------
# Stress Mode Drawing (NO se modificó nada del estrés original)
# ------------------------------------------------------------------

    def _draw_edges_stress(self, surface: pygame.Surface, node) -> None:
        """Draw edges in stress mode: thicker and red/critical color."""
        if node is None:
            return

        sx, sy = self._tree_to_screen(self._positions[node.code])

        for child in (node.getLeftChild(), node.getRightChild()):
            if child is not None:
                cx, cy = self._tree_to_screen(self._positions[child.code])
                pygame.draw.line(surface, CRITICAL, (int(sx), int(sy)), (int(cx), int(cy)), 4)
                self._draw_edges_stress(surface, child)

    def _draw_nodes_stress(self, surface: pygame.Surface, node) -> None:
        """Draw nodes in stress mode with reddish tint."""
        if node is None:
            return
        sx, sy = self._tree_to_screen(self._positions[node.code])
        self._draw_single_node_stress(surface, node, int(sx), int(sy))
        self._draw_nodes_stress(surface, node.getLeftChild())
        self._draw_nodes_stress(surface, node.getRightChild())

    def _draw_single_node_stress(self, surface, node, sx: int, sy: int) -> None:
        """Draw single node with stress visual: reddish fill and thicker border."""
        r = int(NODE_RADIUS * self.zoom)
        if r < 4:
            return

        # Stress colors
        fill = CRITICAL
        stroke = (255, 60, 40)

        # Highlight override (search still works)
        if self._highlighted is not None and node.code == self._highlighted:
            fill = GREEN_TERM
            stroke = (180, 255, 100)

        pts = _hex_points(sx, sy, r)
        pygame.draw.polygon(surface, _darken(fill, 0.15), pts)
        pygame.draw.polygon(surface, stroke, pts, 4)

        # Labels
        if r >= 10:
            font_size = max(8, int(11 * self.zoom))
            font = pygame.font.SysFont("Courier New", font_size, bold=True)
            code_surf = font.render(str(node.code), True, TEXT_PRIMARY)
            surface.blit(code_surf, code_surf.get_rect(centerx=sx, centery=sy))

        if r >= 16:
            bf_size = max(7, int(9 * self.zoom))
            bf_font = pygame.font.SysFont("Courier New", bf_size)
            bf_col = CRITICAL if abs(node.balance_factor) > 1 else TEXT_DIM
            bf_surf = bf_font.render(f"bf:{node.balance_factor}", True, bf_col)
            surface.blit(bf_surf, bf_surf.get_rect(centerx=sx, top=sy + r + 2))

        # Extra "DEFORMADO" label
        if r >= 20:
            warn_font = pygame.font.SysFont("Courier New", max(7, int(8 * self.zoom)))
            warn = warn_font.render("DEFORMADO", True, (255, 220, 180))
            surface.blit(warn, warn.get_rect(centerx=sx, top=sy + r + 18))

    def _draw_stress_overlay(self, surface: pygame.Surface) -> None:
        """Clear visual warning banner when stress mode is active."""
        font = pygame.font.SysFont("Courier New", 18, bold=True)
        text = font.render("MODO ESTRÉS ACTIVO — ÁRBOL DEGRADADO", True, CRITICAL)
        surface.blit(text, (self.viewport.x + 20, self.viewport.y + 15))


# ------------------------------------------------------------------
# NEW: Rotation Animation Support (solo se usa durante Rebalanceo Global)
# ------------------------------------------------------------------

    def _draw_single_node(self, surface, node, sx: int, sy: int) -> None:
        """
        Draws one hexagon node with its code and balance factor labels.
        AÑADIDO: Soporte para animación de rotaciones cuando no está en stress mode.
        """
        r = int(NODE_RADIUS * self.zoom)
        if r < 4:
            return

        fill   = node_color(node)
        stroke = border_color(node)

        # Highlight override
        if self._highlighted is not None and node.code == self._highlighted:
            fill   = GREEN_TERM
            stroke = (180, 255, 100)

        # === ANIMACIÓN DE ROTACIONES (solo cuando hay pulse_nodes) ===
        pulse_offset = 0.0
        if (hasattr(self, '_pulse_nodes') and 
            hasattr(self, '_pulse_offset') and 
            node.code in self._pulse_nodes):
            pulse_offset = self._pulse_offset
            # Pequeño pulso de escala para dar sensación de movimiento
            r = int(r * (1 + 0.07 * math.sin(time.time() * 12)))

        sx += pulse_offset

        # Draw hexagon
        pts = _hex_points(sx, sy, r)
        pygame.draw.polygon(surface, _darken(fill, 0.15), pts)
        pygame.draw.polygon(surface, stroke, pts, max(1, int(1.5 * self.zoom)))

        # Labels
        if r >= 10:
            font_size = max(8, int(11 * self.zoom))
            font = pygame.font.SysFont("Courier New", font_size, bold=True)
            code_surf = font.render(str(node.code), True, TEXT_PRIMARY)
            surface.blit(code_surf, code_surf.get_rect(centerx=sx, centery=sy))

        if r >= 16:
            bf_size = max(7, int(9 * self.zoom))
            bf_font = pygame.font.SysFont("Courier New", bf_size)
            bf_col  = CRITICAL if abs(node.balance_factor) > 1 else TEXT_DIM
            bf_surf = bf_font.render(f"bf:{node.balance_factor}", True, bf_col)
            surface.blit(bf_surf, bf_surf.get_rect(centerx=sx, top=sy + r + 2))

# ------------------------------------------------------------------
# Geometry helpers
# ------------------------------------------------------------------

def _hex_points(cx: int, cy: int, r: int) -> list:
    """
    Returns the 6 vertices of a flat-top hexagon centered at (cx, cy).

    Args:
        cx, cy : Center coordinates.
        r      : Circumscribed circle radius.

    Returns:
        list: List of (x, y) integer tuples.
    """
    return [
        (int(cx + r * math.cos(math.radians(60 * i - 30))),
         int(cy + r * math.sin(math.radians(60 * i - 30))))
        for i in range(6)
    ]


def _subtree_width(node) -> float:
    """
    Returns the horizontal space needed for a subtree.
    Leaf nodes occupy one unit; internal nodes occupy the sum of their children.

    Args:
        node : FlightNode or None.

    Returns:
        float: Width in tree-space units scaled by NODE_H_SPACING.
    """
    if node is None:
        return 0.0
    left  = _subtree_width(node.getLeftChild())
    right = _subtree_width(node.getRightChild())
    return max(NODE_H_SPACING, left + right)


def _all_nodes(node) -> list:
    """Returns a flat list of all nodes via BFS."""
    if node is None:
        return []
    result, queue = [], [node]
    while queue:
        n = queue.pop(0)
        result.append(n)
        if n.getLeftChild():
            queue.append(n.getLeftChild())
        if n.getRightChild():
            queue.append(n.getRightChild())
    return result


def _darken(color: tuple, factor: float) -> tuple:
    """
    Returns a darkened version of a color for node fill.

    Args:
        color  : RGB tuple.
        factor : How much to darken (0.0 = no change, 1.0 = black).

    Returns:
        tuple: Darkened RGB tuple.
    """
    return tuple(max(0, int(c * (1 - factor))) for c in color)