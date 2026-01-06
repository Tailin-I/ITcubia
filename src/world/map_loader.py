import arcade
import logging

from src.core.resource_manager import resource_manager
from src.entities import entity_manager
from src.events.event_manager import EventManager
from config import constants as C
from pathlib import Path
from src.entities.chest import ChestSprite
from src.core.game_data import game_data


class MapLoader:
    """загрузчик карт Tiled."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
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

    def load(self, map_file: str, scale: float = C.SCALE_FACTOR) -> bool:
        """
        Загружает Tiled карту.
        """
        try:
            # Извлекаем имя карты из пути
            map_name = Path(map_file).stem

            self.event_manager = EventManager()

            # Полный путь к файлу
            project_root = Path(self.rm.get_project_root())
            map_path = project_root / "res" / map_file

            self.logger.info(f"Загрузка карты: {map_path}")

            if not map_path.exists():
                self.logger.warning(f"Файл не найден: {map_path}")
                return False

            # Загружаем карту
            self.tile_map = arcade.load_tilemap(
                str(map_path),
                scaling=scale,
                layer_options={
                    "ground": {"use_spatial_hash": False},
                    "walls": {"use_spatial_hash": False},
                    "collisions": {"use_spatial_hash": True},
                    "containers": {"use_spatial_hash": False}
                }
            )

            # Получаем границы
            self._calculate_bounds()

            # Получаем слои
            self.ground_layer = self.tile_map.sprite_lists.get("ground")
            self.walls_layer = self.tile_map.sprite_lists.get("walls")
            self.collisions_layer = self.tile_map.sprite_lists.get("collisions")
            self.containers_layer = self.tile_map.sprite_lists.get("containers")

            # Загружаем события (сундуки, телепорты)
            self._load_events(scale, map_name)

            # Создаем сцену
            self.scene = arcade.Scene.from_tilemap(self.tile_map)

            # Скрываем невидимые слои
            if self.collisions_layer:
                for sprite in self.collisions_layer:
                    sprite.visible = False
            if self.containers_layer:
                for container in self.containers_layer:
                    container.visible = False
            # При загрузке зон добавляем имя карты
            self.load_monster_zones(map_name)

            # При загрузке существ передаем имя карты
            self.load_entities(map_name)


            return True

        except Exception as e:
            self.logger.error(f"Ошибка загрузки карты: {e}")
            return False

    def _load_events(self, scale: float, map_name: str = None):
        """Загружает события из Tiled с восстановлением состояния"""
        for layer_name, object_list in self.tile_map.object_lists.items():
            if layer_name.lower() == "events":
                # Передаем имя карты в менеджер событий
                self.event_manager.load_events_from_objects(object_list, scale, map_name)
                break

        # Создаем визуальные спрайты сундуков
        if self.containers_layer:
            self._create_chest_sprites_from_layer(self.containers_layer, scale, map_name)

    def _create_chest_sprites_from_layer(self, containers_layer, scale, map_name: str = None):
        """Создает спрайты сундуков"""
        if not containers_layer:
            return

        for tile_sprite in containers_layer:
            sprite_x = tile_sprite.center_x
            sprite_y = tile_sprite.center_y

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
                    chest_event.map_name = map_name  # Устанавливаем карту для сундука
                    self.event_manager.chest_sprites.append(sprite)

                    # Восстанавливаем состояние сундука
                    saved_state = self.event_manager.get_event_state(chest_event.event_id)
                    if saved_state:
                        chest_event.is_empty = saved_state.get("is_empty", False)
                        if chest_event.is_empty and sprite:
                            sprite.update_visual()

                except Exception as e:
                    self.logger.warning(f"Ошибка создания спрайта: {e}")
    def _calculate_bounds(self):
        """Вычисляет границы карты в пикселях"""
        if not self.tile_map:
            self.bounds = {'left': 0, 'right': 0, 'bottom': 0, 'top': 0, 'width': 0, 'height': 0}
            return

        # В Tiled координаты уже в пикселях после загрузки через arcade
        width_px = self.tile_map.width * C.TILE_SIZE
        height_px = self.tile_map.height * C.TILE_SIZE

        self.bounds = {
            'left': 0,
            'bottom': 0,
            'right': width_px,
            'top': height_px,
            'width': width_px,
            'height': height_px,
        }

    def load_monster_zones(self, map_name: str = None):
        """Загружает зоны для монстров (прямоугольники)"""
        zones = []

        for layer_name, object_list in self.tile_map.object_lists.items():
            if layer_name.lower() == "zones":
                for i, obj in enumerate(object_list):
                    zone = self._create_zone_from_object(obj, i, map_name)
                    if zone:
                        zones.append(zone)
                        game_data.add_monster_zone(zone["id"], zone)

                self.logger.info(f"Загружено зон для карты '{map_name}': {len(zones)}")
                break

        return zones

    def _create_zone_from_object(self, obj, index: int, map_name: str = None):
        """Создает зону из прямоугольного объекта Tiled"""
        try:
            points = obj.shape

            left = points[0][0]
            top = points[0][1]
            right = points[1][0]
            bottom = points[3][1]

            width = right - left
            height = bottom - top

            x = left
            y = top

            # Получаем свойства
            properties = {}
            if hasattr(obj, 'properties'):
                props = getattr(obj, 'properties', {})
                if isinstance(props, dict):
                    properties = props.copy()

            zone_id = properties.get('id', f"zone_{index}")

            zone_data = {
                "id": zone_id,
                "rect": (x, y, width, height),
                "properties": properties,
                "map_name": map_name
            }

            self.logger.debug(f"Зона: {zone_id} ({x}, {y}, {width}, {height})")
            return zone_data

        except Exception as e:
            self.logger.warning(f"Ошибка создания зоны {index}: {e}")
            return None

    def load_entities(self, map_name: str = None):
        """Загружает существ (монстры и NPC) для конкретной карты"""
        monsters = []

        if not self.tile_map:
            return monsters

        # Загружаем существ
        for layer_name, object_list in self.tile_map.object_lists.items():
            if layer_name.lower() == 'entities':
                for index, obj in enumerate(object_list):
                    monster = self._create_entity_from_object(obj, index, map_name)
                    if monster:
                        monsters.append(monster)

                self.logger.info(f"Загружено существ для карты '{map_name}': {len(monsters)}")
                break

        return monsters

    def _create_entity_from_object(self, obj, index: int, map_name: str = None):
        """Создает сущность из точечного объекта Tiled"""
        try:
            # Точечные объекты в Tiled хранят координаты в shape
            if not hasattr(obj, 'shape'):
                return None

            # shape обычно это tuple (x, y) для точек
            shape = obj.shape
            if isinstance(shape, tuple) and len(shape) == 2:
                x, y = shape
            elif isinstance(shape, list) and len(shape) > 0:
                if isinstance(shape[0], (list, tuple)):
                    x, y = shape[0]
                else:
                    x, y = shape[0], shape[1]
            else:
                return None

            # Тип монстра
            monster_type = getattr(obj, 'type', 'bug').lower()

            # Свойства из Tiled
            properties = {}
            if hasattr(obj, 'properties'):
                props = getattr(obj, 'properties', {})
                if isinstance(props, dict):
                    properties = props.copy()

            # Создаем монстра (scale=1, координаты уже правильные)
            monster = entity_manager.spawn_monster(
                monster_type=monster_type,
                position=(x, y),
                properties=properties,
                map_name = map_name
            )

            if monster:
                self.logger.debug(f"Создан {monster_type} на ({x}, {y})")
                return monster

        except Exception as e:
            self.logger.warning(f"Ошибка создания сущности {index}: {e}")

        return None

    def get_collision_layer(self):
        """Возвращает слой коллизий"""
        return self.collisions_layer

    def get_bounds(self):
        """Возвращает границы карты"""
        return self.bounds

    def draw(self):
        """Отрисовывает карту"""
        if self.scene:
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