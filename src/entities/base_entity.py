import logging
import arcade

from ..core.game_data import game_data


class Entity(arcade.Sprite):
    """Главный класс для всех сущностей"""

    def __init__(self, entity_id, texture_list, scale=1):

        super().__init__(texture_list[0], scale)
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.data_source = game_data
        self.data = self.data_source.get_entity_data(entity_id)

        self.entity_id = entity_id
        # Сохраняем текстуры для анимации
        self.textures = texture_list
        self.cur_texture_index = 0
        self.time_elapsed = 0

    @property
    def name(self):
        return self.data.get("name")

    @name.setter
    def name(self, value):
        self.data["name"] = value

    @property
    def health(self):
        return self.data.get("health", 0)

    @health.setter
    def health(self, value):
        self.data["health"] = value

    @property
    def max_health(self):
        return self.data.get("max_health", 100)

    @max_health.setter
    def max_health(self, value):
        self.data["max_health"] = value

    @property
    def damage(self):
        return self.data.get("damage", 0)

    @damage.setter
    def damage(self, value):
        self.data["damage"] = value

    @property
    def behavior(self):
        return self.data.get("behavior", "passive")

    @behavior.setter
    def behavior(self, value):
        self.data["behavior"] = value

    @property
    def is_alive(self):
        return self.data.get("is_alive", True)

    @is_alive.setter
    def is_alive(self, value: bool):
        self.data["is_alive"] = value


    @property
    def change_x(self):
        return self.data.get("position")[0]

    @change_x.setter
    def change_x(self, value):
        self.data.get("position")[0] = value

    @property
    def change_y(self):
        return self.data.get("position")[1]

    @change_y.setter
    def change_y(self, value):
        self.data.get("position")[1] = value

    @property
    def active_topic(self):
        return self.data.get("active_topic", "greeting")

    @active_topic.setter
    def active_topic(self, value):
        self.data["active_topic"] = value

    @property
    def can_dialogue(self):
        return self.data.get("can_dialogue", False)

    @can_dialogue.setter
    def can_dialogue(self, value):
        self.data["can_dialogue"] = value

    @property
    def speed(self):
        return self.data.get("speed")

    @speed.setter
    def speed(self, value):
        self.data["speed"] = value

    def update(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:
        """Базовое обновление"""
        self.time_elapsed += delta_time

