import logging
import arcade

from ..core.game_data import game_data


class Entity(arcade.Sprite):
    """Главный класс для всех сущностей"""

    def __init__(self, entity_id, texture_list, scale=1):
        super().__init__(texture_list[0], scale)
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

        self.entity_id = entity_id
        self.data_source = game_data  # Ссылка на центральное хранилище

        # Сохраняем текстуры для анимации
        self.textures = texture_list
        self.cur_texture_index = 0
        self.time_elapsed = 0

    @property
    def health(self):
        """Читаем из GameData, не копируем"""
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("health", 0) if data else 0

    @property
    def max_health(self):
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("max_health", 100) if data else 100

    @property
    def is_alive(self):
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("is_alive", True) if data else True

    def update(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:
        """Базовое обновление"""
        self.time_elapsed += delta_time