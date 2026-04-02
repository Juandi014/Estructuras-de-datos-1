"""
screen_main.py
--------------
S1 — Main AVL tree view for SkyBalance.

Layout:
  ┌─────────────────────────┬──────────────┐
  │                         │              │
  │      AVL TREE VIEW      │  SIDE PANEL  │
  │   (zoom + scroll)       │  (controls)  │
  │                         │              │
  └─────────────────────────┴──────────────┘

Side panel operations:
  - Insert flight
  - Delete flight by code
  - Search flight by code → highlights node + shows modal

A search result modal overlays the tree with full flight details.
"""

import pygame
from user_interface.color_scheme import (
    BG_DEEP, BG_SURFACE, BG_SURFACE2,
    BORDER, BORDER_ACTIVE,
    AMBER, AMBER_DIM, GREEN_TERM, CRITICAL,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DIM,
    WINDOW_W, WINDOW_H, NAV_H,
    PANEL_PADDING, BTN_H,
)
from user_interface.tree_renderer import TreeRenderer
from models.flight_node import FlightNode


# ------------------------------------------------------------------
# Layout constants
# ------------------------------------------------------------------

PANEL_W      = 280
TREE_RECT    = pygame.Rect(0, NAV_H, WINDOW_W - PANEL_W, WINDOW_H - NAV_H)
PANEL_RECT   = pygame.Rect(WINDOW_W - PANEL_W, NAV_H, PANEL_W, WINDOW_H - NAV_H)


