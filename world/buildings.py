"""
Buildings defined in world coordinates.
Each building is a pixel-art rectangle drawn top-down.
Kinds: house | shop | company | school | mall
"""
import pygame
from ui.draw_utils import get_font_small, lerp_color

# ── Building definitions ──────────────────────────────
# (kind, x, y, w, h, name)
BUILDINGS = [
    # ── 住宅区（左上）────────────────────────────────
    ('house',   180,  180,  32, 26, '住宅A'),
    ('house',   240,  180,  32, 26, '住宅B'),
    ('house',   300,  180,  32, 26, '住宅C'),
    ('house',   180,  240,  32, 26, '住宅D'),
    ('house',   240,  240,  32, 26, '住宅E'),
    ('house',   300,  240,  32, 26, '住宅F'),
    ('house',   480,  480,  32, 26, '住宅G'),
    ('house',   540,  480,  32, 26, '住宅H'),
    ('house',   480,  540,  32, 26, '住宅I'),
    ('house',   880,  580,  32, 26, '住宅J'),
    ('house',   940,  580,  32, 26, '住宅K'),

    # ── 商店区（中部）────────────────────────────────
    ('shop',    680,  280,  40, 32, '便利店'),
    ('shop',    760,  280,  40, 32, '超市'),
    ('shop',    680,  360,  40, 32, '药店'),
    ('shop',   1080,  680,  40, 32, '餐厅'),
    ('shop',    380,  780,  40, 32, '书店'),

    # ── 公司区（右侧）────────────────────────────────
    ('company', 1180, 230,  56, 70, '科技公司'),
    ('company', 1300, 230,  56, 70, '银行'),
    ('company',  580,  880,  56, 70, '设计公司'),
    ('company', 1480, 480,  56, 70, '贸易公司'),

    # ── 学校（独立地块）──────────────────────────────
    ('school',   700,  700,  80, 64, '第一小学'),
    ('school',  1600,  200,  80, 64, '高中'),

    # ── 商城（大型）──────────────────────────────────
    ('mall',    1100, 1000, 100, 80, '购物中心'),
    ('mall',     300,  900, 100, 80, '商业广场'),
]

# Colors per kind
_KIND_COLORS = {
    'house':   {'wall': (190, 158, 118), 'roof': (168, 62,  52),  'door': (100, 70,  40),  'label': (240, 210, 170)},
    'shop':    {'wall': (230, 210, 170), 'roof': (55,  140, 75),  'door': (140, 90,  50),  'label': (100, 220, 120)},
    'company': {'wall': (150, 170, 210), 'roof': (70,  95,  170), 'door': (55,  75,  140), 'label': (170, 210, 255)},
    'school':  {'wall': (240, 220, 140), 'roof': (200, 80,  40),  'door': (120, 80,  40),  'label': (255, 240, 100)},
    'mall':    {'wall': (210, 190, 230), 'roof': (140, 60,  160), 'door': (100, 50,  130), 'label': (230, 160, 255)},
}


def _bright(color, factor):
    return tuple(max(0, min(255, int(v * factor))) for v in color)


