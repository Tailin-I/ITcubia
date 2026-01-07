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
        self.data = game_data.get_entity_data(self.entity_id)



    @property
    def health(self):
        """Читаем из GameData, не копируем"""
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("health", 0) if data else 0

    @health.setter
    def health(self, value):
        data = self.data_source.get_entity_data(self.entity_id)
        data["health"] = value

    @property
    def max_health(self):
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("max_health", 100) if data else 100

    @max_health.setter
    def max_health(self, value):
        data = self.data_source.get_entity_data(self.entity_id)
        data["max_health"] = value

    @property
    def is_alive(self):
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("is_alive", True) if data else True

    @is_alive.setter
    def is_alive(self, value: bool):
        data = self.data_source.get_entity_data(self.entity_id)
        data["is_alive"] = value
        self.logger.debug(f"Монстр {self.entity_id}: is_alive = {value}")


    @property
    def change_x(self):
        """Читаем из GameData, не копируем"""
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("position")[0]

    @change_x.setter
    def change_x(self, value):
        data = self.data_source.get_entity_data(self.entity_id)
        data.get("position")[0] = value

    @property
    def change_y(self):
        """Читаем из GameData, не копируем"""
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("position")[1]

    @change_y.setter
    def change_y(self, value):
        data = self.data_source.get_entity_data(self.entity_id)
        data.get("position")[1] = value



    def update(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:
        """Базовое обновление"""
        self.time_elapsed += delta_time

