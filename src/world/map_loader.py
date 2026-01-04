import arcade
import logging

from src.core.resource_manager import resource_manager
from src.events.event_manager import EventManager
from config import constants as C
from pathlib import Path
from src.entities.chest import ChestSprite
from src.core.game_data import game_data


class MapLoader:
    """Загрузчик карт Tiled."""

    def __init__(self):
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.rm = resource_manager
        self.event_manager = None

        # Загруженная карта
        self.tile_map = None
        self.scene = None

        # Слои
        self.ground_layer = None
        self.walls_layer = None
        self.collisions_layer = None
        self.containers_layer = None

        # Границы карты
        self.bounds = None

    def _load_events(self, scale: float):
        """Загружает события из Tiled"""

        # Загружаем зоны взаимодействия из event Layer"
        for layer_name, object_list in self.tile_map.object_lists.items():
            if layer_name.lower() == "events":
                self.event_manager.load_events_from_objects(object_list, scale)
                self.logger.debug(f"Загружено событий: {len(self.event_manager.events)}")
                break


        # Создание визуальных спрайтов из Tile Layer "containers"
        self._create_chest_sprites_from_layer(self.containers_layer, scale)

    def _create_chest_sprites_from_layer(self, containers_layer, scale):
        """Создает спрайты сундуков из визуального слоя"""
        if not containers_layer:
            self.logger.warning("Слой containers пустой!")
            return

        for tile_sprite in containers_layer:
            sprite_x = tile_sprite.center_x
            sprite_y = tile_sprite.center_y

            # Поиск события с увеличенным радиусом
            chest_event = self.event_manager.find_nearest_chest_event(
                sprite_x, sprite_y,
                max_distance=self.tile_map.tile_width * 3
            )

            if chest_event:
                try:
                    sprite = ChestSprite(
                        texture=self.rm.load_texture("containers/chest.png"),
                        texture_open=self.rm.load_texture("containers/chest_opened.png"),
                        x=sprite_x,
                        y=sprite_y,
                        event=chest_event,
                        scale=scale
                    )

                    chest_event.set_sprite(sprite)
                    self.event_manager.chest_sprites.append(sprite)
                    self.logger.debug(f"Создан спрайт сундука: {chest_event.event_id}")

                except Exception as e:
                    self.logger.warning(f"Ошибка создания спрайта: {e}")
            else:
                self.logger.warning(f"Не найдено событие для сундука на ({sprite_x}, {sprite_y})")
    # def _create_monster_from_object(self, obj, index, scale: float):
    #     """Создаёт монстра из точки Tiled"""
    #     try:
    #         # Координаты
    #         x, y = obj.shape
    #
    #         # Генерируем уникальный ID
    #         monster_id = f"monster_{obj.type}_{index}"
    #
    #         # Создаём монстра
    #         from src.entities.monster import Monster
    #         monster = Monster(
    #             monster_id=monster_id,
    #             monster_type=obj.type.lower(),
    #             position=(x, y),
    #             properties=obj.properties,
    #             scale=scale
    #         )
    #
    #         return monster
    #     except Exception as e:
    #         self.logger.warning(f"Ошибка создания монстра: {e}")
    #         return None
    #
    # def load_monsters(self, scale: float = 1.0):
    #     """Загружает монстров из слоя 'entities' в Tiled"""
    #     monsters = []
    #
    #     # Ищем слой с монстрами
    #     for layer_name, object_list in self.tile_map.object_lists.items():
    #         if layer_name.lower() == 'entities':
    #             for index, obj in enumerate(object_list):
    #                 monster = self._create_monster_from_object(obj, index, scale)
    #                 if monster:
    #                     monsters.append(monster)
    #                     self.logger.debug(f"Создан монстр: {monster.entity_id}")
    #             break
    #
    #     return monsters
    def load(self, map_file: str, scale: float = C.SCALE_FACTOR) -> bool:
        """
        Загружает Tiled карту.
        """

        try:
            self.event_manager = EventManager()

            # Используем pathlib для кроссплатформенных путей
            map_file_path = Path(map_file)

            # Полный путь к файлу
            project_root = Path(self.rm.get_project_root())
            map_path = project_root / "res" / map_file_path

            self.logger.info(f"Загрузка карты: {map_path}... {'успешно' if map_path.exists() else 'ошибка'}")

            # Проверяем существование файла
            if not map_path.exists():
                self.logger.warning(f"Файл карты не найден: {map_path}")
                self._calculate_bounds()
                return False

            # Загружаем карту через Arcade - передаем строку
            self.tile_map = arcade.load_tilemap(
                str(map_path),  # Преобразуем Path в строку
                scaling=scale,
                layer_options={
                    "ground": {"use_spatial_hash": False},
                    "walls": {"use_spatial_hash": False},
                    "collisions": {"use_spatial_hash": True},
                    "containers": {"use_spatial_hash": False}
                }
            )

            # Получаем границы карты
            self._calculate_bounds()

            self.load_monster_zones(scale)

            # Получаем слои
            self.ground_layer = self.tile_map.sprite_lists.get("ground")
            self.walls_layer = self.tile_map.sprite_lists.get("walls")
            self.collisions_layer = self.tile_map.sprite_lists.get("collisions")
            self.containers_layer = self.tile_map.sprite_lists.get("containers")

            # Загружаем события
            self._load_events(scale)

            # Создаем сцену для отрисовки
            self.scene = arcade.Scene.from_tilemap(self.tile_map)

            # Скрываем невидимые слои
            if self.collisions_layer:
                for sprite in self.collisions_layer:
                    sprite.visible = False

            if self.containers_layer:
                for container in self.containers_layer:
                    container.visible = False



            return True

        except Exception as e:
            self.logger.error(f"Ошибка загрузки карты Tiled {map_file}: {e}")
            return False

    def _calculate_bounds(self):
        """Вычисляет границы карты"""
        if not self.tile_map:
            self.bounds = {'left': 0, 'right': 0, 'bottom': 0, 'top': 0, 'width': 0, 'height': 0}
            return

        width_tiles = self.tile_map.width
        height_tiles = self.tile_map.height
        tile_width = C.TILE_SIZE
        tile_height = C.TILE_SIZE


        self.bounds = {
            'left': 0,
            'bottom': 0,
            'right': width_tiles * tile_width,
            'top': height_tiles * tile_height,
            'width': width_tiles * tile_width,
            'height': height_tiles * tile_height,
        }

    def is_solid_at(self, x: float, y: float) -> bool:
        """Проверяет, есть ли коллизия в координатах (x, y)"""
        if not self.collisions_layer:
            return False

        # Создаем временный спрайт для проверки
        temp_sprite = arcade.Sprite()
        temp_sprite.center_x = x
        temp_sprite.center_y = y
        temp_sprite.width = 10
        temp_sprite.height = 10

        hits = arcade.check_for_collision_with_list(temp_sprite, self.collisions_layer)
        return len(hits) > 0

    def get_collision_layer(self):
        """Возвращает слой коллизий"""
        return self.collisions_layer

    def get_bounds(self):
        """Возвращает границы карты"""
        return self.bounds

    def draw(self):
        """Отрисовывает карту"""
        self.scene.draw()



    def update_events(self, delta_time: float, player, game_state):
        """Обновляет события"""
        if self.event_manager:
            self.event_manager.update(delta_time)
            self.event_manager.check_collisions(player, game_state)

    def draw_events(self):
        """Отрисовывает события"""
        if self.event_manager:
            self.event_manager.draw()

    def load_monster_zones(self, scale: float = 1.0):
        """Загружает зоны для монстров из слоя 'zones'"""
        if not self.tile_map:
            return []

        zones = []

        for layer_name, object_list in self.tile_map.object_lists.items():
            if layer_name.lower() == "zones":
                for i, obj in enumerate(object_list):
                    zone = self._create_zone_from_object(obj, scale, i)
                    if zone:
                        zones.append(zone)
                        # Сохраняем в GameData
                        game_data.add_monster_zone(zone["id"], zone)

                self.logger.info(f"Загружено зон: {len(zones)}")
                break

        return zones

    def _create_zone_from_object(self, obj, scale: float, index: int):
        """Создает зону из объекта Tiled"""
        try:
            # Координаты и размер
            x = getattr(obj, 'x') * scale
            y = getattr(obj, 'y') * scale
            width = getattr(obj, 'width') * scale
            height = getattr(obj, 'height') * scale

            # ID зоны
            properties = getattr(obj, 'properties')
            zone_id = properties.get('id', f"zone_{index}")

            zone_data = {
                "id": zone_id,
                "rect": (x, y, width, height),
                "properties": dict(properties)  # Конвертируем в обычный dict
            }

            self.logger.debug(f"Создана зона: {zone_id} ({x}, {y}, {width}, {height})")
            return zone_data

        except Exception as e:
            self.logger.warning(f"Ошибка создания зоны {index}: {e}")
            return None

    def load_entities(self, entity_manager, scale: float = 1.0):
        """Загружает всех существ (монстры и NPC) через EntityManager"""
        monsters = []

        if not self.tile_map:
            return monsters

        # Сначала загружаем зоны
        self.load_monster_zones(scale)

        # Затем загружаем существ
        for layer_name, object_list in self.tile_map.object_lists.items():
            if layer_name.lower() == 'entities':
                for index, obj in enumerate(object_list):
                    monster = self._create_entity_from_object(obj, entity_manager, scale, index)
                    if monster:
                        monsters.append(monster)

                self.logger.info(f"Загружено существ: {len(monsters)}")
                break

        return monsters

    def _create_entity_from_object(self, obj, entity_manager, scale: float, index: int):
        """Создает сущность из объекта Tiled"""
        try:
            # Координаты
            x, y = obj.shape if hasattr(obj, 'shape') else (obj.x, obj.y)
            x *= scale
            y *= scale

            # Тип и свойства
            monster_type = getattr(obj, 'type').lower()

            # Собираем все свойства
            properties = {}
            if hasattr(obj, 'properties'):
                for prop in obj.properties:
                    properties[prop.name] = prop.value

            # Создаем монстра через EntityManager
            monster = entity_manager.spawn_monster(
                monster_type=monster_type,
                position=(x, y),
                properties=properties,
                scale=scale
            )

            self.logger.debug(f"Создан {monster_type}: id={monster.entity_id}, props={properties}")
            return monster

        except Exception as e:
            self.logger.warning(f"Ошибка создания сущности {index}: {e}")
            return None