"""
flight_detail_modal.py
----------------------
Modal reutilizable para ver y editar vuelos al hacer click en un nodo del árbol.
Primero muestra solo detalles. Botón "Editar" cambia a modo formulario completo.
Diseño idéntico al modal de QueueScreen (paleta Color Hunt).
"""

import copy
import pygame
from models.flight_node import FlightNode
from user_interface.color_scheme import WINDOW_W, NAV_H
from user_interface.panel_ui import UIButton


# ---------------------------------------------------------------------------
# Paleta — idéntica a screen_queue.py
# ---------------------------------------------------------------------------
C_GREEN      = ( 67, 118, 108)
C_GREEN_DARK = ( 45,  80,  73)
C_CREAM      = (248, 250, 229)
C_CREAM_DIM  = (228, 230, 208)
C_TAN        = (177, 148, 112)
C_BROWN      = (118,  69,  59)

TEXT_PRIMARY   = ( 45,  35,  30)
TEXT_SECONDARY = ( 90,  75,  65)
TEXT_DIM       = (160, 140, 120)

PRIMARY      = C_GREEN
LIGHT        = C_CREAM
BG_SURFACE   = C_CREAM
BG_SURFACE2  = C_CREAM_DIM
BG_DEEP      = (235, 237, 215)
BORDER       = C_TAN
SECTION_LINE = C_TAN

_PRIO_LABELS = {1: "Mínima", 2: "Normal", 3: "Moderada", 4: "Alta", 5: "Crítica"}
_PRIO_COLORS = {
    1: TEXT_DIM,
    2: TEXT_SECONDARY,
    3: C_TAN,
    4: (160,  90,  60),
    5: C_BROWN,
}


# ---------------------------------------------------------------------------
# Helpers de dibujo
# ---------------------------------------------------------------------------

def _draw_rounded_rect(surface, color, rect, radius, border=0, border_color=None):
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border and border_color:
        pygame.draw.rect(surface, border_color, rect, border, border_radius=radius)


def _clamp(val, lo, hi):
    return max(lo, min(hi, val))


# ---------------------------------------------------------------------------
# Componente: campo de texto  (copiado de screen_queue.py)
# ---------------------------------------------------------------------------

