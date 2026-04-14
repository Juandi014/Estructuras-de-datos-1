
import pygame
import time
from user_interface.color_scheme import (
    BG_DEEP, BG_SURFACE, BG_SURFACE2, BORDER, PRIMARY, LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DIM, CRITICAL,
    CARD_RADIUS, NAV_H, PANEL_PADDING, BTN_H, WINDOW_W, WINDOW_H
)
from user_interface.panel_ui import UIButton, UIInputField


class VersionDrawer:
    WIDTH = 320
    ANIM_SPEED = 0.22   # velocidad de animación (más alto = más rápido)

    def __init__(self, fonts: dict, avl_tree, version_manager=None, on_restore=None):
        self.fonts = fonts
        self.avl_tree = avl_tree
        # version_manager externo (VersionManager de MainScreen)
        self._vm = version_manager
        # callback opcional llamado tras restaurar (para limpiar caches externos)
        self._on_restore = on_restore

        self.visible = False
        self._x_current = float(WINDOW_W)      # posición actual (fuera de pantalla)
        self._x_target = float(WINDOW_W)       # posición objetivo

        # Input para nueva versión
        self._input = UIInputField(
            rect=pygame.Rect(0, 0, self.WIDTH - 100, 38),
            placeholder="Nombre de la versión...",
            font=fonts["body_md"]
        )

        # Botón Guardar
        self._btn_save = UIButton(
            rect=pygame.Rect(0, 0, 80, 38),
            text="Guardar",
            font=fonts["label_md"],
            bg_color=PRIMARY,
            text_color=LIGHT,
            border_color=PRIMARY,
            callback=self._save_version
        )

        # Botón Cerrar
        self._btn_close = UIButton(
            rect=pygame.Rect(0, 0, 28, 28),
            text="✕",
            font=fonts["label_md"],
            bg_color=CRITICAL,
            text_color=LIGHT,
            border_color=CRITICAL,
            callback=self.close
        )

        # Estado de tarjetas
        self._expanded = {}   # name -> bool

        self._status = ""
        self._status_ok = True

    # ------------------------------------------------------------------
    # API pública (fácil de usar desde cualquier pantalla)
    # ------------------------------------------------------------------

    def open(self):
        """Abre el drawer"""
        self.visible = True
        self._x_target = WINDOW_W - self.WIDTH
        self._input.value = ""

    def close(self):
        """Cierra el drawer"""
        self._x_target = WINDOW_W

    def toggle(self):
        """Alterna entre abierto y cerrado"""
        if self.visible and self._x_current < WINDOW_W - 10:
            self.close()
        else:
            self.open()

    # ------------------------------------------------------------------
    # Operaciones internas
    # ------------------------------------------------------------------

    def _save_version(self):
        import copy
        name = self._input.value.strip()
        if not name:
            self.set_status("Ingresa un nombre para la version", False)
            return

        vm = self._vm
        if vm is None:
            self.set_status("Error: gestor de versiones no disponible", False)
            return

        try:
            snapshot = copy.deepcopy(self.avl_tree)
            vm.saveVersion(name, snapshot)
            self.set_status(f"Version '{name}' guardada", True)
            self._input.value = ""
            self._expanded[name] = True
        except ValueError as e:
            self.set_status(str(e), False)

    def _restore_version(self, name: str):
        import copy
        vm = self._vm
        if vm is None:
            self.set_status("Error: gestor de versiones no disponible", False)
            return
        snapshot = vm.restoreVersion(name)
        if snapshot is None:
            self.set_status(f"Version '{name}' no encontrada", False)
            return
        restored = copy.deepcopy(snapshot)
        self.avl_tree.root               = restored.root
        self.avl_tree.critical_depth     = getattr(restored, 'critical_depth', 0)
        self.avl_tree.rotations_ll       = getattr(restored, 'rotations_ll', 0)
        self.avl_tree.rotations_rr       = getattr(restored, 'rotations_rr', 0)
        self.avl_tree.rotations_lr       = getattr(restored, 'rotations_lr', 0)
        self.avl_tree.rotations_rl       = getattr(restored, 'rotations_rl', 0)
        self.avl_tree.mass_cancellations = getattr(restored, 'mass_cancellations', 0)
        self.set_status(f"Version '{name}' restaurada", True)
        # Notificar al exterior (ej: limpiar cache del renderer)
        if self._on_restore:
            self._on_restore()
        self.close()

    def _delete_version(self, name: str):
        vm = self._vm
        if vm is not None and vm.deleteVersion(name):
            if name in self._expanded:
                del self._expanded[name]
            self.set_status(f"Version '{name}' eliminada", True)
        else:
            self.set_status(f"No se pudo eliminar '{name}'", False)

    def set_status(self, message: str, success: bool = True):
        self._status = message
        self._status_ok = success

    # ------------------------------------------------------------------
    # Eventos y actualización
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event):
        if not self.visible:
            return

        # Click fuera → cerrar
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not pygame.Rect(self._x_current, 0, self.WIDTH, WINDOW_H).collidepoint(event.pos):
                self.close()
                return

        # Input y botones de cabecera reciben todos los eventos
        self._input.handle_event(event)
        self._btn_save.handle_event(event)
        self._btn_close.handle_event(event)

        # Manejo de tarjetas — solo clicks de mouse
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        panel_x = int(self._x_current)
        # y inicial identico al de draw(): NAV_H + PP + 20 + 50 + 70
        y = NAV_H + PANEL_PADDING + 140
        raw = self._vm.getVersions() if self._vm is not None else []
        versions = {v["name"]: v for v in raw}

        for name, data in versions.items():
            expanded = self._expanded.get(name, False)
            card_h = 138 if expanded else 68
            card_rect = pygame.Rect(panel_x + PANEL_PADDING, y, self.WIDTH - 32, card_h)

            if expanded:
                # Rects de botones: ey = card_rect.y + 66, btn_y = ey + 68
                btn_y = card_rect.y + 134
                btn_w = (card_rect.width - 36) // 2
                restore_rect = pygame.Rect(card_rect.x + 12, btn_y, btn_w, 28)
                delete_rect  = pygame.Rect(card_rect.x + 12 + btn_w + 12, btn_y, btn_w, 28)

                if restore_rect.collidepoint(event.pos):
                    self._restore_version(name)
                    return
                if delete_rect.collidepoint(event.pos):
                    self._delete_version(name)
                    return

            # Toggle expansion si el clic fue en la tarjeta (no en botones)
            if card_rect.collidepoint(event.pos):
                self._expanded[name] = not expanded
                return

            y += card_h + 12

    def update(self, dt_ms: float):
        # Animación suave de slide
        diff = self._x_target - self._x_current
        if abs(diff) > 1.0:
            self._x_current += diff * self.ANIM_SPEED
        else:
            self._x_current = self._x_target
            if self._x_current >= WINDOW_W - 5:
                self.visible = False

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface):
        if not self.visible and abs(self._x_current - WINDOW_W) < 5:
            return

        x = int(self._x_current)
        if x >= WINDOW_W:
            return

        # Sombra lateral
        shadow = pygame.Surface((12, WINDOW_H), pygame.SRCALPHA)
        for i in range(12):
            alpha = int(80 * (1 - i / 12))
            pygame.draw.line(shadow, (0, 0, 0, alpha), (11 - i, 0), (11 - i, WINDOW_H))
        surface.blit(shadow, (x - 12, 0))

        # Fondo del panel
        panel_rect = pygame.Rect(x, 0, self.WIDTH, WINDOW_H)
        pygame.draw.rect(surface, BG_SURFACE, panel_rect)
        pygame.draw.line(surface, BORDER, (x, 0), (x, WINDOW_H), 2)

        y = NAV_H + PANEL_PADDING + 20

        # Título
        title = self.fonts["label_md"].render("// VERSIONES GUARDADAS", True, PRIMARY)
        surface.blit(title, (x + PANEL_PADDING, y))
        y += 50

        # Input y botón guardar
        self._input.rect.topleft = (x + PANEL_PADDING, y)
        self._input.draw(surface)

        self._btn_save.rect.topleft = (x + PANEL_PADDING + self._input.rect.width + 8, y)
        self._btn_save.draw(surface)
        y += 70

        # Botón cerrar
        self._btn_close.rect.topleft = (x + self.WIDTH - 42, NAV_H + 18)
        self._btn_close.draw(surface)

        # Lista de versiones
        self._draw_versions_list(surface, y, x)

        # Status
        if self._status:
            color = LIGHT if self._status_ok else CRITICAL
            status_surf = self.fonts["body_xs"].render(self._status[:50], True, color)
            surface.blit(status_surf, (x + PANEL_PADDING, WINDOW_H - 45))

    def _draw_versions_list(self, surface, start_y, panel_x):
        raw = self._vm.getVersions() if self._vm is not None else []
        versions = {v["name"]: v for v in raw}
        y = start_y

        if not versions:
            no_ver = self.fonts["body_sm"].render("No hay versiones guardadas", True, TEXT_DIM)
            surface.blit(no_ver, (panel_x + PANEL_PADDING, y))
            return

        for name, data in versions.items():
            expanded = self._expanded.get(name, False)
            card_h = 138 if expanded else 68

            card_rect = pygame.Rect(panel_x + PANEL_PADDING, y, self.WIDTH - 32, card_h)
            pygame.draw.rect(surface, BG_SURFACE2, card_rect, border_radius=10)
            pygame.draw.rect(surface, PRIMARY if expanded else BORDER, card_rect, width=2, border_radius=10)

            # Nombre
            name_surf = self.fonts["label_md"].render(name, True, TEXT_PRIMARY)
            surface.blit(name_surf, (card_rect.x + 16, card_rect.y + 12))

            # Timestamp
            ts = data.get("timestamp", "—")
            ts_surf = self.fonts["body_xs"].render(ts, True, TEXT_DIM)
            surface.blit(ts_surf, (card_rect.x + 16, card_rect.y + 34))

            # Chevron
            chev = "▲" if expanded else "▼"
            chev_surf = self.fonts["body_sm"].render(chev, True, TEXT_SECONDARY)
            surface.blit(chev_surf, (card_rect.right - 26, card_rect.y + 16))

            # Contenido expandido
            if expanded:
                ey = card_rect.y + 66
                pygame.draw.line(surface, BORDER, (card_rect.x + 12, ey), (card_rect.right - 12, ey), 1)

                # Obtener métricas del snapshot guardado
                snapshot = self._vm.restoreVersion(name) if self._vm else None
                node_count = "—"
                height = "—"
                if snapshot is not None:
                    try:
                        node_count = str(snapshot.nodeCount())
                    except Exception:
                        pass
                    try:
                        height = str(snapshot.getHeight())
                    except Exception:
                        pass

                meta_y = ey + 12
                meta = [
                    ("Nodos", node_count),
                    ("Altura", height),
                ]
                for lbl, val in meta:
                    lbl_s = self.fonts["body_sm"].render(lbl + ": ", True, TEXT_DIM)
                    val_s = self.fonts["body_sm"].render(str(val), True, TEXT_PRIMARY)
                    surface.blit(lbl_s, (card_rect.x + 16, meta_y))
                    surface.blit(val_s, (card_rect.x + 16 + lbl_s.get_width(), meta_y))
                    meta_y += 24

                # Botones
                btn_y = ey + 68
                btn_w = (card_rect.width - 36) // 2

                restore_btn = UIButton(
                    rect=pygame.Rect(card_rect.x + 12, btn_y, btn_w, 28),
                    text="Restaurar",
                    font=self.fonts["body_sm"],
                    bg_color=PRIMARY,
                    text_color=LIGHT,
                    border_color=PRIMARY,
                    callback=lambda n=name: self._restore_version(n)
                )
                restore_btn.draw(surface)

                delete_btn = UIButton(
                    rect=pygame.Rect(card_rect.x + 12 + btn_w + 12, btn_y, btn_w, 28),
                    text="Eliminar",
                    font=self.fonts["body_sm"],
                    bg_color=BG_SURFACE2,
                    text_color=CRITICAL,
                    border_color=CRITICAL,
                    callback=lambda n=name: self._delete_version(n)
                )
                delete_btn.draw(surface)

            y += card_h + 12