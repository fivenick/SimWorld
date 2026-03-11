import pygame
import sys
import math
import random

pygame.init()

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
BLOCK_SIZE = 40

BLACK = (0, 0, 0)
SKIN = (255, 220, 177)
SHIRT = (50, 150, 255)
PANTS = (60, 60, 180)
SHOE = (80, 50, 30)
HAIR = (60, 30, 10)

NPC_SHIRTS = [
    (220, 50, 50), (50, 200, 80), (200, 150, 50), (180, 50, 200),
    (50, 200, 200), (200, 200, 50), (200, 80, 150), (100, 100, 220),
    (80, 180, 100), (220, 120, 80),
]
NPC_NAMES         = ['小明', '小红', '小刚', '小丽', '小华', '小芳', '小强', '小燕', '小龙', '小梅']
CHAT_STRANGER     = ['你好！', '嗨～', '初次见面', '你也在这里？']
CHAT_ACQUAINTANCE = ['今天天气不错', '饿了吗？', '最近怎么样？', '一起走走？']
CHAT_FRIEND       = ['好久不见！', '我就知道是你', '又见面了～', '想你了！', '咱们去找吃的？']
CHAT_PHONE        = ['在干嘛～', '想你了', '出来玩？', '刚吃完饭', '你在哪呢',
                     '哈哈哈哈', '好的好的', '等我一下', '今天好无聊', '发你个表情包']
CHAT_CONFLICT     = ['哼！', '你什么意思！', '烦死了']

FRIEND_THRESHOLD       = 10
ACQUAINTANCE_THRESHOLD = 3
DECAY_INTERVAL         = 1800   # ticks (~1 in-game day)
DECAY_AMOUNT           = 1      # points lost per interval
CONFLICT_PROB          = 0.0003 # per-frame per-NPC probability
CONFLICT_DAMAGE_MIN    = 2
CONFLICT_DAMAGE_MAX    = 5
PHONE_COOLDOWN_MIN     = 600
PHONE_COOLDOWN_MAX     = 1200
PHONE_ICON_W, PHONE_ICON_H = 8, 12

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("虚拟世界模拟 - SimWorld v0.1")

# 玩家属性
player_x = WINDOW_WIDTH // 2
player_y = WINDOW_HEIGHT // 2
player_speed = 4
player_hunger = 100.0   # 饥饿度 0~100
player_thirst = 100.0   # 口渴度 0~100

# 动画
frame = 0
moving = False
facing_right = True

# 昼夜系统：0~1 表示一天进度，0=正午，0.5=午夜
day_length = 1800  # 帧数为一天
game_tick = 0

font = pygame.font.SysFont("microsoftyahei", 16)
font_big = pygame.font.SysFont("microsoftyahei", 22)


# ── 物品 ──────────────────────────────────────────────
class Item:
    def __init__(self, x, y, kind):
        self.x = x
        self.y = y
        self.kind = kind   # 'food' | 'water'
        self.alive = True

    def draw(self, surface):
        if not self.alive:
            return
        if self.kind == 'food':
            pygame.draw.circle(surface, (220, 30, 30), (self.x, self.y), 9)
            pygame.draw.circle(surface, (255, 120, 120), (self.x - 3, self.y - 3), 3)
            pygame.draw.line(surface, (60, 120, 0), (self.x, self.y - 9), (self.x + 4, self.y - 14), 2)
        else:
            pts = [(self.x, self.y - 10), (self.x - 7, self.y + 5), (self.x + 7, self.y + 5)]
            pygame.draw.polygon(surface, (30, 140, 255), pts)
            pygame.draw.polygon(surface, (120, 200, 255), [(self.x, self.y - 6), (self.x - 3, self.y + 2), (self.x + 3, self.y + 2)])


def spawn_items(n=6):
    result = []
    for _ in range(n):
        x = random.randint(BLOCK_SIZE + 40, WINDOW_WIDTH - BLOCK_SIZE - 40)
        y = random.randint(BLOCK_SIZE + 40, WINDOW_HEIGHT - BLOCK_SIZE - 40)
        result.append(Item(x, y, random.choice(['food', 'water'])))
    return result


