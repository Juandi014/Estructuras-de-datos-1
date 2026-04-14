
import pygame
from models.flight_node import FlightNode
from user_interface.color_scheme import (
    WINDOW_W, WINDOW_H, NAV_H, BTN_H, CARD_RADIUS
)
from user_interface.panel_ui import UIButton
from user_interface.background_animation import background_anim


# ---------------------------------------------------------------------------
# Paleta personalizada — se sobreescribe sobre color_scheme
# ---------------------------------------------------------------------------
# Verdes / fondos
C_GREEN      = ( 67, 118, 108)   # #43766C  — acento principal
C_GREEN_DARK = ( 45,  80,  73)   # versión más oscura para hover / header
C_CREAM      = (248, 250, 229)   # #F8FAE5  — fondo del modal
C_CREAM_DIM  = (228, 230, 208)   # crema ligeramente más oscura para campos
C_TAN        = (177, 148, 112)   # #B19470  — arena / secondary
C_BROWN      = (118,  69,  59)   # #76453B  — marrón / danger / close

# Texto
TEXT_PRIMARY   = ( 45,  35,  30)   # casi negro cálido
TEXT_SECONDARY = ( 90,  75,  65)   # marrón medio
TEXT_DIM       = (160, 140, 120)   # arena claro

# Semánticos (dentro de la paleta)
SUCCESS    = C_GREEN
SUCCESS_BG = ( 45,  80,  73)
WARNING    = C_TAN
DANGER_BG  = ( 80,  40,  35)
CRITICAL   = C_BROWN

