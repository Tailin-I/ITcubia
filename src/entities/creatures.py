import math
import random
from random import randint
from typing import Tuple

import arcade

from config.creature_config import CreatureConfig as MC
from .base_entity import Entity
from ..core.asset_loader import AssetLoader
from ..core.resource_manager import resource_manager
from ..core.game_data import game_data
from ..ui.health_bar import HealthBar
from ..ui.notification_system import notifications as ns
from config import constants as C


class Creature(Entity):
    """Простой монстр"""

    def __init__(self, creature_id: str, mob_name: str, creature_type: str, position: list[float], properties=None,
                 scale=1.0):
        # Грузим текстуру

        # Получаем имя существа
        self.creature_name = mob_name
        self.wander_direction = (0, 0)

        # Получаем имя существа
        self.creature_name = mob_name

        # Определяем, является ли существо NPC (по типу)
        is_npc = creature_type == "npc"

        # Для NPC используем имя, для остальных - тип существа
        texture_to_load = mob_name if is_npc else creature_type

        # Загружаем спрайты через AssetLoader
        asset_loader = AssetLoader()

        try:
            sprite_size = MC.get_sprite_size(texture_to_load)
            texture_dict = asset_loader.load_creature_sprites(texture_to_load, sprite_size)
        except:
            # Fallback на дефолт
            sprite_size = MC.get_sprite_size("default")
            texture_dict = asset_loader.load_creature_sprites("default", sprite_size)

        # Собираем все текстуры в один список для Entity
        all_textures = []
        for direction in ["up", "down", "left", "right"]:
            if direction in texture_dict:  # <-- Проверка на случай ошибки
                all_textures.extend(texture_dict[direction])
            else:
                all_textures.extend([texture_dict.get("down", [None])[0]] * 2)

        # Сохраняем texture_dict для анимации
        self.texture_dict = texture_dict
        self.animation_speed = MC.get_animation_speed(self.creature_name)

        # Создаём Entity
        super().__init__(
            entity_id=creature_id,
            texture_list=all_textures,
            scale=scale
        )

        # Инициализация анимации
        self.texture_indexes = {
            "up": 0,  # текстуры 0 и 1
            "down": 2,  # текстуры 2 и 3
            "left": 4,  # текстуры 4 и 5
            "right": 6  # текстуры 6 и 7
        }
        self.last_direction = "down"
        self.cur_texture_index = self.texture_indexes["down"]
        self.is_moving = False

        self.return_timer = 0
        self.wander_timer = 0

        # Таймеры для диалогов
        self.dialogue_said = False
        self.last_dialogue_time = 0
        self.dialogue_cooldown = 3.0  # 3 секунды между диалогами
        # Позиция
        self.center_x, self.center_y = position
        self.creature_type = creature_type

        # Свойства зоны
        self.zone_id = None
        self.zone_rect: Tuple[float, float, float, float] = (0, 0, 0, 0)

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
            x=position[0],
            y=position[1] + self.height,
            width=100,
            height=10,
            font_size=8,
            border=1
        )

        if not self.is_alive:
            self.visible = False
            self.logger.info(f"Монстр {creature_id} уже мертв")

        self.can_start_dialogue = False

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

    def _combat_interaction(self, player):
        """Взаимодействие с игроком - двусторонний урон"""
        if self.is_alive:
            # Монстр наносит урон игроку
            game_data.take_damage(self.damage)
            self.health = max(0, self.health - player.damage)

            # Если здоровье закончилось - монстр умирает
            if self.health <= 0:
                # ВАЖНО: используем сеттер, который сохранит в game_data
                self.is_alive = False  # Это вызовет сеттер
                self.visible = False
                ns.notification(f"Монстр побежден!")

                # Добавляем опыт
                exp_reward = 10
                game_data.add_exp(exp_reward)
                self._drop_loot()

    # Добавим новый метод для выпадения лута:
    def _drop_loot(self):
        """Выпадение лута из монстра"""
        # Получаем таблицу лута из данных монстра
        loot_table = getattr(self, 'loot_table', [])

        for loot_item in loot_table:
            if ':' in loot_item:
                item_id, count_str = loot_item.split(':')
                try:
                    count = int(count_str)
                    game_data.add_item(item_id.strip(), item_id.strip(), count, True)
                except ValueError:
                    pass

    def interact(self, player):
        """Взаимодействие с существом"""
        if not self.is_alive:
            return False

        # Если существо агрессивное - бой
        if self.behavior == "aggressive":
            self._combat_interaction(player)
            return True

        # # Если может разговаривать и игрок рядом
        # elif self.can_dialogue and player:
        #     current_time = time.time()
        #     if current_time - self.last_dialogue_time >= self.dialogue_cooldown:
        #         self.last_dialogue_time = current_time
        #         return "start_dialogue"  # Специальный сигнал
        #     else:
        #         # Можно показать уведомление
        #         return "cooldown"

        return False  # Ничего не произошло

    def update(self, delta_time: float = 1 / 60, player=None, collision_layer=None):
        """Обновление с поддержкой поведения"""
        super().update(delta_time)

        # Определяем направление движения (для анимации)
        dx, dy = self.wander_direction
        current_direction = None
        if abs(dx) > abs(dy):
            current_direction = "right" if dx > 0 else "left"
        elif dy != 0:
            current_direction = "up" if dy > 0 else "down"

        # Обновляем анимацию
        self._update_animation(delta_time, current_direction)

        # Обновляем полоску здоровья
        self.health_bar.x = self.center_x
        self.health_bar.y = self.center_y + self.height

        # Основная логика поведения
        if self.can_see_player(player):
            if self.behavior == "aggressive":
                self.current_state = "chase"
                self._chase_player(player, delta_time, collision_layer)
            if self.behavior == "passive" and self.can_dialogue:
                self.can_start_dialogue = True
                self.current_state = "idle"
                self._wander_behavior(delta_time, collision_layer)
        elif not self._is_point_in_zone():
            self.current_state = "return"
            self._return_to_zone(delta_time)
        else:
            self.current_state = "idle"
            self.can_start_dialogue = False
            self._wander_behavior(delta_time, collision_layer)

        # Обновляем таймеры
        self.wander_timer -= delta_time
        if self.return_timer > 0:
            self.return_timer -= delta_time

    def draw(self):

        self.health_bar.draw()
        self._draw_debug()

    def _draw_debug(self):
        if C.debug_mode:
            arcade.Text(
                f"{self.behavior} {self.name}({self.zone_id}): {self.current_state}",
                x=self.center_x,
                y=self.center_y - self.height,
                anchor_x="center",
                align="center",
                font_size=15
            ).draw()

    def _chase_player(self, player, delta_time, collision_layer=None):
        """Преследование игрока с коллизиями и движением по 4 направлениям"""
        if not hasattr(self, 'chase_speed') or not player:
            self.chase_speed = self.speed
            return

        # Определяем направление (только 4 стороны)
        direction = self._get_cardinal_direction_to_player(player)
        if not direction:
            return

        # Вычисляем смещение
        speed = self.chase_speed * delta_time * 60

        dx, dy = 0, 0
        if direction == "up":
            dy = speed
        elif direction == "down":
            dy = -speed
        elif direction == "left":
            dx = -speed
        elif direction == "right":
            dx = speed

        # Перемещаемся с проверкой коллизий
        self._move_with_collision(dx, dy, collision_layer)

        # Обновляем направление для анимации
        self.wander_direction = (dx, dy)

    def _move_with_collision(self, dx, dy, collision_layer):
        """Перемещение с проверкой коллизий"""
        old_x, old_y = self.center_x, self.center_y

        # Пробуем переместиться
        self.center_x += dx
        self.center_y += dy

        # Проверяем коллизию
        if collision_layer and arcade.check_for_collision_with_list(self, collision_layer):
            # Если есть коллизия - возвращаем на старое место
            self.center_x = old_x
            self.center_y = old_y
            return False

        return True

    def _get_cardinal_direction_to_player(self, player):
        """Определяет направление к игроку по 4 сторонам (без диагоналей)"""
        if not player:
            return None

        dx = player.center_x - self.center_x
        dy = player.center_y - self.center_y

        # Выбираем преобладающее направление
        if abs(dx) > abs(dy):
            # Горизонтальное направление сильнее
            return "right" if dx > 0 else "left"
        else:
            # Вертикальное направление сильнее
            return "up" if dy > 0 else "down"

    def _return_to_zone(self, delta_time, collision_layer=None):
        """Возврат в свою зону с коллизиями"""
        # Определяем целевую позицию в зоне (центр зоны)
        zone_x, zone_y, zone_w, zone_h = self.zone_rect
        target_x = zone_x + zone_w / 2
        target_y = zone_y + zone_h / 2

        # Вычисляем направление к центру зоны (по 4 сторонам)
        dx = target_x - self.center_x
        dy = target_y - self.center_y

        # Выбираем преобладающее направление
        if abs(dx) > abs(dy):
            direction = "right" if dx > 0 else "left"
        else:
            direction = "up" if dy > 0 else "down"

        # Вычисляем смещение
        return_speed = getattr(self, 'speed', 1.5)
        speed = return_speed * delta_time * 60

        dx_move, dy_move = 0, 0
        if direction == "up":
            dy_move = speed
        elif direction == "down":
            dy_move = -speed
        elif direction == "left":
            dx_move = -speed
        elif direction == "right":
            dx_move = speed

        # Перемещаемся
        moved = self._move_with_collision(dx_move, dy_move, collision_layer)
        self.wander_direction = (dx_move, dy_move)

        # Если вернулись в зону, сбрасываем состояние
        if self._is_point_in_zone():
            self.current_state = "idle"

    def _wander_behavior(self, delta_time, collision_layer=None):
        """Случайное блуждание в зоне с коллизиями"""
        if self.wander_timer <= 0:
            # Выбираем случайное направление из 4 возможных
            directions = ["up", "down", "left", "right", None]  # None - стоять на месте
            direction = random.choice(directions)

            if direction:
                if direction == "up":
                    self.wander_direction = (0, self.speed)
                elif direction == "down":
                    self.wander_direction = (0, -self.speed)
                elif direction == "left":
                    self.wander_direction = (-self.speed, 0)
                elif direction == "right":
                    self.wander_direction = (self.speed, 0)
            else:
                self.wander_direction = (0, 0)

            self.wander_timer = random.uniform(1.0, 3.0)

        # Двигаемся в выбранном направлении с коллизиями
        dx = self.wander_direction[0] * delta_time * 60
        dy = self.wander_direction[1] * delta_time * 60

        if dx != 0 or dy != 0:
            self._move_with_collision(dx, dy, collision_layer)

            # Проверяем, не вышел ли за зону
            if not self._is_point_in_zone():
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


    def can_see_player(self, player) -> bool:
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


    def _update_animation(self, delta_time: float, current_direction: str = None):
        """Обновляет анимацию ходьбы"""

        if current_direction and current_direction != self.last_direction:
            # Смена направления - устанавливаем первую текстуру
            self._set_direction_texture(current_direction)
            self.time_elapsed = 0
            self.last_direction = current_direction
            self.is_moving = True

        elif current_direction and self.time_elapsed > self.animation_speed:
            # Анимация движения
            self._animate_direction(current_direction)
            self.time_elapsed = 0
            self.is_moving = True

        elif not current_direction:
            # Стоим на месте - статичная текстура
            self._set_idle_texture()
            self.is_moving = False


    def _set_direction_texture(self, direction):
        """Сразу устанавливает первую текстуру направления"""
        if direction in self.texture_indexes:
            self.cur_texture_index = self.texture_indexes[direction]
            self.set_texture(self.cur_texture_index)


    def _animate_direction(self, direction):
        """Анимирует движение в указанном направлении"""
        if direction not in self.texture_indexes:
            return

        start_index = self.texture_indexes[direction]

        # Переключаем между двумя текстурами
        if self.cur_texture_index == start_index:
            self.cur_texture_index = start_index + 1
            self.set_texture(self.cur_texture_index)
        else:
            self.cur_texture_index = start_index
            self.set_texture(self.cur_texture_index)


    def _set_idle_texture(self):
        """Устанавливает статичную текстуру для стояния"""
        if self.last_direction in self.texture_indexes:
            self.cur_texture_index = self.texture_indexes[self.last_direction]
            self.set_texture(self.cur_texture_index)


    @property
    def chase_speed(self):
        """Читаем из GameData, не копируем"""
        data = self.data_source.get_entity_data(self.entity_id)
        return data.get("chase_speed", self.speed)


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
