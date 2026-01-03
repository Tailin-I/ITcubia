import logging

import arcade
from ..core.resource_manager import resource_manager


class Entity(arcade.Sprite):
    """Главный класс для всех сущностей"""

    def __init__(self, texture_list, scale):
        super().__init__(texture_list[0], scale)
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

        self.rm = resource_manager

        self.time_elapsed = 0  # задержка времени для анимации

        # Базовые параметры
        self.level = 1
        self.exp = 0
        self.max_health = 99
        self.health = self.max_health
        self.speed = 0
        self.strength = 1

        self.is_alive = True
        self.direction = "down"

        # Инициализируем текстуры для анимации
        self.textures = texture_list
        self.cur_texture_index = 0


    def update(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:
        """Базовое обновление - можно переопределять в дочерних классах"""
        pass
