# Window
WINDOW_WIDTH  = 1400
WINDOW_HEIGHT = 900
PANEL_WIDTH   = 260   # right-side character panel

# World
WORLD_WIDTH  = 3000
WORLD_HEIGHT = 3000

# Camera free-roam speed
CAMERA_SPEED = 4.0

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# NPC dot colors
NPC_COLORS = [
    (220, 60,  60),  (60,  200, 80),  (200, 160, 50),  (180, 60,  200),
    (60,  200, 200), (200, 200, 60),  (200, 80,  150),  (100, 110, 220),
    (80,  180, 100), (220, 130, 80),
]

NPC_NAMES   = ['小明', '小红', '小刚', '小丽', '小华', '小芳', '小强', '小燕', '小龙', '小梅',
               '小峰', '小云', '小杰', '小雪', '小磊', '小琴', '小涛', '小玲', '小博', '小慧']
NPC_GENDERS = ['男', '女']
NPC_MARITAL = ['未婚', '已婚', '离异']
NPC_JOBS    = ['便利店', '超市', '药店', '餐厅', '书店', '科技公司', '银行', '设计公司', '贸易公司', '无业']

# Chat lines
CHAT_STRANGER     = ['你好！', '嗨～', '初次见面', '你也在这里？']
CHAT_ACQUAINTANCE = ['今天天气不错', '饿了吗？', '最近怎么样？', '一起走走？']
CHAT_FRIEND       = ['好久不见！', '我就知道是你', '又见面了～', '想你了！', '咱们去找吃的？']
CHAT_PHONE        = ['在干嘛～', '想你了', '出来玩？', '刚吃完饭', '你在哪呢',
                     '哈哈哈哈', '好的好的', '等我一下', '今天好无聊', '发你个表情包']
CHAT_CONFLICT     = ['哼！', '你什么意思！', '烦死了']

# Relationship
FRIEND_THRESHOLD       = 10
ACQUAINTANCE_THRESHOLD = 3
DECAY_INTERVAL         = 1800
DECAY_AMOUNT           = 1
CONFLICT_PROB          = 0.0003
CONFLICT_DAMAGE_MIN    = 2
CONFLICT_DAMAGE_MAX    = 5
PHONE_COOLDOWN_MIN     = 600
PHONE_COOLDOWN_MAX     = 1200

# Day/night
DAY_LENGTH = 3600
