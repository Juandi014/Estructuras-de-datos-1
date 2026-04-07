"""
main.py
-------
Entry point for SkyBalance AVL Flight Management System.

Responsibilities:
  - Initializes Pygame and the main window.
  - Owns the global application state (current screen, trees, depth, history).
  - Routes events and draw calls to the active screen.
  - Handles transitions between screens.
  - Manages undo via HistoryStack (Ctrl+Z).
"""

import pygame
import sys

from user_interface.color_scheme import (
    WINDOW_W, WINDOW_H, FPS,
    AMBER, TEXT_SECONDARY, BORDER,
    NAV_H, NAV_PADDING,
    load_fonts,
)
from user_interface.screen_splash import SplashScreen
from user_interface.screen_main import MainScreen
from user_interface.screen_stress import StressScreen
from user_interface.screen_versions import VersionsScreen
from user_interface.screen_cancel import CancelScreen
from user_interface.screen_rentability import RentabilityScreen
from in_out.json_loader import load_file
from logic.insertion_queue import InsertionQueue
from logic.history_stack import HistoryStack
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
SCREEN_BUILD   = "build"

SCREEN_STRESS   = "stress"
SCREEN_VERSIONS = "versions"
SCREEN_CANCEL   = "cancel"
SCREEN_RENT      = "rentability"

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
        self.avl_tree        = AVLTree()
        self.bst_tree        = BSTTree()
        self.insertion_queue = InsertionQueue()
        self.history         = HistoryStack()
        self.critical_depth  = 0
        self.current_screen  = SCREEN_SPLASH

        # Screen instances
        self.screens = {}
        self._init_splash()
        self._init_main()
        self._init_build()
        self._init_stress()
        self._init_versions()
        self._init_cancel()
        self._init_rentability()

    # ------------------------------------------------------------------
    # Screen initialization
    # ------------------------------------------------------------------

    def _init_splash(self) -> None:
        """Creates the S0 splash screen with its callbacks."""
        self.screens[SCREEN_SPLASH] = SplashScreen(
            fonts    = self.fonts,
            on_load  = self._handle_load_file,
            on_build = self._handle_build_from_scratch,
            on_depth = self._handle_depth_change,
        )

    def _init_main(self) -> None:
        """Creates the S1 main tree screen with its callbacks."""
        self.screens[SCREEN_MAIN] = MainScreen(
            fonts    = self.fonts,
            avl_tree = self.avl_tree,
            on_undo  = self._handle_undo,
        )
    
    def _init_stress(self) -> None:
        """Creates the S3 Stress Mode screen."""
        self.screens[SCREEN_STRESS] = StressScreen(
            fonts              = self.fonts,
            avl_tree           = self.avl_tree,
            on_switch_to_main  = lambda: self._switch_to_screen(SCREEN_MAIN)
        )

    def _init_versions(self) -> None:
        """Creates the S4 Versions screen."""
        self.screens[SCREEN_VERSIONS] = VersionsScreen(
            fonts             = self.fonts,
            avl_tree          = self.avl_tree,
            on_switch_to_main = lambda: self._switch_to_screen(SCREEN_MAIN)
        )

    def _init_cancel(self) -> None:
        """Creates the S6 Mass Cancellation dialog screen."""
        self.screens[SCREEN_CANCEL] = CancelScreen(
            fonts             = self.fonts,
            avl_tree          = self.avl_tree,
            on_switch_to_main = lambda: self._switch_to_screen(SCREEN_MAIN)
        )
    
    def _init_rentability(self) -> None:
        """Creates the S7 Intelligent Elimination by Rentability screen."""
        self.screens[SCREEN_RENT] = RentabilityScreen(
            fonts             = self.fonts,
            avl_tree          = self.avl_tree,
            on_switch_to_main = lambda: self._switch_to_screen(SCREEN_MAIN)
        )

    def _init_build(self) -> None:
        """Creates the S2 build-from-scratch screen (reuses MainScreen)."""
        self.screens[SCREEN_BUILD] = MainScreen(
            fonts    = self.fonts,
            avl_tree = self.avl_tree,
            on_undo  = self._handle_undo,
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
            splash.set_status(f"Archivo cargado — modo {mode}", success=True)
            self.current_screen = SCREEN_MAIN
        except ValueError as e:
            splash.set_status(str(e), success=False)

    def _handle_build_from_scratch(self) -> None:
        """
        Triggered by the CREAR DESDE CERO button.
        Resets both trees and transitions to S2 (build screen).
        """
        self.avl_tree.__init__()
        self.bst_tree.__init__()
        self.history.clear()
        self.avl_tree.critical_depth = self.critical_depth
        self.current_screen = SCREEN_BUILD

    def _handle_depth_change(self, value: int) -> None:
        """
        Triggered when the user changes the critical depth value on the splash.
        Updates the tree's penalty threshold immediately if a tree is loaded.
        """
        self.critical_depth          = value
        self.avl_tree.critical_depth = value
        if self.avl_tree.getRoot() is not None:
            self.avl_tree.applyDepthPenalty(value)

    def _handle_undo(self) -> None:
        """
        Triggered by Ctrl+Z on S1.
        Pops the last snapshot from the history stack and restores the tree.
        """
        entry = self.history.pop()
        main  = self.screens[SCREEN_MAIN]
        if entry is None:
            main.set_status("Nada que deshacer.", success=False)
            return
        snapshot = entry["snapshot"]
        self.avl_tree.root           = snapshot.root
        self.avl_tree.stress_mode    = snapshot.stress_mode
        self.avl_tree.critical_depth = snapshot.critical_depth
        main.set_status(
            f"Deshecho: {entry['action']} — {entry['code']}", success=True)
        
    def _switch_to_screen(self, screen_id: str) -> None:
        """Safe way to change current screen."""
        if screen_id in self.screens:
            self.current_screen = screen_id

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
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_nav_click(event.pos)
            screen = self.screens.get(self.current_screen)
            if screen:
                screen.handle_event(event)

    def _update(self, dt_ms: float) -> None:
        """Advances the active screen's animations."""
        screen = self.screens.get(self.current_screen)
        if screen:
            screen.update(dt_ms)

    def _draw(self) -> None:
        """Renders the active screen and the nav bar on top."""
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
        Buttons are only clickable once a file has been loaded.
        """
        nav_rect = pygame.Rect(0, 0, WINDOW_W, NAV_H)
        pygame.draw.rect(self.surface, (10, 8, 6), nav_rect)
        pygame.draw.line(self.surface, BORDER,
                         (0, NAV_H - 1), (WINDOW_W, NAV_H - 1), 1)

        logo = self.fonts["label_md"].render("SKY//BALANCE", True, AMBER)
        self.surface.blit(logo, (NAV_PADDING, NAV_H // 2 - logo.get_height() // 2))

        tree_loaded = self.avl_tree.getRoot() is not None
        nav_items = [
            ("AVL",       SCREEN_MAIN),
            ("CONSTRUIR", SCREEN_BUILD),
            ("COLA",      SCREEN_QUEUE),
            ("COMPARAR",  SCREEN_COMPARE),
            ("ESTRÉS",    SCREEN_STRESS),
            ("VERSIONES", SCREEN_VERSIONS),
            ("CANCELAR",  SCREEN_CANCEL),
            ("RENTABILIDAD", SCREEN_RENT),
        ]
        bx = 180
        for label, screen_id in nav_items:
            is_active = self.current_screen == screen_id
            color = AMBER if is_active else (
                    TEXT_SECONDARY if tree_loaded else (50, 40, 30))
            btn = self.fonts["label_sm"].render(label, True, color)
            self.surface.blit(btn, (bx, NAV_H // 2 - btn.get_height() // 2))
            bx += btn.get_width() + 24

    def _handle_nav_click(self, pos: tuple) -> None:
        """
        Checks if a nav button was clicked and transitions to that screen.
        Only works if a tree is loaded.
        """
        if self.avl_tree.getRoot() is None:
            return
        if pos[1] > NAV_H:
            return

        nav_items = [
            ("AVL",       SCREEN_MAIN),
            ("CONSTRUIR", SCREEN_BUILD),
            ("COLA",      SCREEN_QUEUE),
            ("COMPARAR",  SCREEN_COMPARE),
            ("ESTRÉS",    SCREEN_STRESS),
            ("VERSIONES", SCREEN_VERSIONS),
            ("CANCELAR",  SCREEN_CANCEL),
            ("RENTABILIDAD", SCREEN_RENT),
        ]   
        bx = 180
        for label, screen_id in nav_items:
            btn = self.fonts["label_sm"].render(label, True, AMBER)
            btn_rect = pygame.Rect(bx, 0, btn.get_width(), NAV_H)
            if btn_rect.collidepoint(pos):
                self.current_screen = screen_id
                return
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