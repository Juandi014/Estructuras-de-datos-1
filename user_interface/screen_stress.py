import copy
import math
import time

import pygame
from user_interface.color_scheme import (
    BG_DEEP, BG_SURFACE, BG_SURFACE2, BORDER, PRIMARY, LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DIM, CRITICAL,
    WINDOW_W, WINDOW_H, NAV_H, BTN_H, CARD_RADIUS
)
from user_interface.tree_renderer import TreeRenderer
from user_interface.panel_ui import UIButton
from user_interface.flight_detail_modal import FlightDetailModal
from models.flight_node import FlightNode

try:
    from logic.history_stack import HistoryStack
except ImportError:
    from history_stack import HistoryStack


class StressScreen:
    def __init__(self, fonts: dict, avl_tree, on_switch_to_main):
        self.fonts = fonts
        self.avl_tree = avl_tree
        self.on_switch_to_main = on_switch_to_main

        # Tree area - mismo estilo que MainScreen
        self.tree_rect = pygame.Rect(40, NAV_H + 105, int(WINDOW_W * 0.68), WINDOW_H - NAV_H - 265)
        self.renderer = TreeRenderer(self.tree_rect)

        # Modo Estrés siempre activo al entrar en esta pantalla
        self.stress_enabled = True
        self.avl_tree.enableStressMode()

        self._status = ""
        self._status_ok = True
        self._rebalance_cost = 0
        self._avl_report = ""
        self._show_report = False

        # Historial interno (mismo patrón que MainScreen)
        self._history = HistoryStack()

        # Modal de vuelo
        self.flight_modal = None

        # Nodo seleccionado (para editar/eliminar/cancelar sin modal)
        self._selected_node = None

        # === Control del panel de reparación ===
        self._show_repair_stats = False
        self.rotation_stats = {"LL": 0, "RR": 0, "LR": 0, "RL": 0, "total": 0}

        # Animación de rotaciones
        self._pulse_nodes = []
        self._pulse_start = 0
        self._pulse_offset = 0.0

        # Estado de recorrido activo (igual que MainScreen)
        self._traversal_result = []
        self._traversal_type = ""
        self._traversal_index = -1
        self._traversal_timer = 0.0
        self._traversal_step_ms = 600

        self._init_ui()

    def on_enter(self):
        """
        Must be called every time this screen becomes the active screen.
        Re-enables stress mode in case the user returned from MainScreen,
        which calls disableStressMode() on exit.
        """
        self.avl_tree.enableStressMode()
        self.stress_enabled = True
        self.renderer._positions = {}
        self._traversal_result  = []
        self._traversal_type    = ""
        self._traversal_index   = -1
        self._show_report       = False
        self._show_repair_stats = False

    # ------------------------------------------------------------------
    # Inicialización de UI
    # ------------------------------------------------------------------

    def _init_ui(self):
        # Panel derecho
        self.panel_rect = pygame.Rect(
            self.tree_rect.right + 30,
            NAV_H + 95,
            310,
            WINDOW_H - NAV_H - 345
        )

        btn_x = self.panel_rect.x
        btn_w = self.panel_rect.width
        btn_h = 36

        # ── Botones del panel derecho (alineados igual que screen_main) ──

        btn_y = self.panel_rect.bottom + 25

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

        self.btn_verify = UIButton(
            rect=pygame.Rect(btn_x, btn_y, btn_w, btn_h),
            text="🔍 Verificar Propiedad AVL",
            font=self.fonts["label_md"],
            bg_color=BG_SURFACE2,
            text_color=PRIMARY,
            border_color=PRIMARY,
            callback=self._verify_avl_property
        )
        btn_y += btn_h + 8

        self.btn_rebalance = UIButton(
            rect=pygame.Rect(btn_x, btn_y, btn_w, btn_h),
            text="⚖ Rebalanceo Global",
            font=self.fonts["label_md"],
            bg_color=BG_SURFACE2,
            text_color=PRIMARY,
            border_color=PRIMARY,
            callback=self._execute_global_rebalance
        )
        btn_y += btn_h + 8

        self.btn_hide_report = UIButton(
            rect=pygame.Rect(btn_x, btn_y, btn_w, btn_h),
            text="✕ Ocultar Reporte",
            font=self.fonts["label_md"],
            bg_color=BG_SURFACE2,
            text_color=CRITICAL,
            border_color=CRITICAL,
            callback=self._hide_report
        )
        btn_y += btn_h + 8

        self.btn_back_to_stress = UIButton(
            rect=pygame.Rect(btn_x, btn_y, btn_w, btn_h),
            text="↩ Volver a Modo Estrés",
            font=self.fonts["label_md"],
            bg_color=BG_SURFACE2,
            text_color=LIGHT,
            border_color=LIGHT,
            callback=self._back_to_stress_mode
        )
        btn_y += btn_h + 8

        self.btn_back = UIButton(
            rect=pygame.Rect(btn_x, btn_y, btn_w, btn_h),
            text="← Volver a Home",
            font=self.fonts["label_md"],
            bg_color=BG_DEEP,
            text_color=TEXT_SECONDARY,
            border_color=BORDER,
            callback=self._return_to_main
        )

        # ── Barra de recorridos (bajo el árbol, igual que screen_main) ──
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
            rect=pygame.Rect(self.tree_rect.x + (trav_w + 20) * 2, trav_y, trav_w, 34),
            text="Post-Order",
            font=self.fonts["label_sm"],
            bg_color=BG_SURFACE2,
            text_color=TEXT_SECONDARY,
            border_color=BORDER,
            callback=lambda: self._show_traversal("postorder")
        )
        self.trav_bfs = UIButton(
            rect=pygame.Rect(self.tree_rect.x + (trav_w + 20) * 3, trav_y, trav_w, 34),
            text="Anchura (BFS)",
            font=self.fonts["label_sm"],
            bg_color=BG_SURFACE2,
            text_color=TEXT_SECONDARY,
            border_color=BORDER,
            callback=lambda: self._show_traversal("bfs")
        )

    # ------------------------------------------------------------------
    # Historial
    # ------------------------------------------------------------------

    def _push_history(self, action: str, code):
        """Guarda snapshot del árbol en el historial."""
        snapshot = copy.deepcopy(self.avl_tree)
        self._history.push(action, code, snapshot)

    # ------------------------------------------------------------------
    # Helpers de árbol (igual que screen_main)
    # ------------------------------------------------------------------

    def _avl_delete(self, code):
        if hasattr(self.avl_tree, 'delete'):
            self.avl_tree.delete(code)
        elif hasattr(self.avl_tree, 'deleteNode'):
            self.avl_tree.deleteNode(code)
        elif hasattr(self.avl_tree, 'remove'):
            self.avl_tree.remove(code)

    def _avl_delete_subtree(self, code) -> int:
        if hasattr(self.avl_tree, 'cancelSubtree'):
            return self.avl_tree.cancelSubtree(code) or 0
        elif hasattr(self.avl_tree, 'delete_subtree'):
            return self.avl_tree.delete_subtree(code) or 0
        elif hasattr(self.avl_tree, 'deleteSubtree'):
            return self.avl_tree.deleteSubtree(code) or 0
        return 0

    # ------------------------------------------------------------------
    # Callbacks principales
    # ------------------------------------------------------------------

    def _do_add(self):
        """Abre el modal de creación de vuelo (igual que screen_main)."""
        self._open_flight_detail_modal(None)

    def _do_undo(self):
        """Restaura el árbol al estado anterior."""
        entry = self._history.pop()
        if entry is None:
            self.set_status("✗ No hay acciones para deshacer", False)
            return
        # Restaurar snapshot — conservar stress_mode activo
        self.avl_tree.root = copy.deepcopy(entry["snapshot"].root)
        self.avl_tree.critical_depth = entry["snapshot"].critical_depth
        self.avl_tree.rotations_ll = entry["snapshot"].rotations_ll
        self.avl_tree.rotations_rr = entry["snapshot"].rotations_rr
        self.avl_tree.rotations_lr = entry["snapshot"].rotations_lr
        self.avl_tree.rotations_rl = entry["snapshot"].rotations_rl
        self.avl_tree.mass_cancellations = entry["snapshot"].mass_cancellations
        # Mantener el modo estrés activo después de deshacer
        self.avl_tree.enableStressMode()
        self._traversal_result = []
        self._traversal_type = ""
        self._traversal_index = -1
        self.set_status(f"✓ Deshecho: {entry['action']} ({entry['code']})", True)

    def _verify_avl_property(self):
        report = self.avl_tree.verifyAvlProperty()
        if report["is_valid"]:
            self._avl_report = "✅ Propiedad AVL VÁLIDA\nTodos los nodos tienen |bf| ≤ 1."
        else:
            lines = [f" {len(report['invalid_nodes'])} nodo(s) inconsistente(s):"]
            for v in report["invalid_nodes"]:
                issues = []
                if not v.get("bf_ok", True):
                    issues.append(f"bf={v['balance_factor']}")
                if not v.get("h_ok", True):
                    issues.append(f"h={v['height']}≠{v['expected_height']}")
                lines.append(f"  [{v['code']}] prof={v['depth']} | {', '.join(issues)}")
            self._avl_report = "\n".join(lines)
        self._show_report = True
        self.set_status("Verificación AVL completada", True)

    def _hide_report(self):
        self._show_report = False
        self._avl_report = ""

    def _execute_global_rebalance(self):
        """Rebalanceo global: aplica rotaciones AVL reales (LL/RR/LR/RL) en post-order sobre el árbol desbalanceado."""
        rotations_before = self.avl_tree.totalRotations()

        # globalRebalance() ya maneja stress_mode internamente: lo desactiva, rota, lo restaura.
        # Cuenta cada rotacion en rotations_ll/rr/lr/rl correctamente.
        self.avl_tree.globalRebalance()

        rotations_after = self.avl_tree.totalRotations()
        self._rebalance_cost = rotations_after - rotations_before

        self.rotation_stats = {
            "LL": self.avl_tree.rotations_ll,
            "RR": self.avl_tree.rotations_rr,
            "LR": self.avl_tree.rotations_lr,
            "RL": self.avl_tree.rotations_rl,
            "total": rotations_after
        }

        # Animación de rotaciones (marcar todos los nodos como "recién rotados" para la animación)
        self._pulse_nodes = [n.code for n in self.avl_tree.breadthFirstSearch()]
        self._pulse_start = time.time()
        self._pulse_offset = 0.0

        # Limpiar recorrido activo
        self._traversal_result = []
        self._traversal_type = ""
        self._traversal_index = -1

        self._show_repair_stats = True
        self.set_status(
            f"Rebalanceo global completado. Costo: {self._rebalance_cost} rotaciones. Árbol completamente balanceado.", True
        )

    def _back_to_stress_mode(self):
        """Vuelve al modo estrés (oculta estadísticas y muestra métricas normales)."""
        self._show_repair_stats = False
        self.set_status("Regresando a Modo Estrés", True)

    def _return_to_main(self):
        """Desactiva el Modo Estrés en el árbol y regresa a MainScreen."""
        self.stress_enabled = False
        self.avl_tree.disableStressMode()
        if isinstance(self.on_switch_to_main, tuple):
            callback, main_screen = self.on_switch_to_main
            if hasattr(main_screen, 'reset_stress_toggle'):
                main_screen.reset_stress_toggle()
            callback()
        else:
            self.on_switch_to_main()

    # ------------------------------------------------------------------
    # Modal de vuelo (portado directamente de screen_main)
    # ------------------------------------------------------------------

    def _open_flight_detail_modal(self, node: FlightNode = None):
            is_create = node is None

            def on_save(updated_node: FlightNode):
                self.avl_tree.enableStressMode()
                self._push_history("INSERT" if is_create else "UPDATE", updated_node.code)
                if is_create:
                    self.avl_tree.insert(updated_node)
                    self.set_status(f"✓ Vuelo {updated_node.code} agregado", True)
                else:
                    self._avl_delete(node.code)
                    self.avl_tree.insert(updated_node)
                    self.set_status(f"✓ Vuelo {updated_node.code} actualizado", True)
                self.flight_modal   = None
                self._selected_node = None

            def on_delete(deleted_node: FlightNode):
                if node is not None:
                    self.avl_tree.enableStressMode()
                    self._push_history("DELETE", deleted_node.code)
                    self._avl_delete(deleted_node.code)
                    self.set_status(f"✓ Vuelo {deleted_node.code} eliminado", True)
                self.flight_modal   = None
                self._selected_node = None

            def on_cancel_subtree(target_node: FlightNode):
                self.avl_tree.enableStressMode()
                self._push_history("CANCEL_SUBTREE", target_node.code)
                count = self._avl_delete_subtree(target_node.code)
                if count > 0:
                    self.set_status(
                        f"✓ Subrama de {target_node.code} cancelada "
                        f"({count} vuelo{'s' if count != 1 else ''} eliminado{'s' if count != 1 else ''})",
                        True,
                    )
                else:
                    self.set_status(f"✓ Subrama de {target_node.code} cancelada", True)
                self.flight_modal   = None
                self._selected_node = None

            # ── ESTE BLOQUE ES EL QUE FALTA ──────────────────────────────────
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

            # En modo creación: limpiar campos y abrir directo en edición
            if is_create:
                for field in self.flight_modal._all_fields:
                    field.value = ""
                self.flight_modal._enter_edit_mode()
            # ─────────────────────────────────────────────────────────────────
    # ------------------------------------------------------------------
    # Recorridos (portado de screen_main)
    # ------------------------------------------------------------------

    def _show_traversal(self, trav_type: str):
        """
        Inicia un recorrido animado del árbol.
        Si el mismo recorrido ya está activo, lo detiene (toggle).
        """
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

        label = {
            "inorder": "In-Order", "preorder": "Pre-Order",
            "postorder": "Post-Order", "bfs": "Anchura BFS"
        }.get(trav_type, trav_type)
        codes = " → ".join(str(n.code) for n in nodes)
        self.set_status(f"▶ {label}: {codes}", True)

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
    # Eventos
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event):
    # Garantía defensiva: stress_mode siempre activo en esta pantalla
        if not self.avl_tree.stress_mode:
            self.avl_tree.enableStressMode()

        # Prioridad 1: Modal de vuelo
        if self.flight_modal and self.flight_modal.visible:
            self.flight_modal.handle_event(event)
            return

        # Eventos del renderer (zoom, drag)
        self.renderer.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked_node = self.renderer.get_node_at(event.pos, self.avl_tree.getRoot())
            if clicked_node:
                self._selected_node = clicked_node
                self._open_flight_detail_modal(clicked_node)
                return

            if self.btn_add.rect.collidepoint(event.pos):
                self._do_add()
            elif self.btn_undo.rect.collidepoint(event.pos):
                self._do_undo()
            elif self.btn_verify.rect.collidepoint(event.pos):
                self._verify_avl_property()
            elif self.btn_rebalance.rect.collidepoint(event.pos):
                self._execute_global_rebalance()
            elif self._show_report and self.btn_hide_report.rect.collidepoint(event.pos):
                self._hide_report()
            elif self._show_repair_stats and self.btn_back_to_stress.rect.collidepoint(event.pos):
                self._back_to_stress_mode()
            elif self.btn_back.rect.collidepoint(event.pos):
                self._return_to_main()
            elif not self._show_repair_stats:
                if self.trav_in.rect.collidepoint(event.pos):
                    self._show_traversal("inorder")
                elif self.trav_pre.rect.collidepoint(event.pos):
                    self._show_traversal("preorder")
                elif self.trav_post.rect.collidepoint(event.pos):
                    self._show_traversal("postorder")
                elif self.trav_bfs.rect.collidepoint(event.pos):
                    self._show_traversal("bfs")

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_z and (event.mod & pygame.KMOD_CTRL):
                self._do_undo()

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt_ms: float):
    # Garantía defensiva en cada frame
        if not self.avl_tree.stress_mode:
            self.avl_tree.enableStressMode()

        # Animación de rotaciones
        if self._pulse_nodes:
            elapsed = time.time() - self._pulse_start
            if elapsed > 2.5:
                self._pulse_nodes = []
                self._pulse_offset = 0.0
            else:
                self._pulse_offset = 14 * math.sin(elapsed * 6)

        # Animación de recorrido
        if self._traversal_index >= 0 and self._traversal_result:
            self._traversal_timer += dt_ms
            if self._traversal_timer >= self._traversal_step_ms:
                self._traversal_timer = 0.0
                self._traversal_index += 1
                if self._traversal_index >= len(self._traversal_result):
                    self._traversal_index = -1

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface):
        surface.fill(BG_DEEP)

        self._draw_header(surface)
        self._draw_tree_area(surface)
        self._draw_right_panel(surface)

        # Botones del panel derecho
        self.btn_add.draw(surface)
        self.btn_undo.draw(surface)
        self.btn_verify.draw(surface)
        self.btn_rebalance.draw(surface)
        self.btn_back.draw(surface)

        if self._show_report:
            self.btn_hide_report.draw(surface)
            self._draw_report(surface)

        if self._show_repair_stats:
            self.btn_back_to_stress.draw(surface)

        # Barra de recorridos y overlay (solo si no está en modo reparación)
        if not self._show_repair_stats:
            self._draw_traversals_bar(surface)

        if self._traversal_index >= 0 and self._traversal_result:
            self._draw_traversal_sequence_overlay(surface)

        self._draw_status_bar(surface)

        # Modal siempre al final
        if self.flight_modal and self.flight_modal.visible:
            self.flight_modal.draw(surface)

    def _draw_header(self, surface):
        title = self.fonts["title_lg"].render("MODO ESTRÉS", True, CRITICAL)
        surface.blit(title, (self.tree_rect.centerx - title.get_width() // 2, NAV_H + 20))

        subtitle = self.fonts["body_md"].render(
            "Rebalanceo diferido y degradación controlada",
            True, TEXT_SECONDARY
        )
        surface.blit(subtitle, (self.tree_rect.centerx - subtitle.get_width() // 2, NAV_H + 58))

    def _draw_tree_area(self, surface):
        # Expandir el área del árbol cuando estamos en modo reparación
        tree_h = (
            WINDOW_H - NAV_H - 265
            if not self._show_repair_stats
            else WINDOW_H - NAV_H - 120
        )
        self.tree_rect.height = tree_h

        pygame.draw.rect(surface, BG_SURFACE, self.tree_rect, border_radius=CARD_RADIUS)

        title_box = pygame.Rect(self.tree_rect.x + 30, self.tree_rect.y + 12, 260, 48)
        pygame.draw.rect(surface, BG_SURFACE2, title_box, border_radius=10)
        pygame.draw.rect(surface, PRIMARY, title_box, width=3, border_radius=10)

        title = self.fonts["label_md"].render("ÁRBOL EN MODO ESTRÉS", True, CRITICAL)
        surface.blit(title, (title_box.x + 25, title_box.y + 14))

        alpha = 90 + 40 * math.sin(pygame.time.get_ticks() / 500)
        border_col = (*CRITICAL[:3], int(alpha))
        pygame.draw.rect(
            surface, border_col,
            self.tree_rect.inflate(18, 18), width=4, border_radius=CARD_RADIUS + 4
        )

        # Pasar animación al renderer
        self.renderer._pulse_nodes = self._pulse_nodes
        self.renderer._pulse_offset = self._pulse_offset

        self.renderer.draw(surface, self.avl_tree.getRoot(), stress_mode=self.stress_enabled)

        # Resaltar nodo activo del recorrido
        if self._traversal_index >= 0 and self._traversal_index < len(self._traversal_result):
            active_node = self._traversal_result[self._traversal_index]
            self._draw_traversal_highlight(surface, active_node)

    def _draw_traversal_highlight(self, surface, target_node):
        """Halo amarillo sobre el nodo activo del recorrido."""
        if target_node is None:
            return
        pos = self.renderer.get_node_screen_pos(target_node.code)
        if pos is None:
            return
        r = max(18, int(22 * self.renderer.zoom))
        pygame.draw.circle(surface, (255, 220, 0), pos, r, 4)

    def _draw_right_panel(self, surface):
        pygame.draw.rect(surface, BG_SURFACE, self.panel_rect, border_radius=12)

        if self._show_repair_stats:
            self._draw_repair_stats_panel(surface)
        else:
            self._draw_metrics_panel(surface)

    def _draw_repair_stats_panel(self, surface):
        title_rect = pygame.Rect(
            self.panel_rect.x + 20, self.panel_rect.y + 20,
            self.panel_rect.width - 40, 42
        )
        pygame.draw.rect(surface, BG_SURFACE2, title_rect, border_radius=10)
        pygame.draw.rect(surface, PRIMARY, title_rect, width=3, border_radius=10)
        title_surf = self.fonts["label_md"].render("ESTADÍSTICAS DE REPARACIÓN", True, PRIMARY)
        surface.blit(title_surf, (title_rect.x + 22, title_rect.y + 11))

        y = self.panel_rect.y + 85
        cost_text = f"Rotaciones totales: {self.rotation_stats['total']}"
        cost_surf = self.fonts["label_md"].render(cost_text, True, LIGHT)
        surface.blit(cost_surf, (self.panel_rect.x + 25, y))
        y += 45

        self._draw_rotation_bar_chart(surface, y, self.panel_rect)

    def _draw_rotation_bar_chart(self, surface, start_y, panel_rect):
        """Gráfica de barras con etiquetas y valores."""
        bar_width = 38
        max_h = 110
        x = panel_rect.x + 30
        types = ["LL", "RR", "LR", "RL"]
        colors = [PRIMARY, PRIMARY, CRITICAL, CRITICAL]
        values = [self.rotation_stats[t] for t in types]
        max_val = max(values) if any(values) else 1

        for i, (typ, val) in enumerate(zip(types, values)):
            h = int((val / max_val) * max_h) if max_val > 0 else 0
            bar_rect = pygame.Rect(
                x + i * (bar_width + 18), start_y + max_h - h, bar_width, h
            )
            pygame.draw.rect(surface, colors[i], bar_rect)

            val_surf = self.fonts["body_sm"].render(str(val), True, LIGHT)
            surface.blit(
                val_surf,
                (bar_rect.centerx - val_surf.get_width() // 2, bar_rect.y - 20)
            )

            lbl = self.fonts["label_sm"].render(typ, True, TEXT_PRIMARY)
            surface.blit(
                lbl,
                (bar_rect.centerx - lbl.get_width() // 2, start_y + max_h + 12)
            )

    def _draw_metrics_panel(self, surface):
        y = self.panel_rect.y + 85
        w = self.panel_rect.width - 40

        # Título
        metrics_title = pygame.Rect(self.panel_rect.x + 20, self.panel_rect.y + 20, w, 42)
        pygame.draw.rect(surface, BG_SURFACE2, metrics_title, border_radius=10)
        pygame.draw.rect(surface, PRIMARY, metrics_title, width=3, border_radius=10)
        title_surf = self.fonts["label_md"].render("MÉTRICAS", True, PRIMARY)
        surface.blit(title_surf, (metrics_title.x + 22, metrics_title.y + 11))

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

    def _draw_report(self, surface):
        lines   = self._avl_report.split("\n")
        line_h  = 22
        panel_h = 20 + len(lines) * line_h

        report_rect = pygame.Rect(
            self.panel_rect.x + 20,
            self.panel_rect.y + 330,
            self.panel_rect.width - 40,
            max(70, panel_h),
        )
        pygame.draw.rect(surface, BG_SURFACE2, report_rect, border_radius=10)
        pygame.draw.rect(surface, CRITICAL,    report_rect, width=2, border_radius=10)

        y = report_rect.y + 12
        for line in lines:
            if "VÁLIDA" in line:
                color = PRIMARY
            elif line.startswith("❌") or line.startswith("  ["):
                color = CRITICAL
            else:
                color = TEXT_PRIMARY
            txt = self.fonts["body_sm"].render(line, True, color)
            surface.blit(txt, (report_rect.x + 12, y))
            y += line_h

    def _draw_traversals_bar(self, surface):
        """Barra de recorridos con etiqueta y resaltado del activo."""
        lbl = self.fonts["body_sm"].render("RECORRIDOS", True, TEXT_DIM)
        surface.blit(lbl, (self.tree_rect.x, self.tree_rect.bottom + 4))

        active_map = {
            "inorder": self.trav_in,
            "preorder": self.trav_pre,
            "postorder": self.trav_post,
            "bfs": self.trav_bfs,
        }
        for key, btn in active_map.items():
            if self._traversal_index >= 0 and self._traversal_type == key:
                pygame.draw.rect(surface, PRIMARY, btn.rect, border_radius=8)
            btn.draw(surface)

    def _draw_traversal_sequence_overlay(self, surface: pygame.Surface):
        """Overlay semitransparente con la secuencia del recorrido activo."""
        if not self._traversal_result or self._traversal_index < 0:
            return

        label_map = {
            "inorder": "IN-ORDER",
            "preorder": "PRE-ORDER",
            "postorder": "POST-ORDER",
            "bfs": "ANCHURA (BFS)"
        }
        label = label_map.get(self._traversal_type, self._traversal_type.upper())

        overlay_h = 54
        overlay_rect = pygame.Rect(
            self.tree_rect.x,
            self.tree_rect.bottom - overlay_h,
            self.tree_rect.width,
            overlay_h
        )

        overlay_surf = pygame.Surface((overlay_rect.w, overlay_rect.h), pygame.SRCALPHA)
        overlay_surf.fill((20, 20, 35, 200))
        surface.blit(overlay_surf, overlay_rect.topleft)

        font_lbl = self.fonts["body_sm"]
        font_code = self.fonts["label_sm"]

        title_surf = font_lbl.render(f"▶ {label}", True, (255, 220, 0))
        surface.blit(title_surf, (overlay_rect.x + 12, overlay_rect.y + 6))

        x = overlay_rect.x + 12
        y = overlay_rect.y + 28
        max_x = overlay_rect.right - 12

        for i, node in enumerate(self._traversal_result):
            is_active = (i == self._traversal_index)
            is_done = (i < self._traversal_index)

            color = (255, 220, 0) if is_active else \
                    ((120, 200, 120) if is_done else (180, 180, 200))

            code_surf = font_code.render(str(node.code), True, color)

            if x + code_surf.get_width() + 12 > max_x:
                break

            surface.blit(code_surf, (x, y))
            x += code_surf.get_width() + 6

            if i < len(self._traversal_result) - 1:
                arrow = font_code.render("→", True, (80, 80, 100))
                surface.blit(arrow, (x, y))
                x += arrow.get_width() + 4

    def _draw_status_bar(self, surface: pygame.Surface):
        """Barra de estado en la parte inferior del panel derecho."""
        if not self._status:
            return

        color = PRIMARY if self._status_ok else CRITICAL
        status_surf = self.fonts["body_sm"].render(self._status, True, color)

        max_w = self.panel_rect.width - 40
        if status_surf.get_width() > max_w:
            chars = self._status
            while status_surf.get_width() > max_w and len(chars) > 10:
                chars = chars[:-1]
                status_surf = self.fonts["body_sm"].render(chars + "…", True, color)

        sx = self.panel_rect.x + 20
        sy = self.panel_rect.bottom + 12
        surface.blit(status_surf, (sx, sy))

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def set_status(self, message: str, success: bool = True):
        self._status = message
        self._status_ok = success