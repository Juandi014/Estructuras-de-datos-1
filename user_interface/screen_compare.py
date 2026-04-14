import math
import pygame
from user_interface.color_scheme import (
    BG_DEEP, BG_SURFACE2, BORDER, PRIMARY, LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DIM, SECONDARY, DARK_ACCENT,
    CARD_RADIUS, NAV_H, BTN_H, WINDOW_W, WINDOW_H
)
from user_interface.tree_renderer import TreeRenderer
from user_interface.panel_ui import UIButton


class CompareScreen:
    """
    Main comparison screen with balanced 50/50 layout for AVL and BST trees.
    """

    def __init__(self, fonts: dict, avl_tree, bst_tree, on_switch_screen):
        self.fonts = fonts
        self.avl_tree = avl_tree
        self.bst_tree = bst_tree
        self.on_switch_screen = on_switch_screen

        # ------------------- Layout Calculation -------------------
        vs_space = int(WINDOW_W * 0.14)          # 14% for VS area
        tree_width = (WINDOW_W - vs_space) // 2 - 50

        avl_viewport = pygame.Rect(30, NAV_H + 140, tree_width, WINDOW_H - NAV_H - 300)
        bst_viewport = pygame.Rect(WINDOW_W - tree_width - 30, NAV_H + 140, tree_width, WINDOW_H - NAV_H - 300)

        self.avl_renderer = TreeRenderer(avl_viewport)
        self.bst_renderer = TreeRenderer(bst_viewport)

        # Center both trees initially
        self.avl_renderer.center_on_root(self.avl_tree.getRoot())
        self.bst_renderer.center_on_root(self.bst_tree.getRoot())

        # VS animation state
        self.vs_pulse = 0.0

        # Playback
        self.is_playing = False
        self.current_step = 0
        self.insertion_list = []

        self._init_ui_buttons()

    def _init_ui_buttons(self):
        btn_y = WINDOW_H - BTN_H - 25
        btn_w = 320

        self.btn_back = UIButton(
            rect=pygame.Rect(WINDOW_W // 2 - btn_w // 2, btn_y, btn_w, BTN_H),
            text="← VISTA AVL",
            font=self.fonts["label_md"],
            bg_color=BG_SURFACE2,
            text_color=TEXT_SECONDARY,
            border_color=BORDER,
            callback=self.on_switch_screen
        )

    # ------------------------------------------------------------------
    # Event Handling (unchanged)
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event):
        self.avl_renderer.handle_event(event)
        self.bst_renderer.handle_event(event)
        self.btn_back.handle_event(event)

    # ------------------------------------------------------------------
    # Update & Animation
    # ------------------------------------------------------------------

    def update(self, dt_ms: float):
        self.vs_pulse += 0.004 * dt_ms

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface):
        surface.fill(BG_DEEP)

        self._draw_header(surface)
        self._draw_vs_separator(surface)
        self._draw_avl_section(surface)
        self._draw_bst_section(surface)
        self._draw_buttons(surface)

    def _draw_header(self, surface):
        title = self.fonts["title_lg"].render("COMPARACIÓN AVL vs BST", True, LIGHT)
        surface.blit(title, (WINDOW_W // 2 - title.get_width() // 2, NAV_H + 20))

        subtitle = self.fonts["body_md"].render(
            "Modo Inserción — Demostrando la ventaja del balanceo automático",
            True, TEXT_SECONDARY
        )
        surface.blit(subtitle, (WINDOW_W // 2 - subtitle.get_width() // 2, NAV_H + 58))

    def _draw_vs_separator(self, surface):
        """Vertical separation line + pulsing circle with VS inside - circle moved to exact middle"""
        cx = WINDOW_W // 2
        cy = NAV_H + 255   # moved down to be exactly in the middle of the VS area

        # Vertical separation line (full height)
        line_alpha = 70 + 50 * abs(math.sin(self.vs_pulse * 0.005))
        line_color = (*SECONDARY[:3], int(line_alpha))
        pygame.draw.line(surface, line_color, (cx, NAV_H + 80), (cx, WINDOW_H - 80), 4)

        # Pulsing circle (centered in VS area)
        radius = 55 + 9 * math.sin(self.vs_pulse * 0.008)
        pygame.draw.circle(surface, BG_SURFACE2, (cx, cy), int(radius + 10))
        pygame.draw.circle(surface, SECONDARY, (cx, cy), int(radius), 6)

        # VS text inside circle
        vs_text = self.fonts["title_md"].render("VS", True, LIGHT)
        surface.blit(vs_text, vs_text.get_rect(center=(cx, cy)))

    def _draw_avl_section(self, surface):
        self._draw_tree_with_metrics(
            surface,
            self.avl_renderer,
            self.avl_tree,
            "ÁRBOL AVL (Balanceado)",
            PRIMARY,
            30
        )

    def _draw_bst_section(self, surface):
        self._draw_tree_with_metrics(
            surface,
            self.bst_renderer,
            self.bst_tree,
            "ÁRBOL BST (Sin balanceo)",
            DARK_ACCENT,
            WINDOW_W // 2 + 10
        )

    def _draw_tree_with_metrics(self, surface, renderer, tree, title, accent_color, x_offset):
        # Tree name in a nice box at the top
        box_rect = pygame.Rect(x_offset + 20, NAV_H + 85, 320, 38)
        pygame.draw.rect(surface, BG_SURFACE2, box_rect, border_radius=8)
        pygame.draw.rect(surface, accent_color, box_rect, width=2, border_radius=8)

        title_surf = self.fonts["label_md"].render(title, True, accent_color)
        surface.blit(title_surf, (box_rect.x + 20, box_rect.y + 10))

        # Tree rendering
        if tree.getRoot():
            renderer.draw(surface, tree.getRoot())
        else:
            self._draw_empty_tree(surface, renderer.viewport, f"{title.split()[1]} vacío")

        # Property cards moved lower
        self._draw_individual_metrics(surface, tree, accent_color, x_offset)

    def _draw_individual_metrics(self, surface, tree, accent_color, x_offset):
        """Only Raíz, Profundidad, Hojas - each in its own cajita (made thinner)"""
        metrics = self._get_tree_metrics(tree)
        card_w = 142
        card_h = 48   # made thinner as requested
        y = WINDOW_H - 125   # moved much lower, near the bottom

        for i, (label, value) in enumerate(metrics):
            card_x = x_offset + 25 + i * (card_w + 18)
            card_rect = pygame.Rect(card_x, y, card_w, card_h)

            pygame.draw.rect(surface, BG_SURFACE2, card_rect, border_radius=9)
            pygame.draw.rect(surface, accent_color, card_rect, width=2, border_radius=9)

            lbl = self.fonts["body_xs"].render(label.upper(), True, TEXT_DIM)
            val = self.fonts["label_md"].render(str(value), True, accent_color)

            surface.blit(lbl, (card_rect.x + 12, card_rect.y + 7))
            surface.blit(val, (card_rect.x + 12, card_rect.y + 25))

    def _get_tree_metrics(self, tree):
        root = tree.getRoot()
        if not root:
            return [("RAÍZ", "—"), ("PROFUNDIDAD", "—"), ("HOJAS", "—")]

        root_value = root.getValue() if hasattr(root, 'getValue') else getattr(root, 'code', '—')

        return [
            ("RAÍZ", root_value),
            ("PROFUNDIDAD", tree.getHeight()),
            ("HOJAS", tree.countLeaves()),
        ]

    def _draw_empty_tree(self, surface, viewport, text):
        msg = self.fonts["body_sm"].render(text, True, TEXT_DIM)
        surface.blit(msg, msg.get_rect(center=viewport.center))

    def _draw_buttons(self, surface):
        self.btn_back.draw(surface)

    def set_insertion_list(self, flights):
        self.insertion_list = flights
        self.current_step = 0