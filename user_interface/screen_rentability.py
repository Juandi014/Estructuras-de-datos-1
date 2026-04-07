"""
screen_rentability.py
---------------------
S7 — Eliminación Inteligente por Impacto Económico

Encuentra automáticamente el nodo de menor rentabilidad usando 
avl_tree.leastProfitableNode() y permite cancelarlo junto con toda su subrama.
"""

import pygame
from user_interface.color_scheme import (
    BG_DEEP, BG_SURFACE, BORDER, AMBER, CRITICAL, GREEN_TERM,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DIM,
    WINDOW_W, WINDOW_H, NAV_H, PANEL_PADDING, BTN_H
)
from user_interface.tree_renderer import TreeRenderer
from user_interface.panel_ui import UIButton, draw_section_header
from user_interface.modal_ui import UIModal


class RentabilityScreen:
    """
    S7 - Intelligent Elimination by Economic Impact (Requirement 8).
    Uses existing avl_tree.leastProfitableNode() and cancelSubtree().
    """

    def __init__(self, fonts: dict, avl_tree, on_switch_to_main):
        self.fonts = fonts
        self.avl_tree = avl_tree
        self.on_switch_to_main = on_switch_to_main

        self.renderer = TreeRenderer(pygame.Rect(0, NAV_H, WINDOW_W - 280, WINDOW_H - NAV_H))

        self._btn_eliminate = None
        self._btn_back = None

        self._confirm_modal = None
        self._node_to_delete = None

        self._status = ""
        self._status_ok = True

        self._init_ui()

    def _init_ui(self):
        """Initialize panel components."""
        panel_x = WINDOW_W - 280
        y = NAV_H + PANEL_PADDING + 60

        # Main elimination button
        eliminate_rect = pygame.Rect(panel_x + PANEL_PADDING, y, 240, BTN_H + 12)
        self._btn_eliminate = UIButton(
            rect=eliminate_rect,
            text="📉 ELIMINAR NODO DE MENOR RENTABILIDAD",
            font=self.fonts["label_md"],
            bg_color=BG_SURFACE,
            text_color=CRITICAL,
            border_color=CRITICAL,
            callback=self._find_and_confirm_lowest
        )
        y += BTN_H + 50

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

    def _find_and_confirm_lowest(self):
        """Find the least profitable node and show confirmation modal."""
        node = self.avl_tree.leastProfitableNode()

        if node is None:
            self.set_status("No hay nodos en el árbol para evaluar.", False)
            return

        self._node_to_delete = node
        self._show_confirmation_modal(node)

    def _show_confirmation_modal(self, node):
        """Display modal with node information and rentability."""
        rentability = self.avl_tree._calculate_rentability(node)   # using your existing private method

        title = f"MENOR RENTABILIDAD DETECTADA: {node.code}"

        modal = UIModal(title, width=500, height=420, fonts=self.fonts)

        modal.add_button("SÍ, CANCELAR SUBRAMA COMPLETA", 
                         self._execute_cancellation, color=CRITICAL)
        modal.add_button("CANCELAR OPERACIÓN", modal.hide)

        self._confirm_modal = modal
        self._confirm_modal.show()

    def _execute_cancellation(self):
        """Execute mass cancellation of the lowest rentability node."""
        if not self._node_to_delete:
            return

        code = self._node_to_delete.code

        try:
            # Usamos el método que ya tienes implementado
            self.avl_tree.cancelSubtree(code)

            self.set_status(f"Nodo {code} (menor rentabilidad) y su subrama eliminados correctamente.", True)
        except Exception as e:
            self.set_status(f"Error durante la cancelación: {str(e)}", False)

        if self._confirm_modal:
            self._confirm_modal.hide()
        self._node_to_delete = None

    # ------------------------------------------------------------------
    # Standard screen methods
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event):
        if self._confirm_modal and getattr(self._confirm_modal, 'visible', False):
            self._confirm_modal.handle_event(event)
            return

        self.renderer.handle_event(event)
        self._btn_eliminate.handle_event(event)
        self._btn_back.handle_event(event)

    def draw(self, surface: pygame.Surface):
        surface.fill(BG_DEEP)
        self.renderer.draw(surface, self.avl_tree.getRoot())

        self._draw_panel(surface)

        if self._confirm_modal and getattr(self._confirm_modal, 'visible', False):
            self._confirm_modal.draw(surface)

    def _draw_panel(self, surface: pygame.Surface):
        panel_rect = pygame.Rect(WINDOW_W - 280, NAV_H, 280, WINDOW_H - NAV_H)
        pygame.draw.rect(surface, BG_SURFACE, panel_rect)
        pygame.draw.line(surface, BORDER, (panel_rect.x, panel_rect.y), (panel_rect.x, panel_rect.bottom), 1)

        y = panel_rect.y + PANEL_PADDING + 20

        title = self.fonts["label_md"].render("// ELIMINACIÓN POR RENTABILIDAD", True, CRITICAL)
        surface.blit(title, (panel_rect.x + PANEL_PADDING, y))
        y += 50

        self._btn_eliminate.draw(surface)
        y += BTN_H + 40

        # Brief explanation
        explanation = self.fonts["body_sm"].render(
            "Calcula rentabilidad y elimina\nel nodo + toda su subrama", 
            True, TEXT_DIM
        )
        surface.blit(explanation, (panel_rect.x + PANEL_PADDING, y))

        self._btn_back.draw(surface)

        # Status bar
        if self._status:
            color = GREEN_TERM if self._status_ok else CRITICAL
            status_surf = self.fonts["body_xs"].render(self._status[:62], True, color)
            surface.blit(status_surf, (panel_rect.x + PANEL_PADDING,
                                       WINDOW_H - PANEL_PADDING - 30))

    def set_status(self, message: str, success: bool = True):
        self._status = message
        self._status_ok = success