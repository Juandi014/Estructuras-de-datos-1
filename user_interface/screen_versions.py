"""
screen_versions.py
------------------
S4 — Sistema de Versionado Persistente para SkyBalance AVL.

Permite guardar y restaurar versiones nombradas del árbol completo.
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


class VersionsScreen:
    def __init__(self, fonts: dict, avl_tree, on_switch_to_main):
        self.fonts = fonts
        self.avl_tree = avl_tree
        self.on_switch_to_main = on_switch_to_main

        self.renderer = TreeRenderer(pygame.Rect(0, NAV_H, WINDOW_W - 280, WINDOW_H - NAV_H))

        self._version_input = None
        self._btn_save = None
        self._btn_back = None
        self._restore_modal = None
        self._version_to_restore = None

        self._status = ""
        self._status_ok = True

        self._init_ui()

    def _init_ui(self):
        panel_x = WINDOW_W - 280
        y = NAV_H + PANEL_PADDING + 30

        # Input para nombre de versión
        input_rect = pygame.Rect(panel_x + PANEL_PADDING, y, 240, 32)
        self._version_input = UIInputField(
            rect=input_rect,
            placeholder="Nombre de versión (ej: Alta Demanda)",
            font=self.fonts["body_sm"]
        )
        y += 50

        # Botón Guardar
        save_rect = pygame.Rect(panel_x + PANEL_PADDING, y, 240, BTN_H)
        self._btn_save = UIButton(
            rect=save_rect,
            text="💾 GUARDAR VERSIÓN ACTUAL",
            font=self.fonts["label_md"],
            bg_color=BG_SURFACE,
            text_color=AMBER,
            border_color=AMBER,
            callback=self._save_version
        )
        y += BTN_H + 30

        # Botón Volver
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

    def _save_version(self):
        name = self._version_input.value.strip()
        if not name:
            self.set_status("Debes ingresar un nombre para la versión", False)
            return

        if self.avl_tree.save_version(name):
            self.set_status(f"Versión '{name}' guardada exitosamente.", True)
            self._version_input.value = ""
        else:
            self.set_status(f"Ya existe una versión con el nombre '{name}'", False)

    def _restore_version(self, name: str):
        self._version_to_restore = name
        modal = UIModal(f"¿Restaurar versión '{name}'?", width=400, height=200, fonts=self.fonts)
        modal.add_button("SÍ, RESTAURAR", self._confirm_restore, color=CRITICAL)
        modal.add_button("CANCELAR", modal.hide)
        self._restore_modal = modal
        self._restore_modal.show()

    def _confirm_restore(self):
        if self.avl_tree.load_version(self._version_to_restore):
            self.set_status(f"Versión '{self._version_to_restore}' restaurada.", True)
        else:
            self.set_status("Error al restaurar la versión.", False)
        self._restore_modal.hide()
        self._version_to_restore = None

    # ------------------------------------------------------------------
    def handle_event(self, event):
        if self._restore_modal and self._restore_modal.visible:
            self._restore_modal.handle_event(event)
            return

        self.renderer.handle_event(event)
        self._version_input.handle_event(event)
        self._btn_save.handle_event(event)
        self._btn_back.handle_event(event)

    def draw(self, surface):
        surface.fill(BG_DEEP)
        self.renderer.draw(surface, self.avl_tree.getRoot())

        self._draw_panel(surface)

        if self._restore_modal and self._restore_modal.visible:
            self._restore_modal.draw(surface)

    def _draw_panel(self, surface):
        panel_rect = pygame.Rect(WINDOW_W - 280, NAV_H, 280, WINDOW_H - NAV_H)
        pygame.draw.rect(surface, BG_SURFACE, panel_rect)
        pygame.draw.line(surface, BORDER, (panel_rect.x, panel_rect.y), (panel_rect.x, panel_rect.bottom), 1)

        y = panel_rect.y + PANEL_PADDING + 10

        title = self.fonts["label_md"].render("// SISTEMA DE VERSIONES", True, AMBER)
        surface.blit(title, (panel_rect.x + PANEL_PADDING, y))
        y += 40

        self._version_input.draw(surface)
        y += 50
        self._btn_save.draw(surface)
        y += BTN_H + 25

        y = draw_section_header(surface, y, "// VERSIONES GUARDADAS", self.fonts, panel_rect)

        versions = self.avl_tree.get_versions()
        if not versions:
            no_ver = self.fonts["body_sm"].render("No hay versiones guardadas aún", True, TEXT_DIM)
            surface.blit(no_ver, (panel_rect.x + PANEL_PADDING, y))
        else:
            for name, data in versions.items():
                lbl = self.fonts["body_sm"].render(f"{name}  ({data['timestamp']})", True, TEXT_PRIMARY)
                surface.blit(lbl, (panel_rect.x + PANEL_PADDING, y))
                y += 26

                restore_rect = pygame.Rect(panel_rect.x + PANEL_PADDING + 10, y, 200, 26)
                btn = UIButton(restore_rect, "RESTABLECER", self.fonts["body_sm"],
                               bg_color=BG_DEEP, text_color=GREEN_TERM, border_color=GREEN_TERM,
                               callback=lambda n=name: self._restore_version(n))
                btn.draw(surface)
                y += 38

        self._btn_back.draw(surface)

        if self._status:
            color = GREEN_TERM if self._status_ok else CRITICAL
            status_surf = self.fonts["body_xs"].render(self._status, True, color)
            surface.blit(status_surf, (panel_rect.x + PANEL_PADDING, WINDOW_H - PANEL_PADDING - 25))

    def set_status(self, message: str, success: bool = True):
        self._status = message
        self._status_ok = success