class NPC:
    def __init__(self, npc_id, x, y):
        self.id = npc_id
        self.x = float(x)
        self.y = float(y)
        self.shirt_color = NPC_SHIRTS[npc_id % len(NPC_SHIRTS)]
        self.hunger = random.uniform(60, 100)
        self.thirst = random.uniform(60, 100)
        self.state = 'wander'
        self.state_timer = 0
        self.target_item = None
        self.target_npc = None
        self.chat_cooldown = 0
        self.speed = 1.8
        self.dx = 0.0
        self.dy = 0.0
        self.facing_right = True
        self.frame = 0
        self.moving = False
        self.has_food = random.random() < 0.3  # 30% start with food
        self.bubble_text = ''
        self.bubble_timer = 0
        self.name = NPC_NAMES[npc_id % len(NPC_NAMES)]
        self.relationships = {}  # {other_npc_id: int} — chat count
        self.phone_contacts      = set()   # set of NPC ids
        self.last_chat_tick      = {}      # {other_npc_id: int}
        self.is_phone_chat       = False   # True while current bubble is a phone chat
        self.phone_chat_cooldown = 0

    def _nearest_item(self, items, kind):
        best, best_d = None, float('inf')
        for item in items:
            if item.alive and item.kind == kind:
                d = math.hypot(self.x - item.x, self.y - item.y)
                if d < best_d:
                    best, best_d = item, d
        return best

    def _friendship_level(self, other_id):
        count = self.relationships.get(other_id, 0)
        if count >= 10: return 'friend'
        if count >= 3:  return 'acquaintance'
        return 'stranger'

    def _record_chat(self, other, tick, phone=False):
        self.relationships[other.id]  = self.relationships.get(other.id, 0) + 1
        other.relationships[self.id]  = other.relationships.get(self.id, 0) + 1
        self.last_chat_tick[other.id]  = tick
        other.last_chat_tick[self.id]  = tick
        self.is_phone_chat  = phone
        other.is_phone_chat = phone
        # Auto-exchange contacts when friendship threshold first crossed
        if (self.relationships[other.id] >= FRIEND_THRESHOLD
                and other.id not in self.phone_contacts):
            self.phone_contacts.add(other.id)
            other.phone_contacts.add(self.id)

    def _start_chat(self, other, tick, phone=False):
        if phone:
            self.bubble_text  = random.choice(CHAT_PHONE)
            other.bubble_text = random.choice(CHAT_PHONE)
            self.chat_cooldown  = random.randint(PHONE_COOLDOWN_MIN, PHONE_COOLDOWN_MAX)
            other.chat_cooldown = random.randint(PHONE_COOLDOWN_MIN, PHONE_COOLDOWN_MAX)
        else:
            lines = {'stranger': CHAT_STRANGER, 'acquaintance': CHAT_ACQUAINTANCE, 'friend': CHAT_FRIEND}
            self.bubble_text  = random.choice(lines[self._friendship_level(other.id)])
            other.bubble_text = random.choice(lines[other._friendship_level(self.id)])
            self.chat_cooldown  = random.randint(300, 600)
            other.chat_cooldown = random.randint(300, 600)
        self.state        = 'chat'
        self.target_npc   = other
        self.bubble_timer  = 180
        other.bubble_timer = 180
        self._record_chat(other, tick, phone=phone)

    def _apply_decay(self, other_id, tick):
        last = self.last_chat_tick.get(other_id, 0)
        if tick - last >= DECAY_INTERVAL:
            new = max(0, self.relationships.get(other_id, 0) - DECAY_AMOUNT)
            self.relationships[other_id]  = new
            self.last_chat_tick[other_id] = tick  # reset so it decays once per interval
            if new < ACQUAINTANCE_THRESHOLD:
                self.phone_contacts.discard(other_id)

    def _trigger_conflict(self, other):
        damage = random.randint(CONFLICT_DAMAGE_MIN, CONFLICT_DAMAGE_MAX)
        self.relationships[other.id]  = max(0, self.relationships.get(other.id, 0) - damage)
        other.relationships[self.id]  = max(0, other.relationships.get(self.id, 0) - damage)
        self.bubble_text   = random.choice(CHAT_CONFLICT)
        other.bubble_text  = random.choice(CHAT_CONFLICT)
        self.bubble_timer  = 120
        other.bubble_timer = 120
        self.is_phone_chat  = False
        other.is_phone_chat = False
        if self.relationships[other.id] < ACQUAINTANCE_THRESHOLD:
            self.phone_contacts.discard(other.id)
            other.phone_contacts.discard(self.id)

    def update(self, items, npcs, px, py, tick):
        # Decay needs
        self.hunger = max(0, self.hunger - 0.008)
        self.thirst = max(0, self.thirst - 0.012)
        if self.chat_cooldown > 0:
            self.chat_cooldown -= 1
        if self.phone_chat_cooldown > 0:
            self.phone_chat_cooldown -= 1
        if self.bubble_timer > 0:
            self.bubble_timer -= 1
        else:
            self.bubble_text = ''

        # Decay relationships
        for other_id in list(self.relationships.keys()):
            self._apply_decay(other_id, tick)

        # Random conflict
        if self.relationships and random.random() < CONFLICT_PROB:
            conflict_id  = random.choice(list(self.relationships.keys()))
            conflict_npc = next((n for n in npcs if n.id == conflict_id), None)
            if conflict_npc:
                self._trigger_conflict(conflict_npc)

        # State transitions (priority order)
        if self.state != 'chat':
            if self.hunger < 40:
                self.state = 'seek_food'
            elif self.thirst < 40:
                self.state = 'seek_water'
            elif self.has_food and math.hypot(self.x - px, self.y - py) < 60:
                self.state = 'give_food'
            elif self.chat_cooldown == 0:
                # Pass 0: phone chat with a contact (no proximity needed)
                if self.phone_contacts and self.phone_chat_cooldown == 0:
                    contact_id  = random.choice(list(self.phone_contacts))
                    contact_npc = next((n for n in npcs if n.id == contact_id
                                        and n.chat_cooldown == 0
                                        and n.phone_chat_cooldown == 0), None)
                    if contact_npc:
                        self._start_chat(contact_npc, tick, phone=True)
                        self.phone_chat_cooldown        = random.randint(PHONE_COOLDOWN_MIN, PHONE_COOLDOWN_MAX)
                        contact_npc.phone_chat_cooldown = random.randint(PHONE_COOLDOWN_MIN, PHONE_COOLDOWN_MAX)
                # Pass 1: seek a friend within 120px
                best_friend, best_d = None, float('inf')
                for other in npcs:
                    if other is not self and other.chat_cooldown == 0:
                        d = math.hypot(self.x - other.x, self.y - other.y)
                        if d < 120 and self._friendship_level(other.id) == 'friend' and d < best_d:
                            best_friend, best_d = other, d
                if best_friend:
                    self.state = 'seek_friend'
                    self.target_npc = best_friend
                else:
                    # Pass 2: original proximity chat
                    for other in npcs:
                        if other is not self and math.hypot(self.x - other.x, self.y - other.y) < 50:
                            self._start_chat(other, tick)
                            break
                    else:
                        if self.state not in ('seek_food', 'seek_water', 'give_food'):
                            self.state = 'wander'

        # State behaviour
        if self.state == 'wander':
            self.state_timer -= 1
            if self.state_timer <= 0:
                angle = random.uniform(0, 2 * math.pi)
                self.dx = math.cos(angle) * self.speed
                self.dy = math.sin(angle) * self.speed
                self.state_timer = random.randint(120, 180)
            self.x += self.dx
            self.y += self.dy
            self.moving = True

        elif self.state == 'seek_food':
            item = self._nearest_item(items, 'food')
            if item is None:
                self.state = 'wander'
            else:
                self.target_item = item
                d = math.hypot(self.x - item.x, self.y - item.y)
                if d < 18:
                    item.alive = False
                    self.hunger = min(100, self.hunger + 30)
                    self.state = 'wander'
                else:
                    jitter_x = random.uniform(-0.3, 0.3)
                    jitter_y = random.uniform(-0.3, 0.3)
                    self.x += (item.x - self.x) / d * self.speed + jitter_x
                    self.y += (item.y - self.y) / d * self.speed + jitter_y
                    self.moving = True

        elif self.state == 'seek_water':
            item = self._nearest_item(items, 'water')
            if item is None:
                self.state = 'wander'
            else:
                self.target_item = item
                d = math.hypot(self.x - item.x, self.y - item.y)
                if d < 18:
                    item.alive = False
                    self.thirst = min(100, self.thirst + 35)
                    self.state = 'wander'
                else:
                    jitter_x = random.uniform(-0.3, 0.3)
                    jitter_y = random.uniform(-0.3, 0.3)
                    self.x += (item.x - self.x) / d * self.speed + jitter_x
                    self.y += (item.y - self.y) / d * self.speed + jitter_y
                    self.moving = True

        elif self.state == 'chat':
            self.moving = False
            if self.target_npc:
                self.facing_right = self.target_npc.x > self.x
            if self.bubble_timer <= 0:
                self.state = 'wander'
                self.target_npc = None

        elif self.state == 'seek_friend':
            if self.target_npc is None or self.chat_cooldown > 0:
                self.state = 'wander'
            else:
                d = math.hypot(self.x - self.target_npc.x, self.y - self.target_npc.y)
                if d < 22:
                    self._start_chat(self.target_npc, tick)
                elif d > 200:
                    self.state = 'wander'
                    self.target_npc = None
                else:
                    self.x += (self.target_npc.x - self.x) / d * self.speed
                    self.y += (self.target_npc.y - self.y) / d * self.speed
                    self.moving = True

        elif self.state == 'give_food':
            d = math.hypot(self.x - px, self.y - py)
            if d < 22:
                self.has_food = False
                self.state = 'wander'
                return 'give_food'
            else:
                self.x += (px - self.x) / d * self.speed
                self.y += (py - self.y) / d * self.speed
                self.moving = True

        # Clamp to arena
        self.x = max(BLOCK_SIZE + 12, min(self.x, WINDOW_WIDTH - BLOCK_SIZE - 12))
        self.y = max(BLOCK_SIZE + 50, min(self.y, WINDOW_HEIGHT - BLOCK_SIZE - 12))

        # Update facing and animation
        if self.moving and self.dx != 0:
            self.facing_right = self.dx > 0
        if self.moving:
            self.frame += 1
        else:
            self.frame = 0

        return None

    def draw(self, surface):
        global SHIRT
        old_shirt = SHIRT
        SHIRT = self.shirt_color
        draw_stickman(surface, int(self.x), int(self.y), self.frame, self.moving, self.facing_right)
        SHIRT = old_shirt

        # Name tag
        name_surf = font.render(self.name, True, (40, 40, 40))
        nw = name_surf.get_width()
        pygame.draw.rect(surface, (255, 255, 255),
                         (int(self.x) - nw // 2 - 3, int(self.y) - 64, nw + 6, 14),
                         border_radius=3)
        surface.blit(name_surf, (int(self.x) - nw // 2, int(self.y) - 64))

        # Warning dot above head
        if self.hunger < 30:
            pygame.draw.circle(surface, (255, 60, 60), (int(self.x), int(self.y) - 68), 5)
        elif self.thirst < 30:
            pygame.draw.circle(surface, (60, 120, 255), (int(self.x), int(self.y) - 68), 5)

        # Speech bubble
        if self.bubble_text and self.bubble_timer > 0:
            txt_surf = font.render(self.bubble_text, True, (20, 20, 20))
            bw = txt_surf.get_width() + 10
            bh = txt_surf.get_height() + 6
            bx = int(self.x) - bw // 2
            by = int(self.y) - 72
            pygame.draw.rect(surface, (255, 255, 255), (bx, by, bw, bh), border_radius=5)
            pygame.draw.rect(surface, (180, 180, 180), (bx, by, bw, bh), 1, border_radius=5)
            if self.is_phone_chat:
                draw_phone_icon(surface, bx + bw + 6, by + bh // 2)
            else:
                tail_x = int(self.x)
                pygame.draw.polygon(surface, (255, 255, 255),
                                     [(tail_x - 4, by + bh), (tail_x + 4, by + bh), (tail_x, by + bh + 6)])
            surface.blit(txt_surf, (bx + 5, by + 3))


items = spawn_items()
npcs = [NPC(i, random.randint(BLOCK_SIZE + 40, WINDOW_WIDTH - BLOCK_SIZE - 40),
               random.randint(BLOCK_SIZE + 50, WINDOW_HEIGHT - BLOCK_SIZE - 40))
        for i in range(10)]
messages = []   # [(text, ttl_frames)]


# ── 昼夜颜色 ─────────────────────────────────────────
def sky_color(t):
    """t: 0~1，0=正午，0.5=午夜"""
    noon   = (180, 220, 255)
    sunset = (255, 140, 60)
    night  = (10, 10, 40)
    if t < 0.25:
        r = t / 0.25
        return lerp_color(noon, sunset, r)
    elif t < 0.5:
        r = (t - 0.25) / 0.25
        return lerp_color(sunset, night, r)
    elif t < 0.75:
        r = (t - 0.5) / 0.25
        return lerp_color(night, sunset, r)
    else:
        r = (t - 0.75) / 0.25
        return lerp_color(sunset, noon, r)


def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def ground_color(sky):
    return (max(0, sky[0] - 80), max(0, sky[1] - 60), max(0, sky[2] - 120))


def night_overlay_alpha(t):
    """夜晚时加深遮罩透明度"""
    if 0.35 < t < 0.65:
        mid = abs(t - 0.5) / 0.15
        return int((1 - mid) * 140)
    return 0


# ── 绘制函数 ──────────────────────────────────────────
def draw_phone_icon(surface, cx, cy):
    # Body
    pygame.draw.rect(surface, (30, 30, 30),
                     (cx - PHONE_ICON_W // 2, cy - PHONE_ICON_H // 2,
                      PHONE_ICON_W, PHONE_ICON_H), border_radius=2)
    # Screen
    pygame.draw.rect(surface, (100, 200, 255),
                     (cx - PHONE_ICON_W // 2 + 1, cy - PHONE_ICON_H // 2 + 2,
                      PHONE_ICON_W - 2, PHONE_ICON_H - 5))
    # Home button
    pygame.draw.circle(surface, (80, 80, 80),
                       (cx, cy + PHONE_ICON_H // 2 - 2), 1)


def draw_block(surface, x, y, color_base=(80, 80, 80)):
    c1 = color_base
    c2 = tuple(min(255, v + 40) for v in c1)
    c3 = tuple(min(255, v + 80) for v in c1)
    pygame.draw.rect(surface, c1, (x, y, BLOCK_SIZE, BLOCK_SIZE))
    pygame.draw.rect(surface, c2, (x + 2, y + 2, BLOCK_SIZE - 4, BLOCK_SIZE - 4))
    pygame.draw.rect(surface, c3, (x + 4, y + 4, BLOCK_SIZE - 8, BLOCK_SIZE - 8))
    pygame.draw.rect(surface, tuple(max(0, v - 20) for v in c1), (x, y, BLOCK_SIZE, BLOCK_SIZE), 2)


def draw_border(surface, t):
    day_ratio = 1 - min(1, abs(t - 0.5) * 4)
    base = (int(60 + 60 * day_ratio), int(50 + 30 * day_ratio), int(20 + 10 * day_ratio))
    for x in range(0, WINDOW_WIDTH, BLOCK_SIZE):
        draw_block(surface, x, 0, base)
        draw_block(surface, x, WINDOW_HEIGHT - BLOCK_SIZE, base)
    for y in range(BLOCK_SIZE, WINDOW_HEIGHT - BLOCK_SIZE, BLOCK_SIZE):
        draw_block(surface, 0, y, base)
        draw_block(surface, WINDOW_WIDTH - BLOCK_SIZE, y, base)


def draw_sun_moon(surface, t):
    # 太阳轨迹：t=0 正午在顶部，t=0.5 午夜
    angle = t * 2 * math.pi - math.pi / 2
    cx = WINDOW_WIDTH // 2 + int(math.cos(angle) * 320)
    cy = 80 + int(math.sin(angle) * 60)
    if t < 0.25 or t > 0.75:  # 白天
        pygame.draw.circle(surface, (255, 240, 100), (cx, cy), 22)
        pygame.draw.circle(surface, (255, 255, 180), (cx, cy), 16)
    else:  # 夜晚
        pygame.draw.circle(surface, (220, 220, 200), (cx, cy), 16)
        pygame.draw.circle(surface, (240, 240, 220), (cx, cy), 11)


def draw_stickman(surface, x, y, frm, mv, right):
    if mv:
        leg_a = math.sin(frm * 0.3) * 20
        arm_a = math.sin(frm * 0.3) * 25
    else:
        leg_a = arm_a = 0
    flip = 1 if right else -1

    head_r = 12
    head_y = y - 38
    pygame.draw.circle(surface, SKIN, (x, head_y), head_r)
    pygame.draw.arc(surface, HAIR, (x - head_r, head_y - head_r, head_r * 2, head_r * 2), 0, math.pi, 4)
    pygame.draw.circle(surface, BLACK, (x + flip * 4, head_y - 2), 2)
    pygame.draw.arc(surface, BLACK, (x - 5, head_y + 2, 10, 6), math.pi, 2 * math.pi, 1)

    body_top = y - 24
    body_bot = y + 4
    pygame.draw.rect(surface, SHIRT, (x - 9, body_top, 18, body_bot - body_top), border_radius=3)

    arm_len = 18
    for side in [-1, 1]:
        ar = math.radians(arm_a * side * flip)
        ex = x + side * (arm_len * math.cos(ar) + 9)
        ey = body_top + 8 + arm_len * math.sin(abs(ar))
        pygame.draw.line(surface, SKIN, (x + side * 9, body_top + 8), (int(ex), int(ey)), 4)
        pygame.draw.circle(surface, SKIN, (int(ex), int(ey)), 4)

    leg_len = 22
    for side in [-1, 1]:
        lr = math.radians(leg_a * side)
        ex = x + side * leg_len * math.sin(lr)
        ey = body_bot + leg_len * math.cos(abs(lr))
        pygame.draw.line(surface, PANTS, (x + side * 4, body_bot), (int(ex), int(ey)), 6)
        pygame.draw.ellipse(surface, SHOE, (int(ex) - 7, int(ey) - 3, 14, 7))


def draw_hud(surface, hunger, thirst, t):
    # 状态栏背景
    pygame.draw.rect(surface, (0, 0, 0, 160), (8, 8, 180, 56), border_radius=6)
    pygame.draw.rect(surface, (40, 40, 40), (8, 8, 180, 56), border_radius=6)

    # 饥饿条
    label = font.render("饥饿", True, (255, 200, 100))
    surface.blit(label, (14, 14))
    pygame.draw.rect(surface, (60, 30, 0), (60, 16, 120, 12), border_radius=4)
    pygame.draw.rect(surface, (220, 140, 0), (60, 16, int(120 * hunger / 100), 12), border_radius=4)

    # 口渴条
    label2 = font.render("口渴", True, (100, 180, 255))
    surface.blit(label2, (14, 36))
    pygame.draw.rect(surface, (0, 30, 80), (60, 38, 120, 12), border_radius=4)
    pygame.draw.rect(surface, (30, 140, 255), (60, 38, int(120 * thirst / 100), 12), border_radius=4)

    # 时间显示
    hour = int((t * 24)) % 24
    minute = int((t * 24 * 60) % 60)
    time_str = f"{'白天' if 6 <= hour < 18 else '夜晚'}  {hour:02d}:{minute:02d}"
    ts = font.render(time_str, True, (220, 220, 180))
    surface.blit(ts, (WINDOW_WIDTH - ts.get_width() - 12, 12))


def draw_messages(surface, msgs):
    y = WINDOW_HEIGHT // 2 - 60
    for text, _ in msgs:
        s = font_big.render(text, True, (255, 255, 100))
        surface.blit(s, (WINDOW_WIDTH // 2 - s.get_width() // 2, y))
        y += 30


# ── 主循环 ────────────────────────────────────────────
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    keys = pygame.key.get_pressed()
    moving = False

    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        player_x -= player_speed;  moving = True;  facing_right = False
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        player_x += player_speed;  moving = True;  facing_right = True
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        player_y -= player_speed;  moving = True
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        player_y += player_speed;  moving = True

    player_x = max(BLOCK_SIZE + 12, min(player_x, WINDOW_WIDTH - BLOCK_SIZE - 12))
    player_y = max(BLOCK_SIZE + 50, min(player_y, WINDOW_HEIGHT - BLOCK_SIZE - 12))

    if moving:
        frame += 1

    # 时间推进
    game_tick += 1
    day_t = (game_tick % day_length) / day_length  # 0~1

    # 属性自然衰减（每秒约 0.5）
    player_hunger = max(0, player_hunger - 0.008)
    player_thirst = max(0, player_thirst - 0.012)

    # 物品拾取
    for item in items:
        if item.alive and math.hypot(player_x - item.x, player_y - item.y) < 20:
            item.alive = False
            if item.kind == 'food':
                player_hunger = min(100, player_hunger + 30)
                messages.append(("吃到食物 +30 饱腹", 90))
            else:
                player_thirst = min(100, player_thirst + 35)
                messages.append(("喝到水 +35 解渴", 90))

    # NPC 更新
    for npc in npcs:
        result = npc.update(items, npcs, player_x, player_y, game_tick)
        if result == 'give_food':
            player_hunger = min(100, player_hunger + 25)
            messages.append(("NPC 给了你食物 +25", 90))

    # 物品耗尽后重新生成
    if all(not i.alive for i in items):
        items = spawn_items()
        messages.append(("新的资源出现了！", 90))

    # 消息计时
    messages = [(t, ttl - 1) for t, ttl in messages if ttl > 1]

    # ── 绘制 ──
    sky = sky_color(day_t)
    gnd = ground_color(sky)
    screen.fill(sky)

    # 地面
    pygame.draw.rect(screen, gnd, (BLOCK_SIZE, WINDOW_HEIGHT - BLOCK_SIZE * 2,
                                   WINDOW_WIDTH - BLOCK_SIZE * 2, BLOCK_SIZE))

    draw_sun_moon(screen, day_t)
    draw_border(screen, day_t)

    for item in items:
        item.draw(screen)

    draw_stickman(screen, player_x, player_y, frame, moving, facing_right)

    for npc in npcs:
        npc.draw(screen)

    # 夜晚遮罩
    alpha = night_overlay_alpha(day_t)
    if alpha > 0:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, alpha))
        screen.blit(overlay, (0, 0))

    draw_hud(screen, player_hunger, player_thirst, day_t)
    draw_messages(screen, messages)

    hint = font.render("WASD/方向键移动  |  靠近物品自动拾取  |  ESC退出", True, (180, 180, 180))
    screen.blit(hint, (WINDOW_WIDTH // 2 - hint.get_width() // 2, WINDOW_HEIGHT - 24))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
