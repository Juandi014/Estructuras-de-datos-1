"""
color_scheme.py
---------------
Centralized design tokens for the SkyBalance 'Terminal Aéreo' theme.
All UI modules import colors, fonts, and sizing constants from here.
This ensures visual consistency across every screen.
"""

import pygame


# ------------------------------------------------------------------
# Color palette — Terminal Aéreo
# ------------------------------------------------------------------

# Backgrounds
BG_DEEP        = (14,  11,  8)     # #0e0b08 — main background
BG_SURFACE     = (26,  20,  16)    # #1a1410 — card / panel surface
BG_SURFACE2    = (36,  28,  22)    # #241c16 — elevated surface
BG_GRID        = (22,  17,  13)    # subtle grid line color

# Borders
BORDER         = (60,  45,  32)    # #3c2d20 — default border
BORDER_ACTIVE  = (245, 166, 35)    # #f5a623 — active / focused border

# Accents
AMBER          = (245, 166, 35)    # #f5a623 — primary accent (amber)
AMBER_DIM      = (140, 90,  15)    # dimmed amber for inactive states
GREEN_TERM     = (57,  255, 20)    # #39ff14 — success / active terminal green
GREEN_DIM      = (30,  100, 10)    # dimmed green
CRITICAL       = (255, 69,  69)    # #ff4545 — critical / error
CRITICAL_DIM   = (120, 30,  30)    # dimmed critical
WARN           = (255, 200, 50)    # warning yellow
BLUE_INFO      = (80,  180, 255)   # informational blue

# Text
TEXT_PRIMARY   = (240, 230, 211)   # #f0e6d3 — cream main text
TEXT_SECONDARY = (160, 140, 115)   # muted secondary text
TEXT_DIM       = (90,  75,  60)    # very muted / disabled text

# Node states
NODE_NORMAL    = AMBER
NODE_CRITICAL  = CRITICAL
NODE_STRESS    = (80,  65,  55)    # grey-brown for stress mode
NODE_ROTATED   = (255, 200, 50)    # yellow highlight after rotation
NODE_SELECTED  = GREEN_TERM
NODE_NEXT      = (255, 140, 40)    # next-in-queue node

# Transparent overlays (RGBA — use only with surfaces that support alpha)
OVERLAY_DARK   = (0,   0,   0,   180)
OVERLAY_AMBER  = (245, 166, 35,  25)
OVERLAY_RED    = (255, 69,  69,  25)


# ------------------------------------------------------------------
# Typography
# ------------------------------------------------------------------

def load_fonts() -> dict:
    """
    Loads and returns the font registry.
    Falls back to pygame's default monospace font if system fonts are unavailable.

    Returns:
        dict: Mapping of font role → pygame.font.Font instance.
    """
    mono = _find_mono_font()

    return {
        # Display — large titles
        "title_xl":  pygame.font.SysFont(mono, 52, bold=True),
        "title_lg":  pygame.font.SysFont(mono, 36, bold=True),
        "title_md":  pygame.font.SysFont(mono, 24, bold=True),

        # UI labels and headings
        "label_lg":  pygame.font.SysFont(mono, 18, bold=True),
        "label_md":  pygame.font.SysFont(mono, 14, bold=True),
        "label_sm":  pygame.font.SysFont(mono, 11, bold=True),

        # Body and data
        "body_md":   pygame.font.SysFont(mono, 14),
        "body_sm":   pygame.font.SysFont(mono, 12),
        "body_xs":   pygame.font.SysFont(mono, 10),

        # Node labels (rendered inside tree nodes)
        "node_md":   pygame.font.SysFont(mono, 12, bold=True),
        "node_sm":   pygame.font.SysFont(mono, 10, bold=True),
    }


def _find_mono_font() -> str:
    """
    Finds the best available monospace font on the system.

    Returns:
        str: Font name suitable for pygame.font.SysFont.
    """
    candidates = [
        "Courier New", "Courier", "Lucida Console",
        "Consolas", "DejaVu Sans Mono", "monospace",
    ]
    available = pygame.font.get_fonts()
    for name in candidates:
        if name.lower().replace(" ", "") in available:
            return name
    return pygame.font.get_default_font()


# ------------------------------------------------------------------
# Sizing and layout constants
# ------------------------------------------------------------------

# Window
WINDOW_W       = 1280
WINDOW_H       = 720
FPS            = 60

# Navigation bar
NAV_H          = 44
NAV_PADDING    = 16

# Panels
PANEL_PADDING  = 16
PANEL_RADIUS   = 0          # Sharp corners — no border radius in Pygame rects

# Buttons
BTN_H          = 34
BTN_PADDING_X  = 16
BTN_RADIUS     = 2

# Tree node
NODE_RADIUS    = 26         # Radius of the hexagon circumscribed circle
NODE_H_SPACING = 72         # Horizontal spacing between sibling nodes
NODE_V_SPACING = 80         # Vertical spacing between tree levels

# Grid
GRID_SPACING   = 40         # Pixels between grid lines on background


# ------------------------------------------------------------------
# Node color resolver
# ------------------------------------------------------------------

def node_color(flight_node) -> tuple:
    """
    Returns the appropriate fill color for a tree node based on its state.

    Priority order:
      1. Critical depth   → CRITICAL
      2. Just rotated     → NODE_ROTATED  (caller must set node._just_rotated)
      3. Selected         → NODE_SELECTED
      4. Stress mode node → NODE_STRESS
      5. Default          → NODE_NORMAL

    Args:
        flight_node: FlightNode instance with state flags.

    Returns:
        tuple: RGB color tuple.
    """
    if flight_node.is_critical:
        return NODE_CRITICAL
    if getattr(flight_node, "_just_rotated", False):
        return NODE_ROTATED
    if getattr(flight_node, "_selected", False):
        return NODE_SELECTED
    if getattr(flight_node, "_stress", False):
        return NODE_STRESS
    return NODE_NORMAL


def border_color(flight_node) -> tuple:
    """
    Returns the border color for a tree node.

    Args:
        flight_node: FlightNode instance.

    Returns:
        tuple: RGB color tuple.
    """
    base = node_color(flight_node)
    # Brighten slightly for the border
    return tuple(min(255, c + 40) for c in base)