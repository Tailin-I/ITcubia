from .base_entity import Entity
from ..core.resource_manager import resource_manager
from ..core.game_data import game_data
from ..ui.notification_system import notifications as ns


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

        # Свойства зоны
        self.zone_id = None
        self.zone_rect = None  # (x, y, width, height)

        # Состояние поведения
        self.current_state = "idle"  # idle, chase, return
        self.current_action = None
        self.action_timer = 0

        # Для возврата в зону
        self.return_target = None

        # Загружаем свойства из GameData
        self._load_properties_from_data()

    def _load_properties_from_data(self):
        """Загружает свойства из GameData"""
        data = self.data_source.get_entity_data(self.entity_id)
        if data:
            # Устанавливаем свойства
            self.aggro_range = data.get("aggro_range", 150)
            self.vision_range = data.get("vision_range", 200)
            self.behavior = data.get("behavior", "passive")
            # self.patrol_speed = data.get("patrol_speed", 1.5)
            self.chase_speed = data.get("chase_speed", 3.0)

            # Зона
            self.zone_id = data.get("zone_id")

            # Находим rect зоны
            if self.zone_id:
                zone = self.data_source.get_monster_zone(self.zone_id)
                if zone:
                    self.zone_rect = zone.get("rect")

    def interact(self):
        """Взаимодействие с игроком - двусторонний урон"""
        data = self.data_source.get_entity_data(self.entity_id)
        if data and data.get("is_alive", True):
            # Монстр наносит урон игроку
            monster_damage = data.get("damage", 1)
            game_data.take_damage(monster_damage)

            # Игрок наносит урон монстру (просто для теста)
            player_damage = game_data.player_data.get("strength", 1)
            current_health = data.get("health", 1)

            # Обновляем здоровье монстра
            new_health = max(0, current_health - player_damage)
            data["health"] = new_health

            # Если здоровье закончилось - монстр умирает
            if new_health <= 0:
                data["is_alive"] = False
                self.visible = False
                ns.notification(f"Монстр побежден!")

                # Можно добавить опыт или лут
                exp_reward = 10  # Просто пример
                game_data.add_exp(exp_reward)

            ns.notification(f"Вы получили {monster_damage} урона, монстр получил {player_damage}")

    # Также добавим метод для обработки смерти в update:
    def update(self, delta_time: float = 1 / 60, player=None, collision_layer=None):
        """Обновление с поддержкой поведения"""
        super().update(delta_time)

        # Если монстр мертв, скрываем его
        if not self.is_alive:
            self.visible = False
            # Можно добавить анимацию смерти
            return

        # Простое преследование для теста (очень простое!)
        if player and self._can_see_player(player):
            self._simple_chase(player, delta_time)

        # Базовое поведение
        self._update_behavior(delta_time, player, collision_layer)

    def _simple_chase(self, player, delta_time):
        """Простое преследование игрока"""
        if not hasattr(self, 'chase_speed'):
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

    def _update_behavior(self, delta_time, player, collision_layer):
        """Обновляет поведение монстра"""
        # Базовое поведение
        # Пока просто стоим на месте
        pass

    def _is_point_in_zone(self, x, y):
        """Проверяет, находится ли точка в зоне монстра"""
        if not self.zone_rect:
            return True  # Если зоны нет, считаем что везде можно

        zone_x, zone_y, zone_w, zone_h = self.zone_rect
        return (zone_x <= x <= zone_x + zone_w and
                zone_y <= y <= zone_y + zone_h)

    def _get_distance_to_player(self, player):
        """Расстояние до игрока"""
        return ((self.center_x - player.center_x) ** 2 +
                (self.center_y - player.center_y) ** 2) ** 0.5

    def _can_see_player(self, player):
        """Может ли монстр видеть игрока"""
        distance = self._get_distance_to_player(player)

        # Проверяем зрение
        if distance > self.vision_range:
            return False

        # Проверяем находится ли игрок в зоне (если есть зона)
        if self.zone_rect:
            if not self._is_point_in_zone(player.center_x, player.center_y):
                return False

        # TODO: Добавить проверку на препятствия (стены)

        return True