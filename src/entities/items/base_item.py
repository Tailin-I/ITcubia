from ..base_entity import Entity
import arcade
from typing import Dict, Any



class Item(Entity):
    """Базовый класс для всех предметов"""

    def __init__(self, item_id: str, name: str, texture_path: str, scale: float = 1.0):
        # Загружаем текстуру
        texture = arcade.load_texture(texture_path)
        super().__init__(item_id, [texture], scale)


        self.item_id = item_id
        self.name = name
        self.description = ""
        self.is_stackable = True
        self.max_stack = 99
        self.count = 1

        # Флаги
        self.is_equippable = False
        self.is_consumable = False
        self.is_quest_item = False

    def use(self, user):
        """Использовать предмет"""

    def get_info(self) -> Dict[str, Any]:
        """Возвращает информацию о предмете для UI"""
        return {
            "id": self.item_id,
            "name": self.name,
            "description": self.description,
            "count": self.count,
            "stackable": self.is_stackable
        }

    def __str__(self):
        return f"{self.name} (x{self.count})"
