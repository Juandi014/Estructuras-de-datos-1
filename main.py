"""
main.py
-------
Entry point for SkyBalance AVL Flight Management System.

Responsibilities:
  - Initializes Pygame and the main window.
  - Owns the global application state (current screen, trees, depth).
  - Routes events and draw calls to the active screen.
  - Handles transitions between screens.
"""

import pygame
import sys

from user_interface.color_scheme import (
    WINDOW_W, WINDOW_H, FPS, BG_DEEP,
    AMBER, TEXT_SECONDARY, BORDER,
    load_fonts,
)
from user_interface.screen_splash import SplashScreen
from in_out.json_loader import load_file
from logic.insertion_queue import InsertionQueue
from models.avl_tree import AVLTree
from models.bst_tree import BSTTree


# ------------------------------------------------------------------
# Screen identifiers
# ------------------------------------------------------------------

SCREEN_SPLASH  = "splash"
SCREEN_MAIN    = "main"
SCREEN_INSERT  = "insert"
SCREEN_QUEUE   = "queue"
SCREEN_COMPARE = "compare"


class App:
    """
    Main application controller.
    Owns all shared state and delegates per-frame work to the active screen.
    """

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("SkyBalance — AVL Flight System")

        self.surface = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        self.clock   = pygame.time.Clock()
        self.fonts   = load_fonts()

        # Shared application state
        self.avl_tree       = AVLTree()
        self.bst_tree       = BSTTree()
        self.insertion_queue = InsertionQueue()
        self.critical_depth  = 0
        self.current_screen  = SCREEN_SPLASH

        # Screen instances — lazy: only splash created at startup
        self.screens = {}
        self._init_splash()

    # ------------------------------------------------------------------
    # Screen initialization
    # ------------------------------------------------------------------

    def _init_splash(self) -> None:
        """Creates the S0 splash screen with its callbacks."""
        self.screens[SCREEN_SPLASH] = SplashScreen(
            fonts    = self.fonts,
            on_load  = self._handle_load_file,
            on_depth = self._handle_depth_change,
        )

    # ------------------------------------------------------------------
    # Callbacks passed to screens
    # ------------------------------------------------------------------

    def _handle_load_file(self) -> None:
        """
        Triggered by the splash screen's LOAD FILE button.
        Opens the file dialog, loads the tree, and transitions to S1.
        """
        splash = self.screens[SCREEN_SPLASH]
        try:
            mode = load_file(self.avl_tree, self.bst_tree)
            self.avl_tree.critical_depth = self.critical_depth
            splash.set_status(f"Archivo cargado correctamente — modo {mode}", success=True)
            # TODO: transition to SCREEN_MAIN once S1 is implemented
            # self.current_screen = SCREEN_MAIN
        except ValueError as e:
            splash.set_status(str(e), success=False)

    def _handle_depth_change(self, value: int) -> None:
        """
        Triggered when the user changes the critical depth value.
        Updates the tree's penalty threshold immediately.
        """
        self.critical_depth = value
        self.avl_tree.critical_depth = value
        if self.avl_tree.getRoot() is not None:
            self.avl_tree.applyDepthPenalty(value)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Starts the main game loop."""
        while True:
            dt_ms = self.clock.tick(FPS)
            self._process_events()
            self._update(dt_ms)
            self._draw()
            pygame.display.flip()

    def _process_events(self) -> None:
        """Reads the event queue and dispatches to the active screen."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._quit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._quit()
            screen = self.screens.get(self.current_screen)
            if screen:
                screen.handle_event(event)

    def _update(self, dt_ms: float) -> None:
        """Advances the active screen's animations."""
        screen = self.screens.get(self.current_screen)
        if screen:
            screen.update(dt_ms)

    def _draw(self) -> None:
        """Renders the active screen and the nav bar."""
        screen = self.screens.get(self.current_screen)
        if screen:
            screen.draw(self.surface)
        self._draw_nav()

    # ------------------------------------------------------------------
    # Navigation bar
    # ------------------------------------------------------------------

    def _draw_nav(self) -> None:
        """
        Draws the top navigation bar with the logo and screen buttons.
        Buttons are only active once a file has been loaded.
        """
        from user_interface.color_scheme import NAV_H, NAV_PADDING
        nav_rect = pygame.Rect(0, 0, WINDOW_W, NAV_H)
        pygame.draw.rect(self.surface, (10, 8, 6), nav_rect)
        pygame.draw.line(self.surface, BORDER, (0, NAV_H - 1), (WINDOW_W, NAV_H - 1), 1)

        # Logo
        logo = self.fonts["label_md"].render("SKY//BALANCE", True, AMBER)
        self.surface.blit(logo, (NAV_PADDING, NAV_H // 2 - logo.get_height() // 2))

        # Nav buttons (disabled until file loaded)
        tree_loaded = self.avl_tree.getRoot() is not None
        nav_items = [
            ("AVL",     SCREEN_MAIN),
            ("INSERT",  SCREEN_INSERT),
            ("QUEUE",   SCREEN_QUEUE),
            ("COMPARE", SCREEN_COMPARE),
        ]
        bx = 180
        for label, screen_id in nav_items:
            color  = AMBER if self.current_screen == screen_id else (
                     TEXT_SECONDARY if tree_loaded else (50, 40, 30))
            btn    = self.fonts["label_sm"].render(label, True, color)
            self.surface.blit(btn, (bx, NAV_H // 2 - btn.get_height() // 2))
            bx += btn.get_width() + 24

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def _quit(self) -> None:
        """Gracefully exits the application."""
        pygame.quit()
        sys.exit()


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    App().run()