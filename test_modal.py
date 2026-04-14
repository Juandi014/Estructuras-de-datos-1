"""
test_modal.py
-------------
Prueba rápida del FlightDetailModal sin tocar el resto del proyecto.
"""

import pygame
import sys
from models.flight_node import FlightNode
from user_interface.flight_detail_modal import FlightDetailModal
from user_interface.color_scheme import load_fonts

# ====================== CONFIGURACIÓN ======================
pygame.init()
WINDOW_W, WINDOW_H = 1280, 720
surface = pygame.display.set_mode((WINDOW_W, WINDOW_H))
pygame.display.set_caption("Prueba Modal - FlightDetailModal")
clock = pygame.time.Clock()
fonts = load_fonts()

# Crear un nodo de prueba
test_node = FlightNode(
    code="SB400",
    origin="Medellín",
    destination="Cartagena",
    departure_time="10:00",
    base_price=400,
    passengers=120,
    promotion=True,
    alert=False,
    priority=3
)

# Callback vacío para prueba
def on_close():
    print("Modal cerrado")

def on_save(node):
    print(f"Guardado: {node.code} - {node.origin} → {node.destination}")

def on_delete(node):
    print(f"Eliminado: {node.code}")

# Crear el modal
modal = FlightDetailModal(
    fonts=fonts,
    node=test_node,
    on_close=on_close,
    on_save=on_save,
    on_delete=on_delete
)

modal.show()

# ====================== BUCLE PRINCIPAL ======================
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

        modal.handle_event(event)

    # Fondo
    surface.fill((14, 11, 8))

    # Dibujar el modal
    modal.draw(surface)

    # Instrucciones en pantalla
    font = fonts.get("label_md")
    instr = font.render("Haz clic en 'EDITAR VUELO' para probar el modo edición", True, (248, 250, 229))
    surface.blit(instr, (50, 30))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()