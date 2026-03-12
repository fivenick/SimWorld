import math
import random
from constants import (
    NPC_COLORS, NPC_NAMES, NPC_GENDERS, NPC_MARITAL, NPC_JOBS,
    CHAT_STRANGER, CHAT_ACQUAINTANCE, CHAT_FRIEND, CHAT_PHONE, CHAT_CONFLICT,
    FRIEND_THRESHOLD, ACQUAINTANCE_THRESHOLD,
    DECAY_INTERVAL, DECAY_AMOUNT,
    CONFLICT_PROB, CONFLICT_DAMAGE_MIN, CONFLICT_DAMAGE_MAX,
    PHONE_COOLDOWN_MIN, PHONE_COOLDOWN_MAX,
    WORLD_WIDTH, WORLD_HEIGHT,
)


class NPC:
    def __init__(self, npc_id, x, y):
        self.id    = npc_id
        self.x     = float(x)
        self.y     = float(y)
        self.color = NPC_COLORS[npc_id % len(NPC_COLORS)]
        self.name  = NPC_NAMES[npc_id % len(NPC_NAMES)]

        # ── 个人属性 ──────────────────────────────────
        self.gender  = random.choice(NPC_GENDERS)
        self.marital = random.choice(NPC_MARITAL)
        self.job     = random.choice(NPC_JOBS)
        self.balance = random.randint(500, 50000)   # 银行卡余额
        self.age     = random.randint(18, 60)

        # ── 状态 ──────────────────────────────────────
        self.hunger  = random.uniform(60, 100)
        self.thirst  = random.uniform(60, 100)
        self.state   = 'wander'
        self.state_timer = 0
        self.target_npc  = None

        self.chat_cooldown       = 0
        self.phone_chat_cooldown = 0
        self.speed = 1.0
        self.dx = 0.0
        self.dy = 0.0

        self.bubble_text  = ''
        self.bubble_timer = 0
        self.is_phone_chat = False

        self.relationships  = {}   # {other_id: int}
        self.phone_contacts = set()
        self.last_chat_tick = {}   # {other_id: int}

    # ── 关系工具 ──────────────────────────────────────

    def friendship_level(self, other_id):
        count = self.relationships.get(other_id, 0)
        if count >= FRIEND_THRESHOLD:       return 'friend'
        if count >= ACQUAINTANCE_THRESHOLD: return 'acquaintance'
        return 'stranger'

    def _record_chat(self, other, tick, phone=False):
        self.relationships[other.id]  = self.relationships.get(other.id, 0) + 1
        other.relationships[self.id]  = other.relationships.get(self.id, 0) + 1
        self.last_chat_tick[other.id]  = tick
        other.last_chat_tick[self.id]  = tick
        self.is_phone_chat  = phone
        other.is_phone_chat = phone
        if (self.relationships[other.id] >= FRIEND_THRESHOLD
                and other.id not in self.phone_contacts):
            self.phone_contacts.add(other.id)
            other.phone_contacts.add(self.id)

    def _start_chat(self, other, tick, phone=False):
        lines = {
            'stranger':     CHAT_STRANGER,
            'acquaintance': CHAT_ACQUAINTANCE,
            'friend':       CHAT_FRIEND,
        }
        if phone:
            self.bubble_text  = random.choice(CHAT_PHONE)
            other.bubble_text = random.choice(CHAT_PHONE)
            self.chat_cooldown  = random.randint(PHONE_COOLDOWN_MIN, PHONE_COOLDOWN_MAX)
            other.chat_cooldown = random.randint(PHONE_COOLDOWN_MIN, PHONE_COOLDOWN_MAX)
        else:
            self.bubble_text  = random.choice(lines[self.friendship_level(other.id)])
            other.bubble_text = random.choice(lines[other.friendship_level(self.id)])
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
            self.last_chat_tick[other_id] = tick
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

    # ── 每帧更新 ──────────────────────────────────────

    def update(self, npcs, tick):
        self.hunger = max(0, self.hunger - 0.004)
        self.thirst = max(0, self.thirst - 0.006)
        if self.chat_cooldown > 0:       self.chat_cooldown -= 1
        if self.phone_chat_cooldown > 0: self.phone_chat_cooldown -= 1
        if self.bubble_timer > 0:
            self.bubble_timer -= 1
        else:
            self.bubble_text = ''

        for other_id in list(self.relationships.keys()):
            self._apply_decay(other_id, tick)

        if self.relationships and random.random() < CONFLICT_PROB:
            cid  = random.choice(list(self.relationships.keys()))
            cnpc = next((n for n in npcs if n.id == cid), None)
            if cnpc:
                self._trigger_conflict(cnpc)

        if self.state != 'chat':
            if self.chat_cooldown == 0:
                # 电话聊天
                if self.phone_contacts and self.phone_chat_cooldown == 0:
                    cid  = random.choice(list(self.phone_contacts))
                    cnpc = next((n for n in npcs if n.id == cid
                                 and n.chat_cooldown == 0
                                 and n.phone_chat_cooldown == 0), None)
                    if cnpc:
                        self._start_chat(cnpc, tick, phone=True)
                        self.phone_chat_cooldown = random.randint(PHONE_COOLDOWN_MIN, PHONE_COOLDOWN_MAX)
                        cnpc.phone_chat_cooldown = random.randint(PHONE_COOLDOWN_MIN, PHONE_COOLDOWN_MAX)

                # 主动找朋友
                best, best_d = None, float('inf')
                for other in npcs:
                    if other is not self and other.chat_cooldown == 0:
                        d = math.hypot(self.x - other.x, self.y - other.y)
                        if d < 120 and self.friendship_level(other.id) == 'friend' and d < best_d:
                            best, best_d = other, d
                if best:
                    self.state      = 'seek_friend'
                    self.target_npc = best
                else:
                    for other in npcs:
                        if other is not self and math.hypot(self.x - other.x, self.y - other.y) < 30:
                            self._start_chat(other, tick)
                            break
                    else:
                        if self.state != 'seek_friend':
                            self.state = 'wander'

        if self.state == 'wander':
            self.state_timer -= 1
            if self.state_timer <= 0:
                angle = random.uniform(0, 2 * math.pi)
                self.dx = math.cos(angle) * self.speed
                self.dy = math.sin(angle) * self.speed
                self.state_timer = random.randint(120, 240)
            self.x += self.dx
            self.y += self.dy

        elif self.state == 'chat':
            if self.bubble_timer <= 0:
                self.state      = 'wander'
                self.target_npc = None

        elif self.state == 'seek_friend':
            if self.target_npc is None or self.chat_cooldown > 0:
                self.state = 'wander'
            else:
                d = math.hypot(self.x - self.target_npc.x, self.y - self.target_npc.y)
                if d < 16:
                    self._start_chat(self.target_npc, tick)
                elif d > 300:
                    self.state = 'wander'
                    self.target_npc = None
                else:
                    self.x += (self.target_npc.x - self.x) / d * self.speed
                    self.y += (self.target_npc.y - self.y) / d * self.speed

        self.x = max(10, min(self.x, WORLD_WIDTH  - 10))
        self.y = max(10, min(self.y, WORLD_HEIGHT - 10))
