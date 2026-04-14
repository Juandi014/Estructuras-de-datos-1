"""
color_scheme.py
---------------
SkyBalance - Versión Híbrida Segura
- Usa tu paleta Color Hunt (#43766C, #F8FAE5, #B19470, #76453B)
- Mantiene compatibilidad TOTAL con todas las pantallas existentes
"""

import pygame

# ==================================================================
# TU PALETA COLOR HUNT (la que elegiste)
# ==================================================================

PRIMARY        = (67,  118, 108)   # #43766C - Verde azulado
LIGHT          = (248, 250, 229)   # #F8FAE5 - Crema claro
SECONDARY      = (177, 148, 112)   # #B19470 - Beige cálido
DARK_ACCENT    = (118, 69,  59)    # #76453B - Marrón oscuro

# ==================================================================
# COLORES DE FONDO (mantienen estilo terminal oscuro)
# ==================================================================

BG_DEEP        = (14,  11,  8)
BG_SURFACE     = (26,  20,  16)
BG_SURFACE2    = (36,  28,  22)
BG_GRID        = (22,  17,  13)

# ==================================================================
# COMPATIBILIDAD TOTAL (alias para que NO se rompa nada)
# ==================================================================

AMBER          = PRIMARY           # ← Ahora es tu verde-azulado
AMBER_DIM      = (100, 140, 120)
GREEN_TERM     = PRIMARY           # ← También usa tu primary
CRITICAL       = DARK_ACCENT    # Rojo se mantiene para alertas
WARN           = SECONDARY
BLUE_INFO      = (80,  180, 255)

# Text
TEXT_PRIMARY   = LIGHT
TEXT_SECONDARY = (200, 190, 170)
TEXT_DIM       = (130, 130, 120)

# Node states
NODE_NORMAL    = PRIMARY
NODE_CRITICAL  = CRITICAL
NODE_STRESS    = DARK_ACCENT
NODE_ROTATED   = (255, 200, 50)
NODE_SELECTED  = LIGHT
NODE_NEXT      = (255, 140, 40)

# Borders
BORDER         = (60,  45,  32)
BORDER_ACTIVE  = PRIMARY

# Overlays
OVERLAY_DARK   = (0,   0,   0,   180)

# ==================================================================
# LAYOUT CONSTANTS - TODAS las que usan tus pantallas
# ==================================================================

WINDOW_W       = 1280
WINDOW_H       = 720
FPS            = 60

NAV_H          = 44
NAV_PADDING    = 16

PANEL_PADDING  = 16
PANEL_RADIUS   = 0

CARD_RADIUS    = 12          # ← Agregado (el que faltaba)
BTN_H          = 34
BTN_PADDING_X  = 16
BTN_RADIUS     = 2

NODE_RADIUS    = 26
NODE_H_SPACING = 72
NODE_V_SPACING = 80

GRID_SPACING   = 40

# ==================================================================
# TYPOGRAPHY
# ==================================================================

def load_fonts() -> dict:
    mono = _find_mono_font()
    return {
        "title_xl":  pygame.font.SysFont(mono, 52, bold=True),
        "title_lg":  pygame.font.SysFont(mono, 36, bold=True),
        "title_md":  pygame.font.SysFont(mono, 24, bold=True),
        "label_lg":  pygame.font.SysFont(mono, 18, bold=True),
        "label_md":  pygame.font.SysFont(mono, 14, bold=True),
        "label_sm":  pygame.font.SysFont(mono, 11, bold=True),
        "body_md":   pygame.font.SysFont(mono, 14),
        "body_sm":   pygame.font.SysFont(mono, 12),
        "body_xs":   pygame.font.SysFont(mono, 10),
        "node_md":   pygame.font.SysFont(mono, 12, bold=True),
        "node_sm":   pygame.font.SysFont(mono, 10, bold=True),
    }


def _find_mono_font() -> str:
    candidates = ["Courier New", "Courier", "Lucida Console", "Consolas", "DejaVu Sans Mono", "monospace"]
    available = pygame.font.get_fonts()
    for name in candidates:
        if name.lower().replace(" ", "") in available:
            return name
    return pygame.font.get_default_font()


# ==================================================================
# HELPERS (sin cambios)
# ==================================================================

def node_color(flight_node):
    if getattr(flight_node, 'is_critical', False):
        return NODE_CRITICAL
    if getattr(flight_node, "_just_rotated", False):
        return NODE_ROTATED
    if getattr(flight_node, "_selected", False):
        return NODE_SELECTED
    if getattr(flight_node, "_stress", False):
        return NODE_STRESS
    return NODE_NORMAL


def border_color(flight_node):
    base = node_color(flight_node)
    return tuple(min(255, c + 40) for c in base)