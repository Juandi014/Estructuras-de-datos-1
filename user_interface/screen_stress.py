"""
screen_stress.py
----------------
S3 — Stress Mode (Rebalanceo Diferido) for SkyBalance AVL System.

Allows enabling stress mode (no automatic balancing), performing degrading operations,
and triggering global rebalance with cost measurement.
Uses panel_ui and modal_ui for clean, reusable components.
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
    S3 Stress Mode Screen.
    Manages stress mode toggle, global rebalance, and visual feedback.
    """

    def __init__(self, fonts: dict, avl_tree, on_switch_to_main):
        self.fonts = fonts
        self.avl_tree = avl_tree
        self.on_switch_to_main = on_switch_to_main

        # Tree renderer (same area as main screen)
        self.tree_rect = pygame.Rect(0, NAV_H, WINDOW_W - 280, WINDOW_H - NAV_H)
        self.renderer = TreeRenderer(self.tree_rect)

        # State
        self.stress_enabled = False
        self._status = ""
        self._status_ok = True
        self._rebalance_cost = 0

        # UI Components
        self._toggle_stress = None
        self._btn_rebalance = None
        self._btn_back = None
        self._result_modal = None

        self._init_ui()

    def _init_ui(self):
        """Create panel controls using reusable components."""
        panel_x = WINDOW_W - 280
        y = NAV_H + PANEL_PADDING + 30

        # Stress Mode Toggle
        toggle_rect = pygame.Rect(panel_x + PANEL_PADDING, y, 240, 36)
        self._toggle_stress = UIToggle(
            rect=toggle_rect,
            label="Modo Estrés (sin balanceo automático)",
            font=self.fonts["body_sm"],
            initial_state=False,
            callback=self._on_stress_toggle
        )
        y += 60

        # Global Rebalance Button
        rebalance_rect = pygame.Rect(panel_x + PANEL_PADDING, y, 240, BTN_H)
        self._btn_rebalance = UIButton(
            rect=rebalance_rect,
            text="⚖ REBALANCEO GLOBAL",
            font=self.fonts["label_md"],
            bg_color=BG_SURFACE,
            text_color=AMBER,
            border_color=AMBER,
            callback=self._execute_global_rebalance
        )
        y += BTN_H + 30

        # Back button
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

    def _on_stress_toggle(self, new_state: bool):
        """Enable/disable stress mode in the backend."""
        self.stress_enabled = new_state
        if new_state:
            self.avl_tree.enableStressMode()
            self.set_status("Modo Estrés ACTIVADO → Operaciones sin balanceo automático.", True)
        else:
            self.avl_tree.disableStressMode()
            self.set_status("Modo Estrés DESACTIVADO → Balanceo automático restaurado.", True)

    def _execute_global_rebalance(self):
        """Perform global rebalance and show cost."""
        if not self.stress_enabled:
            self.set_status("Primero activa el Modo Estrés", False)
            return

        rotations_before = self.avl_tree.totalRotations()
        self.avl_tree.globalRebalance()
        rotations_after = self.avl_tree.totalRotations()

        self._rebalance_cost = rotations_after - rotations_before

        self.set_status(f"Rebalanceo completado. Costo estructural: {self._rebalance_cost} rotaciones.", True)
        self._show_rebalance_result_modal()

    def _show_rebalance_result_modal(self):
        """Display detailed rebalance results."""
        modal = UIModal("REBALANCEO GLOBAL FINALIZADO", width=460, height=280, fonts=self.fonts)
        modal.add_button("CERRAR", modal.hide, color=GREEN_TERM)
        self._result_modal = modal
        self._result_modal.show()

    # ------------------------------------------------------------------
    # Public API for App
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._result_modal and self._result_modal.visible:
            self._result_modal.handle_event(event)
            return

        self.renderer.handle_event(event)

        self._toggle_stress.handle_event(event)
        self._btn_rebalance.handle_event(event)
        self._btn_back.handle_event(event)

    def update(self, dt_ms: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BG_DEEP)

        # Draw tree with stress visual mode
        root = self.avl_tree.getRoot()
        self.renderer.draw(surface, root, stress_mode=self.stress_enabled)

        self._draw_panel(surface)

        if self._result_modal and self._result_modal.visible:
            self._result_modal.draw(surface)

    def set_status(self, message: str, success: bool = True):
        self._status = message
        self._status_ok = success

    # ------------------------------------------------------------------
    # Panel drawing
    # ------------------------------------------------------------------

    def _draw_panel(self, surface: pygame.Surface) -> None:
        panel_rect = pygame.Rect(WINDOW_W - 280, NAV_H, 280, WINDOW_H - NAV_H)
        pygame.draw.rect(surface, BG_SURFACE, panel_rect)
        pygame.draw.line(surface, BORDER, (panel_rect.x, panel_rect.y), (panel_rect.x, panel_rect.bottom), 1)

        y = panel_rect.y + PANEL_PADDING + 10

        title = self.fonts["label_md"].render("// MODO ESTRÉS", True, CRITICAL)
        surface.blit(title, (panel_rect.x + PANEL_PADDING, y))
        y += 45

        self._toggle_stress.draw(surface)
        y += 70

        self._btn_rebalance.draw(surface)
        y += BTN_H + 25

        # Live metrics
        y = draw_section_header(surface, y, "// MÉTRICAS ACTUALES", self.fonts, panel_rect)

        root = self.avl_tree.getRoot()
        height = self.avl_tree.getHeight() if root else 0
        nodes = self.avl_tree.nodeCount() if root else 0
        rotations = self.avl_tree.totalRotations() if root else 0

        y = draw_metric_row(surface, y, "Altura", str(height), self.fonts, panel_rect)
        y = draw_metric_row(surface, y, "Nodos", str(nodes), self.fonts, panel_rect)
        y = draw_metric_row(surface, y, "Rotaciones", str(rotations), self.fonts, panel_rect)

        if self.stress_enabled:
            y = draw_metric_row(surface, y, "Estado", "DEGRADADO", self.fonts, panel_rect)

        # Status at bottom
        if self._status:
            color = GREEN_TERM if self._status_ok else CRITICAL
            status_surf = self.fonts["body_xs"].render(self._status[:60], True, color)  # truncate if too long
            surface.blit(status_surf, (panel_rect.x + PANEL_PADDING,
                                       WINDOW_H - PANEL_PADDING - status_surf.get_height()))

        # Back button
        self._btn_back.draw(surface)