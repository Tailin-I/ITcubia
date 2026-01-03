import logging

import arcade
from typing import List
from .event import GameEvent
from .chest_event import ChestEvent
from .teleport_event import TeleportEvent
from config import  constants as C
from ..core.resource_manager import resource_manager
from ..ui.notification_system import notifications as ns


class EventManager:
    def __init__(self):
        """Инициализация менеджера событий."""
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

        self.rm = resource_manager
        self.tile_size = C.TILE_SIZE

        # Логика событий (зоны взаимодействия из event Layer)
        self.events: List[GameEvent] = []

        # Визуальные спрайты (будут созданы из Tile Layer "chests_visual")
        self.chest_sprites = arcade.SpriteList()

    def load_events_from_objects(self, object_list, scale: float = 1.0):
        """Загружает события (зоны взаимодействия) из events"""
        for i, obj in enumerate(object_list):
            event = self._create_event_from_object(obj, scale, i)
            if event:
                self.events.append(event)

    def _create_event_from_object(self, obj, scale: float, index: int):
        """Создаёт события"""
        try:
            if hasattr(obj, 'shape') and isinstance(obj.shape, list) and len(obj.shape) >= 4:
                points = obj.shape

                left = points[0][0]
                top = points[0][1]
                right = points[1][0]
                bottom = points[3][1]

                width = right - left
                height = bottom - top

                x = left
                y = top

                if height < 0:
                    height = abs(height)
                    y = bottom


            else:
                x = getattr(obj, 'x', 0) * scale
                y = getattr(obj, 'y', 0) * scale
                width = getattr(obj, 'width', self.tile_size) * scale
                height = getattr(obj, 'height', self.tile_size) * scale

            # Получаем свойства
            properties = getattr(obj, 'properties', {})
            event_type = getattr(obj, 'type', 'trigger').lower()
            name = getattr(obj, 'name','!')
            event_id = properties.get('id', f"{event_type}_{index}")

            # Создаем событие
            if event_type == "chest":
                return ChestEvent(event_id, name, (x, y, width, height), properties)
            elif event_type == "teleport":
                return TeleportEvent(event_id, name,(x, y, width, height), properties)
            else:
                return GameEvent(event_id, name, event_type, (x, y, width, height), properties)

        except Exception as e:
            self.logger.warning(f"❌ Ошибка создания события {index}: {e}")
            return None

    def find_nearest_chest_event(self, x: float, y: float, max_distance: float = None):
        """Находит ближайшее событие сундука к координатам."""
        if max_distance is None:
            max_distance = self.tile_size * 3

        nearest_event = None
        min_distance = float('inf')

        for event in self.events:
            if event.type == "chest":

                # Вычисляем расстояние
                distance = ((x - event.center_x) ** 2 + (y - event.center_y) ** 2) ** 0.5

                if distance < min_distance and distance <= max_distance:
                    min_distance = distance
                    nearest_event = event

        return nearest_event

    def update(self, delta_time: float):
        """Обновляет логику событий"""
        for event in self.events:
            event.update(delta_time)

        # Обновляем визуалы сундуков
        for sprite in self.chest_sprites:
            if hasattr(sprite, 'update_visual'):
                sprite.update_visual()

    def check_collisions(self, player, game_state):
        """Проверяет коллизии игрока с событиями"""
        if not player:
            return

        player_rect = (
            player.center_x - player.width / 2,
            player.center_y - player.height / 2,
            player.width,
            player.height
        )



        for event in self.events:
            if event.check_collision(player_rect):


                # ДЛЯ ВСЕХ СОБЫТИЙ проверяем дистанцию через общий метод
                if self._is_player_close_enough(player, event):
                    # Для сундуков проверяем кнопку взаимодействия
                    if event.type == "chest":
                        event.show_text_description = True
                        if hasattr(player, 'input_manager') and player.input_manager:
                            if player.input_manager.get_action('select'):
                                event.activate(player, game_state)
                                player.input_manager.reset_action("select")
                    else:
                        # Для других событий (телепортов) активируем сразу
                        event.activate(player, game_state)


    def _is_player_close_enough(self, player, event) -> bool:
        """Проверяет, достаточно ли близко игрок к событию."""

        # Дистанция
        distance = ((player.center_x - event.center_x) ** 2 +
                    (player.center_y - event.center_y) ** 2) ** 0.5

        # Максимальная дистанция для взаимодействия
        max_distance = self.tile_size * 1.5

        return distance <= max_distance

    def draw(self):
        """Отрисовывает визуальные элементы событий"""
        self.chest_sprites.draw()

        for i in self.events:
            if i.type == "chest":
                i.draw_names()

        if C.show_area_mode:
            for i in self.events:
                i.draw_debug()
