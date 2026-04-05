"""
panel_ui.py
-----------
Reusable UI components for side panels in SkyBalance AVL system.
Designed to keep code clean and distributed. All components are small 
and single-responsibility. Style matches the existing buttons in screen_main.py.
"""

import pygame
from user_interface.color_scheme import (
    BG_DEEP, BG_SURFACE, BG_SURFACE2, BORDER, BORDER_ACTIVE,
    AMBER, CRITICAL, GREEN_TERM, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DIM,
    PANEL_PADDING, BTN_H
)


def draw_clipped_border(surface: pygame.Surface, rect: pygame.Rect, color, clip=10, width=1):
    """
    Strategy: Draw a rectangle with diagonally clipped corners to match 
    the current visual style of screen_main.py.
    """
    x, y, w, h = rect.x, rect.y, rect.width, rect.height
    points = [
        (x + clip, y), (x + w - clip, y),
        (x + w, y + clip), (x + w, y + h - clip),
        (x + w - clip, y + h), (x + clip, y + h),
        (x, y + h - clip), (x, y + clip),
    ]
    pygame.draw.polygon(surface, color, points, width)


class UIButton:
    """
    Reusable button with hover effect and callback.
    Matches the style of _draw_button in screen_main.py.
    """

    def __init__(self, rect: pygame.Rect, text: str, font,
                 bg_color=BG_DEEP, text_color=TEXT_PRIMARY,
                 border_color=BORDER, callback=None):
        self.rect = rect
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.text_color = text_color
        self.border_color = border_color
        self.callback = callback
        self.hovered = False

    def draw(self, surface: pygame.Surface) -> None:
        """Draw button with hover feedback."""
        bg = AMBER if self.hovered else self.bg_color
        border = AMBER if self.hovered else self.border_color

        pygame.draw.rect(surface, bg, self.rect)
        draw_clipped_border(surface, self.rect, border, clip=5, width=1)

        label = self.font.render(self.text, True, self.text_color)
        surface.blit(label, label.get_rect(center=self.rect.center))

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events and trigger callback if clicked."""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) and self.callback:
                self.callback()
                return True
        return False


class UIInputField:
    """
    Reusable single-line text input.
    Matches the style used in _draw_input of screen_main.py.
    """

    def __init__(self, rect: pygame.Rect, placeholder: str, font, initial_value=""):
        self.rect = rect
        self.placeholder = placeholder
        self.font = font
        self.value = initial_value
        self.active = False

    def draw(self, surface: pygame.Surface) -> None:
        """Draw input field with active/ inactive states."""
        bg = BG_SURFACE2 if self.active else BG_DEEP
        border = BORDER_ACTIVE if self.active else BORDER

        pygame.draw.rect(surface, bg, self.rect)
        pygame.draw.rect(surface, border, self.rect, 1)

        display_text = self.value if self.value else self.placeholder
        if self.active and self.value:
            display_text += "_"

        color = TEXT_PRIMARY if self.value else TEXT_DIM
        text_surf = self.font.render(display_text, True, color)

        surface.blit(text_surf,
                     (self.rect.x + 6,
                      self.rect.y + self.rect.height // 2 - text_surf.get_height() // 2))

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle mouse click to activate and keyboard input."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)

        if not self.active or event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_BACKSPACE:
            self.value = self.value[:-1]
        elif event.unicode and event.unicode.isprintable():
            self.value += event.unicode


class UIToggle:
    """
    On/Off toggle switch for options like Stress Mode.
    Small, clean, and matches the overall UI style.
    """

    def __init__(self, rect: pygame.Rect, label: str, font, initial_state=False, callback=None):
        self.rect = rect          # Full area including label + switch
        self.label = label
        self.font = font
        self.state = initial_state
        self.callback = callback
        self.hovered = False

    def draw(self, surface: pygame.Surface) -> None:
        """Draw label + toggle switch."""
        # Label
        lbl_surf = self.font.render(self.label, True, TEXT_PRIMARY)
        surface.blit(lbl_surf, (self.rect.x,
                                self.rect.y + (self.rect.height - lbl_surf.get_height()) // 2))

        # Toggle background
        toggle_rect = pygame.Rect(self.rect.right - 52, self.rect.y + 4, 48, 20)
        bg_color = GREEN_TERM if self.state else BORDER
        pygame.draw.rect(surface, bg_color, toggle_rect, border_radius=10)

        # Knob
        knob_x = toggle_rect.right - 14 if self.state else toggle_rect.x + 4
        pygame.draw.circle(surface, BG_SURFACE, (knob_x, toggle_rect.centery), 8)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Toggle state on click and call callback."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.state = not self.state
                if self.callback:
                    self.callback(self.state)
                return True
        return False


def draw_section_header(surface: pygame.Surface, y: int, title: str, fonts, panel_rect) -> int:
    """
    Strategy: Draw labeled divider exactly like _draw_section_divider in screen_main.py.
    Returns new y position.
    """
    pygame.draw.line(surface, BORDER,
                     (panel_rect.x + PANEL_PADDING, y),
                     (panel_rect.right - PANEL_PADDING, y), 1)
    y += 6
    lbl = fonts["label_sm"].render(title, True, TEXT_DIM)
    surface.blit(lbl, (panel_rect.x + PANEL_PADDING, y))
    return y + 18


def draw_metric_row(surface: pygame.Surface, y: int, label: str, value: str, fonts, panel_rect) -> int:
    """
    Strategy: Draw label + right-aligned value. Reusable for metrics in any panel.
    Returns new y position.
    """
    lbl = fonts["body_sm"].render(label, True, TEXT_SECONDARY)
    val = fonts["label_md"].render(value, True, AMBER)

    surface.blit(lbl, (panel_rect.x + PANEL_PADDING, y))
    surface.blit(val, (panel_rect.right - PANEL_PADDING - val.get_width(), y))
    return y + 18