import pygame
import sys
import random

from constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT, WORLD_WIDTH, WORLD_HEIGHT,
    DAY_LENGTH, CAMERA_SPEED, PANEL_WIDTH,
)
from entities.npc import NPC
from world.buildings import draw_buildings, get_all_buildings_for_minimap
from ui.draw_utils import (
    Camera, get_font_small,
    night_overlay_alpha,
    draw_ground, draw_roads,
    draw_pixel_char_with_label, draw_bubble,
)
from ui.hud import draw_hud, draw_messages, draw_minimap, CharacterPanel


ROADS = [
    ((0, 500),    (WORLD_WIDTH, 500)),
    ((0, 1000),   (WORLD_WIDTH, 1000)),
    ((0, 1500),   (WORLD_WIDTH, 1500)),
    ((0, 2000),   (WORLD_WIDTH, 2000)),
    ((0, 2500),   (WORLD_WIDTH, 2500)),
    ((500,  0),   (500,  WORLD_HEIGHT)),
    ((1000, 0),   (1000, WORLD_HEIGHT)),
    ((1500, 0),   (1500, WORLD_HEIGHT)),
    ((2000, 0),   (2000, WORLD_HEIGHT)),
    ((2500, 0),   (2500, WORLD_HEIGHT)),
]


def make_npcs(count=20):
    return [
        NPC(i,
            random.randint(100, WORLD_WIDTH  - 100),
            random.randint(100, WORLD_HEIGHT - 100))
        for i in range(count)
    ]


def run():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("SimWorld — 模拟世界")
    clock     = pygame.time.Clock()
    font      = get_font_small()

    npcs      = make_npcs(20)
    npcs_by_id = {npc.id: npc for npc in npcs}
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

        messages = [(t, ttl - 1) for t, ttl in messages if ttl > 1]

        # ── 绘制游戏区域 ──────────────────────────────
        draw_ground(game_surf, camera, day_t, WORLD_WIDTH, WORLD_HEIGHT)
        draw_roads(game_surf, camera, day_t, ROADS)
        draw_buildings(game_surf, camera, day_t)

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
