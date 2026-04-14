
import pygame
import math
import random
from user_interface.color_scheme import (
    BG_DEEP, BG_SURFACE, BG_SURFACE2,
    BORDER, BORDER_ACTIVE,
    AMBER, AMBER_DIM, GREEN_TERM, CRITICAL,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DIM,
    GRID_SPACING, WINDOW_W, WINDOW_H, NAV_H,
    BTN_H, BTN_PADDING_X,
)

# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

TITLE_TEXT     = "SKY BALANCE"
SUBTITLE_TEXT  = "AVL FLIGHT MANAGEMENT SYSTEM"
TYPEWRITER_SPD = 60
GRID_PULSE_SPD = 0.0008
SCAN_LINE_SPD  = 0.15

# Aviation animation constants
RADAR_CENTER_X = WINDOW_W // 4
RADAR_RADIUS   = 180
PLANE_COUNT    = 8


class FlyingPlane:
    """Small class representing one animated airplane."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = random.uniform(-50, RADAR_CENTER_X - 100)
        self.y = random.uniform(NAV_H + 50, WINDOW_H - 100)
        self.speed = random.uniform(0.08, 0.18)
        self.angle = random.uniform(-0.3, 0.3)
        self.size = random.randint(14, 22)


class SplashScreen:
    """
    Handles all rendering and input for the S0 splash screen.
    Title is now centered on the left half, above the animation area.
    """

    def __init__(self, fonts: dict, on_load, on_build, on_depth):
        self.fonts      = fonts
        self.on_load    = on_load
        self.on_build   = on_build
        self.on_depth   = on_depth

        # Typewriter state
        self._title_chars   = 0
        self._title_done    = False
        self._sub_chars     = 0
        self._sub_done      = False
        self._last_type_ms  = 0

        # Scan line & grid
        self._scan_y        = float(NAV_H)
        self._pulse_phase   = 0.0

        # Critical depth
        self._depth_value   = 0
        self._depth_active  = False
        self._depth_str     = "0"

        self._status        = ""
        self._status_color  = TEXT_SECONDARY

        # Layout rects for right card
        self._card_rect     = None
        self._load_btn      = None
        self._build_btn     = None
        self._depth_rect    = None
        self._minus_btn     = None
        self._plus_btn      = None

        # Aviation animation
        self._planes        = [FlyingPlane() for _ in range(PLANE_COUNT)]
        self._radar_angle   = 0.0

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Processes a single pygame event for this screen."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos)
        if event.type == pygame.KEYDOWN and self._depth_active:
            self._handle_depth_key(event)

    def update(self, dt_ms: float) -> None:
        """Advances all animations by dt_ms milliseconds."""
        self._update_typewriter(dt_ms)
        self._update_scan_line(dt_ms)
        self._update_grid_pulse(dt_ms)
        self._update_aviation_animation(dt_ms)

    def draw(self, surface: pygame.Surface) -> None:
        """Renders the full splash screen onto surface."""
        surface.fill(BG_DEEP)

        self._draw_grid(surface)
        self._draw_scan_line(surface)

        # Left side content
        self._draw_aviation_visualization(surface)
        self._draw_title_left(surface)          # ← Nuevo: título centrado en izquierda

        # Right side content
        self._draw_card(surface)
        self._draw_status(surface)

    def set_status(self, message: str, success: bool = True) -> None:
        """Allows main.py to push a status message."""
        self._status       = message
        self._status_color = GREEN_TERM if success else CRITICAL

    # ------------------------------------------------------------------
    # Animation updaters
    # ------------------------------------------------------------------

    def _update_typewriter(self, dt_ms: float) -> None:
        self._last_type_ms += dt_ms
        if self._last_type_ms < TYPEWRITER_SPD:
            return
        self._last_type_ms = 0

        if not self._title_done:
            self._title_chars += 1
            if self._title_chars >= len(TITLE_TEXT):
                self._title_done = True
        elif not self._sub_done:
            self._sub_chars += 1
            if self._sub_chars >= len(SUBTITLE_TEXT):
                self._sub_done = True

    def _update_scan_line(self, dt_ms: float) -> None:
        self._scan_y += SCAN_LINE_SPD * dt_ms
        if self._scan_y > WINDOW_H:
            self._scan_y = float(NAV_H)

    def _update_grid_pulse(self, dt_ms: float) -> None:
        self._pulse_phase += GRID_PULSE_SPD * dt_ms

    def _update_aviation_animation(self, dt_ms: float) -> None:
        self._radar_angle += 0.0028 * dt_ms

        for plane in self._planes:
            plane.x += plane.speed * dt_ms
            plane.y += plane.angle * 0.3
            if plane.x > WINDOW_W // 2 + 100:
                plane.reset()

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _draw_grid(self, surface: pygame.Surface) -> None:
        alpha   = int(18 + 10 * math.sin(self._pulse_phase))
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)

        for x in range(0, WINDOW_W, GRID_SPACING):
            pygame.draw.line(overlay, (*AMBER_DIM, alpha), (x, 0), (x, WINDOW_H))
        for y in range(0, WINDOW_H, GRID_SPACING):
            pygame.draw.line(overlay, (*AMBER_DIM, alpha), (0, y), (WINDOW_W, y))

        surface.blit(overlay, (0, 0))

    def _draw_scan_line(self, surface: pygame.Surface) -> None:
        scan = pygame.Surface((WINDOW_W, 2), pygame.SRCALPHA)
        scan.fill((*AMBER, 18))
        surface.blit(scan, (0, int(self._scan_y)))

    # ====================== LEFT SIDE TITLE ======================
    def _draw_title_left(self, surface: pygame.Surface) -> None:
        """Draws the typewriter title centered on the LEFT half, above the radar."""
        cx = WINDOW_W * 3 // 4                     # Center of left half
        ty = WINDOW_H // 2 - 190               # Positioned above the card/radar

        # Title with subtle glow effect
        visible = TITLE_TEXT[: self._title_chars]
        cursor  = "_" if not self._title_done else ""

        # Glow layer
        glow_surf = self.fonts["title_xl"].render(visible + cursor, True, (*AMBER, 60))
        glow_rect = glow_surf.get_rect(centerx=cx, top=ty - 3)
        surface.blit(glow_surf, glow_rect)

        # Main title
        title_surf = self.fonts["title_xl"].render(visible + cursor, True, AMBER)
        surface.blit(title_surf, title_surf.get_rect(centerx=cx, top=ty))

        # Subtitle (appears after title)
        if self._title_done:
            vis_sub   = SUBTITLE_TEXT[: self._sub_chars]
            cur_sub   = "_" if not self._sub_done else ""
            sub_surf  = self.fonts["label_sm"].render(vis_sub + cur_sub, True, TEXT_SECONDARY)
            surface.blit(sub_surf, sub_surf.get_rect(centerx=cx, top=ty + 68))

        # Decorative separator line
        if self._sub_done:
            lx = cx - 160
            pygame.draw.line(surface, BORDER_ACTIVE, (lx, ty + 95), (lx + 320, ty + 95), 2)

    # ====================== LEFT SIDE ANIMATION ======================
    def _draw_aviation_visualization(self, surface: pygame.Surface) -> None:
        """Draws rotating radar + flying airplanes on the left half."""
        left_center_x = WINDOW_W // 4
        left_center_y = WINDOW_H // 2 + 20

        # Radar background
        pygame.draw.circle(surface, BG_SURFACE2, (left_center_x, left_center_y), RADAR_RADIUS + 20, 0)
        pygame.draw.circle(surface, BORDER, (left_center_x, left_center_y), RADAR_RADIUS + 20, 2)

        # Radar sweep
        sweep_x = left_center_x + RADAR_RADIUS * math.cos(self._radar_angle)
        sweep_y = left_center_y + RADAR_RADIUS * math.sin(self._radar_angle)
        pygame.draw.line(surface, AMBER, (left_center_x, left_center_y), (sweep_x, sweep_y), 3)

        # Concentric circles
        for r in range(40, RADAR_RADIUS + 1, 40):
            pygame.draw.circle(surface, AMBER_DIM, (left_center_x, left_center_y), r, 1)

        # Radar cross
        pygame.draw.line(surface, AMBER_DIM,
                        (left_center_x - RADAR_RADIUS, left_center_y),
                        (left_center_x + RADAR_RADIUS, left_center_y), 1)
        pygame.draw.line(surface, AMBER_DIM,
                        (left_center_x, left_center_y - RADAR_RADIUS),
                        (left_center_x, left_center_y + RADAR_RADIUS), 1)

        # Flying planes
        for plane in self._planes:
            self._draw_plane(surface, plane, left_center_x, left_center_y)

    def _draw_plane(self, surface, plane, radar_cx, radar_cy):
        """Draws a simple airplane silhouette."""
        # Body
        pygame.draw.line(surface, AMBER, (plane.x, plane.y), (plane.x + plane.size, plane.y), 4)
        # Wings
        pygame.draw.line(surface, AMBER, (plane.x + plane.size//2, plane.y - 8),
                        (plane.x + plane.size//2, plane.y + 8), 3)
        # Tail
        pygame.draw.line(surface, AMBER, (plane.x, plane.y - 4), (plane.x - 6, plane.y), 2)

        # Blip connection to radar
        dist = math.hypot(plane.x - radar_cx, plane.y - radar_cy)
        if dist < RADAR_RADIUS + 40:
            alpha = max(30, int(90 * (1 - dist / (RADAR_RADIUS + 60))))
            pygame.draw.line(surface, (*AMBER, alpha),
                           (plane.x + plane.size//2, plane.y),
                           (radar_cx, radar_cy), 1)

    # ====================== RIGHT SIDE CARD ======================
    def _draw_card(self, surface: pygame.Surface) -> None:
        if not self._sub_done:
            return

        cx    = WINDOW_W * 3 // 4          # Right half
        cy    = WINDOW_H // 2 + 90
        cw, ch = 380, 248

        card_rect = pygame.Rect(cx - cw // 2, cy - ch // 2, cw, ch)
        self._card_rect = card_rect

        pygame.draw.rect(surface, BG_SURFACE, card_rect)
        _draw_clipped_border(surface, card_rect, BORDER, clip=10)

        label = self.fonts["label_sm"].render("CARGAR SISTEMA", True, TEXT_DIM)
        surface.blit(label, (card_rect.x + 16, card_rect.y + 14))

        btn_rect = pygame.Rect(card_rect.x + 16, card_rect.y + 40, cw - 32, BTN_H)
        self._load_btn = btn_rect
        _draw_button(surface, btn_rect, "CARGAR ARCHIVO JSON", self.fonts["label_md"],
                     AMBER, BG_DEEP, AMBER)

        build_rect = pygame.Rect(card_rect.x + 16, card_rect.y + 80, cw - 32, BTN_H)
        self._build_btn = build_rect
        _draw_button(surface, build_rect, "CREAR ÁRBOL DESDE CERO", self.fonts["label_md"],
                     BG_SURFACE2, TEXT_SECONDARY, BORDER)

        sep_y = card_rect.y + 128
        pygame.draw.line(surface, BORDER,
                         (card_rect.x + 16, sep_y),
                         (card_rect.right - 16, sep_y), 1)

        dlabel = self.fonts["label_sm"].render("PROFUNDIDAD CRÍTICA", True, TEXT_DIM)
        surface.blit(dlabel, (card_rect.x + 16, sep_y + 10))

        self._draw_depth_controls(surface, card_rect, sep_y + 32)

    def _draw_depth_controls(self, surface, card_rect, top_y):
        cx = card_rect.centerx

        minus_rect = pygame.Rect(cx - 80, top_y, 32, 32)
        self._minus_btn = minus_rect
        _draw_button(surface, minus_rect, "−", self.fonts["label_lg"],
                     TEXT_PRIMARY, BG_SURFACE2, BORDER)

        depth_rect = pygame.Rect(cx - 36, top_y, 72, 32)
        self._depth_rect = depth_rect
        border_col = BORDER_ACTIVE if self._depth_active else BORDER
        pygame.draw.rect(surface, BG_DEEP, depth_rect)
        pygame.draw.rect(surface, border_col, depth_rect, 1)

        val_text = self._depth_str if self._depth_active else str(self._depth_value)
        cursor   = "_" if self._depth_active else ""
        val_surf = self.fonts["label_lg"].render(val_text + cursor, True, AMBER)
        surface.blit(val_surf, val_surf.get_rect(center=depth_rect.center))

        plus_rect = pygame.Rect(cx + 48, top_y, 32, 32)
        self._plus_btn = plus_rect
        _draw_button(surface, plus_rect, "+", self.fonts["label_lg"],
                     TEXT_PRIMARY, BG_SURFACE2, BORDER)

        hint_text = "0 = desactivado" if self._depth_value == 0 else f"penaliza nodos > nivel {self._depth_value}"
        hint = self.fonts["body_xs"].render(hint_text, True, TEXT_DIM)
        surface.blit(hint, hint.get_rect(centerx=card_rect.centerx, top=top_y + 38))

    def _draw_status(self, surface: pygame.Surface) -> None:
        if not self._status:
            return
        surf = self.fonts["body_sm"].render(self._status, True, self._status_color)
        surface.blit(surf, surf.get_rect(centerx=WINDOW_W * 3 // 4, top=WINDOW_H // 2 + 238))

    # ------------------------------------------------------------------
    # Input handlers (unchanged)
    # ------------------------------------------------------------------

    def _handle_click(self, pos: tuple) -> None:
        if self._load_btn and self._load_btn.collidepoint(pos):
            self.on_load()
            return
        if self._build_btn and self._build_btn.collidepoint(pos):
            self.on_build()
            return
        if self._minus_btn and self._minus_btn.collidepoint(pos):
            self._depth_value = max(0, self._depth_value - 1)
            self._depth_str   = str(self._depth_value)
            self.on_depth(self._depth_value)
            return
        if self._plus_btn and self._plus_btn.collidepoint(pos):
            self._depth_value = min(20, self._depth_value + 1)
            self._depth_str   = str(self._depth_value)
            self.on_depth(self._depth_value)
            return
        if self._depth_rect and self._depth_rect.collidepoint(pos):
            self._depth_active = True
            self._depth_str    = ""
            return

        self._depth_active = False

    def _handle_depth_key(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
            self._commit_depth()
        elif event.key == pygame.K_ESCAPE:
            self._depth_active = False
            self._depth_str    = str(self._depth_value)
        elif event.key == pygame.K_BACKSPACE:
            self._depth_str = self._depth_str[:-1]
        elif event.unicode.isdigit() and len(self._depth_str) < 2:
            self._depth_str += event.unicode

    def _commit_depth(self) -> None:
        try:
            val = int(self._depth_str) if self._depth_str else 0
            self._depth_value = max(0, min(20, val))
        except ValueError:
            self._depth_value = 0
        self._depth_str    = str(self._depth_value)
        self._depth_active = False
        self.on_depth(self._depth_value)


# ------------------------------------------------------------------
# Shared drawing utilities
# ------------------------------------------------------------------

def _draw_clipped_border(surface, rect, color, clip=10, width=1):
    """Draws a rectangle border with diagonally clipped corners (HUD style)."""
    x, y, w, h = rect.x, rect.y, rect.width, rect.height
    points = [
        (x + clip, y), (x + w - clip, y),
        (x + w, y + clip), (x + w, y + h - clip),
        (x + w - clip, y + h), (x + clip, y + h),
        (x, y + h - clip), (x, y + clip),
    ]
    pygame.draw.polygon(surface, color, points, width)


def _draw_button(surface, rect, text, font, text_color, bg_color, border_color):
    """Draws a flat button with clipped corners and centered text."""
    pygame.draw.rect(surface, bg_color, rect)
    _draw_clipped_border(surface, rect, border_color, clip=6, width=1)
    label = font.render(text, True, text_color)
    surface.blit(label, label.get_rect(center=rect.center))