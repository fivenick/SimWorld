import pygame
from ui.draw_utils import get_font_small, get_font_mid
from constants import WINDOW_WIDTH, WINDOW_HEIGHT, PANEL_WIDTH, FRIEND_THRESHOLD, ACQUAINTANCE_THRESHOLD


# ── HUD 顶部信息栏 ────────────────────────────────────

def draw_hud(surface, day_t):
    font = get_font_mid()
    hour   = int(day_t * 24) % 24
    minute = int(day_t * 24 * 60) % 60
    period = '白天' if 6 <= hour < 18 else '夜晚'
    ts = font.render(f"{period}  {hour:02d}:{minute:02d}", True, (220, 220, 180))
    # 居中在游戏区域顶部
    game_w = WINDOW_WIDTH - PANEL_WIDTH
    surface.blit(ts, (game_w // 2 - ts.get_width() // 2, 10))


def draw_messages(surface, msgs):
    font = get_font_mid()
    game_w = WINDOW_WIDTH - PANEL_WIDTH
    y = WINDOW_HEIGHT // 2 - 60
    for text, _ in msgs:
        s = font.render(text, True, (255, 255, 100))
        surface.blit(s, (game_w // 2 - s.get_width() // 2, y))
        y += 28


# ── 小地图 ────────────────────────────────────────────

def draw_minimap(surface, npcs, buildings, camera, world_w, world_h):
    mm_w, mm_h = 200, 200
    game_w = WINDOW_WIDTH - PANEL_WIDTH
    mm_x = game_w - mm_w - 10
    mm_y = WINDOW_HEIGHT - mm_h - 10
    scale_x = mm_w / world_w
    scale_y = mm_h / world_h

    bg = pygame.Surface((mm_w, mm_h), pygame.SRCALPHA)
    bg.fill((10, 20, 10, 190))
    surface.blit(bg, (mm_x, mm_y))
    pygame.draw.rect(surface, (80, 120, 80), (mm_x, mm_y, mm_w, mm_h), 1)

    for kind, bx, by, bw, bh, *_ in buildings:
        color = (160, 100, 60)  if kind == 'house'   else \
                (80,  160, 80)  if kind == 'shop'    else \
                (100, 120, 180) if kind == 'company' else \
                (220, 200, 80)  if kind == 'school'  else \
                (180, 80,  200)
        rx = mm_x + int(bx * scale_x)
        ry = mm_y + int(by * scale_y)
        pygame.draw.rect(surface, color, (rx, ry, max(2, int(bw * scale_x)), max(2, int(bh * scale_y))))

    for npc in npcs:
        nx = mm_x + int(npc.x * scale_x)
        ny = mm_y + int(npc.y * scale_y)
        surface.fill(npc.color, (nx, ny, 2, 2))

    # 视口框
    vx = mm_x + int(camera.x * scale_x)
    vy = mm_y + int(camera.y * scale_y)
    vw = int(camera.screen_w * scale_x)
    vh = int(camera.screen_h * scale_y)
    pygame.draw.rect(surface, (255, 255, 255), (vx, vy, vw, vh), 1)


# ── 右侧角色面板 ──────────────────────────────────────

PANEL_BG        = (18, 22, 30)
PANEL_BORDER    = (50, 65, 90)
ITEM_H          = 28          # 每个角色条目高度
ITEM_HOVER_BG   = (35, 45, 65)
ITEM_SELECT_BG  = (50, 80, 130)
DETAIL_BG       = (24, 30, 42)
SCROLL_BAR_W    = 6


class CharacterPanel:
    """右侧角色列表 + 详情面板，支持鼠标点击和滚动。"""

    def __init__(self, npcs):
        self.npcs        = npcs
        self.selected_id = None   # 当前展开的 NPC id
        self.scroll_y    = 0      # 列表滚动偏移（像素）
        self._hovered    = None

        self.panel_x = WINDOW_WIDTH - PANEL_WIDTH
        self.panel_y = 0
        self.font_s  = None
        self.font_m  = None

    def _fonts(self):
        if self.font_s is None:
            self.font_s = get_font_small()
            self.font_m = get_font_mid()
        return self.font_s, self.font_m

    # ── 事件处理 ──────────────────────────────────────

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if mx < self.panel_x:
                return
            if event.button == 1:
                self._on_click(mx, my)
            elif event.button == 4:   # scroll up
                self.scroll_y = max(0, self.scroll_y - ITEM_H * 2)
            elif event.button == 5:   # scroll down
                max_scroll = max(0, len(self.npcs) * ITEM_H - (WINDOW_HEIGHT - 40))
                self.scroll_y = min(max_scroll, self.scroll_y + ITEM_H * 2)

        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            if mx >= self.panel_x:
                self._hovered = self._item_at(my)
            else:
                self._hovered = None

    def _list_top(self):
        """列表区域起始 y（详情展开时列表在下方）"""
        if self.selected_id is not None:
            return 260   # 详情面板占上方约 260px
        return 40

    def _item_at(self, my):
        """根据鼠标 y 返回对应 NPC id，或 None"""
        list_top = self._list_top()
        rel_y = my - list_top + self.scroll_y
        idx = rel_y // ITEM_H
        if 0 <= idx < len(self.npcs):
            return self.npcs[idx].id
        return None

    def _on_click(self, mx, my):
        nid = self._item_at(my)
        if nid is None:
            return
        if self.selected_id == nid:
            self.selected_id = None   # 再次点击折叠
        else:
            self.selected_id = nid
            self.scroll_y = 0

    # ── 绘制 ──────────────────────────────────────────

    def draw(self, surface, npcs_by_id):
        font_s, font_m = self._fonts()
        px = self.panel_x
        pw = PANEL_WIDTH
        ph = WINDOW_HEIGHT

        # 背景
        pygame.draw.rect(surface, PANEL_BG, (px, 0, pw, ph))
        pygame.draw.line(surface, PANEL_BORDER, (px, 0), (px, ph), 1)

        # 标题
        title = font_m.render("角色列表", True, (180, 200, 230))
        surface.blit(title, (px + pw // 2 - title.get_width() // 2, 10))

        # 详情区
        if self.selected_id is not None and self.selected_id in npcs_by_id:
            self._draw_detail(surface, npcs_by_id[self.selected_id], px, pw, npcs_by_id)

        # 列表区
        list_top  = self._list_top()
        list_h    = ph - list_top
        clip_rect = pygame.Rect(px, list_top, pw, list_h)
        old_clip  = surface.get_clip()
        surface.set_clip(clip_rect)

        for i, npc in enumerate(self.npcs):
            iy = list_top + i * ITEM_H - self.scroll_y
            if iy + ITEM_H < list_top or iy > ph:
                continue

            # 背景
            if npc.id == self.selected_id:
                bg = ITEM_SELECT_BG
            elif npc.id == self._hovered:
                bg = ITEM_HOVER_BG
            else:
                bg = PANEL_BG
            pygame.draw.rect(surface, bg, (px + 1, iy, pw - 2, ITEM_H - 1))

            # 色块
            pygame.draw.rect(surface, npc.color, (px + 8, iy + 8, 10, 10))

            # 名字
            name_s = font_s.render(npc.name, True, (210, 220, 235))
            surface.blit(name_s, (px + 24, iy + 7))

            # 状态小字
            state_map = {'wander': '漫步', 'chat': '聊天', 'seek_friend': '找朋友'}
            state_str = state_map.get(npc.state, npc.state)
            st_s = font_s.render(state_str, True, (120, 140, 160))
            surface.blit(st_s, (px + pw - st_s.get_width() - 14, iy + 7))

            # 分隔线
            pygame.draw.line(surface, PANEL_BORDER,
                             (px + 4, iy + ITEM_H - 1), (px + pw - 4, iy + ITEM_H - 1))

        surface.set_clip(old_clip)

        # 滚动条
        total_h = len(self.npcs) * ITEM_H
        if total_h > list_h:
            bar_h   = max(20, list_h * list_h // total_h)
            bar_y   = list_top + self.scroll_y * (list_h - bar_h) // max(1, total_h - list_h)
            pygame.draw.rect(surface, (70, 90, 120),
                             (px + pw - SCROLL_BAR_W - 1, bar_y, SCROLL_BAR_W, bar_h),
                             border_radius=3)

    def _draw_detail(self, surface, npc, px, pw, npcs_by_id):
        font_s, font_m = self._fonts()
        dy = 40
        dh = 215

        pygame.draw.rect(surface, DETAIL_BG, (px + 1, dy, pw - 2, dh))
        pygame.draw.rect(surface, PANEL_BORDER, (px + 1, dy, pw - 2, dh), 1)

        # 色块 + 姓名
        pygame.draw.rect(surface, npc.color, (px + 10, dy + 10, 14, 14))
        name_s = font_m.render(npc.name, True, (230, 240, 255))
        surface.blit(name_s, (px + 30, dy + 8))

        # 基本信息
        lines = [
            ("性别",   npc.gender),
            ("年龄",   f"{npc.age} 岁"),
            ("婚姻",   npc.marital),
            ("工作",   npc.job),
            ("余额",   f"¥ {npc.balance:,}"),
            ("状态",   {'wander': '漫步中', 'chat': '聊天中', 'seek_friend': '找朋友'}.get(npc.state, npc.state)),
        ]
        for i, (label, val) in enumerate(lines):
            y = dy + 34 + i * 22
            lbl = font_s.render(label, True, (120, 140, 165))
            val_s = font_s.render(val, True, (210, 225, 245))
            surface.blit(lbl, (px + 10, y))
            surface.blit(val_s, (px + 60, y))

        # 好友列表
        friend_ids = [oid for oid, cnt in npc.relationships.items() if cnt >= FRIEND_THRESHOLD]
        friend_names = [npcs_by_id[fid].name for fid in friend_ids if fid in npcs_by_id]
        friends_str = "、".join(friend_names) if friend_names else "暂无"
        fl = font_s.render("好友", True, (120, 140, 165))
        fv = font_s.render(friends_str[:18], True, (255, 200, 100))   # 截断防溢出
        surface.blit(fl, (px + 10, dy + 34 + len(lines) * 22))
        surface.blit(fv, (px + 60, dy + 34 + len(lines) * 22))
