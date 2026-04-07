"""
screen_cancel.py
----------------
S6 — Diálogo de Cancelación Masiva (SkyBalance AVL)

Permite buscar un vuelo por código y cancelarlo junto con toda su subrama.
Usa los métodos existentes: cancel_flight(), find_node(), remove_subtree().
"""

import pygame
from user_interface.color_scheme import (
    BG_DEEP, BG_SURFACE, BORDER, AMBER, CRITICAL, GREEN_TERM,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DIM,
    WINDOW_W, WINDOW_H, NAV_H, PANEL_PADDING, BTN_H
)
from user_interface.tree_renderer import TreeRenderer
from user_interface.panel_ui import UIButton, UIInputField, draw_section_header
from user_interface.modal_ui import UIModal


class CancelScreen:
    """
    S6 - Mass Cancellation Screen.
    Uses existing avl_tree.cancel_flight(code) method.
    """

    def __init__(self, fonts: dict, avl_tree, on_switch_to_main):
        self.fonts = fonts
        self.avl_tree = avl_tree
        self.on_switch_to_main = on_switch_to_main

        self.renderer = TreeRenderer(pygame.Rect(0, NAV_H, WINDOW_W - 280, WINDOW_H - NAV_H))

        self._search_input = None
        self._btn_search = None
        self._btn_back = None

        self._confirm_modal = None
        self._node_to_cancel = None   # FlightNode found

        self._status = ""
        self._status_ok = True

        self._init_ui()

    def _init_ui(self):
        panel_x = WINDOW_W - 280
        y = NAV_H + PANEL_PADDING + 40

        # Input field
        input_rect = pygame.Rect(panel_x + PANEL_PADDING, y, 240, 32)
        self._search_input = UIInputField(
            rect=input_rect,
            placeholder="Código del vuelo (ej: SB400)",
            font=self.fonts["body_sm"]
        )
        y += 50

        # Search + Cancel button
        btn_rect = pygame.Rect(panel_x + PANEL_PADDING, y, 240, BTN_H)
        self._btn_search = UIButton(
            rect=btn_rect,
            text="🔍 BUSCAR Y CONFIRMAR CANCELACIÓN",
            font=self.fonts["label_md"],
            bg_color=BG_SURFACE,
            text_color=CRITICAL,
            border_color=CRITICAL,
            callback=self._find_and_show_confirmation
        )
        y += BTN_H + 40

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

    def _find_and_show_confirmation(self):
        """Busca el nodo usando find_node y muestra modal de confirmación."""
        code_str = self._search_input.value.strip()
        if not code_str:
            self.set_status("Por favor ingresa un código de vuelo", False)
            return

        # Usamos el método que ya tienes
        node = self.avl_tree.find_node(code_str)

        if node is None:
            self.set_status(f"Vuelo {code_str} no encontrado en el árbol.", False)
            return

        self._node_to_cancel = node
        self._show_cancel_confirmation_modal(node)

    def _show_cancel_confirmation_modal(self, node):
        """Modal con información del vuelo y advertencia de cancelación masiva."""
        modal = UIModal(f"CANCELACIÓN MASIVA - {node.code}", 
                        width=480, height=420, fonts=self.fonts)

        modal.add_button("SÍ, CANCELAR VUELO Y SUBRAMA", 
                         self._execute_mass_cancel, color=CRITICAL)
        modal.add_button("NO, CANCELAR OPERACIÓN", 
                         modal.hide, color=TEXT_SECONDARY)

        self._confirm_modal = modal
        self._confirm_modal.show()

    def _execute_mass_cancel(self):
        """Ejecuta la cancelación usando el método que ya tienes."""
        if not self._node_to_cancel:
            return

        code = self._node_to_cancel.code

        try:
            # Aquí llamamos directamente al método que ya implementaste
            self.avl_tree.cancel_flight(code)

            self.set_status(f"Vuelo {code} y toda su subrama fueron cancelados correctamente.", True)
            self._search_input.value = ""   # limpiar campo
        except Exception as e:
            self.set_status(f"Error durante la cancelación: {str(e)}", False)

        if self._confirm_modal:
            self._confirm_modal.hide()
        self._node_to_cancel = None

    # ------------------------------------------------------------------
    # Standard screen methods
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event):
        if self._confirm_modal and getattr(self._confirm_modal, 'visible', False):
            self._confirm_modal.handle_event(event)
            return

        self.renderer.handle_event(event)
        self._search_input.handle_event(event)
        self._btn_search.handle_event(event)
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

        y = panel_rect.y + PANEL_PADDING + 10

        title = self.fonts["label_md"].render("// CANCELACIÓN MASIVA", True, CRITICAL)
        surface.blit(title, (panel_rect.x + PANEL_PADDING, y))
        y += 45

        self._search_input.draw(surface)
        y += 55
        self._btn_search.draw(surface)
        y += BTN_H + 30

        self._btn_back.draw(surface)

        # Status message
        if self._status:
            color = GREEN_TERM if self._status_ok else CRITICAL
            status_surf = self.fonts["body_xs"].render(self._status[:58], True, color)
            surface.blit(status_surf, (panel_rect.x + PANEL_PADDING,
                                       WINDOW_H - PANEL_PADDING - 30))

    def set_status(self, message: str, success: bool = True):
        self._status = message
        self._status_ok = success