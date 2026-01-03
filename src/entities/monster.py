from .base_entity import Entity
from ..core.resource_manager import resource_manager
from ..core.game_data import game_data


class Monster(Entity):
    """Простой монстр"""

    def __init__(self, monster_id: str, monster_type: str, position, properties=None, scale=1.0):
        # Грузим текстуру
        texture = resource_manager.load_texture("monsters/bug.png")

        # Создаём Entity с уникальным ID
        super().__init__(
            entity_id=monster_id,
            texture_list=[texture],
            scale=scale
        )

        # Позиция
        self.center_x, self.center_y = position
        self.monster_type = monster_type

        # Регистрируем в GameData
        self._register_in_game_data(properties)

    def _register_in_game_data(self, properties):
        """Создаем запись в GameData"""
        monster_data = {
            "id": self.entity_id,
            "type": self.monster_type,
            "position": {"x": self.center_x, "y": self.center_y},
            "health": properties.get('health', 20) if properties else 20,
            "max_health": properties.get('health', 20) if properties else 20,
            "damage": properties.get('damage', 1) if properties else 1,
            "is_alive": True
        }

        game_data.add_monster(self.entity_id, monster_data)

    def interact(self):
        """Взаимодействие с игроком"""
        data = self.data_source.get_entity_data(self.entity_id)
        if data and data.get("is_alive", True):
            # Берем урон из данных монстра
            damage = data.get("damage", 1)
            # Наносим урон игроку
            game_data.take_damage(damage)

    def update(self, delta_time: float = 1 / 60, player=None, collision_layer=None):
        """Базовая логика монстра"""
        super().update(delta_time)

        # Проверяем жив ли монстр
        if not self.is_alive:
            self.visible = False
            return