"""
screen_home.py
--------------
Home Screen - Versión ajustada para que el historial entre completamente en pantalla.
Tarjeta de bienvenida ancha + tarjetas de acciones más compactas + historial subido.
"""

import pygame
from user_interface.color_scheme import (
    BG_DEEP, BG_SURFACE, BG_SURFACE2, PRIMARY, LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DIM, SECONDARY, DARK_ACCENT,
    CARD_RADIUS, NAV_H, BTN_H, WINDOW_W, WINDOW_H
)
from user_interface.tree_renderer import TreeRenderer
from user_interface.panel_ui import UIButton


class HomeScreen:
    """Dashboard principal de SkyBalance AVL - Layout optimizado para evitar desbordamiento."""

    def __init__(self, fonts: dict, avl_tree, on_switch_screen):
        self.fonts = fonts
        self.avl_tree = avl_tree
        self.on_switch_screen = on_switch_screen

        self.mini_renderer = TreeRenderer(pygame.Rect(0, 0, 1, 1))

        # Animación de hover
        self.hover_scales = [1.0] * 5
        self.target_scales = [1.0] * 5
        self.hovered_index = -1

        self.card_rects = []
        self.card_data = self._get_card_data()

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos)

    def _update_hover(self, pos):
        self.hovered_index = -1
        for i, rect in enumerate(self.card_rects):
            if rect.collidepoint(pos):
                self.hovered_index = i
                self.target_scales[i] = 1.06
                break

        for i in range(len(self.target_scales)):
            if i != self.hovered_index:
                self.target_scales[i] = 1.0

    def _handle_click(self, pos):
        for i, rect in enumerate(self.card_rects):
            if rect.collidepoint(pos):
                screen_id = self.card_data[i][3]
                if screen_id:
                    self.on_switch_screen(screen_id)
                return

    def update(self, dt_ms: float):
        """Actualiza animaciones suaves de hover."""
        for i in range(len(self.hover_scales)):
            diff = self.target_scales[i] - self.hover_scales[i]
            self.hover_scales[i] += diff * 0.18

    def draw(self, surface: pygame.Surface):
        surface.fill(BG_DEEP)
        self.card_rects.clear()

        self._draw_wide_welcome_card(surface)
        self._draw_quick_actions(surface)
        self._draw_history_section(surface)
        self._draw_right_panel(surface)

    # ==================================================================
    # ======================  TARJETA ANCHA DE BIENVENIDA  =============
    # ==================================================================

    def _draw_wide_welcome_card(self, surface: pygame.Surface):
        """Tarjeta principal ancha (manteniendo tu preferencia)."""
        welcome_rect = pygame.Rect(40, NAV_H + 20, int(WINDOW_W * 0.68) - 40, 128)

        pygame.draw.rect(surface, BG_SURFACE, welcome_rect, border_radius=CARD_RADIUS)
        pygame.draw.rect(surface, PRIMARY, welcome_rect, width=4, border_radius=CARD_RADIUS)

        title = self.fonts["title_lg"].render("SkyBalance AVL", True, LIGHT)
        surface.blit(title, (welcome_rect.x + 40, welcome_rect.y + 25))

        subtitle = self.fonts["body_md"].render(
            "Sistema de gestión aérea optimizado con Árbol AVL en tiempo real", 
            True, TEXT_SECONDARY
        )
        surface.blit(subtitle, (welcome_rect.x + 40, welcome_rect.y + 68))

        btn_rect = pygame.Rect(welcome_rect.right - 340, welcome_rect.y + 35, 310, BTN_H)
        btn = UIButton(btn_rect, "CARGAR ARCHIVO JSON", self.fonts["label_md"],
                       bg_color=PRIMARY, text_color=BG_DEEP, border_color=LIGHT)
        btn.draw(surface)

    # ==================================================================
    # ======================  TARJETAS COMPACTAS  ======================
    # ==================================================================

    def _get_card_data(self):
        return [
            ("AVL Principal",      "Gestión del árbol balanceado",      PRIMARY,      "main"),
            ("Modo Estrés",        "Degradación y rebalanceo",          DARK_ACCENT, "stress"),
            ("Versiones",          "Guardar / Restaurar",               SECONDARY,   "versions"),
            ("Cancelación Masiva", "Eliminar vuelo + subrama",          DARK_ACCENT, "cancel"),
            ("Rentabilidad",       "Nodo de menor impacto",             PRIMARY,    "rentability"),
        ]

    def _draw_quick_actions(self, surface: pygame.Surface):
        """Dos filas de tarjetas más cortas para liberar espacio vertical."""
        card_w = 248
        card_h = 125          # Reducido para que el historial entre
        spacing_x = 24
        spacing_y = 18        # Espaciado vertical reducido

        start_y = NAV_H + 165

        for i, (title, desc, accent_color, screen_id) in enumerate(self.card_data):
            row = i // 3
            col = i % 3

            base_x = 40 + col * (card_w + spacing_x)
            base_y = start_y + row * (card_h + spacing_y)

            base_rect = pygame.Rect(base_x, base_y, card_w, card_h)
            self.card_rects.append(base_rect)

            scale = self.hover_scales[i]
            draw_w = int(card_w * scale)
            draw_h = int(card_h * scale)

            offset_x = (card_w - draw_w) // 2
            offset_y = (card_h - draw_h) // 2

            draw_rect = pygame.Rect(base_x + offset_x, base_y + offset_y, draw_w, draw_h)

            self._draw_single_card(surface, draw_rect, title, desc, accent_color, scale > 1.02)

    def _draw_single_card(self, surface, rect, title, desc, accent_color, is_hovered):
        base_color = tuple(min(255, int(c * 0.93)) for c in accent_color)

        pygame.draw.rect(surface, base_color, rect, border_radius=CARD_RADIUS)

        glass = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        alpha = 48 if is_hovered else 26
        glass.fill((255, 255, 255, alpha))
        surface.blit(glass, rect.topleft)

        border_w = 5 if is_hovered else 3
        pygame.draw.rect(surface, accent_color, rect, width=border_w, border_radius=CARD_RADIUS)

        shadow_offset = 8 if is_hovered else 5
        shadow_rect = pygame.Rect(rect.x + shadow_offset, rect.y + shadow_offset, rect.width, rect.height)
        pygame.draw.rect(surface, (0, 0, 0, 38 if is_hovered else 26), shadow_rect, border_radius=CARD_RADIUS)

        icon = self.fonts["title_lg"].render(self._get_card_icon(title), True, accent_color)
        surface.blit(icon, (rect.x + 24, rect.y + 12))

        title_surf = self.fonts["label_md"].render(title, True, TEXT_PRIMARY)
        surface.blit(title_surf, (rect.x + 24, rect.y + 64))

        desc_surf = self.fonts["body_sm"].render(desc, True, TEXT_SECONDARY)
        surface.blit(desc_surf, (rect.x + 24, rect.y + 86))

    def _get_card_icon(self, title: str) -> str:
        icons = {
            "AVL Principal":      "🌳",
            "Modo Estrés":        "⚠️",
            "Versiones":          "📌",
            "Cancelación Masiva": "🗑️",
            "Rentabilidad":       "💰"
        }
        return icons.get(title, "✈️")

    # ==================================================================
    # ======================  HISTORIAL SUBIDO  ========================
    # ==================================================================

    def _draw_history_section(self, surface: pygame.Surface):
        """Historial subido y compacto para que entre completamente en pantalla."""
        # Posición calculada después de tarjeta ancha + 2 filas compactas
        history_y = NAV_H + 165 + (125 + 18) * 2 + 18

        rect = pygame.Rect(40, history_y, int(WINDOW_W * 0.68) - 40, 130)

        pygame.draw.rect(surface, BG_SURFACE, rect, border_radius=CARD_RADIUS)
        pygame.draw.rect(surface, SECONDARY, rect, width=2, border_radius=CARD_RADIUS)

        title = self.fonts["label_md"].render("Historial Reciente", True, LIGHT)
        surface.blit(title, (rect.x + 30, rect.y + 14))

        entries = [
            "Versión 'Alta Demanda' guardada",
            "Vuelo SB400 cancelado con subrama",
            "Rebalanceo global ejecutado",
            "JSON ModoTopología cargado exitosamente"
        ]

        y = rect.y + 44
        for entry in entries:
            surf = self.fonts["body_sm"].render("• " + entry, True, TEXT_SECONDARY)
            surface.blit(surf, (rect.x + 30, y))
            y += 19   # línea más compacta

    def _draw_right_panel(self, surface: pygame.Surface):
        right_rect = pygame.Rect(int(WINDOW_W * 0.7), NAV_H, int(WINDOW_W * 0.3), WINDOW_H - NAV_H)
        pygame.draw.rect(surface, BG_SURFACE, right_rect)

        y = NAV_H + 35
        title = self.fonts["label_md"].render("Vista Previa del Árbol", True, PRIMARY)
        surface.blit(title, (right_rect.x + 28, y))
        y += 45

        preview_rect = pygame.Rect(right_rect.x + 28, y, right_rect.width - 56, 255)
        pygame.draw.rect(surface, BG_SURFACE2, preview_rect, border_radius=CARD_RADIUS)

        if self.avl_tree.getRoot():
            self.mini_renderer.rect = preview_rect
            self.mini_renderer.zoom = 0.47
            self.mini_renderer.draw(surface, self.avl_tree.getRoot())
        else:
            msg = self.fonts["body_sm"].render("Carga un JSON\npara visualizar el árbol", True, TEXT_DIM)
            surface.blit(msg, msg.get_rect(center=preview_rect.center))

    def set_status(self, message: str, success: bool = True):
        self._status = message
        self._status_ok = success