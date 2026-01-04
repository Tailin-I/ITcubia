import arcade
from arcade import SpriteList

from .base_entity import Entity
from .monster import Monster
from config import constants as C


class Player(Entity):
    def __init__(self, texture_dict, input_manager, scale=1):
        # Собираем все текстуры в один список
        all_textures = []
        for direction in ["up", "down", "left", "right"]:
            all_textures.extend(texture_dict[direction])

        # Важно: entity_id = "player"
        super().__init__(entity_id="player", texture_list=all_textures, scale=scale)

        self.texture_dict = texture_dict
        self.input_manager = input_manager

        # Маппинг направлений
        self.texture_indexes = {
            "up": 0,  # текстуры 0 и 1
            "down": 2,  # текстуры 2 и 3
            "left": 4,  # текстуры 4 и 5
            "right": 6  # текстуры 6 и 7
        }
        self.last_direction = "down"
        self.cur_texture_index = self.texture_indexes["down"]

        # Позиция из GameData
        pos_data = self.data_source.get_entity_data("player")
        if pos_data:
            pos = pos_data.get("position")
            self.center_x = pos["x"]
            self.center_y = pos["y"]

        # Инициализируем текстуру
        self.set_texture(self.cur_texture_index)

    @property
    def speed(self):
        """Скорость из GameData"""
        data = self.data_source.get_entity_data("player")
        return data.get("speed", 10) if data else 10

    @property
    def inventory(self):
        """Инвентарь из GameData"""
        data = self.data_source.get_entity_data("player")
        return data.get("inventory", [])

    def update(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:
        super().update(delta_time)

        dx, dy = 0, 0
        current_direction = None

        # Обработка ввода
        if self.input_manager.get_action('up'):
            current_direction = "up"
            dy += self.speed * delta_time * 60
        if self.input_manager.get_action('down'):
            current_direction = "down"
            dy -= self.speed * delta_time * 60
        if self.input_manager.get_action('left'):
            current_direction = "left"
            dx -= self.speed * delta_time * 60
        if self.input_manager.get_action('right'):
            current_direction = "right"
            dx += self.speed * delta_time * 60

        # Обработка анимации
        if current_direction and current_direction != self.last_direction:
            self._set_direction_texture(current_direction)
            self.time_elapsed = 0

        if current_direction and self.time_elapsed > 0.3:
            self._animate_direction(current_direction)
            self.time_elapsed = 0
        elif not current_direction:
            self._set_idle_texture()

        # Обновляем последнее направление
        if current_direction:
            self.last_direction = current_direction

        # Перемещение с учетом коллизий
        collision_layer = kwargs.get('collision_layer')
        monsters = kwargs.get('monsters')

        self._move_with_tiled_collision(collision_layer, monsters, dx, dy)
        self._update_ghost_appearance()

    def _move_with_tiled_collision(self, collision_layer, monsters: SpriteList[Monster], dx, dy):
        """
        метод коллизий.
        """
        # Если режим призрака
        if C.ghost_mode:
            self.center_x += dx
            self.center_y += dy
            return

        # Сохраняем старую позицию
        old_x, old_y = self.center_x, self.center_y

        self.center_x += dx
        self.center_y += dy
        if arcade.check_for_collision_with_list(self, collision_layer):
            self.center_x = old_x
            self.center_y = old_y
        if arcade.check_for_collision_with_list(self, monsters):
            for m in monsters:
                if m.collides_with_sprite(self):
                    m.interact()
            self.center_y = old_y
            self.center_x = old_x

    def _set_direction_texture(self, direction):
        """Сразу устанавливает первую текстуру направления"""
        if direction == "up":
            self.cur_texture_index = 0
        elif direction == "down":
            self.cur_texture_index = 2
        elif direction == "left":
            self.cur_texture_index = 4
        elif direction == "right":
            self.cur_texture_index = 6

        self.set_texture(self.cur_texture_index)

    def _animate_direction(self, direction):
        """Анимирует движение в указанном направлении"""
        direction_map = {
            "up": (0, 1),  # текстуры 0 и 1
            "down": (2, 3),  # текстуры 2 и 3
            "left": (4, 5),  # текстуры 4 и 5
            "right": (6, 7)  # текстуры 6 и 7
        }

        tex1, tex2 = direction_map[direction]

        # Переключаем между двумя текстурами
        if self.cur_texture_index == tex1:
            self.cur_texture_index = tex2
            self.set_texture(tex2)
        else:
            self.cur_texture_index = tex1
            self.set_texture(tex1)

    def _set_idle_texture(self):
        """Устанавливает статичную текстуру для стояния"""
        # Определяем последнее направление для idle-позы
        if self.last_direction == "up":
            self.cur_texture_index = 0
            self.set_texture(0)
        elif self.last_direction == "down":
            self.cur_texture_index = 2
            self.set_texture(2)
        elif self.last_direction == "left":
            self.cur_texture_index = 4
            self.set_texture(4)
        elif self.last_direction == "right":
            self.cur_texture_index = 6
            self.set_texture(6)

    def _update_ghost_appearance(self):
        """Обновляет внешний вид в режиме призрака"""
        if C.ghost_mode and self.color != C.ghost_color:
            # Устанавливаем синий полупрозрачный цвет
            self.color = C.ghost_color
        elif not C.ghost_mode and self.color != C.player_color:
            # Возвращаем нормальный цвет
            self.color = C.player_color