class _TextField:
    def __init__(self, rect: pygame.Rect, label: str, placeholder: str,
                 font_label, font_body, numeric=False):
        self.rect        = rect
        self.label       = label
        self.placeholder = placeholder
        self.font_label  = font_label
        self.font_body   = font_body
        self.numeric     = numeric
        self.value       = ""
        self.active      = False
        self._enabled    = True          # False en modo sólo-lectura

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        if not enabled:
            self.active = False

    def handle_event(self, event: pygame.event.Event):
        if not self._enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = True
                return True
            else:
                self.active = False
        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.value = self.value[:-1]
            elif event.key == pygame.K_TAB:
                self.active = False
            elif event.unicode.isprintable():
                if not self.numeric or event.unicode in "0123456789.":
                    self.value += event.unicode
        return False

    def draw(self, surface: pygame.Surface):
        if self._enabled:
            border_col = C_GREEN if self.active else C_TAN
            bg_col     = C_CREAM if self.active else BG_DEEP
        else:
            border_col = SECTION_LINE
            bg_col     = BG_SURFACE2

        _draw_rounded_rect(surface, bg_col, self.rect, 10, 2, border_col)

        lbl = self.font_label.render(self.label, True, TEXT_SECONDARY)
        surface.blit(lbl, (self.rect.x, self.rect.y - 22))

        display = self.value if self.value else self.placeholder
        color   = TEXT_PRIMARY if self.value else TEXT_DIM
        val = self.font_body.render(display, True, color)
        clip = pygame.Rect(self.rect.x + 14, self.rect.y, self.rect.w - 28, self.rect.h)
        surface.set_clip(clip)
        surface.blit(val, (self.rect.x + 14,
                           self.rect.y + (self.rect.h - val.get_height()) // 2))
        surface.set_clip(None)


# ---------------------------------------------------------------------------
# Componente: slider de prioridad  (copiado de screen_queue.py)
# ---------------------------------------------------------------------------

class _PrioritySlider:
    TRACK_H = 6
    THUMB_R = 9

    def __init__(self, rect: pygame.Rect, label: str, font_label, font_body):
        self.rect       = rect
        self.label      = label
        self.font_label = font_label
        self.font_body  = font_body
        self.value      = 2
        self._dragging  = False
        self._enabled   = True

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        if not enabled:
            self._dragging = False

    def _track_rect(self):
        ty = self.rect.y + self.rect.h // 2
        return pygame.Rect(self.rect.x, ty - self.TRACK_H // 2,
                           self.rect.w, self.TRACK_H)

    def _thumb_cx(self):
        t = (self.value - 1) / 4
        return self.rect.x + int(t * self.rect.w)

    def handle_event(self, event: pygame.event.Event):
        if not self._enabled:
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            thumb_cx = self._thumb_cx()
            thumb_cy = self._track_rect().centery
            if (abs(event.pos[0] - thumb_cx) <= self.THUMB_R + 4 and
                    abs(event.pos[1] - thumb_cy) <= self.THUMB_R + 4):
                self._dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self._dragging = False
        elif event.type == pygame.MOUSEMOTION and self._dragging:
            rel = _clamp(event.pos[0] - self.rect.x, 0, self.rect.w)
            raw = 1 + rel / self.rect.w * 4
            self.value = _clamp(round(raw), 1, 5)

    def draw(self, surface: pygame.Surface):
        lbl = self.font_label.render(self.label, True, TEXT_SECONDARY)
        surface.blit(lbl, (self.rect.x, self.rect.y - 22))

        track = self._track_rect()
        track_col = BORDER if not self._enabled else BORDER
        _draw_rounded_rect(surface, track_col, track, self.TRACK_H // 2)

        fill_col = C_TAN if not self._enabled else PRIMARY
        fill = pygame.Rect(track.x, track.y,
                           self._thumb_cx() - track.x, track.h)
        _draw_rounded_rect(surface, fill_col, fill, self.TRACK_H // 2)

        cx = self._thumb_cx()
        cy = track.centery
        pygame.draw.circle(surface, BG_DEEP, (cx, cy), self.THUMB_R + 2)
        thumb_col = C_TAN if not self._enabled else PRIMARY
        pygame.draw.circle(surface, thumb_col, (cx, cy), self.THUMB_R)

        prio_col = _PRIO_COLORS[self.value]
        badge_txt = self.font_body.render(
            f"{self.value}  {_PRIO_LABELS[self.value]}", True, prio_col)
        surface.blit(badge_txt,
                     (self.rect.right - badge_txt.get_width(),
                      self.rect.y - 24))


# ---------------------------------------------------------------------------
# Modal principal
# ---------------------------------------------------------------------------

class FlightDetailModal:
    MODAL_W   = 780
    MODAL_PAD = 48
    FIELD_H   = 42

    def __init__(self, fonts: dict, node: FlightNode,
                 on_close, on_save=None, on_delete=None,
                 on_cancel_subtree=None, avl_tree=None):
        self.fonts              = fonts
        self.node               = node
        self.on_close           = on_close
        self.on_save            = on_save
        self.on_delete          = on_delete
        self.on_cancel_subtree  = on_cancel_subtree
        self.avl_tree           = avl_tree

        self.visible    = False
        self._edit_mode = False

        self._f_title  = fonts.get("title_lg",  fonts.get("label_md"))
        self._f_body   = fonts.get("body_md",   fonts.get("label_md"))
        self._f_label  = fonts.get("body_sm",   fonts.get("label_md"))
        self._f_small  = fonts.get("body_sm",   fonts.get("label_md"))

        self._status    = ""
        self._status_ok = True

        self._build_layout()

    # -----------------------------------------------------------------------
    # Layout  (espejo exacto de QueueScreen._build_layout)
    # -----------------------------------------------------------------------

    def _build_layout(self):
        mw  = self.MODAL_W
        mx  = WINDOW_W // 2 - mw // 2
        my  = NAV_H + 40
        pad = self.MODAL_PAD

        self._modal_x = mx
        self._modal_y = my

        inner_w = mw - pad * 2
        col2    = inner_w // 2 - 8
        lx      = mx + pad
        rx      = lx + col2 + 16

        # ── Fila 1: código · hora · slider prioridad ──────────────────────
        y = my + 110

        self._field_codigo = _TextField(
            rect=pygame.Rect(lx, y, col2, self.FIELD_H),
            label="Código de vuelo",
            placeholder="Ej. AA-101",
            font_label=self._f_label,
            font_body=self._f_body,
        )

        self._field_hora = _TextField(
            rect=pygame.Rect(rx, y, col2 // 2 - 8, self.FIELD_H),
            label="Hora de salida (HH:MM)",
            placeholder="00:00",
            font_label=self._f_label,
            font_body=self._f_body,
        )

        slider_x = rx + col2 // 2 + 8
        slider_w = col2 - col2 // 2 - 8
        self._slider_prio = _PrioritySlider(
            rect=pygame.Rect(slider_x, y + 4, slider_w, self.FIELD_H - 8),
            label="Prioridad",
            font_label=self._f_label,
            font_body=self._f_small,
        )

        y += self.FIELD_H + 44

        # ── Fila 2: origen · destino ──────────────────────────────────────
        arrow_gap = 28
        route_w   = (inner_w - arrow_gap) // 2

        self._field_origen = _TextField(
            rect=pygame.Rect(lx, y, route_w, self.FIELD_H),
            label="Ciudad de origen",
            placeholder="Bogotá",
            font_label=self._f_label,
            font_body=self._f_body,
        )
        self._arrow_pos = (lx + route_w + arrow_gap // 2, y + self.FIELD_H // 2)

        self._field_destino = _TextField(
            rect=pygame.Rect(lx + route_w + arrow_gap, y, route_w, self.FIELD_H),
            label="Ciudad de destino",
            placeholder="Medellín",
            font_label=self._f_label,
            font_body=self._f_body,
        )

        y += self.FIELD_H + 44

        # ── Fila 3: precio · pasajeros ────────────────────────────────────
        self._field_precio = _TextField(
            rect=pygame.Rect(lx, y, col2, self.FIELD_H),
            label="Precio base (USD)",
            placeholder="0.00",
            font_label=self._f_label,
            font_body=self._f_body,
            numeric=True,
        )

        self._field_pax = _TextField(
            rect=pygame.Rect(rx, y, col2, self.FIELD_H),
            label="Número de pasajeros",
            placeholder="0",
            font_label=self._f_label,
            font_body=self._f_body,
            numeric=True,
        )

        y += self.FIELD_H + 52

        # ── Botones ───────────────────────────────────────────────────────
        # Modo vista: 4 botones  |  Modo edición: 3 botones (save · cancel · delete)
        btn_w4 = (inner_w - 30) // 4    # cuatro botones con gap de 10
        btn_w3 = (inner_w - 20) // 3    # tres botones con gap de 10

        # ── Botones modo VISTA ────────────────────────────────────────────
        self.btn_edit = UIButton(
            rect=pygame.Rect(lx, y, btn_w4, 52),
            text="✏  EDITAR",
            font=self._f_label,
            bg_color=C_GREEN,
            text_color=C_CREAM,
            border_color=C_GREEN,
            callback=self._enter_edit_mode,
        )

        self.btn_cancel_subtree = UIButton(
            rect=pygame.Rect(lx + btn_w4 + 10, y, btn_w4, 52),
            text="⛔  CANCELAR SUBRAMA",
            font=self._f_label,
            bg_color=C_CREAM_DIM,
            text_color=C_BROWN,
            border_color=C_TAN,
            callback=self._cancel_subtree,
        )

        self.btn_delete = UIButton(
            rect=pygame.Rect(lx + 2 * (btn_w4 + 10), y, btn_w4, 52),
            text="🗑  ELIMINAR",
            font=self._f_label,
            bg_color=C_BROWN,
            text_color=C_CREAM,
            border_color=C_BROWN,
            callback=self._delete_node,
        )

        # (cuarto slot vacío intencionalmente para equilibrio visual)

        # ── Botones modo EDICIÓN ──────────────────────────────────────────
        self.btn_save = UIButton(
            rect=pygame.Rect(lx, y, btn_w3, 52),
            text="💾  GUARDAR CAMBIOS",
            font=self._f_label,
            bg_color=C_GREEN,
            text_color=C_CREAM,
            border_color=C_GREEN,
            callback=self._save_changes,
        )

        self.btn_cancel = UIButton(
            rect=pygame.Rect(lx + btn_w3 + 10, y, btn_w3, 52),
            text="CANCELAR",
            font=self._f_label,
            bg_color=C_CREAM_DIM,
            text_color=C_GREEN_DARK,
            border_color=C_TAN,
            callback=self._exit_edit_mode,
        )

        self.btn_delete_edit = UIButton(
            rect=pygame.Rect(lx + 2 * (btn_w3 + 10), y, btn_w3, 52),
            text="🗑  ELIMINAR",
            font=self._f_label,
            bg_color=C_BROWN,
            text_color=C_CREAM,
            border_color=C_BROWN,
            callback=self._delete_node,
        )

        self._btn_y     = y
        self._status_y  = y + 60
        self._content_h = y + 60 + 28 - my

        # Botón cerrar
        self.btn_close = UIButton(
            rect=pygame.Rect(mx + mw - 58, my + 22, 36, 36),
            text="✕",
            font=self._f_label,
            bg_color=C_BROWN,
            text_color=C_CREAM,
            border_color=C_BROWN,
            callback=self.on_close,
        )

        self._all_fields = [
            self._field_codigo, self._field_hora,
            self._field_origen, self._field_destino,
            self._field_precio, self._field_pax,
        ]

    # -----------------------------------------------------------------------
    # Tamaño del modal
    # -----------------------------------------------------------------------

    def _modal_rect(self) -> pygame.Rect:
        h = self._content_h + 20
        return pygame.Rect(self._modal_x, self._modal_y, self.MODAL_W, h)

    # -----------------------------------------------------------------------
    # API pública
    # -----------------------------------------------------------------------

    def show(self):
        self.visible    = True
        self._edit_mode = False
        self._load_node_to_fields()
        self._set_fields_enabled(False)
        self._status = ""

    def hide(self):
        self.visible = False

    def set_status(self, message: str, success: bool = True):
        self._status    = message
        self._status_ok = success

    # -----------------------------------------------------------------------
    # Helpers internos
    # -----------------------------------------------------------------------

    def _load_node_to_fields(self):
        self._field_codigo.value  = str(self.node.code)
        self._field_hora.value    = self.node.departure_time
        self._field_origen.value  = self.node.origin
        self._field_destino.value = self.node.destination
        self._field_precio.value  = str(self.node.base_price)
        self._field_pax.value     = str(self.node.passengers)
        self._slider_prio.value   = getattr(self.node, 'priority', 2)

    def _set_fields_enabled(self, enabled: bool):
        for f in self._all_fields:
            f.set_enabled(enabled)
        self._slider_prio.set_enabled(enabled)

    def _enter_edit_mode(self):
        self._edit_mode = True
        self._set_fields_enabled(True)
        self._status = ""

    def _exit_edit_mode(self):
        self._edit_mode = False
        self._set_fields_enabled(False)
        self._load_node_to_fields()
        self._status = ""

    def _save_changes(self):
        """
        Crea una copia del nodo con los valores del formulario y la pasa
        a on_save. El nodo original (self.node) NUNCA se muta, lo que
        garantiza que el árbol quede íntegro si el guardado falla.
        """
        if not self.on_save:
            self.hide()
            return
        try:
            # Copia superficial: preserva atributos extra (promotion, alert, etc.)
            updated = copy.copy(self.node)
            updated.code           = self._field_codigo.value.strip() or self.node.code
            updated.origin         = self._field_origen.value.strip() or self.node.origin
            updated.destination    = self._field_destino.value.strip() or self.node.destination
            updated.departure_time = self._field_hora.value.strip() or self.node.departure_time
            updated.base_price     = float(self._field_precio.value or self.node.base_price)
            updated.passengers     = int(self._field_pax.value or self.node.passengers)
            updated.priority       = self._slider_prio.value
            # Limpiar referencias del árbol para que pueda insertarse limpio
            updated.leftChild  = None
            updated.rightChild = None
            updated.parent     = None
            self.on_save(updated)
            self.hide()
        except Exception as e:
            self.set_status(f"✗ {e}", False)

    def _cancel_subtree(self):
        if self.on_cancel_subtree:
            self.on_cancel_subtree(self.node)
        elif self.avl_tree is not None:
            count = self.avl_tree.delete_subtree(self.node.getValue())
            print(f"Subrama cancelada: {count} nodo(s) eliminado(s) desde {self.node.code}")
        self.hide()

    def _delete_node(self):
        if self.on_delete:
            self.on_delete(self.node)
        self.hide()

    # -----------------------------------------------------------------------
    # Eventos
    # -----------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event):
        if not self.visible:
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self._edit_mode:
                self._exit_edit_mode()
            else:
                self.on_close()
            return

        if self._edit_mode:
            for f in self._all_fields:
                f.handle_event(event)
            self._slider_prio.handle_event(event)
            self.btn_save.handle_event(event)
            self.btn_cancel.handle_event(event)
            self.btn_delete_edit.handle_event(event)
        else:
            self.btn_edit.handle_event(event)
            self.btn_cancel_subtree.handle_event(event)
            self.btn_delete.handle_event(event)

        self.btn_close.handle_event(event)

    # -----------------------------------------------------------------------
    # Draw  (espejo exacto del estilo de QueueScreen.draw)
    # -----------------------------------------------------------------------

    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return

        modal = self._modal_rect()
        pad   = self.MODAL_PAD
        lx    = modal.x + pad
        rend  = modal.x + modal.w - pad

        # ── Sombra ────────────────────────────────────────────────────────
        shadow_rect = modal.inflate(12, 12)
        shadow_surf = pygame.Surface((shadow_rect.w, shadow_rect.h), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (67, 50, 40, 80),
                         pygame.Rect(0, 0, shadow_rect.w, shadow_rect.h),
                         border_radius=22)
        surface.blit(shadow_surf, shadow_rect.topleft)

        # ── Fondo del modal ───────────────────────────────────────────────
        _draw_rounded_rect(surface, C_CREAM, modal, 18, 2, C_GREEN)

        # ── Encabezado ────────────────────────────────────────────────────
        header_rect = pygame.Rect(modal.x, modal.y, modal.w, 80)
        pygame.draw.rect(surface, C_GREEN_DARK, header_rect,
                         border_top_left_radius=18, border_top_right_radius=18)
        pygame.draw.line(surface, C_TAN,
                         (modal.x, modal.y + 80),
                         (modal.x + modal.w, modal.y + 80), 1)

        mode_eyebrow = "EDICIÓN DE VUELO" if self._edit_mode else "DETALLES DEL VUELO"
        eyebrow = self._f_small.render(mode_eyebrow, True, C_TAN)
        title   = self._f_title.render(self.node.code, True, C_CREAM)
        surface.blit(eyebrow, (modal.x + pad, modal.y + 80 // 2 - eyebrow.get_height() - 2))
        surface.blit(title,   (modal.x + pad, modal.y + 80 // 2 + 2))

        # ── Separadores de sección ────────────────────────────────────────
        def _section_header(label, y):
            s = self._f_small.render(label, True, TEXT_DIM)
            surface.blit(s, (lx, y))
            line_x = lx + s.get_width() + 12
            pygame.draw.line(surface, SECTION_LINE,
                             (line_x, y + s.get_height() // 2),
                             (rend, y + s.get_height() // 2), 1)

        _section_header("IDENTIFICACIÓN",
                        self._field_codigo.rect.y - 44)
        _section_header("RUTA",
                        self._field_origen.rect.y - 44)
        _section_header("DETALLES",
                        self._field_precio.rect.y - 44)

        # ── Campos de texto ───────────────────────────────────────────────
        for f in self._all_fields:
            f.draw(surface)

        # Flecha entre origen y destino
        ax, ay = self._arrow_pos
        arrow  = self._f_body.render("→", True, TEXT_DIM)
        surface.blit(arrow, (ax - arrow.get_width() // 2,
                             ay - arrow.get_height() // 2))

        # ── Slider ────────────────────────────────────────────────────────
        self._slider_prio.draw(surface)

        # ── Botones según modo ────────────────────────────────────────────
        if self._edit_mode:
            self.btn_save.draw(surface)
            self.btn_cancel.draw(surface)
            self.btn_delete_edit.draw(surface)
        else:
            self.btn_edit.draw(surface)
            self.btn_cancel_subtree.draw(surface)
            self.btn_delete.draw(surface)

        self.btn_close.draw(surface)

        # ── Feedback ──────────────────────────────────────────────────────
        if self._status:
            col = C_GREEN if self._status_ok else C_BROWN
            st  = self._f_small.render(self._status, True, col)
            surface.blit(st, (lx, self._status_y))