class MainScreen:
    """
    Handles rendering and input for the S1 main tree view.

    Args:
        fonts    : Font registry from color_scheme.load_fonts().
        avl_tree : Shared AVLTree instance.
        on_undo  : Callable triggered by Ctrl+Z. Signature: on_undo()
    """

    def __init__(self, fonts: dict, avl_tree, on_undo):
        self.fonts    = fonts
        self.avl_tree = avl_tree
        self.on_undo  = on_undo

        self.renderer = TreeRenderer(TREE_RECT)

        # Panel input state
        self._active_field  = None   # "insert" | "delete" | "search"
        self._insert_fields = {
            "codigo":   "", "origen":  "", "destino":  "",
            "hora":     "", "precio":  "", "pasajeros": "",
        }
        self._delete_code   = ""
        self._search_code   = ""

        # Status messages
        self._status        = ""
        self._status_ok     = True

        # Search result modal
        self._modal_node    = None   # FlightNode to display in modal

        # Button rects — computed during draw
        self._btn_insert    = None
        self._btn_delete    = None
        self._btn_search    = None
        self._btn_center    = None
        self._modal_close   = None
        self._field_rects   = {}

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Dispatches events to modal, panel, or tree renderer."""
        if self._modal_node is not None:
            self._handle_modal_event(event)
            return
        self.renderer.handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos)
        if event.type == pygame.KEYDOWN:
            self._handle_key(event)

    def update(self, dt_ms: float) -> None:
        """No per-frame animation on this screen (renderer handles its own)."""
        pass

    def draw(self, surface: pygame.Surface) -> None:
        """Renders tree view, side panel, and optional modal."""
        surface.fill(BG_DEEP)
        self.renderer.draw(surface, self.avl_tree.getRoot())
        self._draw_panel(surface)
        if self._modal_node is not None:
            self._draw_modal(surface)

    def set_status(self, message: str, success: bool = True) -> None:
        """Allows external callers to push a status message."""
        self._status    = message
        self._status_ok = success

    # ------------------------------------------------------------------
    # Panel drawing
    # ------------------------------------------------------------------

    def _draw_panel(self, surface: pygame.Surface) -> None:
        """Renders the full right-side control panel."""
        pygame.draw.rect(surface, BG_SURFACE, PANEL_RECT)
        pygame.draw.line(surface, BORDER,
                         (PANEL_RECT.x, PANEL_RECT.y),
                         (PANEL_RECT.x, PANEL_RECT.bottom), 1)

        y = PANEL_RECT.y + PANEL_PADDING
        y = self._draw_metrics(surface, y)
        y = self._draw_section_divider(surface, y, "// INSERTAR VUELO")
        y = self._draw_insert_section(surface, y)
        y = self._draw_section_divider(surface, y, "// ELIMINAR")
        y = self._draw_delete_section(surface, y)
        y = self._draw_section_divider(surface, y, "// BUSCAR")
        y = self._draw_search_section(surface, y)
        self._draw_status_bar(surface)

    def _draw_metrics(self, surface, y: int) -> int:
        """Renders live tree metrics at the top of the panel."""
        label = self.fonts["label_sm"].render("// MÉTRICAS DEL ÁRBOL", True, TEXT_DIM)
        surface.blit(label, (PANEL_RECT.x + PANEL_PADDING, y))
        y += 20

        root = self.avl_tree.getRoot()
        height  = self.avl_tree.getHeight() if root else 0
        nodes   = self.avl_tree.nodeCount() if root else 0
        leaves  = self.avl_tree.countLeaves() if root else 0
        rotations = self.avl_tree.totalRotations() if root else 0

        metrics = [
            ("Altura",     str(height)),
            ("Nodos",      str(nodes)),
            ("Hojas",      str(leaves)),
            ("Rotaciones", str(rotations)),
        ]
        for label_text, value in metrics:
            lbl = self.fonts["body_sm"].render(label_text, True, TEXT_SECONDARY)
            val = self.fonts["label_md"].render(value, True, AMBER)
            surface.blit(lbl, (PANEL_RECT.x + PANEL_PADDING, y))
            surface.blit(val, (PANEL_RECT.right - PANEL_PADDING - val.get_width(), y))
            y += 18
        return y + 6

    def _draw_section_divider(self, surface, y: int, title: str) -> int:
        """Draws a labeled horizontal section divider."""
        pygame.draw.line(surface, BORDER,
                         (PANEL_RECT.x + PANEL_PADDING, y),
                         (PANEL_RECT.right - PANEL_PADDING, y), 1)
        y += 6
        lbl = self.fonts["label_sm"].render(title, True, TEXT_DIM)
        surface.blit(lbl, (PANEL_RECT.x + PANEL_PADDING, y))
        return y + 18

    def _draw_insert_section(self, surface, y: int) -> int:
        """Renders the insert flight form."""
        fields = [
            ("codigo",    "Código"),
            ("origen",    "Origen"),
            ("destino",   "Destino"),
            ("hora",      "Hora (HH:MM)"),
            ("precio",    "Precio base"),
            ("pasajeros", "Pasajeros"),
        ]
        for key, placeholder in fields:
            rect = pygame.Rect(PANEL_RECT.x + PANEL_PADDING, y,
                               PANEL_W - PANEL_PADDING * 2, 24)
            self._field_rects[key] = rect
            active = self._active_field == key
            self._draw_input(surface, rect, self._insert_fields[key],
                             placeholder, active)
            y += 28

        # Insert button
        btn = pygame.Rect(PANEL_RECT.x + PANEL_PADDING, y,
                          PANEL_W - PANEL_PADDING * 2, BTN_H)
        self._btn_insert = btn
        _draw_button(surface, btn, "+ INSERTAR", self.fonts["label_md"],
                     BG_DEEP, AMBER, AMBER)
        return y + BTN_H + 8

    def _draw_delete_section(self, surface, y: int) -> int:
        """Renders the delete by code input and button."""
        rect = pygame.Rect(PANEL_RECT.x + PANEL_PADDING, y,
                           PANEL_W - PANEL_PADDING * 2, 24)
        self._field_rects["delete"] = rect
        self._draw_input(surface, rect, self._delete_code,
                         "Código a eliminar", self._active_field == "delete")
        y += 28

        btn = pygame.Rect(PANEL_RECT.x + PANEL_PADDING, y,
                          PANEL_W - PANEL_PADDING * 2, BTN_H)
        self._btn_delete = btn
        _draw_button(surface, btn, "✕ ELIMINAR", self.fonts["label_md"],
                     BG_DEEP, CRITICAL, CRITICAL)
        return y + BTN_H + 8

    def _draw_search_section(self, surface, y: int) -> int:
        """Renders the search input and button."""
        rect = pygame.Rect(PANEL_RECT.x + PANEL_PADDING, y,
                           PANEL_W - PANEL_PADDING * 2, 24)
        self._field_rects["search"] = rect
        self._draw_input(surface, rect, self._search_code,
                         "Código a buscar", self._active_field == "search")
        y += 28

        btn = pygame.Rect(PANEL_RECT.x + PANEL_PADDING, y,
                          PANEL_W - PANEL_PADDING * 2, BTN_H)
        self._btn_search = btn
        _draw_button(surface, btn, "⌕ BUSCAR", self.fonts["label_md"],
                     BG_DEEP, GREEN_TERM, GREEN_TERM)

        # Center view button
        y += BTN_H + 6
        btn_c = pygame.Rect(PANEL_RECT.x + PANEL_PADDING, y,
                            PANEL_W - PANEL_PADDING * 2, BTN_H)
        self._btn_center = btn_c
        _draw_button(surface, btn_c, "⊙ CENTRAR VISTA", self.fonts["label_md"],
                     BG_SURFACE, TEXT_SECONDARY, BORDER)
        return y + BTN_H + 8

    def _draw_input(self, surface, rect, value, placeholder, active):
        """Renders a single text input field."""
        bg = BG_SURFACE2 if active else BG_DEEP
        border = BORDER_ACTIVE if active else BORDER
        pygame.draw.rect(surface, bg, rect)
        pygame.draw.rect(surface, border, rect, 1)

        if value:
            text_surf = self.fonts["body_sm"].render(value, True, TEXT_PRIMARY)
        else:
            text_surf = self.fonts["body_sm"].render(placeholder, True, TEXT_DIM)

        cursor = "_" if active else ""
        if active and value is not None:
            text_surf = self.fonts["body_sm"].render(value + cursor, True, AMBER)

        surface.blit(text_surf, (rect.x + 6, rect.y + rect.height // 2 - text_surf.get_height() // 2))

    def _draw_status_bar(self, surface) -> None:
        """Renders the status message at the bottom of the panel."""
        if not self._status:
            return
        color = GREEN_TERM if self._status_ok else CRITICAL
        surf  = self.fonts["body_xs"].render(self._status, True, color)
        surface.blit(surf, (PANEL_RECT.x + PANEL_PADDING,
                            WINDOW_H - PANEL_PADDING - surf.get_height()))

    # ------------------------------------------------------------------
    # Modal drawing
    # ------------------------------------------------------------------

    def _draw_modal(self, surface: pygame.Surface) -> None:
        """Renders the flight detail modal over the tree."""
        node = self._modal_node

        # Dim background
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # Modal card
        mw, mh = 420, 340
        mx = WINDOW_W // 2 - mw // 2
        my = WINDOW_H // 2 - mh // 2
        modal_rect = pygame.Rect(mx, my, mw, mh)
        pygame.draw.rect(surface, BG_SURFACE, modal_rect)
        _draw_clipped_border(surface, modal_rect, AMBER, clip=12, width=1)

        # Header
        header = self.fonts["label_md"].render(
            f"// VUELO {node.code}", True, AMBER)
        surface.blit(header, (mx + 20, my + 16))

        # Close button
        close_rect = pygame.Rect(mx + mw - 40, my + 10, 28, 28)
        self._modal_close = close_rect
        _draw_button(surface, close_rect, "✕", self.fonts["label_md"],
                     CRITICAL, BG_SURFACE2, CRITICAL)

        # Divider
        pygame.draw.line(surface, BORDER,
                         (mx + 16, my + 44), (mx + mw - 16, my + 44), 1)

        # Flight data rows
        rows = [
            ("Origen",      node.origin),
            ("Destino",     node.destination),
            ("Hora salida", node.departure_time),
            ("Precio base", f"$ {node.base_price:,.0f}"),
            ("Precio final",f"$ {node.final_price:,.0f}"),
            ("Pasajeros",   str(node.passengers)),
            ("Promoción",   "SÍ" if node.promotion else "NO"),
            ("Alerta",      "SÍ" if node.alert else "NO"),
            ("Profundidad", str(node.depth)),
            ("Factor eq.",  str(node.balance_factor)),
            ("Crítico",     "SÍ" if node.is_critical else "NO"),
        ]

        y = my + 54
        for i, (label, value) in enumerate(rows):
            row_bg = BG_SURFACE2 if i % 2 == 0 else BG_SURFACE
            row_rect = pygame.Rect(mx + 16, y, mw - 32, 20)
            pygame.draw.rect(surface, row_bg, row_rect)

            lbl_surf = self.fonts["body_sm"].render(label, True, TEXT_SECONDARY)
            val_col  = CRITICAL if label == "Crítico" and node.is_critical else TEXT_PRIMARY
            val_surf = self.fonts["body_sm"].render(value, True, val_col)
            surface.blit(lbl_surf, (mx + 22, y + 3))
            surface.blit(val_surf, (mx + mw - 22 - val_surf.get_width(), y + 3))
            y += 22

    # ------------------------------------------------------------------
    # Input handlers
    # ------------------------------------------------------------------

    def _handle_click(self, pos: tuple) -> None:
        """Routes click events to the correct control."""
        # Field activation
        for key, rect in self._field_rects.items():
            if rect.collidepoint(pos):
                self._active_field = key
                return

        self._active_field = None

        # Buttons
        if self._btn_insert and self._btn_insert.collidepoint(pos):
            self._do_insert()
        elif self._btn_delete and self._btn_delete.collidepoint(pos):
            self._do_delete()
        elif self._btn_search and self._btn_search.collidepoint(pos):
            self._do_search()
        elif self._btn_center and self._btn_center.collidepoint(pos):
            self.renderer.center_on_root(self.avl_tree.getRoot())

    def _handle_modal_event(self, event: pygame.event.Event) -> None:
        """Handles input when the modal is open."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._close_modal()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._modal_close and self._modal_close.collidepoint(event.pos):
                self._close_modal()

    def _handle_key(self, event: pygame.event.Event) -> None:
        """Routes keyboard input to the active field or global shortcuts."""
        if event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.on_undo()
            return

        if self._active_field is None:
            return

        if event.key == pygame.K_TAB:
            self._advance_focus()
            return
        if event.key == pygame.K_RETURN:
            self._active_field = None
            return

        self._type_into_active(event)

    def _type_into_active(self, event: pygame.event.Event) -> None:
        """Appends or deletes a character in the currently active field."""
        field = self._active_field

        if field in self._insert_fields:
            if event.key == pygame.K_BACKSPACE:
                self._insert_fields[field] = self._insert_fields[field][:-1]
            elif event.unicode and event.unicode.isprintable():
                self._insert_fields[field] += event.unicode

        elif field == "delete":
            if event.key == pygame.K_BACKSPACE:
                self._delete_code = self._delete_code[:-1]
            elif event.unicode and event.unicode.isprintable():
                self._delete_code += event.unicode

        elif field == "search":
            if event.key == pygame.K_BACKSPACE:
                self._search_code = self._search_code[:-1]
            elif event.unicode and event.unicode.isprintable():
                self._search_code += event.unicode

    def _advance_focus(self) -> None:
        """Moves focus to the next insert field on Tab press."""
        order = ["codigo", "origen", "destino", "hora", "precio", "pasajeros"]
        if self._active_field in order:
            idx = order.index(self._active_field)
            self._active_field = order[(idx + 1) % len(order)]

    # ------------------------------------------------------------------
    # Operations
    # ------------------------------------------------------------------

    def _do_insert(self) -> None:
        """Validates and inserts a new flight into the AVL tree."""
        f = self._insert_fields
        try:
            node = FlightNode(
                code           = _parse_code(f["codigo"]),
                origin         = _require(f["origen"],    "Origen requerido"),
                destination    = _require(f["destino"],   "Destino requerido"),
                departure_time = _require(f["hora"],      "Hora requerida"),
                base_price     = float(_require(f["precio"],    "Precio requerido")),
                passengers     = int(_require(f["pasajeros"], "Pasajeros requeridos")),
            )
            self.avl_tree.insert(node)
            self._clear_insert_fields()
            self.set_status(f"Vuelo {node.code} insertado.", success=True)
        except (ValueError, KeyError) as e:
            self.set_status(str(e), success=False)

    def _do_delete(self) -> None:
        """Deletes a flight by code from the AVL tree."""
        code = self._delete_code.strip()
        if not code:
            self.set_status("Ingresa un código para eliminar.", success=False)
            return
        try:
            self.avl_tree.delete(_parse_code(code))
            self._delete_code = ""
            self.renderer.clear_highlight()
            self.set_status(f"Vuelo {code} eliminado.", success=True)
        except Exception as e:
            self.set_status(str(e), success=False)

    def _do_search(self) -> None:
        """Searches for a flight and shows its detail modal if found."""
        code = self._search_code.strip()
        if not code:
            self.set_status("Ingresa un código para buscar.", success=False)
            return
        node = self.avl_tree.search(_parse_code(code))
        if node is None:
            self.set_status(f"Vuelo {code} no encontrado.", success=False)
            self.renderer.clear_highlight()
        else:
            self.renderer.set_highlighted(node.code)
            self._modal_node = node
            self.set_status(f"Vuelo {code} encontrado.", success=True)

    def _close_modal(self) -> None:
        """Closes the search result modal."""
        self._modal_node = None

    def _clear_insert_fields(self) -> None:
        """Resets all insert form fields to empty."""
        for key in self._insert_fields:
            self._insert_fields[key] = ""


