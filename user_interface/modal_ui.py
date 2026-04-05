"""
modal_ui.py
-----------
Reusable modal dialog system for SkyBalance AVL.
Supports info, confirmation, and custom content modals.
Style matches the search modal already present in screen_main.py.
"""

import pygame
from user_interface.color_scheme import BG_DEEP, BG_SURFACE, BORDER, AMBER, CRITICAL, TEXT_PRIMARY
from user_interface.panel_ui import draw_clipped_border, UIButton


class UIModal:
    """
    Generic centered modal with title, close button and optional custom content area.
    """

    def __init__(self, title: str, width: int = 420, height: int = 340, fonts=None):
        self.title = title
        self.width = width
        self.height = height
        self.fonts = fonts
        self.visible = False
        self.rect = None
        self.close_callback = None
        self.buttons = []          # list of (text, callback, color)

    def show(self):
        """Make modal visible."""
        self.visible = True

    def hide(self):
        """Hide modal."""
        self.visible = False

    def set_close_callback(self, callback):
        self.close_callback = callback

    def add_button(self, text: str, callback, color=AMBER):
        """Add action button at bottom."""
        self.buttons.append((text, callback, color))

    def draw(self, surface: pygame.Surface) -> None:
        """Draw modal with overlay and clipped border."""
        if not self.visible or not self.fonts:
            return

        # Dark overlay
        overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # Modal card
        mx = surface.get_width() // 2 - self.width // 2
        my = surface.get_height() // 2 - self.height // 2
        self.rect = pygame.Rect(mx, my, self.width, self.height)

        pygame.draw.rect(surface, BG_SURFACE, self.rect)
        draw_clipped_border(surface, self.rect, AMBER, clip=12, width=2)

        # Title
        title_surf = self.fonts["label_md"].render(f"// {self.title}", True, AMBER)
        surface.blit(title_surf, (mx + 20, my + 16))

        # Close button (top-right)
        close_rect = pygame.Rect(mx + self.width - 40, my + 10, 28, 28)
        close_btn = UIButton(close_rect, "✕", self.fonts["label_md"],
                             bg_color=CRITICAL, text_color=TEXT_PRIMARY,
                             border_color=CRITICAL, callback=self._on_close)
        close_btn.draw(surface)

        # Content area (to be overridden or filled by subclasses)
        self._draw_content(surface, mx, my)

        # Bottom buttons
        self._draw_buttons(surface, mx, my)

    def _on_close(self):
        self.hide()
        if self.close_callback:
            self.close_callback()

    def _draw_content(self, surface: pygame.Surface, mx: int, my: int):
        """Override in subclasses for custom content."""
        pass

    def _draw_buttons(self, surface: pygame.Surface, mx: int, my: int):
        """Draw action buttons at bottom if any."""
        if not self.buttons:
            return
        btn_w = 120
        spacing = 15
        total_w = len(self.buttons) * btn_w + (len(self.buttons) - 1) * spacing
        start_x = mx + self.width // 2 - total_w // 2
        y = my + self.height - 60

        for i, (text, cb, color) in enumerate(self.buttons):
            rect = pygame.Rect(start_x + i * (btn_w + spacing), y, btn_w, 36)
            btn = UIButton(rect, text, self.fonts["label_md"],
                           bg_color=BG_DEEP, text_color=TEXT_PRIMARY,
                           border_color=color, callback=cb)
            btn.draw(surface)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Pass events to buttons. Returns True if event was consumed."""
        if not self.visible:
            return False
        # Close button and action buttons are handled internally via UIButton
        return False  # Extend in subclasses if needed