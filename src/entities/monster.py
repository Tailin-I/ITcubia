import arcade
from .base_entity import Entity
from ..core.resource_manager import resource_manager
from ..core.game_data import game_data


class Monster(Entity):
    """Простой монстр"""

    def __init__(self, monster_type: str, position, properties=None, scale=1.0):
        # Грузим текстуру (пока везде bug.png)
        texture = resource_manager.load_texture("monsters/bug.png")

        # Entity
        super().__init__([texture], scale=scale)

        self.center_x, self.center_y = position

        # Характеристики из Tiled или дефолтные
        self.health = properties.get('health', 20) if properties else 20
        self.max_health = self.health
        self.damage = properties.get('damage', 1) if properties else 1

    def interact(self):
        game_data.take_damage(self.damage)

    def update(self, delta_time: float = 1 / 60, player=None, collision_layer=None):
        """Ничего не делаем - просто висим"""
        pass