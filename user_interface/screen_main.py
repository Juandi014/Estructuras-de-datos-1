
import pygame
import math
import copy
from user_interface.color_scheme import (
    BG_DEEP, BG_SURFACE, BG_SURFACE2, BORDER, PRIMARY, LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DIM, CRITICAL,
    WINDOW_W, WINDOW_H, NAV_H, BTN_H, CARD_RADIUS
)
from user_interface.tree_renderer import TreeRenderer
from user_interface.panel_ui import UIButton, UIToggle
from user_interface.version_drawer import VersionDrawer
from models.flight_node import FlightNode
from user_interface.flight_detail_modal import FlightDetailModal

# Importar HistoryStack y VersionManager con tolerancia a rutas distintas
try:
    from logic.history_stack import HistoryStack
except ImportError:
    from history_stack import HistoryStack

try:
    from logic.version_manager import VersionManager
except ImportError:
    from version_manager import VersionManager


class _ReverseStr:
    """Wrapper para comparar strings en orden descendente sin funciones lambda complejas."""
    __slots__ = ('s',)
    def __init__(self, s): self.s = s
    def __lt__(self, other): return self.s > other.s
    def __le__(self, other): return self.s >= other.s
    def __gt__(self, other): return self.s < other.s
    def __ge__(self, other): return self.s <= other.s
    def __eq__(self, other): return self.s == other.s


