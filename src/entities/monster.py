import math
import random
from random import randint
from typing import Tuple
from .base_entity import Entity
from ..core.resource_manager import resource_manager
from ..core.game_data import game_data
from ..ui.health_bar import HealthBar
from ..ui.notification_system import notifications as ns


class Monster(Entity):
    """Простой монстр"""

    def __init__(self, monster_id: str, monster_type: str, position: list[float], properties=None, scale=1.0):
        # Грузим текстуру
        self.return_timer = 0
        self.wander_timer = 0
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

        # Свойства зоны
        self.zone_id = None
        self.zone_rect: Tuple[float,float,float,float] = (0,0,0,0)

        # Состояние поведения
        self.current_state = "idle"  # idle, chase, return
        self.current_action = None
        self.action_timer = 0

        # Для возврата в зону
        self.return_target = None

        # Для уникализации диалога
        self.dialogue_said = False

        # Загружаем свойства из GameData
        self._load_properties_from_data()

        self.health_bar = HealthBar(
            self,
            x= position[0],
            y=position[1] + self.height,
            width=100,
            height=10,
            font_size=8,
            border=1
        )

        if not self.is_alive:
            self.visible = False
            self.logger.info(f"Монстр {monster_id} уже мертв")

    def _load_properties_from_data(self):
        """Загружает свойства из GameData"""
        data = self.data_source.get_entity_data(self.entity_id)
        if data:
            # Устанавливаем свойства как атрибуты
            for key, value in data.items():
                if key not in ["id", "type", "position"]:  # Исключаем базовые поля
                    setattr(self, key, value)

            # Если монстр мертв - скрываем
            if not data.get("is_alive", True):
                self.visible = False

    def interact(self):
        """Взаимодействие с игроком - двусторонний урон"""
        data = self.data_source.get_entity_data(self.entity_id)
        if data and data.get("is_alive", True):
            # Монстр наносит урон игроку
            monster_damage = data.get("damage", 1)
            game_data.take_damage(monster_damage)

            # Игрок наносит урон монстру
            player_damage = game_data.player_data.get("strength", 1)
            current_health = data.get("health", 1)

            # Обновляем здоровье монстра
            new_health = max(0, current_health - player_damage)
            data["health"] = new_health

            # Если здоровье закончилось - монстр умирает
            if new_health <= 0:
                # ВАЖНО: используем сеттер, который сохранит в game_data
                self.is_alive = False  # Это вызовет сеттер
                self.visible = False
                ns.notification(f"Монстр побежден!")

                # Добавляем опыт
                exp_reward = 10
                game_data.add_exp(exp_reward)

            ns.notification(f"Вы получили {monster_damage} урона, монстр получил {player_damage}")
    # Также добавим метод для обработки смерти в update:
    def update(self, delta_time: float = 1 / 60, player=None, collision_layer=None):
        """Обновление с поддержкой поведения"""
        super().update(delta_time)

        # Обновляем полоску здоровья
        self.health_bar.x = self.center_x
        self.health_bar.y = self.center_y + self.height

        # Основная логика поведения
        if self._can_see_player(player):
            if self.dialogue_said:
                self
            self.current_state = "chase"
            self._chase_player(player, delta_time)
        elif not self._is_point_in_zone():
            self.current_state = "return"
            self._return_to_zone(delta_time)
        else:
            self.current_state = "idle"
            self._wander_behavior(delta_time)

        # Обновляем таймеры
        self.wander_timer -= delta_time
        if self.return_timer > 0:
            self.return_timer -= delta_time

    def draw(self):

        self.health_bar.draw()


    def _chase_player(self, player, delta_time):
        """Преследование игрока"""
        if not hasattr(self, 'chase_speed') or not player:
            return

        # Вычисляем направление к игроку
        dx = player.center_x - self.center_x
        dy = player.center_y - self.center_y

        # Нормализуем направление
        distance = (dx ** 2 + dy ** 2) ** 0.5
        if distance > 0:
            dx = dx / distance
            dy = dy / distance

            # Двигаем монстра
            self.center_x += dx * self.chase_speed * delta_time * 60
            self.center_y += dy * self.chase_speed * delta_time * 60

    def _return_to_zone(self, delta_time):
        """Возврат в свою зону"""
        # Определяем целевую позицию в зоне (центр зоны)
        zone_x, zone_y, zone_w, zone_h = self.zone_rect
        target_x = zone_x + zone_w / 2
        target_y = zone_y + zone_h / 2

        # Вычисляем направление к центру зоны
        dx = target_x - self.center_x
        dy = target_y - self.center_y

        # Нормализуем и двигаемся
        distance = (dx ** 2 + dy ** 2) ** 0.5
        if distance > 0:
            dx = dx / distance
            dy = dy / distance

            # Двигаем монстра к зоне (медленнее чем преследование)
            return_speed = getattr(self, 'speed', 1.5)
            self.center_x += dx * return_speed * delta_time * 60
            self.center_y += dy * return_speed * delta_time * 60

            # Если вернулись в зону, сбрасываем состояние
            if self._is_point_in_zone():
                self.current_state = "idle"

    def _wander_behavior(self, delta_time):
        """Случайное блуждание в зоне"""
        if self.wander_timer <= 0:
            # Выбираем случайное направление или стоим на месте
            roll = randint(0, 5)
            if roll < 4:  # 0-3: двигаемся
                angle = random.uniform(0, 2 * 3.14159)
                speed = getattr(self, 'speed', 1.0) * 0.5  # Медленнее чем обычная скорость
                self.wander_direction = (
                    math.cos(angle) * speed,
                    math.sin(angle) * speed
                )
            else:  # 4-5: стоим на месте
                self.wander_direction = (0, 0)

            # Устанавливаем новый таймер
            self.wander_timer = random.uniform(1.0, 3.0)  # От 1 до 3 секунд

        # Двигаемся в выбранном направлении
        if hasattr(self, 'speed'):
            self.center_x += self.wander_direction[0] * delta_time * 60
            self.center_y += self.wander_direction[1] * delta_time * 60

            # Проверяем, не вышел ли за зону
            if not self._is_point_in_zone():
                # Если вышел, возвращаем назад
                self.current_state = "return"

    def _update_behavior(self, delta_time, player, collision_layer):
        """Обновляет поведение монстра"""
        # Базовое поведение
        # Пока просто стоим на месте
        pass

    def _is_point_in_zone(self):
        """Проверяет, находится ли точка в зоне монстра"""
        if not self.zone_rect:
            return True  # Если зоны нет, считаем что везде можно

        zone_x, zone_y, zone_w, zone_h = self.zone_rect
        zone_h = abs(zone_h)
        zone_y -= zone_h

        return (zone_x <= self.center_x <= zone_x + zone_w and
                zone_y <= self.center_y <= zone_y + zone_h)

    def _can_see_player(self, player) -> bool:
        """Может ли монстр видеть игрока"""
        if not player:
            return False

        distance = self._get_distance_to_player(player)

        # Проверяем зрение
        if distance > self.vision_range:
            return False

        # TODO: Добавить проверку на препятствия (стены)
        return True

    def _get_distance_to_player(self, player):
        """Расстояние до игрока"""
        return ((self.center_x - player.center_x) ** 2 +
                (self.center_y - player.center_y) ** 2) ** 0.5

    @property
    def chase_speed(self):
        """Читаем из GameData, не копируем"""
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("chase_speed")

    @chase_speed.setter
    def chase_speed(self, value):
        data = self.data_source.get_entity_data(self.entity_id)
        data["chase_speed"] = value

    @property
    def vision_range(self):
        """Читаем из GameData, не копируем"""
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("vision_range")

    @vision_range.setter
    def vision_range(self, value):
        data = self.data_source.get_entity_data(self.entity_id)
        data["vision_range"] = value