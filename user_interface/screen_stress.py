"""
screen_stress.py
----------------
S3 — Stress Mode (Rebalanceo Diferido) for SkyBalance AVL System.

This screen allows the user to:
- Enable/Disable stress mode (operations without automatic balancing)
- Perform insertions, deletions and cancellations that degrade the tree
- Trigger global rebalance and see the cost in rotations
- Visually observe tree deformation

All UI components reuse panel_ui and modal_ui to keep code clean.
"""

import pygame
from user_interface.color_scheme import (
    BG_DEEP, BG_SURFACE, BORDER, AMBER, CRITICAL, GREEN_TERM,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DIM,
    WINDOW_W, WINDOW_H, NAV_H, PANEL_PADDING, BTN_H
)
from user_interface.tree_renderer import TreeRenderer
from user_interface.panel_ui import (
    UIButton, UIToggle, draw_section_header, draw_metric_row
)
from user_interface.modal_ui import UIModal


class StressScreen:
    """
    Main class for Stress Mode screen (S3).

    Args:
        fonts: Font registry from color_scheme
        avl_tree: Shared AVLTree instance with stress mode support
        on_switch_to_main: Callback to return to main screen
    """

    def __init__(self, fonts: dict, avl_tree, on_switch_to_main):
        self.fonts = fonts
        self.avl_tree = avl_tree
        self.on_switch_to_main = on_switch_to_main

        # Renderer (same as main screen)
        TREE_RECT = pygame.Rect(0, NAV_H, WINDOW_W - 280, WINDOW_H - NAV_H)
        self.renderer = TreeRenderer(TREE_RECT)

        # Stress mode state
        self.stress_enabled = False

        # UI Components
        self._toggle_stress = None
        self._btn_rebalance = None
        self._btn_back = None

        # Rebalance statistics
        self._rotations_before = 0
        self._rotations_after = 0
        self._rebalance_cost = 0

        # Status message
        self._status = ""
        self._status_ok = True

        # Modal for rebalance results
        self._result_modal = None

        self._init_ui_components()

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def _init_ui_components(self):
        """Initialize all panel buttons and toggles."""
        panel_x = WINDOW_W - 280
        y = NAV_H + PANEL_PADDING + 40

        # Toggle for Stress Mode
        toggle_rect = pygame.Rect(panel_x + PANEL_PADDING, y, 240, 32)
        self._toggle_stress = UIToggle(
            rect=toggle_rect,
            label="Modo Estrés Activo",
            font=self.fonts["body_sm"],
            initial_state=False,
            callback=self._on_toggle_stress
        )
        y += 50

        # Rebalance Global button
        rebalance_rect = pygame.Rect(panel_x + PANEL_PADDING, y, 240, BTN_H)
        self._btn_rebalance = UIButton(
            rect=rebalance_rect,
            text="⚖ REBALANCEO GLOBAL",
            font=self.fonts["label_md"],
            bg_color=BG_SURFACE,
            text_color=AMBER,
            border_color=AMBER,
            callback=self._trigger_global_rebalance
        )
        y += BTN_H + 20

        # Back to main screen
        back_rect = pygame.Rect(panel_x + PANEL_PADDING, y, 240, BTN_H)
        self._btn_back = UIButton(
            rect=back_rect,
            text="← VOLVER A VISTA PRINCIPAL",
            font=self.fonts["label_md"],
            bg_color=BG_DEEP,
            text_color=TEXT_SECONDARY,
            border_color=BORDER,
            callback=self.on_switch_to_main
        )

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_toggle_stress(self, new_state: bool):
        """Enable or disable stress mode in the AVL tree."""
        self.stress_enabled = new_state
        if new_state:
            self.avl_tree.enableStressMode()
            self.set_status("Modo Estrés activado. Las operaciones NO balancearán automáticamente.", success=True)
        else:
            self.avl_tree.disableStressMode()
            self.set_status("Modo Estrés desactivado. Balanceo automático reactivado.", success=True)

    def _trigger_global_rebalance(self):
        """
        Strategy:
        1. Record number of rotations before rebalance
        2. Execute globalRebalance() from backend
        3. Calculate cost (extra rotations performed)
        4. Show results in modal
        """
        if not self.stress_enabled:
            self.set_status("Activa primero el Modo Estrés", success=False)
            return

        self._rotations_before = self.avl_tree.totalRotations()

        # Perform global rebalance (post-order as specified in backend)
        self.avl_tree.globalRebalance()

        self._rotations_after = self.avl_tree.totalRotations()
        self._rebalance_cost = self._rotations_after - self._rotations_before

        self.set_status(f"Rebalanceo completado. Costo: {self._rebalance_cost} rotaciones.", success=True)

        # Show detailed modal
        self._show_rebalance_modal()

    def _show_rebalance_modal(self):
        """Create and display modal with rebalance statistics."""
        modal = UIModal("RESULTADO DE REBALANCEO GLOBAL", width=460, height=320, fonts=self.fonts)

        modal.add_button("CERRAR", modal.hide, color=GREEN_TERM)

        # Content will be drawn in overridden method (see below)
        self._result_modal = modal
        self._result_modal.show()

    # ------------------------------------------------------------------
    # Public interface (to be used by main application loop)
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Dispatch events to UI components and renderer."""
        if self._result_modal and self._result_modal.visible:
            self._result_modal.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Allow closing modal by clicking outside (optional)
                pass
            return

        # Tree renderer (zoom, pan, etc.)
        self.renderer.handle_event(event)

        # Panel components
        if self._toggle_stress.handle_event(event):
            return
        if self._btn_rebalance.handle_event(event):
            return
        if self._btn_back.handle_event(event):
            return

        # Optional: allow clicks on tree to highlight nodes even in stress mode
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # You can add node selection here if needed
            pass

    def update(self, dt_ms: float) -> None:
        """No continuous animation needed for this screen."""
        pass

    def draw(self, surface: pygame.Surface) -> None:
        """Main draw method."""
        surface.fill(BG_DEEP)

        # Draw tree with stress visual feedback
        root = self.avl_tree.getRoot()
        self.renderer.draw(surface, root, stress_mode=self.stress_enabled)

        # Draw right panel
        self._draw_panel(surface)

        # Draw modal if active
        if self._result_modal and self._result_modal.visible:
            self._result_modal.draw(surface)

    def set_status(self, message: str, success: bool = True) -> None:
        """Show temporary status message in panel."""
        self._status = message
        self._status_ok = success

    # ------------------------------------------------------------------
    # Panel drawing
    # ------------------------------------------------------------------

    def _draw_panel(self, surface: pygame.Surface) -> None:
        """Draw the right control panel for Stress Mode."""
        panel_rect = pygame.Rect(WINDOW_W - 280, NAV_H, 280, WINDOW_H - NAV_H)
        pygame.draw.rect(surface, BG_SURFACE, panel_rect)
        pygame.draw.line(surface, BORDER, (panel_rect.x, panel_rect.y),
                         (panel_rect.x, panel_rect.bottom), 1)

        y = panel_rect.y + PANEL_PADDING + 10

        # Title
        title = self.fonts["label_md"].render("// MODO ESTRÉS", True, CRITICAL)
        surface.blit(title, (panel_rect.x + PANEL_PADDING, y))
        y += 40

        # Toggle
        self._toggle_stress.draw(surface)
        y += 60

        # Rebalance button
        self._btn_rebalance.draw(surface)
        y += BTN_H + 30

        # Current metrics
        y = draw_section_header(surface, y, "// ESTADO ACTUAL", self.fonts, panel_rect)

        root = self.avl_tree.getRoot()
        height = self.avl_tree.getHeight() if root else 0
        nodes = self.avl_tree.nodeCount() if root else 0
        rotations = self.avl_tree.totalRotations() if root else 0

        y = draw_metric_row(surface, y, "Altura", str(height), self.fonts, panel_rect)
        y = draw_metric_row(surface, y, "Nodos", str(nodes), self.fonts, panel_rect)
        y = draw_metric_row(surface, y, "Rotaciones totales", str(rotations), self.fonts, panel_rect)

        if self.stress_enabled:
            y = draw_metric_row(surface, y, "Modo", "DEGRADADO", self.fonts, panel_rect)

        y += 20

        # Back button at bottom
        self._btn_back.draw(surface)

        # Status bar
        if self._status:
            color = GREEN_TERM if self._status_ok else CRITICAL
            status_surf = self.fonts["body_xs"].render(self._status, True, color)
            surface.blit(status_surf, (panel_rect.x + PANEL_PADDING,
                                       WINDOW_H - PANEL_PADDING - status_surf.get_height()))

    # ------------------------------------------------------------------
    # Optional: Override modal content for better rebalance report
    # ------------------------------------------------------------------

    def _result_modal_draw_content(self, surface, mx, my):   # You can extend UIModal if needed
        pass