class MainScreen:
    def __init__(self, fonts: dict, avl_tree, on_undo, on_stress_screen=None):
        self.fonts = fonts
        self.avl_tree = avl_tree
        self.on_undo = on_undo          # callback externo (se sigue respetando)
        self.on_stress_screen = on_stress_screen  # callback para ir a la pantalla de modo estres

        # Historial interno para deshacer sin depender de main.py
        self._history = HistoryStack()
        # Gestor de versiones nombradas
        self._version_manager = VersionManager()

        # Con los 4 botones horizontales eliminados, el árbol puede crecer hacia abajo
        self.tree_rect = pygame.Rect(40, NAV_H + 105, int(WINDOW_W * 0.68), WINDOW_H - NAV_H - 175)

        self.panel_rect = pygame.Rect(
            self.tree_rect.right + 30,
            NAV_H + 95,
            310,
            WINDOW_H - NAV_H - 355
        )

        self.renderer = TreeRenderer(self.tree_rect)

        self.stress_enabled = False
        self._status = ""
        self._status_ok = True

        # Estado de recorrido activo
        self._traversal_result = []      # lista de nodos en orden
        self._traversal_type = ""        # "inorder" | "preorder" | "postorder" | "bfs"
        self._traversal_index = -1       # índice del paso actual (-1 = inactivo)
        self._traversal_timer = 0.0      # ms acumulados
        self._traversal_step_ms = 600    # ms entre pasos

        # Panel de versiones guardadas
        self._versions_panel_visible = False
        self._versions_close_rect    = None
        self._version_restore_rects  = []

        # === NUEVO: Version Drawer ===
        self.version_drawer = VersionDrawer(
            fonts, avl_tree,
            version_manager=self._version_manager,
            on_restore=self._on_version_restored,
        )
        self.flight_modal = None   # Modal para click en nodo / agregar vuelo
        self._init_ui()

    def _init_ui(self):
        # Toggle Modo Estrés
        toggle_rect = pygame.Rect(self.panel_rect.x, NAV_H + 25, self.panel_rect.width, 44)
        self.stress_toggle = UIToggle(
            rect=toggle_rect,
            label="Modo Estrés",
            font=self.fonts["label_md"],
            initial_state=False,
            callback=self._on_stress_toggle
        )

        # Botones verticales del panel derecho
        btn_x = self.panel_rect.x
        btn_y = self.panel_rect.bottom + 25
        btn_w = self.panel_rect.width
        btn_h = 36

        # Botón Agregar ocupa la posición que tenía Buscar Vuelo
        self.btn_add = UIButton(
            rect=pygame.Rect(btn_x, btn_y, btn_w, btn_h),
            text="➕ Agregar Vuelo",
            font=self.fonts["label_md"],
            bg_color=BG_SURFACE2,
            text_color=PRIMARY,
            border_color=PRIMARY,
            callback=self._do_add
        )
        btn_y += btn_h + 8

        self.btn_undo = UIButton(
            rect=pygame.Rect(btn_x, btn_y, btn_w, btn_h),
            text="↩ Deshacer",
            font=self.fonts["label_md"],
            bg_color=BG_SURFACE2,
            text_color=TEXT_SECONDARY,
            border_color=BORDER,
            callback=self._do_undo
        )
        btn_y += btn_h + 8

        self.btn_low_rent = UIButton(
            rect=pygame.Rect(btn_x, btn_y, btn_w, btn_h),
            text="📉 Eliminar nodo crítico",
            font=self.fonts["label_md"],
            bg_color=BG_SURFACE2,
            text_color=CRITICAL,
            border_color=CRITICAL,
            callback=self._delete_lowest_rentability
        )
        btn_y += btn_h + 8

        self.btn_depth = UIButton(
            rect=pygame.Rect(btn_x, btn_y, btn_w, btn_h),
            text="⚙ Modificar profundidad",
            font=self.fonts["label_md"],
            bg_color=BG_SURFACE2,
            text_color=PRIMARY,
            border_color=PRIMARY,
            callback=self._modify_critical_depth
        )
        btn_y += btn_h + 12

        # === BOTONES EXPORTAR Y GUARDAR EN LA MISMA FILA ===
        half_w = (btn_w - 12) // 2

        self.btn_export = UIButton(
            rect=pygame.Rect(btn_x, btn_y, half_w, btn_h),
            text="💾 Exportar JSON",
            font=self.fonts["label_md"],
            bg_color=BG_SURFACE2,
            text_color=PRIMARY,
            border_color=PRIMARY,
            callback=self._export_json
        )

        self.btn_save_version = UIButton(
            rect=pygame.Rect(btn_x + half_w + 12, btn_y, half_w, btn_h),
            text="📌 Guardar Versión",
            font=self.fonts["label_md"],
            bg_color=BG_SURFACE2,
            text_color=PRIMARY,
            border_color=PRIMARY,
            callback=self._open_version_drawer
        )

        # Barra de recorridos — ubicada bajo el árbol, cerca del borde inferior
        trav_y = self.tree_rect.bottom + 18
        trav_w = int((self.tree_rect.width - 60) / 4)

        self.trav_in = UIButton(
            rect=pygame.Rect(self.tree_rect.x, trav_y, trav_w, 34),
            text="In-Order",
            font=self.fonts["label_sm"],
            bg_color=BG_SURFACE2,
            text_color=TEXT_SECONDARY,
            border_color=BORDER,
            callback=lambda: self._show_traversal("inorder")
        )
        self.trav_pre = UIButton(
            rect=pygame.Rect(self.tree_rect.x + trav_w + 20, trav_y, trav_w, 34),
            text="Pre-Order",
            font=self.fonts["label_sm"],
            bg_color=BG_SURFACE2,
            text_color=TEXT_SECONDARY,
            border_color=BORDER,
            callback=lambda: self._show_traversal("preorder")
        )
        self.trav_post = UIButton(
            rect=pygame.Rect(self.tree_rect.x + (trav_w + 20)*2, trav_y, trav_w, 34),
            text="Post-Order",
            font=self.fonts["label_sm"],
            bg_color=BG_SURFACE2,
            text_color=TEXT_SECONDARY,
            border_color=BORDER,
            callback=lambda: self._show_traversal("postorder")
        )
        self.trav_bfs = UIButton(
            rect=pygame.Rect(self.tree_rect.x + (trav_w + 20)*3, trav_y, trav_w, 34),
            text="Anchura (BFS)",
            font=self.fonts["label_sm"],
            bg_color=BG_SURFACE2,
            text_color=TEXT_SECONDARY,
            border_color=BORDER,
            callback=lambda: self._show_traversal("bfs")
        )

    # ------------------------------------------------------------------
    # NUEVA LÓGICA PARA GUARDAR VERSIÓN
    # ------------------------------------------------------------------

    def _open_version_drawer(self):
        """
        Abre/cierra el drawer lateral de versiones guardadas.
        No muestra ninguna ventana emergente; el guardado se hace
        desde el input del propio drawer.
        """
        self.version_drawer.toggle()

    # ------------------------------------------------------------------
    # Callbacks existentes (sin cambios)
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Callbacks funcionales
    # ------------------------------------------------------------------

    def _export_json(self):
        """Exporta el árbol a JSON usando json_exporter.py."""
        try:
            from in_out.json_exporter import export_file
            path = export_file(self.avl_tree)
            self.set_status(f"✓ Árbol exportado en: {path}", True)
        except ValueError as e:
            self.set_status(f"✗ {e}", False)
        except Exception as e:
            self.set_status(f"✗ Error al exportar: {e}", False)

    def _on_stress_toggle(self, state):
        self.stress_enabled = state
        if state:
            self.avl_tree.enableStressMode()
            self.set_status("Modo Estrés activado", True)
            # Navegar a la pantalla de modo estrés si hay callback
            if self.on_stress_screen:
                self.on_stress_screen()
        else:
            self.avl_tree.disableStressMode()
            self.set_status("Modo Normal activado", True)
            # Si el toggle se apaga desde aquí (sin volver desde StressScreen),
            # asegurarse de que el árbol queda en modo normal.
            self.avl_tree.stress_mode = False

    def _do_add(self):
        self._open_flight_detail_modal(None)

    def _do_undo(self):
        """Restaura el árbol al estado anterior usando el historial interno."""
        entry = self._history.pop()
        if entry is None:
            # Intentar también el callback externo
            try:
                self.on_undo()
            except Exception:
                pass
            self.set_status("✗ No hay acciones para deshacer", False)
            return
        # Restaurar snapshot profundo
        self.avl_tree.root = copy.deepcopy(entry["snapshot"].root)
        self.avl_tree.critical_depth = entry["snapshot"].critical_depth
        self.avl_tree.rotations_ll = entry["snapshot"].rotations_ll
        self.avl_tree.rotations_rr = entry["snapshot"].rotations_rr
        self.avl_tree.rotations_lr = entry["snapshot"].rotations_lr
        self.avl_tree.rotations_rl = entry["snapshot"].rotations_rl
        self.avl_tree.mass_cancellations = entry["snapshot"].mass_cancellations
        self.set_status(f"✓ Deshecho: {entry['action']} ({entry['code']})", True)

    def _delete_lowest_rentability(self):
        """
        Eliminación Inteligente por Impacto Económico.
        1. Rentabilidad = pasajeros × precioFinal – promoción (10 % si aplica) + penalización (25 % si aplica)
        2. Nodo de menor rentabilidad; empate → más lejano a la raíz; persiste → código más grande.
        3. Cancela ese nodo Y su subrama completa.
        4. Rebalancea el árbol.
        """
        if self.avl_tree.getRoot() is None:
            self.set_status("✗ El árbol está vacío", False)
            return

        all_nodes = self.avl_tree.breadthFirstSearch()
        if not all_nodes:
            self.set_status("✗ El árbol está vacío", False)
            return

        def rentability(n):
            base       = n.passengers * getattr(n, 'final_price', n.base_price)
            promo      = base * 0.10 if getattr(n, 'promotion', False) else 0.0
            penalty    = base * 0.25 if getattr(n, 'is_critical', False) else 0.0
            return base - promo + penalty

        # Clave de ordenamiento:
        #   1° menor rentabilidad (asc)
        #   2° mayor profundidad en empate (desc → negamos depth)
        #   3° mayor código en empate (desc → comparamos con negación de str no es posible,
        #      usamos truco: reversed string comparison via key)
        def sort_key(n):
            # Para código desc: invertimos el orden natural con una clase comparadora
            return (rentability(n), -n.depth, _ReverseStr(str(n.code)))

        target = min(all_nodes, key=sort_key)

        self._push_history("CANCEL_SUBTREE", target.code)
        count = self._avl_delete_subtree(target.code)
        if count == 0:
            # Si delete_subtree no existe, eliminar solo el nodo
            self._avl_delete(target.code)
            count = 1

        # Rebalancear
        if hasattr(self.avl_tree, 'globalRebalance'):
            self.avl_tree.globalRebalance()

        self.avl_tree.mass_cancellations = getattr(self.avl_tree, 'mass_cancellations', 0) + 1
        self.set_status(
            f"✓ Subrama de {target.code} cancelada "
            f"(rentabilidad {rentability(target):.0f}, {count} nodo{'s' if count != 1 else ''} eliminado{'s' if count != 1 else ''})",
            True
        )

    # ------------------------------------------------------------------
    # Helpers internos de árbol y historial
    # ------------------------------------------------------------------

    def _push_history(self, action: str, code):
        """Guarda un snapshot del árbol actual en el historial de deshacer."""
        snapshot = copy.deepcopy(self.avl_tree)
        self._history.push(action, code, snapshot)

    def _avl_delete(self, code):
        """Elimina un nodo del árbol usando el método disponible."""
        if hasattr(self.avl_tree, 'delete'):
            self.avl_tree.delete(code)
        elif hasattr(self.avl_tree, 'deleteNode'):
            self.avl_tree.deleteNode(code)
        elif hasattr(self.avl_tree, 'remove'):
            self.avl_tree.remove(code)

    def _avl_delete_subtree(self, code) -> int:
        """Elimina la subrama de un nodo. Retorna cantidad de nodos eliminados."""
        if hasattr(self.avl_tree, 'delete_subtree'):
            return self.avl_tree.delete_subtree(code) or 0
        elif hasattr(self.avl_tree, 'deleteSubtree'):
            return self.avl_tree.deleteSubtree(code) or 0
        return 0

    def _modify_critical_depth(self):
        """Pide una nueva profundidad crítica mediante un cuadro de diálogo Tkinter."""
        import tkinter as tk
        from tkinter import simpledialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        current = self.avl_tree.critical_depth
        value = simpledialog.askinteger(
            "Modificar profundidad crítica",
            f"Profundidad crítica actual: {current}\n"
            "Ingresa la nueva profundidad (0 = sin penalización):",
            minvalue=0,
            maxvalue=50,
            parent=root,
        )
        root.destroy()
        if value is None:
            self.set_status("Modificación cancelada", True)
            return
        self.avl_tree.applyDepthPenalty(value)
        self.set_status(f"✓ Profundidad crítica actualizada a {value}", True)

    def _show_traversal(self, trav_type: str):
        """
        Inicia un recorrido animado del árbol.
        Si el mismo recorrido ya está activo, lo detiene (toggle).
        El nodo activo se resalta con un halo amarillo en el árbol.
        La secuencia completa se muestra en el panel lateral.
        """
        # Toggle: si ya está corriendo el mismo recorrido, detenerlo
        if self._traversal_index >= 0 and self._traversal_type == trav_type:
            self._traversal_index = -1
            self._traversal_result = []
            self._traversal_type = ""
            self.set_status("Recorrido detenido", True)
            return

        if self.avl_tree.getRoot() is None:
            self.set_status("✗ El árbol está vacío", False)
            return

        if trav_type == "inorder":
            nodes = self._collect_inorder(self.avl_tree.getRoot())
        elif trav_type == "preorder":
            nodes = self._collect_preorder(self.avl_tree.getRoot())
        elif trav_type == "postorder":
            nodes = self._collect_postorder(self.avl_tree.getRoot())
        else:  # bfs
            nodes = self.avl_tree.breadthFirstSearch()

        self._traversal_result = nodes
        self._traversal_type = trav_type
        self._traversal_index = 0
        self._traversal_timer = 0.0

        label = {"inorder": "In-Order", "preorder": "Pre-Order",
                 "postorder": "Post-Order", "bfs": "Anchura BFS"}.get(trav_type, trav_type)
        codes = " → ".join(str(n.code) for n in nodes)
        self.set_status(f"▶ {label}: {codes}", True)

    # Helpers de recorrido
    def _collect_inorder(self, node, result=None):
        if result is None:
            result = []
        if node is None:
            return result
        self._collect_inorder(node.getLeftChild(), result)
        result.append(node)
        self._collect_inorder(node.getRightChild(), result)
        return result

    def _collect_preorder(self, node, result=None):
        if result is None:
            result = []
        if node is None:
            return result
        result.append(node)
        self._collect_preorder(node.getLeftChild(), result)
        self._collect_preorder(node.getRightChild(), result)
        return result

    def _collect_postorder(self, node, result=None):
        if result is None:
            result = []
        if node is None:
            return result
        self._collect_postorder(node.getLeftChild(), result)
        self._collect_postorder(node.getRightChild(), result)
        result.append(node)
        return result

    # ------------------------------------------------------------------
    # EVENTOS - SOLO LO NECESARIO
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Dispatches events to the flight detail modal or normal controls."""

        # Prioridad 1: Modal de vuelo (click en nodo o botón agregar)
        if self.flight_modal and self.flight_modal.visible:
            self.flight_modal.handle_event(event)
            return

        # Prioridad 2: Version drawer si está abierto
        self.version_drawer.handle_event(event)

        # Eventos del renderer (zoom, drag)
        self.renderer.handle_event(event)

        # Toggle Modo Estrés — debe recibir eventos ANTES del bloque de botones
        self.stress_toggle.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Cerrar panel de versiones
            if self._versions_panel_visible:
                close_rect = getattr(self, '_versions_close_rect', None)
                if close_rect and close_rect.collidepoint(event.pos):
                    self._versions_panel_visible = False
                    return
                for btn_rect, vname in getattr(self, '_version_restore_rects', []):
                    if btn_rect.collidepoint(event.pos):
                        self._restore_version(vname)
                        return

            clicked_node = self.renderer.get_node_at(event.pos, self.avl_tree.getRoot())
            if clicked_node:
                self._open_flight_detail_modal(clicked_node)
                return

            # Botones del panel derecho
            if self.btn_add.rect.collidepoint(event.pos):
                self._do_add()
            elif self.btn_undo.rect.collidepoint(event.pos):
                self._do_undo()
            elif self.btn_low_rent.rect.collidepoint(event.pos):
                self._delete_lowest_rentability()
            elif self.btn_depth.rect.collidepoint(event.pos):
                self._modify_critical_depth()
            elif self.btn_export.rect.collidepoint(event.pos):
                self._export_json()
            elif self.btn_save_version.rect.collidepoint(event.pos):
                self._open_version_drawer()
            # Botones de recorrido
            elif self.trav_in.rect.collidepoint(event.pos):
                self._show_traversal("inorder")
            elif self.trav_pre.rect.collidepoint(event.pos):
                self._show_traversal("preorder")
            elif self.trav_post.rect.collidepoint(event.pos):
                self._show_traversal("postorder")
            elif self.trav_bfs.rect.collidepoint(event.pos):
                self._show_traversal("bfs")

        if event.type == pygame.KEYDOWN:
            self._handle_key(event)

    def _handle_key(self, event: pygame.event.Event):
        """Maneja eventos de teclado globales de la pantalla principal."""
        # Ctrl+Z → deshacer
        if event.key == pygame.K_z and (event.mod & pygame.KMOD_CTRL):
            self._do_undo()
            return
        # El drawer ya recibe los KEYDOWN directamente desde handle_event,
        # no se reenvían aquí para evitar doble escritura en el input.


    def update(self, dt_ms: float):
        self.version_drawer.update(dt_ms)

        # Animación de recorrido: avanzar al siguiente nodo
        if self._traversal_index >= 0 and self._traversal_result:
            self._traversal_timer += dt_ms
            if self._traversal_timer >= self._traversal_step_ms:
                self._traversal_timer = 0.0
                self._traversal_index += 1
                if self._traversal_index >= len(self._traversal_result):
                    # Recorrido completado
                    self._traversal_index = -1

    def _draw_traversal_sequence_overlay(self, surface: pygame.Surface):
        """
        Strategy:
            Dibuja en la parte inferior del área del árbol la secuencia completa
            del recorrido actual, resaltando el nodo que se está "visitando".
            Método pequeño, reutilizable y de única responsabilidad.
        """
        if not self._traversal_result or self._traversal_index < 0:
            return

        label_map = {
            "inorder": "IN-ORDER",
            "preorder": "PRE-ORDER",
            "postorder": "POST-ORDER",
            "bfs": "ANCHURA (BFS)"
        }
        label = label_map.get(self._traversal_type, self._traversal_type.upper())

        # Rectángulo del overlay (fondo semi-transparente)
        overlay_h = 54
        overlay_rect = pygame.Rect(
            self.tree_rect.x,
            self.tree_rect.bottom - overlay_h,
            self.tree_rect.width,
            overlay_h
        )

        # Fondo oscuro con transparencia
        overlay_surf = pygame.Surface((overlay_rect.w, overlay_rect.h), pygame.SRCALPHA)
        overlay_surf.fill((20, 20, 35, 200))
        surface.blit(overlay_surf, overlay_rect.topleft)

        font_lbl = self.fonts["body_sm"]
        font_code = self.fonts["label_sm"]

        # Título del recorrido
        title_surf = font_lbl.render(f"▶ {label}", True, (255, 220, 0))
        surface.blit(title_surf, (overlay_rect.x + 12, overlay_rect.y + 6))

        # Secuencia de códigos
        x = overlay_rect.x + 12
        y = overlay_rect.y + 28
        max_x = overlay_rect.right - 12

        for i, node in enumerate(self._traversal_result):
            is_active = (i == self._traversal_index)
            is_done   = (i < self._traversal_index)

            color = (255, 220, 0) if is_active else \
                    ((120, 200, 120) if is_done else (180, 180, 200))

            code_surf = font_code.render(str(node.code), True, color)

            # No desbordar el rectángulo
            if x + code_surf.get_width() + 12 > max_x:
                break

            surface.blit(code_surf, (x, y))
            x += code_surf.get_width() + 6

            if i < len(self._traversal_result) - 1:
                arrow = font_code.render("→", True, (80, 80, 100))
                surface.blit(arrow, (x, y))
                x += arrow.get_width() + 4

    def draw(self, surface: pygame.Surface):
        """
        Main drawing method for S1 — AVL Tree View.
        Responsibilities:
            - Clear background
            - Draw header, tree area, right panel
            - Draw all UI buttons and toggles
            - Draw traversal bar
            - Draw traversal sequence overlay (if active)
            - Draw versions panel (if visible)
            - Draw version drawer and flight modal on top
        """
        surface.fill(BG_DEEP)

        self._draw_header(surface)
        self._draw_tree_area(surface)
        self._draw_right_panel(surface)

        # UI controls
        self.stress_toggle.draw(surface)
        self.btn_add.draw(surface)
        self.btn_undo.draw(surface)
        self.btn_low_rent.draw(surface)
        self.btn_depth.draw(surface)
        self.btn_export.draw(surface)
        self.btn_save_version.draw(surface)

        self._draw_traversals_bar(surface)
        
        # ←←← NUEVO: Status bar (método que faltaba)
        self._draw_status_bar(surface)

        # Overlay de secuencia de recorrido
        if self._traversal_index >= 0 and self._traversal_result:
            self._draw_traversal_sequence_overlay(surface)

        # Panel flotante de versiones
        if self._versions_panel_visible:
            self._draw_versions_panel(surface)

        # Version drawer y modal (siempre al final)
        self.version_drawer.draw(surface)
        self._draw_flight_modal(surface)

    # ------------------------------------------------------------------
    # MÉTODOS PARA EL MODAL (solo lo necesario)
    # ------------------------------------------------------------------

    def _open_flight_detail_modal(self, node: FlightNode = None):
        """
        Abre el modal para ver, editar o crear un vuelo.
        - Si node es None → modo creación (campos vacíos, edición inmediata)
        - Si node existe  → modo detalle/edición con cancelar subrama
        """
        is_create = node is None

        def on_save(updated_node: FlightNode):
            # Guardar snapshot ANTES de la operación
            self._push_history("INSERT" if is_create else "UPDATE",
                               updated_node.code)
            if is_create:
                self.avl_tree.insert(updated_node)
                self.set_status(f"✓ Vuelo {updated_node.code} agregado correctamente", True)
            else:
                self._avl_delete(node.code)
                self.avl_tree.insert(updated_node)
                self.set_status(f"✓ Vuelo {updated_node.code} actualizado", True)
            self.flight_modal = None

        def on_delete(deleted_node: FlightNode):
            if node is not None:
                self._push_history("DELETE", deleted_node.code)
                self._avl_delete(deleted_node.code)
                self.set_status(f"✓ Vuelo {deleted_node.code} eliminado", True)
            self.flight_modal = None

        def on_cancel_subtree(target_node: FlightNode):
            self._push_history("CANCEL_SUBTREE", target_node.code)
            count = self._avl_delete_subtree(target_node.code)
            if count > 0:
                self.set_status(
                    f"✓ Subrama de {target_node.code} cancelada "
                    f"({count} vuelo{'s' if count != 1 else ''} eliminado{'s' if count != 1 else ''})",
                    True
                )
            else:
                self.set_status(f"✗ No se encontró la subrama de {target_node.code}", False)
            self.flight_modal = None

        target_node = node if node is not None else FlightNode(
            code="", origin="", destination="",
            departure_time="00:00", base_price=0, passengers=0
        )

        self.flight_modal = FlightDetailModal(
            fonts=self.fonts,
            node=target_node,
            on_close=lambda: setattr(self, 'flight_modal', None),
            on_save=on_save,
            on_delete=on_delete if node is not None else None,
            on_cancel_subtree=on_cancel_subtree if node is not None else None,
            avl_tree=self.avl_tree,
        )
        self.flight_modal.show()

        # En modo creación: limpiar los campos que show() cargó del nodo vacío
        # y entrar directamente en modo edición para que se pueda escribir
        if is_create:
            for field in self.flight_modal._all_fields:
                field.value = ""
            self.flight_modal._enter_edit_mode()

    def _draw_flight_modal(self, surface: pygame.Surface):
        """Dibuja el modal si está visible."""
        if self.flight_modal and self.flight_modal.visible:
            self.flight_modal.draw(surface)

    # ------------------------------------------------------------------
    # Métodos de dibujo existentes (sin cambios)
    # ------------------------------------------------------------------

    def _draw_header(self, surface):
        title = self.fonts["title_lg"].render("AVL PRINCIPAL", True, LIGHT)
        surface.blit(title, (self.tree_rect.centerx - title.get_width() // 2, NAV_H + 20))

        subtitle = self.fonts["body_md"].render(
            "Gestión de vuelos con balanceo automático en tiempo real",
            True, TEXT_SECONDARY
        )
        surface.blit(subtitle, (self.tree_rect.centerx - subtitle.get_width() // 2, NAV_H + 58))

    def _draw_tree_area(self, surface):
        pygame.draw.rect(surface, BG_SURFACE, self.tree_rect, border_radius=CARD_RADIUS)

        title_box = pygame.Rect(self.tree_rect.x + 30, self.tree_rect.y + 12, 260, 48)
        pygame.draw.rect(surface, BG_SURFACE2, title_box, border_radius=10)
        pygame.draw.rect(surface, PRIMARY, title_box, width=3, border_radius=10)

        alpha = 90 + 40 * math.sin(pygame.time.get_ticks() / 500)
        border_col = (*PRIMARY[:3], int(alpha))
        pygame.draw.rect(surface, border_col, self.tree_rect.inflate(18, 18), width=4, border_radius=CARD_RADIUS + 4)

        self.renderer.draw(surface, self.avl_tree.getRoot())

        # Resaltar el nodo activo del recorrido con un halo amarillo
        if self._traversal_index >= 0 and self._traversal_index < len(self._traversal_result):
            active_node = self._traversal_result[self._traversal_index]
            self._draw_traversal_highlight(surface, active_node)

    def _draw_traversal_highlight(self, surface, target_node):
        """
        Dibuja un halo amarillo sobre el nodo activo del recorrido.
        Usa get_node_screen_pos() del renderer para obtener la posición exacta,
        respetando el zoom y scroll actuales.
        """
        if target_node is None:
            return
        pos = self.renderer.get_node_screen_pos(target_node.code)
        if pos is None:
            return
        r = max(18, int(22 * self.renderer.zoom))
        pygame.draw.circle(surface, (255, 220, 0), pos, r, 4)

    def _draw_right_panel(self, surface):
        pygame.draw.rect(surface, BG_SURFACE, self.panel_rect, border_radius=12)

        metrics_title = pygame.Rect(self.panel_rect.x + 20, self.panel_rect.y + 20, self.panel_rect.width - 40, 42)
        pygame.draw.rect(surface, BG_SURFACE2, metrics_title, border_radius=10)
        pygame.draw.rect(surface, PRIMARY, metrics_title, width=3, border_radius=10)

        title_surf = self.fonts["label_md"].render("MÉTRICAS", True, PRIMARY)
        surface.blit(title_surf, (metrics_title.x + 22, metrics_title.y + 11))

        self._draw_metrics_panel(surface)

    def _draw_metrics_panel(self, surface):
        y = self.panel_rect.y + 85
        w = self.panel_rect.width - 40

        metrics = [
            ("Altura", str(self.avl_tree.getHeight())),
            ("Nodos", str(self.avl_tree.nodeCount())),
            ("Hojas", str(self.avl_tree.countLeaves())),
            ("Rotaciones", str(self.avl_tree.totalRotations())),
            ("Cancelaciones", str(getattr(self.avl_tree, 'mass_cancellations', 0))),
        ]

        for label, value in metrics:
            rect = pygame.Rect(self.panel_rect.x + 20, y, w, 38)
            pygame.draw.rect(surface, BG_SURFACE2, rect, border_radius=8)
            lbl = self.fonts["body_sm"].render(label, True, TEXT_SECONDARY)
            val = self.fonts["label_md"].render(value, True, PRIMARY)
            surface.blit(lbl, (rect.x + 15, rect.y + 9))
            surface.blit(val, (rect.right - 20 - val.get_width(), rect.y + 9))
            y += 48

    def _draw_traversals_bar(self, surface):
        # Etiqueta
        lbl = self.fonts["body_sm"].render("RECORRIDOS", True, TEXT_DIM)
        surface.blit(lbl, (self.tree_rect.x, self.tree_rect.bottom + 4))

        # Resaltar el botón del recorrido activo
        active_colors = {
            "inorder":   self.trav_in,
            "preorder":  self.trav_pre,
            "postorder": self.trav_post,
            "bfs":       self.trav_bfs,
        }
        for key, btn in active_colors.items():
            if self._traversal_index >= 0 and self._traversal_type == key:
                pygame.draw.rect(surface, PRIMARY, btn.rect, border_radius=8)
            btn.draw(surface)

    def _restore_version(self, name: str):
        """
        Restaura el árbol desde una versión guardada.
        Limpia cualquier recorrido activo para evitar confusiones visuales.
        """
        snapshot = self._version_manager.restoreVersion(name)
        if snapshot is None:
            self.set_status(f"✗ Versión '{name}' no encontrada", False)
            return

        # Guardar en historial antes de restaurar
        self._push_history("RESTORE", name)

        # Restaurar el estado completo del árbol
        restored = copy.deepcopy(snapshot)
        self.avl_tree.root                = restored.root
        self.avl_tree.critical_depth      = getattr(restored, 'critical_depth', 0)
        self.avl_tree.rotations_ll        = getattr(restored, 'rotations_ll', 0)
        self.avl_tree.rotations_rr        = getattr(restored, 'rotations_rr', 0)
        self.avl_tree.rotations_lr        = getattr(restored, 'rotations_lr', 0)
        self.avl_tree.rotations_rl        = getattr(restored, 'rotations_rl', 0)
        self.avl_tree.mass_cancellations  = getattr(restored, 'mass_cancellations', 0)

        # Limpiar recorrido activo (importante)
        self._traversal_result = []
        self._traversal_type = ""
        self._traversal_index = -1

        self._versions_panel_visible = False
        self.set_status(f"✓ Versión '{name}' restaurada correctamente", True)

    def _draw_versions_panel(self, surface: pygame.Surface):
        """
        Panel flotante que lista todas las versiones guardadas.
        Se dibuja sobre el panel derecho, con botón de restaurar por cada versión.
        """
        versions = self._version_manager.getVersions()

        panel_w = self.panel_rect.width
        row_h   = 44
        header_h = 40
        panel_h = header_h + max(1, len(versions)) * row_h + 50
        px = self.panel_rect.x
        py = self.panel_rect.y

        # Fondo
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((30, 34, 54, 240))
        pygame.draw.rect(panel_surf, PRIMARY, pygame.Rect(0, 0, panel_w, panel_h),
                         2, border_radius=12)
        surface.blit(panel_surf, (px, py))

        font_title = self.fonts["label_md"]
        font_body  = self.fonts["body_sm"]

        # Título
        title = font_title.render("VERSIONES GUARDADAS", True, PRIMARY)
        surface.blit(title, (px + 14, py + 10))

        # Botón cerrar (×)
        close_rect = pygame.Rect(px + panel_w - 30, py + 8, 22, 22)
        pygame.draw.rect(surface, CRITICAL, close_rect, border_radius=5)
        x_surf = font_body.render("✕", True, (255, 255, 255))
        surface.blit(x_surf, (close_rect.x + 4, close_rect.y + 2))
        # Registrar rect para handle_event
        self._versions_close_rect = close_rect

        if not versions:
            msg = font_body.render("No hay versiones guardadas", True, TEXT_DIM)
            surface.blit(msg, (px + 14, py + header_h + 10))
            return

        # Filas de versiones
        self._version_restore_rects = []
        for i, v in enumerate(versions):
            row_y = py + header_h + i * row_h
            # Fondo alternado
            if i % 2 == 0:
                row_surf = pygame.Surface((panel_w, row_h), pygame.SRCALPHA)
                row_surf.fill((255, 255, 255, 15))
                surface.blit(row_surf, (px, row_y))

            name_surf = font_body.render(v["name"], True, LIGHT)
            ts_surf   = font_body.render(v["timestamp"], True, TEXT_DIM)
            surface.blit(name_surf, (px + 12, row_y + 4))
            surface.blit(ts_surf,   (px + 12, row_y + 22))

            # Botón restaurar
            btn_rect = pygame.Rect(px + panel_w - 80, row_y + 10, 68, 24)
            pygame.draw.rect(surface, PRIMARY, btn_rect, border_radius=6)
            btn_surf = font_body.render("Restaurar", True, (255, 255, 255))
            surface.blit(btn_surf, (btn_rect.x + 4, btn_rect.y + 4))
            self._version_restore_rects.append((btn_rect, v["name"]))
        """Dibuja la barra de estado en la zona inferior derecha del panel."""
        if not self._status:
            return
        color = PRIMARY if self._status_ok else CRITICAL
        # Posición: debajo del panel derecho, alineada con él
        status_surf = self.fonts["body_sm"].render(self._status, True, color)
        # Recortar si es muy largo
        max_w = self.panel_rect.width
        if status_surf.get_width() > max_w:
            # Truncar y redibujar
            chars = self._status
            while len(chars) > 10:
                chars = chars[:-1]
                status_surf = self.fonts["body_sm"].render(chars + "…", True, color)
                if status_surf.get_width() <= max_w:
                    break
        sx = self.panel_rect.x
        sy = self.panel_rect.bottom + 8
        surface.blit(status_surf, (sx, sy))

    def _draw_status_bar(self, surface: pygame.Surface):
        """
        Strategy:
            Dibuja un mensaje de estado en la parte inferior del panel derecho.
            Método pequeño y de única responsabilidad.
            Trunca el texto si es demasiado largo.
        """
        if not self._status:
            return

        color = PRIMARY if self._status_ok else CRITICAL
        status_surf = self.fonts["body_sm"].render(self._status, True, color)

        # Truncar si es muy largo
        max_w = self.panel_rect.width - 40
        if status_surf.get_width() > max_w:
            chars = self._status
            while status_surf.get_width() > max_w and len(chars) > 10:
                chars = chars[:-1]
                status_surf = self.fonts["body_sm"].render(chars + "…", True, color)

        # Posición: justo debajo del panel derecho
        sx = self.panel_rect.x + 20
        sy = self.panel_rect.bottom + 12
        surface.blit(status_surf, (sx, sy))

    def _on_version_restored(self):
        """Limpia el cache de posiciones del renderer tras restaurar una version.
        Evita KeyError en get_node_at cuando el nuevo arbol tiene nodos distintos."""
        self.renderer._positions = {}
        # Limpiar recorrido activo para evitar indices invalidos
        self._traversal_result = []
        self._traversal_type = ""
        self._traversal_index = -1

    def set_status(self, message: str, success: bool = True):
        self._status = message
        self._status_ok = success

    def reset_stress_toggle(self):
        """Resetea el toggle de Modo Estrés a OFF (llamar al volver de StressScreen)."""
        self.stress_enabled = False
        self.stress_toggle.state = False
        self.avl_tree.disableStressMode()
        self.set_status("Modo Normal activado", True)