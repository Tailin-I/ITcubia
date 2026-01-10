from ..base_entity import Entity
import arcade
from typing import Dict, Any



class Item(Entity):
    """Базовый класс для всех предметов"""

    def __init__(self, item_id: str, name: str,  texture=None, scale: float = 1.0):
        # Сохраняем текстуру
        self._texture = texture

        # Создаем список текстур для Entity
        texture_list = [texture] if texture else []
        super().__init__(item_id, texture_list, scale)
        self.data = {}

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

    def use(self, player):
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

    @property
    def texture(self):
        return self._texture