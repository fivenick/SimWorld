import pygame
import sys
import random

from constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT, WORLD_WIDTH, WORLD_HEIGHT,
    DAY_LENGTH, CAMERA_SPEED, PANEL_WIDTH,
)
from entities.npc import NPC
from entities.car import Car
from world.buildings import draw_buildings, get_all_buildings_for_minimap
from ui.draw_utils import (
    Camera, get_font_small,
    night_overlay_alpha,
    draw_ground, draw_roads, draw_road_markings, draw_car,
    draw_pixel_char_with_label, draw_bubble,
)
from ui.hud import draw_hud, draw_messages, draw_minimap, CharacterPanel


ROADS = [
    # 主干道（横向）
    ('main', (0, 400),    (WORLD_WIDTH, 400)),
    ('main', (0, 900),    (WORLD_WIDTH, 900)),
    ('main', (0, 1500),   (WORLD_WIDTH, 1500)),
    ('main', (0, 2100),   (WORLD_WIDTH, 2100)),
    ('main', (0, 2600),   (WORLD_WIDTH, 2600)),
    # 主干道（纵向）
    ('main', (400,  0),   (400,  WORLD_HEIGHT)),
    ('main', (900,  0),   (900,  WORLD_HEIGHT)),
    ('main', (1500, 0),   (1500, WORLD_HEIGHT)),
    ('main', (2100, 0),   (2100, WORLD_HEIGHT)),
    ('main', (2600, 0),   (2600, WORLD_HEIGHT)),
    # 支路（横向）
    ('side', (0, 650),    (900, 650)),
    ('side', (900, 650),  (1500, 650)),
    ('side', (0, 1200),   (900, 1200)),
    ('side', (1500, 1200),(2100, 1200)),
    ('side', (0, 1800),   (900, 1800)),
    ('side', (900, 1800), (1500, 1800)),
    ('side', (2100, 1800),(WORLD_WIDTH, 1800)),
    ('side', (0, 2300),   (900, 2300)),
    ('side', (2100, 2300),(WORLD_WIDTH, 2300)),
    # 支路（纵向）
    ('side', (650,  0),   (650,  900)),
    ('side', (650,  900), (650,  1500)),
    ('side', (1200, 0),   (1200, 900)),
    ('side', (1200, 1500),(1200, 2100)),
    ('side', (1800, 900), (1800, 1500)),
    ('side', (1800, 1500),(1800, 2100)),
    ('side', (2300, 0),   (2300, 900)),
    ('side', (2300, 2100),(2300, WORLD_HEIGHT)),
]


def make_npcs(count=20):
    return [
        NPC(i,
            random.randint(100, WORLD_WIDTH  - 100),
            random.randint(100, WORLD_HEIGHT - 100))
        for i in range(count)
    ]


def make_cars(roads):
    cars = []
    car_id = 0
    for road_type, (x1, y1), (x2, y2) in roads:
        if road_type != 'main':
            continue
        is_h = (y1 == y2)
        count = random.randint(3, 6)
        for i in range(count):
            direction = 1 if i % 2 == 0 else -1
            if is_h:
                offset = 5 if direction == 1 else -5
                cx = random.randint(min(x1, x2), max(x1, x2))
                cy = y1 + offset
                cars.append(Car(car_id, 'h', cx, cy, direction))
            else:
                offset = 5 if direction == 1 else -5
                cx = x1 + offset
                cy = random.randint(min(y1, y2), max(y1, y2))
                cars.append(Car(car_id, 'v', cx, cy, direction))
            car_id += 1
    return cars


def run():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("SimWorld — 模拟世界")
    clock     = pygame.time.Clock()
    font      = get_font_small()

    npcs      = make_npcs(20)
    npcs_by_id = {npc.id: npc for npc in npcs}
    cars      = make_cars(ROADS)
    camera    = Camera()
    camera.center_on(WORLD_WIDTH // 2, WORLD_HEIGHT // 2, WORLD_WIDTH, WORLD_HEIGHT)

    panel     = CharacterPanel(npcs)
    messages  = []
    game_tick = 0

    # 游戏区域 surface（裁剪右侧面板）
    game_w    = WINDOW_WIDTH - PANEL_WIDTH
    game_surf = pygame.Surface((game_w, WINDOW_HEIGHT))

    running = True
    while running:
        # ── 事件 ──────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            panel.handle_event(event)

        # ── 视角移动（WASD）──────────────────────────
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = (keys[pygame.K_s] or keys[pygame.K_DOWN])  - (keys[pygame.K_w] or keys[pygame.K_UP])
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707
        camera.move(dx, dy, WORLD_WIDTH, WORLD_HEIGHT, CAMERA_SPEED)

        # ── 逻辑更新 ──────────────────────────────────
        game_tick += 1
        day_t = (game_tick % DAY_LENGTH) / DAY_LENGTH

        for npc in npcs:
            npc.update(npcs, game_tick)

        for car in cars:
            car.update()

        messages = [(t, ttl - 1) for t, ttl in messages if ttl > 1]

        # ── 绘制游戏区域 ──────────────────────────────
        draw_ground(game_surf, camera, day_t, WORLD_WIDTH, WORLD_HEIGHT)
        draw_roads(game_surf, camera, day_t, ROADS)
        draw_road_markings(game_surf, camera, ROADS)
        draw_buildings(game_surf, camera, day_t)

        for car in cars:
            draw_car(game_surf, camera, car)

        for npc in npcs:
            shadow = tuple(max(0, c - 60) for c in npc.color)
            draw_pixel_char_with_label(game_surf, camera, npc.x, npc.y,
                                       npc.color, npc.name, shadow_color=shadow, size=4)
            if npc.bubble_text and npc.bubble_timer > 0:
                draw_bubble(game_surf, camera, npc.x, npc.y,
                            npc.bubble_text, is_phone=npc.is_phone_chat)

        # 夜晚遮罩
        alpha = night_overlay_alpha(day_t)
        if alpha > 0:
            overlay = pygame.Surface((game_w, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 20, alpha))
            game_surf.blit(overlay, (0, 0))

        # HUD（时间、消息、小地图）
        draw_hud(game_surf, day_t)
        draw_messages(game_surf, messages)
        draw_minimap(game_surf, npcs, get_all_buildings_for_minimap(),
                     camera, WORLD_WIDTH, WORLD_HEIGHT)

        # 底部提示
        hint = font.render("WASD / 方向键  移动视角    ESC 退出", True, (130, 140, 150))
        game_surf.blit(hint, (game_w // 2 - hint.get_width() // 2, WINDOW_HEIGHT - 18))

        # ── 合并到主屏幕 ──────────────────────────────
        screen.blit(game_surf, (0, 0))
        panel.draw(screen, npcs_by_id)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run()
