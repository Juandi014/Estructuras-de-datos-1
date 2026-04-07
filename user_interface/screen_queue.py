"""
screen_queue.py
---------------
S3 — Cola de Inserciones Concurrencia (Requirement 3)

Permite agregar vuelos a una cola FIFO y procesarlos uno a uno o todos.
Muestra:
  - Árbol AVL actual (izquierda)
  - Formulario para agregar vuelo a la cola
  - Lista de vuelos pendientes
  - Log de procesamientos (éxitos y conflictos de profundidad crítica)
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
from models.flight_node import FlightNode


class QueueScreen:
    def __init__(self, fonts: dict, avl_tree, insertion_queue, on_switch_to_main):
        self.fonts = fonts
        self.avl_tree = avl_tree
        self.queue = insertion_queue          # InsertionQueue instance
        self.on_switch_to_main = on_switch_to_main

        self.renderer = TreeRenderer(pygame.Rect(0, NAV_H, WINDOW_W - 280, WINDOW_H - NAV_H))

        # Formulario para agregar vuelo a la cola
        self._fields = {
            "codigo": "", "origen": "", "destino": "",
            "hora": "", "precio": "", "pasajeros": ""
        }
        self._active_field = None

        # UI components
        self._btn_add = None
        self._btn_process_one = None
        self._btn_process_all = None
        self._btn_clear_queue = None
        self._btn_clear_log = None
        self._btn_back = None

        self._status = ""
        self._status_ok = True

        self._confirm_modal = None

        self._init_ui()

    def _init_ui(self):
        panel_x = WINDOW_W - 280
        y = NAV_H + PANEL_PADDING + 20

        # --- Formulario de nuevo vuelo ---
        fields_info = [
            ("codigo",    "Código (ej: SB501)"),
            ("origen",    "Origen"),
            ("destino",   "Destino"),
            ("hora",      "Hora (HH:MM)"),
            ("precio",    "Precio base"),
            ("pasajeros", "Pasajeros"),
        ]
        self._field_rects = {}
        for key, placeholder in fields_info:
            rect = pygame.Rect(panel_x + PANEL_PADDING, y, 240, 32)
            self._field_rects[key] = rect
            y += 40

        # Botón Agregar a Cola
        self._btn_add = UIButton(
            rect=pygame.Rect(panel_x + PANEL_PADDING, y, 240, BTN_H),
            text="➕ AGREGAR A COLA",
            font=self.fonts["label_md"],
            bg_color=BG_SURFACE,
            text_color=AMBER,
            border_color=AMBER,
            callback=self._add_to_queue
        )
        y += BTN_H + 30

        # Procesar botones
        self._btn_process_one = UIButton(
            rect=pygame.Rect(panel_x + PANEL_PADDING, y, 240, BTN_H),
            text="▶ PROCESAR SIGUIENTE",
            font=self.fonts["label_md"],
            bg_color=BG_SURFACE,
            text_color=GREEN_TERM,
            border_color=GREEN_TERM,
            callback=self._process_next
        )
        y += BTN_H + 12

        self._btn_process_all = UIButton(
            rect=pygame.Rect(panel_x + PANEL_PADDING, y, 240, BTN_H),
            text="▶ PROCESAR TODA LA COLA",
            font=self.fonts["label_md"],
            bg_color=BG_SURFACE,
            text_color=GREEN_TERM,
            border_color=GREEN_TERM,
            callback=self._process_all
        )
        y += BTN_H + 30

        # Botones de limpieza
        self._btn_clear_queue = UIButton(
            rect=pygame.Rect(panel_x + PANEL_PADDING, y, 240, BTN_H),
            text="🗑️ LIMPIAR COLA",
            font=self.fonts["label_md"],
            bg_color=BG_SURFACE,
            text_color=TEXT_SECONDARY,
            border_color=BORDER,
            callback=self._clear_queue
        )
        y += BTN_H + 12

        self._btn_clear_log = UIButton(
            rect=pygame.Rect(panel_x + PANEL_PADDING, y, 240, BTN_H),
            text="🗑️ LIMPIAR LOG",
            font=self.fonts["label_md"],
            bg_color=BG_SURFACE,
            text_color=TEXT_SECONDARY,
            border_color=BORDER,
            callback=self._clear_log
        )
        y += BTN_H + 30

        # Botón volver
        self._btn_back = UIButton(
            rect=pygame.Rect(panel_x + PANEL_PADDING, y, 240, BTN_H),
            text="← VOLVER A VISTA PRINCIPAL",
            font=self.fonts["label_md"],
            bg_color=BG_DEEP,
            text_color=TEXT_SECONDARY,
            border_color=BORDER,
            callback=self.on_switch_to_main
        )

    # ------------------------------------------------------------------
    # Operaciones
    # ------------------------------------------------------------------

    def _add_to_queue(self):
        try:
            node = FlightNode(
                code=self._fields["codigo"].strip(),
                origin=self._fields["origen"].strip(),
                destination=self._fields["destino"].strip(),
                departure_time=self._fields["hora"].strip(),
                base_price=float(self._fields["precio"]),
                passengers=int(self._fields["pasajeros"]),
            )
            self.queue.enqueue(node)
            self.set_status(f"Vuelo {node.code} agregado a la cola", True)
            self._clear_fields()
        except Exception as e:
            self.set_status(f"Error al agregar: {e}", False)

    def _process_next(self):
        if self.queue.is_empty():
            self.set_status("La cola está vacía", False)
            return
        result = self.queue.process_next(self.avl_tree)
        if result:
            self.set_status(result["message"], result["success"])

    def _process_all(self):
        if self.queue.is_empty():
            self.set_status("La cola está vacía", False)
            return

        results = self.queue.process_all(self.avl_tree)
        self.set_status(f"Se procesaron {len(results)} vuelos", True)

    def _clear_queue(self):
        if self.queue.is_empty():
            self.set_status("La cola ya está vacía", False)
            return
        self.queue.clear()
        self.set_status("Cola limpiada completamente", True)

    def _clear_log(self):
        self.queue.clear_log()
        self.set_status("Log de procesamientos limpiado", True)

    def _clear_fields(self):
        for key in self._fields:
            self._fields[key] = ""

    # ------------------------------------------------------------------
    # Eventos y Dibujo
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event):
        if self._confirm_modal and getattr(self._confirm_modal, 'visible', False):
            self._confirm_modal.handle_event(event)
            return

        self.renderer.handle_event(event)

        # Inputs del formulario
        for key, rect in self._field_rects.items():
            if event.type == pygame.MOUSEBUTTONDOWN and rect.collidepoint(event.pos):
                self._active_field = key
            if self._active_field == key and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self._fields[key] = self._fields[key][:-1]
                elif event.unicode.isprintable():
                    self._fields[key] += event.unicode

        self._btn_add.handle_event(event)
        self._btn_process_one.handle_event(event)
        self._btn_process_all.handle_event(event)
        self._btn_clear_queue.handle_event(event)
        self._btn_clear_log.handle_event(event)
        self._btn_back.handle_event(event)

    def draw(self, surface: pygame.Surface):
        surface.fill(BG_DEEP)
        self.renderer.draw(surface, self.avl_tree.getRoot())

        self._draw_panel(surface)

    def _draw_panel(self, surface: pygame.Surface):
        panel_rect = pygame.Rect(WINDOW_W - 280, NAV_H, 280, WINDOW_H - NAV_H)
        pygame.draw.rect(surface, BG_SURFACE, panel_rect)
        pygame.draw.line(surface, BORDER, (panel_rect.x, panel_rect.y), (panel_rect.x, panel_rect.bottom), 1)

        y = panel_rect.y + PANEL_PADDING + 10

        # Título
        title = self.fonts["label_md"].render("// COLA DE INSERCIONES", True, AMBER)
        surface.blit(title, (panel_rect.x + PANEL_PADDING, y))
        y += 45

        # Formulario
        y = self._draw_form(surface, y, panel_rect)

        # Botones de procesamiento
        y += 10
        self._btn_process_one.draw(surface)
        y += BTN_H + 12
        self._btn_process_all.draw(surface)
        y += BTN_H + 20

        # Lista de pendientes
        y = draw_section_header(surface, y, "// PENDIENTES EN COLA", self.fonts, panel_rect)
        pending = self.queue.get_pending()
        if not pending:
            no_pending = self.fonts["body_sm"].render("Cola vacía", True, TEXT_DIM)
            surface.blit(no_pending, (panel_rect.x + PANEL_PADDING, y))
            y += 30
        else:
            for node in pending[:8]:  # máximo 8 para no desbordar
                txt = self.fonts["body_sm"].render(f"• {node.code} → {node.origin}-{node.destination}", True, TEXT_PRIMARY)
                surface.blit(txt, (panel_rect.x + PANEL_PADDING, y))
                y += 22

        # Log
        y = draw_section_header(surface, y, "// LOG DE PROCESAMIENTOS", self.fonts, panel_rect)
        log = self.queue.get_log()[-6:]  # últimos 6
        if not log:
            no_log = self.fonts["body_sm"].render("Sin procesamientos aún", True, TEXT_DIM)
            surface.blit(no_log, (panel_rect.x + PANEL_PADDING, y))
        else:
            for entry in reversed(log):
                color = GREEN_TERM if entry["success"] else CRITICAL
                txt = self.fonts["body_xs"].render(entry["message"][:48], True, color)
                surface.blit(txt, (panel_rect.x + PANEL_PADDING, y))
                y += 18

        # Botones de limpieza y volver
        y = WINDOW_H - PANEL_PADDING - BTN_H * 3 - 20
        self._btn_clear_queue.draw(surface)
        y += BTN_H + 12
        self._btn_clear_log.draw(surface)
        y += BTN_H + 12
        self._btn_back.draw(surface)

        # Status
        if self._status:
            color = GREEN_TERM if self._status_ok else CRITICAL
            status_surf = self.fonts["body_xs"].render(self._status[:58], True, color)
            surface.blit(status_surf, (panel_rect.x + PANEL_PADDING, WINDOW_H - PANEL_PADDING - 30))

    def _draw_form(self, surface, y: int, panel_rect):
        for key, rect in self._field_rects.items():
            active = self._active_field == key
            bg = BG_SURFACE2 if active else BG_DEEP
            border = BORDER if not active else (245, 166, 35)
            pygame.draw.rect(surface, bg, rect)
            pygame.draw.rect(surface, border, rect, 1)

            text = self._fields[key] or " "
            color = TEXT_PRIMARY if self._fields[key] else TEXT_DIM
            txt_surf = self.fonts["body_sm"].render(text, True, color)
            surface.blit(txt_surf, (rect.x + 8, rect.y + 8))
            y = rect.y + rect.height + 8

        self._btn_add.draw(surface)
        return y + BTN_H + 10

    def set_status(self, message: str, success: bool = True):
        self._status = message
        self._status_ok = success