# ------------------------------------------------------------------
# Shared drawing utilities
# ------------------------------------------------------------------

def _draw_clipped_border(surface, rect, color, clip=10, width=1):
    """Draws a rectangle with diagonally clipped corners."""
    x, y, w, h = rect.x, rect.y, rect.width, rect.height
    points = [
        (x + clip, y), (x + w - clip, y),
        (x + w, y + clip), (x + w, y + h - clip),
        (x + w - clip, y + h), (x + clip, y + h),
        (x, y + h - clip), (x, y + clip),
    ]
    pygame.draw.polygon(surface, color, points, width)


def _draw_button(surface, rect, text, font, bg, text_color, border_color):
    """Draws a flat button with clipped corners and centered label."""
    pygame.draw.rect(surface, bg, rect)
    _draw_clipped_border(surface, rect, border_color, clip=5, width=1)
    label = font.render(text, True, text_color)
    surface.blit(label, label.get_rect(center=rect.center))


# ------------------------------------------------------------------
# Input validation helpers
# ------------------------------------------------------------------

def _require(value: str, error_msg: str) -> str:
    """Raises ValueError if value is empty."""
    if not value.strip():
        raise ValueError(error_msg)
    return value.strip()


def _parse_code(value: str):
    """
    Tries to parse a flight code as int, falls back to str.
    Raises ValueError if empty.
    """
    value = value.strip()
    if not value:
        raise ValueError("Código requerido")
    try:
        return int(value)
    except ValueError:
        return value