def draw_building(surface, camera, bld, day_t):
    kind, bx, by, bw, bh, name = bld
    sx, sy = camera.to_screen(bx, by)

    # cull
    if sx + bw < 0 or sx > camera.screen_w or sy + bh < 0 or sy > camera.screen_h:
        return

    c = _KIND_COLORS[kind]
    factor = min(1.0, max(0.35, 1.0 - abs(day_t - 0.5) * 2))
    wall = _bright(c['wall'], factor)
    roof = _bright(c['roof'], factor)
    door = c['door']

    # ── 地基阴影（增加立体感）
    pygame.draw.rect(surface, (30, 30, 30), (sx + 3, sy + 3, bw, bh))

    # ── 主体墙
    pygame.draw.rect(surface, wall, (sx, sy, bw, bh))

    if kind == 'house':
        # 屋顶色带（顶部 5px）
        pygame.draw.rect(surface, roof, (sx, sy, bw, 5))
        # 烟囱
        pygame.draw.rect(surface, _bright(roof, 0.8), (sx + bw - 8, sy - 4, 4, 5))
        # 门（中下，4×6）
        pygame.draw.rect(surface, door, (sx + bw // 2 - 2, sy + bh - 6, 4, 6))
        # 两扇窗（4×4，带亮色）
        win = (min(255, wall[0] + 55), min(255, wall[1] + 55), min(255, wall[2] + 80))
        pygame.draw.rect(surface, win, (sx + 4,       sy + 7, 5, 5))
        pygame.draw.rect(surface, win, (sx + bw - 9,  sy + 7, 5, 5))
        # 窗框
        pygame.draw.rect(surface, (80, 60, 40), (sx + 4,      sy + 7, 5, 5), 1)
        pygame.draw.rect(surface, (80, 60, 40), (sx + bw - 9, sy + 7, 5, 5), 1)

    elif kind == 'shop':
        # 遮阳棚（顶部 6px，条纹）
        pygame.draw.rect(surface, roof, (sx, sy, bw, 6))
        for i in range(0, bw, 6):
            pygame.draw.rect(surface, _bright(roof, 0.75), (sx + i, sy, 3, 6))
        # 招牌（红底白字区域）
        pygame.draw.rect(surface, (210, 55, 55), (sx + 2, sy + 7, bw - 4, 6))
        # 橱窗（大玻璃）
        win = (min(255, wall[0] + 30), min(255, wall[1] + 40), min(255, wall[2] + 70))
        pygame.draw.rect(surface, win, (sx + 3,       sy + 15, bw // 2 - 5, bh - 22))
        pygame.draw.rect(surface, win, (sx + bw // 2 + 2, sy + 15, bw // 2 - 5, bh - 22))
        # 门
        pygame.draw.rect(surface, door, (sx + bw // 2 - 2, sy + bh - 7, 5, 7))

    elif kind == 'company':
        # 顶部深色屋顶
        pygame.draw.rect(surface, roof, (sx, sy, bw, 6))
        # 玻璃幕墙网格（4列 × 5行）
        win = (min(255, wall[0] + 40), min(255, wall[1] + 55), min(255, wall[2] + 80))
        cols, rows = 4, 5
        pw = (bw - 10) // cols
        ph = (bh - 16) // rows
        for row in range(rows):
            for col in range(cols):
                wx = sx + 5 + col * pw
                wy = sy + 8 + row * ph
                pygame.draw.rect(surface, win, (wx, wy, pw - 2, ph - 2))
        # 大门（双开）
        pygame.draw.rect(surface, door, (sx + bw // 2 - 5, sy + bh - 8, 4, 8))
        pygame.draw.rect(surface, door, (sx + bw // 2 + 1, sy + bh - 8, 4, 8))
        # 门把手
        pygame.draw.rect(surface, (200, 200, 200), (sx + bw // 2 - 2, sy + bh - 5, 1, 2))
        pygame.draw.rect(surface, (200, 200, 200), (sx + bw // 2 + 4, sy + bh - 5, 1, 2))

    elif kind == 'school':
        # 屋顶（橙红色，宽带）
        pygame.draw.rect(surface, roof, (sx, sy, bw, 7))
        # 旗杆
        pygame.draw.rect(surface, (180, 180, 180), (sx + bw // 2, sy - 12, 2, 13))
        pygame.draw.rect(surface, (220, 50, 50),   (sx + bw // 2 + 2, sy - 11, 7, 5))
        # 主门（拱形用矩形近似，居中，宽）
        pygame.draw.rect(surface, door, (sx + bw // 2 - 6, sy + bh - 10, 12, 10))
        pygame.draw.rect(surface, _bright(door, 1.3), (sx + bw // 2 - 5, sy + bh - 9, 10, 4))
        # 窗户（3列 × 2行，方形）
        win = (min(255, wall[0] + 40), min(255, wall[1] + 40), min(255, wall[2] + 60))
        for row in range(2):
            for col in range(3):
                wx = sx + 6 + col * ((bw - 12) // 3)
                wy = sy + 10 + row * 18
                pygame.draw.rect(surface, win, (wx, wy, 10, 10))
                pygame.draw.rect(surface, (80, 80, 100), (wx, wy, 10, 10), 1)
        # 台阶
        pygame.draw.rect(surface, _bright(wall, 0.85), (sx + bw // 2 - 10, sy + bh, 20, 3))

    elif kind == 'mall':
        # 顶部装饰带（紫色）
        pygame.draw.rect(surface, roof, (sx, sy, bw, 8))
        # 顶部锯齿装饰
        for i in range(0, bw, 10):
            pygame.draw.polygon(surface, _bright(roof, 1.2), [
                (sx + i, sy), (sx + i + 5, sy - 5), (sx + i + 10, sy)
            ])
        # 大型玻璃橱窗（两侧）
        win = (min(255, wall[0] + 20), min(255, wall[1] + 30), min(255, wall[2] + 50))
        pygame.draw.rect(surface, win, (sx + 4,          sy + 10, bw // 3 - 4, bh - 18))
        pygame.draw.rect(surface, win, (sx + bw * 2 // 3 + 4, sy + 10, bw // 3 - 8, bh - 18))
        # 中央入口（宽大）
        pygame.draw.rect(surface, door, (sx + bw // 3,   sy + bh - 14, bw // 3, 14))
        # 入口上方招牌
        pygame.draw.rect(surface, (180, 50, 180), (sx + bw // 3, sy + bh - 20, bw // 3, 6))
        # 停车场标线（底部）
        for i in range(3):
            pygame.draw.rect(surface, (200, 200, 200),
                             (sx + 6 + i * (bw // 3), sy + bh + 2, bw // 3 - 4, 2))

    # 轮廓
    pygame.draw.rect(surface, (0, 0, 0), (sx, sy, bw, bh), 1)

    # 标签
    font = get_font_small()
    lbl = font.render(name, True, c['label'])
    surface.blit(lbl, (sx + bw // 2 - lbl.get_width() // 2, sy - 14))


def draw_buildings(surface, camera, day_t):
    for bld in BUILDINGS:
        draw_building(surface, camera, bld, day_t)


def get_shop_buildings():
    """Return (name, center_x, center_y) for shop-type buildings."""
    return [(name, bx + bw // 2, by + bh // 2)
            for kind, bx, by, bw, bh, name in BUILDINGS if kind == 'shop']


def get_all_buildings_for_minimap():
    """Return list of (kind, x, y, w, h, name) for minimap rendering."""
    return [(kind, bx, by, bw, bh, name) for kind, bx, by, bw, bh, name in BUILDINGS]