# Alias para compatibilidad con helpers internos
PRIMARY      = C_GREEN
LIGHT        = C_CREAM
BG_SURFACE   = C_CREAM
BG_SURFACE2  = C_CREAM_DIM
BG_DEEP      = (235, 237, 215)   # crema más profunda para campos inactivos
BORDER       = C_TAN
SECTION_LINE = C_TAN


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
# Componente: campo de texto
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

    # --- eventos ---
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Devuelve True si este campo capturó el foco."""
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

    # --- dibujo ---
    def draw(self, surface: pygame.Surface):
        border_col = C_GREEN   if self.active else C_TAN
        bg_col     = C_CREAM   if self.active else BG_DEEP

        _draw_rounded_rect(surface, bg_col, self.rect, 10, 2, border_col)

        # Etiqueta
        lbl = self.font_label.render(self.label, True, TEXT_SECONDARY)
        surface.blit(lbl, (self.rect.x, self.rect.y - 22))

        # Valor / placeholder
        display = self.value if self.value else self.placeholder
        color   = TEXT_PRIMARY if self.value else TEXT_DIM
        val = self.font_body.render(display, True, color)
        clip = pygame.Rect(self.rect.x + 14, self.rect.y, self.rect.w - 28, self.rect.h)
        surface.set_clip(clip)
        surface.blit(val, (self.rect.x + 14, self.rect.y + (self.rect.h - val.get_height()) // 2))
        surface.set_clip(None)


# ---------------------------------------------------------------------------
# Componente: toggle (checkbox estilo switch)
# ---------------------------------------------------------------------------

class _Toggle:
    W, H = 46, 24
    RADIUS = 12

    def __init__(self, cx: int, cy: int, label: str, sublabel: str,
                 font_body, font_small):
        self.label     = label
        self.sublabel  = sublabel
        self.font_body  = font_body
        self.font_small = font_small
        self.value     = False
        # Área clickeable = toda la fila (se calcula en draw)
        self._track_rect = pygame.Rect(cx, cy - self.H // 2, self.W, self.H)

    @property
    def rect(self):
        return self._track_rect

    def set_pos(self, cx, cy):
        self._track_rect.topleft = (cx, cy - self.H // 2)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self._track_rect.collidepoint(event.pos):
                self.value = not self.value

    def draw(self, surface: pygame.Surface, row_rect: pygame.Rect):
        # Fondo de la fila
        _draw_rounded_rect(surface, BG_SURFACE2, row_rect, 10, 1, SECTION_LINE)

        # Labels
        lbl  = self.font_body.render(self.label, True, TEXT_PRIMARY)
        sub  = self.font_small.render(self.sublabel, True, TEXT_DIM)
        lx   = row_rect.x + 16
        ly   = row_rect.centery - lbl.get_height() // 2 - 2
        surface.blit(lbl, (lx, ly))
        surface.blit(sub, (lx, ly + lbl.get_height() + 2))

        # Track
        tx = row_rect.right - self.W - 16
        ty = row_rect.centery - self.H // 2
        self._track_rect.topleft = (tx, ty)
        track_col = PRIMARY if self.value else BORDER
        _draw_rounded_rect(surface, track_col, self._track_rect, self.RADIUS)

        # Thumb
        thumb_x = tx + self.W - self.H + 2 if self.value else tx + 2
        thumb_rect = pygame.Rect(thumb_x, ty + 2, self.H - 4, self.H - 4)
        pygame.draw.ellipse(surface, LIGHT, thumb_rect)


# ---------------------------------------------------------------------------
# Componente: slider de prioridad
# ---------------------------------------------------------------------------

_PRIO_LABELS = {1: "Mínima", 2: "Normal", 3: "Moderada", 4: "Alta", 5: "Crítica"}
_PRIO_COLORS = {
    1: TEXT_DIM,
    2: TEXT_SECONDARY,
    3: C_TAN,
    4: (160,  90,  60),   # marrón medio cálido
    5: C_BROWN,
}


class _PrioritySlider:
    TRACK_H = 6
    THUMB_R = 9

    def __init__(self, rect: pygame.Rect, label: str, font_label, font_body):
        self.rect       = rect          # área total del control
        self.label      = label
        self.font_label = font_label
        self.font_body  = font_body
        self.value      = 2             # 1-5
        self._dragging  = False

    # --- helpers de geometría ---
    def _track_rect(self):
        ty = self.rect.y + self.rect.h // 2
        return pygame.Rect(self.rect.x, ty - self.TRACK_H // 2,
                           self.rect.w, self.TRACK_H)

    def _thumb_cx(self):
        t = (self.value - 1) / 4          # 0..1
        return self.rect.x + int(t * self.rect.w)

    # --- eventos ---
    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            thumb_cx = self._thumb_cx()
            thumb_cy = self._track_rect().centery
            if abs(event.pos[0] - thumb_cx) <= self.THUMB_R + 4 and \
               abs(event.pos[1] - thumb_cy) <= self.THUMB_R + 4:
                self._dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self._dragging = False
        elif event.type == pygame.MOUSEMOTION and self._dragging:
            rel = _clamp(event.pos[0] - self.rect.x, 0, self.rect.w)
            raw = 1 + rel / self.rect.w * 4
            self.value = _clamp(round(raw), 1, 5)

    # --- dibujo ---
    def draw(self, surface: pygame.Surface):
        # Etiqueta
        lbl = self.font_label.render(self.label, True, TEXT_SECONDARY)
        surface.blit(lbl, (self.rect.x, self.rect.y - 22))

        track = self._track_rect()
        # Pista de fondo
        _draw_rounded_rect(surface, BORDER, track, self.TRACK_H // 2)
        # Pista activa
        fill = pygame.Rect(track.x, track.y,
                           self._thumb_cx() - track.x, track.h)
        _draw_rounded_rect(surface, PRIMARY, fill, self.TRACK_H // 2)

        # Thumb
        cx = self._thumb_cx()
        cy = track.centery
        pygame.draw.circle(surface, BG_DEEP, (cx, cy), self.THUMB_R + 2)
        pygame.draw.circle(surface, PRIMARY, (cx, cy), self.THUMB_R)

        # Badge de texto
        prio_col = _PRIO_COLORS[self.value]
        badge_txt = self.font_body.render(
            f"{self.value}  {_PRIO_LABELS[self.value]}", True, prio_col)
        surface.blit(badge_txt,
                     (self.rect.right - badge_txt.get_width(),
                      self.rect.y - 24))


# ---------------------------------------------------------------------------
# Componente: ítem de la cola
# ---------------------------------------------------------------------------

class _QueueItem:
    H = 44

    def __init__(self, flight: FlightNode, font_mono, font_small):
        self.flight     = flight
        self.font_mono  = font_mono
        self.font_small = font_small

    def draw(self, surface: pygame.Surface, rect: pygame.Rect):
        _draw_rounded_rect(surface, BG_DEEP, rect, 8, 1, SECTION_LINE)

        # Código (mono)
        code = self.font_mono.render(self.flight.code, True, PRIMARY)
        surface.blit(code, (rect.x + 14, rect.centery - code.get_height() // 2))

        # Ruta
        route = self.font_small.render(
            f"{self.flight.origin}  →  {self.flight.destination}",
            True, TEXT_SECONDARY)
        surface.blit(route, (rect.x + 14 + code.get_width() + 16,
                             rect.centery - route.get_height() // 2))

        # Badges
        bx = rect.right - 14
        badges = []
        if self.flight.promotion:
            badges.append(("PROMO", SUCCESS, SUCCESS_BG))
        if self.flight.alert:
            badges.append(("ALERTA", CRITICAL, DANGER_BG))
        prio_col = _PRIO_COLORS[self.flight.priority]
        badges.append((f"P{self.flight.priority}", prio_col, BG_SURFACE2))

        for label, fg, bg in reversed(badges):
            badge = self.font_small.render(label, True, fg)
            bw    = badge.get_width() + 14
            bh    = 20
            brect = pygame.Rect(bx - bw, rect.centery - bh // 2, bw, bh)
            _draw_rounded_rect(surface, bg, brect, 6)
            surface.blit(badge, (brect.x + 7, brect.centery - badge.get_height() // 2))
            bx -= bw + 8


# ---------------------------------------------------------------------------
# Pantalla principal
# ---------------------------------------------------------------------------

class QueueScreen:
    # Dimensiones del modal
    MODAL_W  = 780
    MODAL_H  = 640          # puede crecer si hay cola
    MODAL_PAD_X = 48
    FIELD_H  = 42
    ROW_H    = 56           # alto de filas de toggles

    def __init__(self, fonts: dict, avl_tree, insertion_queue, on_switch_to_main):
        self.fonts             = fonts
        self.avl_tree          = avl_tree
        self.queue             = insertion_queue
        self.on_switch_to_main = on_switch_to_main

        self._status    = ""
        self._status_ok = True

        # Alias de fuentes (garantizamos que existen)
        self._f_title   = fonts.get("title_lg",  fonts.get("label_md"))
        self._f_body    = fonts.get("body_md",   fonts.get("label_md"))
        self._f_label   = fonts.get("body_sm",   fonts.get("label_md"))
        self._f_small   = fonts.get("body_sm",   fonts.get("label_md"))
        # Intentamos fuente monoespaciada, si no existe usamos body
        self._f_mono    = fonts.get("mono",      fonts.get("body_md", fonts.get("label_md")))

        self._queue_items: list[_QueueItem] = []

        self._build_layout()

    # -----------------------------------------------------------------------
    # Layout
    # -----------------------------------------------------------------------

    def _build_layout(self):
        mw = self.MODAL_W
        mx = WINDOW_W // 2 - mw // 2
        my = NAV_H + 40
        pad = self.MODAL_PAD_X

        # Posición dinámica del modal (recalculada en draw si hay cola)
        self._modal_x = mx
        self._modal_y = my

        inner_w = mw - pad * 2
        col2    = inner_w // 2 - 8        # ancho de media columna
        lx      = mx + pad                # columna izquierda
        rx      = lx + col2 + 16         # columna derecha

        # ── Sección 1: Identificación ──────────────────────────────────────
        y = my + 110                      # deja espacio al título

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

        # Slider de prioridad ocupa segunda mitad de la columna derecha
        slider_x = rx + col2 // 2 + 8
        slider_w = col2 - col2 // 2 - 8
        self._slider_prio = _PrioritySlider(
            rect=pygame.Rect(slider_x, y + 4, slider_w, self.FIELD_H - 8),
            label="Prioridad",
            font_label=self._f_label,
            font_body=self._f_small,
        )

        y += self.FIELD_H + 44

        # ── Sección 2: Ruta ───────────────────────────────────────────────
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

        # ── Sección 3: Detalles ───────────────────────────────────────────
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

        y += self.FIELD_H + 44

        # ── Sección 4: Toggles ────────────────────────────────────────────
        toggle_w = (inner_w - 12) // 2

        self._toggle_promo = _Toggle(
            cx=0, cy=0,
            label="Promoción activa",
            sublabel="Vuelo con descuento especial",
            font_body=self._f_body,
            font_small=self._f_small,
        )
        self._toggle_row_promo = pygame.Rect(lx, y, toggle_w, self.ROW_H)

        self._toggle_alerta = _Toggle(
            cx=0, cy=0,
            label="Alerta activada",
            sublabel="Requiere atención especial",
            font_body=self._f_body,
            font_small=self._f_small,
        )
        self._toggle_row_alerta = pygame.Rect(rx, y, toggle_w, self.ROW_H)

        y += self.ROW_H + 32

        # ── Botones ───────────────────────────────────────────────────────
        btn_w = (inner_w - 12) // 2

        self.btn_add = UIButton(
            rect=pygame.Rect(lx, y, btn_w, 52),
            text="+ AGREGAR A LA COLA",
            font=self._f_label,
            bg_color=C_GREEN,
            text_color=C_CREAM,
            border_color=C_GREEN,
            callback=self._add_to_queue,
        )

        self.btn_process = UIButton(
            rect=pygame.Rect(rx, y, btn_w, 52),
            text="▶ PROCESAR TODA LA COLA",
            font=self._f_label,
            bg_color=C_CREAM_DIM,
            text_color=C_GREEN_DARK,
            border_color=C_GREEN,
            callback=self._process_queue,
        )

        self._btn_y      = y
        self._status_y   = y + 60
        self._content_h  = y + 60 + 28 - my    # altura mínima del modal

        # Botón cerrar (esquina superior derecha) — marrón de la paleta
        self.btn_close = UIButton(
            rect=pygame.Rect(mx + mw - 58, my + 22, 36, 36),
            text="✕",
            font=self._f_label,
            bg_color=C_BROWN,
            text_color=C_CREAM,
            border_color=C_BROWN,
            callback=self.on_switch_to_main,
        )

        # Guardamos todos los campos para iterar
        self._all_fields = [
            self._field_codigo, self._field_hora,
            self._field_origen, self._field_destino,
            self._field_precio, self._field_pax,
        ]

    # -----------------------------------------------------------------------
    # Calcular altura del modal (crece con la cola)
    # -----------------------------------------------------------------------

    def _modal_rect(self) -> pygame.Rect:
        queue_extra = len(self._queue_items) * (_QueueItem.H + 8)
        if queue_extra:
            queue_extra += 48   # espacio para el label "En cola"
        h = self._content_h + queue_extra + 20
        return pygame.Rect(
            self._modal_x,
            self._modal_y,
            self.MODAL_W,
            h,
        )

    # -----------------------------------------------------------------------
    # Operaciones de cola
    # -----------------------------------------------------------------------

    def _add_to_queue(self):
        try:
            node = FlightNode(
                code=self._field_codigo.value.strip(),
                origin=self._field_origen.value.strip(),
                destination=self._field_destino.value.strip(),
                departure_time=self._field_hora.value.strip(),
                base_price=float(self._field_precio.value or 0),
                passengers=int(self._field_pax.value or 0),
                priority=self._slider_prio.value,
                promotion=self._toggle_promo.value,
                alert=self._toggle_alerta.value,
            )
            if not node.code:
                raise ValueError("El código de vuelo es obligatorio.")
            if not node.origin or not node.destination:
                raise ValueError("Origen y destino son obligatorios.")

            self.queue.enqueue(node)
            self._queue_items.append(
                _QueueItem(node, self._f_mono, self._f_small))
            self.set_status(
                f"✓ Vuelo {node.code} agregado · {len(self._queue_items)} en cola", True)
            self._clear_fields()
        except Exception as e:
            self.set_status(f"✗ {e}", False)

    def _process_queue(self):
        if self.queue.is_empty():
            self.set_status("La cola está vacía.", False)
            return
        count = len(self._queue_items)
        results = self.queue.process_all(self.avl_tree)
        self._queue_items.clear()
        self.set_status(f"✓ Se procesaron {count} vuelo{'s' if count != 1 else ''} correctamente.", True)

    def _clear_fields(self):
        for f in self._all_fields:
            f.value = ""
        self._slider_prio.value   = 2
        self._toggle_promo.value  = False
        self._toggle_alerta.value = False

    # -----------------------------------------------------------------------
    # Eventos
    # -----------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.on_switch_to_main()
            return

        for field in self._all_fields:
            field.handle_event(event)

        self._slider_prio.handle_event(event)
        self._toggle_promo.handle_event(event)
        self._toggle_alerta.handle_event(event)

        self.btn_add.handle_event(event)
        self.btn_process.handle_event(event)
        self.btn_close.handle_event(event)

    # -----------------------------------------------------------------------
    # Update
    # -----------------------------------------------------------------------

    def update(self, dt_ms: float):
        background_anim.update(dt_ms)

    # -----------------------------------------------------------------------
    # Draw
    # -----------------------------------------------------------------------

    def draw(self, surface: pygame.Surface):
        # ── Sin overlay: el modal flota sobre la página ──────────────────
        # Solo una sombra suave alrededor del modal para separarlo del fondo
        modal = self._modal_rect()
        shadow_rect = modal.inflate(12, 12)
        shadow_surf = pygame.Surface((shadow_rect.w, shadow_rect.h), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (67, 50, 40, 80),
                         pygame.Rect(0, 0, shadow_rect.w, shadow_rect.h),
                         border_radius=22)
        surface.blit(shadow_surf, shadow_rect.topleft)

        # ── Fondo del modal ──────────────────────────────────────────────
        _draw_rounded_rect(surface, C_CREAM, modal, 18, 2, C_GREEN)

        # ── Encabezado ───────────────────────────────────────────────────
        hx = modal.x
        hy = modal.y
        hw = modal.w

        # Banda de título en verde oscuro
        header_rect = pygame.Rect(hx, hy, hw, 80)
        pygame.draw.rect(surface, C_GREEN_DARK, header_rect,
                         border_top_left_radius=18, border_top_right_radius=18)
        pygame.draw.line(surface, C_TAN, (hx, hy + 80), (hx + hw, hy + 80), 1)

        eyebrow = self._f_small.render("COLA DE INSERCIONES", True, C_TAN)
        title   = self._f_title.render("Nuevo vuelo", True, C_CREAM)
        surface.blit(eyebrow, (hx + self.MODAL_PAD_X,
                               hy + 80 // 2 - eyebrow.get_height() - 2))
        surface.blit(title,   (hx + self.MODAL_PAD_X,
                               hy + 80 // 2 + 2))

        # ── Separadores de sección ───────────────────────────────────────
        pad  = self.MODAL_PAD_X
        lx   = modal.x + pad
        rend = modal.x + modal.w - pad

        def _section_header(label, y):
            s = self._f_small.render(label, True, TEXT_DIM)
            surface.blit(s, (lx, y))
            line_x = lx + s.get_width() + 12
            pygame.draw.line(surface, SECTION_LINE,
                             (line_x, y + s.get_height() // 2),
                             (rend, y + s.get_height() // 2), 1)

        # Calculamos la y de cada sección desde los rects de los campos
        _section_header("IDENTIFICACIÓN",
                        self._field_codigo.rect.y - 44)
        _section_header("RUTA",
                        self._field_origen.rect.y - 44)
        _section_header("DETALLES",
                        self._field_precio.rect.y - 44)
        _section_header("OPCIONES",
                        self._toggle_row_promo.y - 24)

        # ── Campos de texto ───────────────────────────────────────────────
        for field in self._all_fields:
            field.draw(surface)

        # Flecha entre origen y destino
        ax, ay = self._arrow_pos
        arrow = self._f_body.render("→", True, TEXT_DIM)
        surface.blit(arrow, (ax - arrow.get_width() // 2,
                             ay - arrow.get_height() // 2))

        # ── Slider ────────────────────────────────────────────────────────
        self._slider_prio.draw(surface)

        # ── Toggles ───────────────────────────────────────────────────────
        self._toggle_promo.draw(surface,  self._toggle_row_promo)
        self._toggle_alerta.draw(surface, self._toggle_row_alerta)

        # ── Botones ───────────────────────────────────────────────────────
        self.btn_add.draw(surface)
        self.btn_process.draw(surface)
        self.btn_close.draw(surface)

        # ── Estado / feedback ─────────────────────────────────────────────
        if self._status:
            col = C_GREEN if self._status_ok else C_BROWN
            st  = self._f_small.render(self._status, True, col)
            surface.blit(st, (lx, self._status_y))

        # ── Cola en vivo ──────────────────────────────────────────────────
        if self._queue_items:
            q_y = self._status_y + 28
            q_label = self._f_small.render(
                f"EN COLA  ({len(self._queue_items)})", True, TEXT_DIM)
            surface.blit(q_label, (lx, q_y))
            pygame.draw.line(surface, SECTION_LINE,
                             (lx + q_label.get_width() + 12, q_y + q_label.get_height() // 2),
                             (rend, q_y + q_label.get_height() // 2), 1)
            q_y += q_label.get_height() + 10
            for item in self._queue_items:
                item_rect = pygame.Rect(lx, q_y,
                                        modal.w - pad * 2,
                                        _QueueItem.H)
                item.draw(surface, item_rect)
                q_y += _QueueItem.H + 8

    # -----------------------------------------------------------------------
    # API pública
    # -----------------------------------------------------------------------

    def set_status(self, message: str, success: bool = True):
        self._status    = message
        self._status_ok = success