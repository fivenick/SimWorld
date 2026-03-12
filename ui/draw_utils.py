import pygame
import math
import random

from constants import PANEL_WIDTH, WINDOW_WIDTH, WINDOW_HEIGHT

_font_small = None
_font_mid   = None


def get_font_small():
    global _font_small
    if _font_small is None:
        _font_small = pygame.font.SysFont("microsoftyahei", 13)
    return _font_small


def get_font_mid():
    global _font_mid
    if _font_mid is None:
        _font_mid = pygame.font.SysFont("microsoftyahei", 20)
    return _font_mid


# ── Camera（自由漫游，WASD 移动视角）─────────────────

class Camera:
    def __init__(self):
        # 游戏区域宽度（去掉右侧面板）
        self.screen_w = WINDOW_WIDTH - PANEL_WIDTH
        self.screen_h = WINDOW_HEIGHT
        self.x = 0.0
        self.y = 0.0

    def move(self, dx, dy, world_w, world_h, speed):
        self.x = max(0, min(self.x + dx * speed, world_w - self.screen_w))
        self.y = max(0, min(self.y + dy * speed, world_h - self.screen_h))

    def center_on(self, wx, wy, world_w, world_h):
        self.x = max(0, min(wx - self.screen_w / 2, world_w - self.screen_w))
        self.y = max(0, min(wy - self.screen_h / 2, world_h - self.screen_h))

    def to_screen(self, wx, wy):
        return int(wx - self.x), int(wy - self.y)

    def in_view(self, wx, wy, margin=20):
        sx, sy = self.to_screen(wx, wy)
        return (-margin <= sx <= self.screen_w + margin and
                -margin <= sy <= self.screen_h + margin)


# ── 昼夜颜色 ──────────────────────────────────────────

def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def sky_color(t):
    noon   = (100, 160, 80)
    sunset = (160, 110, 60)
    night  = (20,  30,  20)
    if t < 0.25:
        return lerp_color(noon, sunset, t / 0.25)
    elif t < 0.5:
        return lerp_color(sunset, night, (t - 0.25) / 0.25)
    elif t < 0.75:
        return lerp_color(night, sunset, (t - 0.5) / 0.25)
    else:
        return lerp_color(sunset, noon, (t - 0.75) / 0.25)


def night_overlay_alpha(t):
    if 0.35 < t < 0.65:
        mid = abs(t - 0.5) / 0.15
        return int((1 - mid) * 160)
    return 0


# ── 地面噪点 ──────────────────────────────────────────

_GROUND_NOISE = None
_NOISE_CELL   = 16


def _build_ground_noise(world_w, world_h):
    global _GROUND_NOISE
    cols = world_w // _NOISE_CELL + 1
    rows = world_h // _NOISE_CELL + 1
    _GROUND_NOISE = [[random.randint(0, 18) for _ in range(cols)] for _ in range(rows)]


def draw_ground(surface, camera, day_t, world_w, world_h):
    global _GROUND_NOISE
    if _GROUND_NOISE is None:
        _build_ground_noise(world_w, world_h)

    base = sky_color(day_t)
    col0 = max(0, int(camera.x) // _NOISE_CELL)
    row0 = max(0, int(camera.y) // _NOISE_CELL)
    col1 = min(len(_GROUND_NOISE[0]) - 1, col0 + camera.screen_w // _NOISE_CELL + 2)
    row1 = min(len(_GROUND_NOISE)    - 1, row0 + camera.screen_h // _NOISE_CELL + 2)

    for row in range(row0, row1 + 1):
        for col in range(col0, col1 + 1):
            v  = _GROUND_NOISE[row][col]
            c  = (max(0, min(255, base[0] + v - 9)),
                  max(0, min(255, base[1] + v - 9)),
                  max(0, min(255, base[2] + v - 9)))
            sx = col * _NOISE_CELL - int(camera.x)
            sy = row * _NOISE_CELL - int(camera.y)
            surface.fill(c, (sx, sy, _NOISE_CELL, _NOISE_CELL))


# ── 道路 ──────────────────────────────────────────────

ROAD_COLOR_DAY   = (140, 130, 110)
ROAD_COLOR_NIGHT = (60,  55,  45)
ROAD_W = 12


def draw_roads(surface, camera, day_t, roads):
    t     = min(1.0, abs(day_t - 0.5) * 4)
    color = lerp_color(ROAD_COLOR_NIGHT, ROAD_COLOR_DAY, t)
    for (x1, y1), (x2, y2) in roads:
        sx1, sy1 = camera.to_screen(x1, y1)
        sx2, sy2 = camera.to_screen(x2, y2)
        pygame.draw.line(surface, color, (sx1, sy1), (sx2, sy2), ROAD_W)


# ── 像素人物（俯视 4×4 点）────────────────────────────

def draw_pixel_char(surface, camera, wx, wy, color, shadow_color=None, size=4):
    if not camera.in_view(wx, wy):
        return
    sx, sy = camera.to_screen(wx, wy)
    if shadow_color:
        surface.fill(shadow_color, (sx - size // 2 + 1, sy - size // 2 + 1, size, size))
    surface.fill(color, (sx - size // 2, sy - size // 2, size, size))


def draw_pixel_char_with_label(surface, camera, wx, wy, color, label,
                                shadow_color=None, size=4):
    if not camera.in_view(wx, wy, margin=60):
        return
    draw_pixel_char(surface, camera, wx, wy, color, shadow_color, size)
    font = get_font_small()
    sx, sy = camera.to_screen(wx, wy)
    txt = font.render(label, True, (230, 230, 230))
    surface.blit(txt, (sx - txt.get_width() // 2, sy - size // 2 - 14))


# ── 对话气泡 ──────────────────────────────────────────

def draw_bubble(surface, camera, wx, wy, text, is_phone=False):
    if not camera.in_view(wx, wy, margin=80):
        return
    font = get_font_small()
    sx, sy = camera.to_screen(wx, wy)
    txt = font.render(text, True, (20, 20, 20))
    bw  = txt.get_width() + 8
    bh  = txt.get_height() + 4
    bx  = sx - bw // 2
    by  = sy - 22
    pygame.draw.rect(surface, (255, 255, 255), (bx, by, bw, bh), border_radius=3)
    pygame.draw.rect(surface, (160, 160, 160), (bx, by, bw, bh), 1, border_radius=3)
    surface.blit(txt, (bx + 4, by + 2))
    if is_phone:
        pygame.draw.rect(surface, (30, 30, 30),   (bx + bw + 2, by + 1, 5, 8), border_radius=1)
        pygame.draw.rect(surface, (80, 180, 255), (bx + bw + 3, by + 2, 3, 5))
