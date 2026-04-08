"""
screen_compare.py
-----------------
Pantalla de Comparación AVL vs BST (modo INSERCIÓN)

Muestra ambos árboles lado a lado y permite reproducir las inserciones paso a paso.
"""

import pygame
from user_interface.color_scheme import (
    BG_DEEP, BG_SURFACE, BG_SURFACE2, BORDER, PRIMARY, LIGHT, TEXT_DIM,
    TEXT_PRIMARY, TEXT_SECONDARY, SECONDARY, DARK_ACCENT,
    CARD_RADIUS, NAV_H, PANEL_PADDING, BTN_H, WINDOW_W, WINDOW_H
)
from user_interface.tree_renderer import TreeRenderer
from user_interface.panel_ui import UIButton


class CompareScreen:
    def __init__(self, fonts: dict, avl_tree, bst_tree, on_switch_screen):
        self.fonts = fonts
        self.avl_tree = avl_tree
        self.bst_tree = bst_tree
        self.on_switch_screen = on_switch_screen

        # Renderers para ambos árboles
        avl_rect = pygame.Rect(40, NAV_H + 80, int(WINDOW_W * 0.38), WINDOW_H - NAV_H - 140)
        bst_rect = pygame.Rect(int(WINDOW_W * 0.42), NAV_H + 80, int(WINDOW_W * 0.28), WINDOW_H - NAV_H - 140)

        self.avl_renderer = TreeRenderer(avl_rect)
        self.bst_renderer = TreeRenderer(bst_rect)

        self.is_playing = False
        self.current_step = 0
        self.insertion_list = []   # Se llenará cuando se cargue el JSON

        self.hovered_button = None

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos)

    def _update_hover(self, pos):
        self.hovered_button = None
        # Se puede expandir más adelante

    def _handle_click(self, pos):
        # Aquí irá la lógica del botón "Reproducir"
        print("Botón reproducir clickeado - lógica pendiente")

    def update(self, dt_ms: float):
        pass

    def draw(self, surface: pygame.Surface):
        surface.fill(BG_DEEP)

        self._draw_header(surface)
        self._draw_trees(surface)
        self._draw_right_panel(surface)

    def _draw_header(self, surface):
        title = self.fonts["title_lg"].render("Comparación AVL vs BST", True, LIGHT)
        surface.blit(title, (WINDOW_W // 2 - title.get_width() // 2, NAV_H + 20))

        subtitle = self.fonts["body_md"].render("Modo Inserción - Demostración de balanceo", True, TEXT_SECONDARY)
        surface.blit(subtitle, (WINDOW_W // 2 - subtitle.get_width() // 2, NAV_H + 55))

    def _draw_trees(self, surface):
        # Títulos sobre cada árbol
        avl_title = self.fonts["label_md"].render("ÁRBOL AVL (Balanceado)", True, PRIMARY)
        surface.blit(avl_title, (80, NAV_H + 90))

        bst_title = self.fonts["label_md"].render("ÁRBOL BST (Sin balanceo)", True, DARK_ACCENT)
        surface.blit(bst_title, (int(WINDOW_W * 0.45), NAV_H + 90))

        # Dibujar árboles
        self.avl_renderer.draw(surface, self.avl_tree.getRoot())
        self.bst_renderer.draw(surface, self.bst_tree.getRoot())

    def _draw_right_panel(self, surface):
        panel_rect = pygame.Rect(int(WINDOW_W * 0.68), NAV_H, int(WINDOW_W * 0.32), WINDOW_H - NAV_H)
        pygame.draw.rect(surface, BG_SURFACE, panel_rect)

        y = NAV_H + 30

        title = self.fonts["label_md"].render("Análisis Comparativo", True, PRIMARY)
        surface.blit(title, (panel_rect.x + 30, y))
        y += 50

        # Tarjetas verticales de métricas
        metrics = [
            ("Altura", "AVL: 7", "BST: 14"),
            ("Rotaciones", "AVL: 12", "BST: 0"),
            ("Profundidad Máx.", "AVL: 7", "BST: 14"),
            ("Nodos Críticos", "AVL: 2", "BST: 9"),
        ]

        for label, avl_val, bst_val in metrics:
            # Tarjeta
            card_rect = pygame.Rect(panel_rect.x + 30, y, panel_rect.width - 60, 52)
            pygame.draw.rect(surface, BG_SURFACE2, card_rect, border_radius=10)

            lbl = self.fonts["body_sm"].render(label, True, TEXT_SECONDARY)
            surface.blit(lbl, (card_rect.x + 16, card_rect.y + 8))

            avl_text = self.fonts["label_md"].render(avl_val, True, PRIMARY)
            surface.blit(avl_text, (card_rect.x + 16, card_rect.y + 26))

            bst_text = self.fonts["label_md"].render(bst_val, True, DARK_ACCENT)
            surface.blit(bst_text, (card_rect.right - bst_text.get_width() - 16, card_rect.y + 26))

            y += 68

        # Botón Reproducir
        btn_rect = pygame.Rect(panel_rect.x + 30, y + 20, panel_rect.width - 60, BTN_H + 10)
        btn = UIButton(btn_rect, "▶ REPRODUCIR INSERCIONES PASO A PASO", self.fonts["label_md"],
                       bg_color=PRIMARY, text_color=BG_DEEP, border_color=PRIMARY)
        btn.draw(surface)

        # Mini historial de inserciones
        y += 100
        hist_title = self.fonts["label_sm"].render("Inserciones realizadas:", True, TEXT_DIM)
        surface.blit(hist_title, (panel_rect.x + 30, y))

    def set_insertion_list(self, flights):
        """Recibe la lista de vuelos para la reproducción paso a paso"""
        self.insertion_list = flights
        self.current_step = 0