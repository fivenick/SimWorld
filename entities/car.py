import random
from constants import WORLD_WIDTH, WORLD_HEIGHT

CAR_COLORS = [
    (220, 50,  50),   # red
    (50,  80,  220),  # blue
    (220, 200, 50),   # yellow
    (50,  180, 80),   # green
    (200, 200, 200),  # white
    (60,  60,  60),   # black
    (200, 120, 50),   # orange
]


class Car:
    def __init__(self, car_id, road_type, x, y, direction):
        """
        road_type: 'h' (horizontal) or 'v' (vertical)
        direction: 1 (right/down) or -1 (left/up)
        """
        self.id = car_id
        self.x = float(x)
        self.y = float(y)
        self.road_type = road_type
        self.direction = direction
        self.speed = random.uniform(1.2, 2.5)
        self.color = CAR_COLORS[car_id % len(CAR_COLORS)]
        self.road_center = y if road_type == 'h' else x

    def update(self):
        if self.road_type == 'h':
            self.x += self.speed * self.direction
            if self.x > WORLD_WIDTH + 20:
                self.x = -20.0
            elif self.x < -20:
                self.x = float(WORLD_WIDTH + 20)
        else:
            self.y += self.speed * self.direction
            if self.y > WORLD_HEIGHT + 20:
                self.y = -20.0
            elif self.y < -20:
                self.y = float(WORLD_HEIGHT + 20)
