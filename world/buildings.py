"""
Buildings defined in world coordinates.
Each building is a pixel-art rectangle drawn top-down.
Entry: (kind, world_x, world_y, w, h, name, color, roof_color)
"""
import pygame
from ui.draw_utils import get_font_small, lerp_color

# ── Building definitions ──────────────────────────────
# (kind, x, y, w, h, name)
BUILDINGS = [
    # Houses cluster — top-left area
    ('house',   200,  200,  20, 16, '住宅A'),
    ('house',   260,  200,  20, 16, '住宅B'),
    ('house',   200,  260,  20, 16, '住宅C'),
    ('house',   260,  260,  20, 16, '住宅D'),
    ('house',   320,  200,  20, 16, '住宅E'),
    ('house',   320,  260,  20, 16, '住宅F'),

    # Shops — center area
    ('shop',    700,  300,  28, 22, '便利店'),
    ('shop',    780,  300,  28, 22, '超市'),
    ('shop',    700,  380,  28, 22, '药店'),

    # Company — right area
    ('company', 1200, 250,  40, 50, '科技公司'),
    ('company', 1320, 250,  40, 50, '银行'),

    # More houses — scattered
    ('house',   500,  500,  20, 16, '住宅G'),
    ('house',   560,  500,  20, 16, '住宅H'),
    ('house',   500,  560,  20, 16, '住宅I'),
    ('house',   900,  600,  20, 16, '住宅J'),
    ('house',   960,  600,  20, 16, '住宅K'),

    # More shops
    ('shop',   1100,  700,  28, 22, '餐厅'),
    ('shop',    400,  800,  28, 22, '书店'),

    # More companies
    ('company', 600,  900,  40, 50, '设计公司'),
    ('company', 1500, 500,  40, 50, '贸易公司'),
]

# Colors per kind
_KIND_COLORS = {
    'house':   {'wall': (180, 150, 110), 'roof': (160, 60,  50),  'door': (100, 70, 40),  'label': (220, 200, 160)},
    'shop':    {'wall': (220, 200, 160), 'roof': (60,  130, 70),  'door': (140, 90, 50),  'label': (100, 200, 120)},
    'company': {'wall': (140, 160, 200), 'roof': (80,  100, 160), 'door': (60,  80, 130), 'label': (160, 200, 255)},
}


def draw_building(surface, camera, bld, day_t):
    kind, bx, by, bw, bh, name = bld
    sx, sy = camera.to_screen(bx, by)

    # cull
    if sx + bw < 0 or sx > camera.screen_w or sy + bh < 0 or sy > camera.screen_h:
        return

    c = _KIND_COLORS[kind]
    # brightness by day
    bright = min(1.0, max(0.3, 1.0 - abs(day_t - 0.5) * 2))
    wall  = tuple(int(v * bright) for v in c['wall'])
    roof  = tuple(int(v * bright) for v in c['roof'])
    door  = c['door']

    # wall
    pygame.draw.rect(surface, wall, (sx, sy, bw, bh))

    if kind == 'house':
        # roof strip (top 4px)
        pygame.draw.rect(surface, roof, (sx, sy, bw, 4))
        # door (center bottom, 3×4)
        pygame.draw.rect(surface, door, (sx + bw // 2 - 1, sy + bh - 4, 3, 4))
        # two windows (2×2)
        win = (min(255, wall[0] + 60), min(255, wall[1] + 60), min(255, wall[2] + 80))
        pygame.draw.rect(surface, win, (sx + 3,      sy + 5, 4, 4))
        pygame.draw.rect(surface, win, (sx + bw - 7, sy + 5, 4, 4))

    elif kind == 'shop':
        # awning strip
        pygame.draw.rect(surface, roof, (sx, sy, bw, 5))
        # sign strip
        pygame.draw.rect(surface, (200, 60, 60), (sx + 2, sy + 5, bw - 4, 4))
        # door
        pygame.draw.rect(surface, door, (sx + bw // 2 - 2, sy + bh - 5, 4, 5))
        # windows
        win = (min(255, wall[0] + 40), min(255, wall[1] + 40), min(255, wall[2] + 60))
        pygame.draw.rect(surface, win, (sx + 3,      sy + 10, 5, 5))
        pygame.draw.rect(surface, win, (sx + bw - 8, sy + 10, 5, 5))

    elif kind == 'company':
        # roof
        pygame.draw.rect(surface, roof, (sx, sy, bw, 5))
        # grid windows (3 cols × 4 rows)
        win = (min(255, wall[0] + 50), min(255, wall[1] + 60), min(255, wall[2] + 80))
        for row in range(4):
            for col in range(3):
                wx = sx + 4 + col * (bw - 8) // 3
                wy = sy + 7 + row * 9
                pygame.draw.rect(surface, win, (wx, wy, 4, 5))
        # door
        pygame.draw.rect(surface, door, (sx + bw // 2 - 2, sy + bh - 6, 5, 6))

    # outline
    pygame.draw.rect(surface, (0, 0, 0), (sx, sy, bw, bh), 1)

    # label (only when close enough — within ~400 world px of camera center)
    font = get_font_small()
    lbl = font.render(name, True, c['label'])
    surface.blit(lbl, (sx + bw // 2 - lbl.get_width() // 2, sy - 13))


def draw_buildings(surface, camera, day_t):
    for bld in BUILDINGS:
        draw_building(surface, camera, bld, day_t)


def get_shop_buildings():
    """Return (name, center_x, center_y) for shop-type buildings."""
    return [(name, bx + bw // 2, by + bh // 2)
            for kind, bx, by, bw, bh, name in BUILDINGS if kind == 'shop']


def get_all_buildings_for_minimap():
    """Return list of (kind, x, y, w, h) for minimap rendering."""
    return [(kind, bx, by, bw, bh, name) for kind, bx, by, bw, bh, name in BUILDINGS]
