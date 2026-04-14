"""
background_animation.py
-----------------------
Animación de fondo temática de aerolínea para SkyBalance.
Versión sin grid (solo scan line, aviones y blips).
Usa el color claro de la paleta (LIGHT).
"""

import pygame
import math
import random
from user_interface.color_scheme import LIGHT


class BackgroundAnimation:
    def __init__(self):
        self._scan_y = 0.0

        # Aviones que se mueven por la pantalla
        self._planes = []
        for _ in range(8):
            self._planes.append({
                'x': random.randint(-100, 1280),
                'y': random.randint(80, 720),
                'speed': random.uniform(0.4, 1.1),
                'angle': random.uniform(-0.3, 0.3),
                'size': random.randint(12, 18)
            })

        # Blips de radar
        self._blips = []
        for _ in range(15):
            self._blips.append({
                'x': random.randint(0, 1280),
                'y': random.randint(0, 720),
                'alpha': random.randint(40, 120),
                'life': random.randint(30, 90)
            })

    def update(self, dt_ms: float):
        self._scan_y += 0.15 * dt_ms
        if self._scan_y > 720:
            self._scan_y = 0

        # Actualizar aviones
        for plane in self._planes:
            plane['x'] += plane['speed'] * dt_ms
            plane['y'] += plane['angle'] * 0.4
            if plane['x'] > 1380:
                plane['x'] = -100
                plane['y'] = random.randint(80, 720)

        # Actualizar blips
        for blip in self._blips:
            blip['life'] -= 1
            if blip['life'] <= 0:
                blip['x'] = random.randint(0, 1280)
                blip['y'] = random.randint(0, 720)
                blip['life'] = random.randint(40, 100)
                blip['alpha'] = random.randint(40, 120)

    def draw(self, surface: pygame.Surface):
        w, h = surface.get_size()

        # Scan line suave (línea de radar)
        scan_surf = pygame.Surface((w, 2), pygame.SRCALPHA)
        scan_surf.fill((*LIGHT[:3], 35))
        surface.blit(scan_surf, (0, int(self._scan_y)))

        # Aviones pequeños
        for plane in self._planes:
            # Cuerpo
            pygame.draw.line(surface, LIGHT, 
                           (plane['x'], plane['y']), 
                           (plane['x'] + plane['size'], plane['y']), 2)
            # Alas
            pygame.draw.line(surface, LIGHT, 
                           (plane['x'] + plane['size']//2, plane['y'] - 5),
                           (plane['x'] + plane['size']//2, plane['y'] + 5), 2)

        # Blips de radar
        for blip in self._blips:
            color = (*LIGHT[:3], blip['alpha'])
            pygame.draw.circle(surface, color, (int(blip['x']), int(blip['y'])), 2)


# Instancia global
background_anim = BackgroundAnimation()