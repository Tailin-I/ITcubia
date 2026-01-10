import logging
import arcade
from typing import Dict, List
from .base_entity import Entity
from .creatures import Creature
from ..core.game_data import game_data


class EntityManager:
    """Простой менеджер сущностей"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.entities: Dict[str, Entity] = {}  # Все сущности по ID
        self.mob: List[Creature] = []  # Только монстры
        self.current_map_name = None

    def set_current_map(self, map_name: str):
        """Устанавливает текущую карту и очищает визуальные монстры"""
        self.current_map_name = map_name
        self.logger.info(f"Установлена карта: {map_name}")

    def get_monsters_for_current_map(self):
        """Возвращает монстров только для текущей карты (на основе данных в GameData)"""
        if not self.current_map_name:
            return []

        current_map_monsters = []

        for monster in self.mob:
            # Простая проверка по ID - если в ID есть имя текущей карты
            if self.current_map_name in monster.entity_id:
                current_map_monsters.append(monster)

        return current_map_monsters

    def spawn_monster(self, mob_id: str, mob_name: str, mob_type: str, position, properties=None, map_name: str = None):
        """
        Создает монстра.
        position: координаты (x, y) в пикселях
        scale: масштаб спрайта (не влияет на координаты!)
        """

        # ПРОВЕРЯЕМ: если монстр уже существует - возвращаем его
        if mob_id in self.entities.keys():
            existing = self.entities[mob_id]
            self.logger.info(f"Монстр {mob_id} уже существует")
            return existing

        # ПРОВЕРЯЕМ: если монстр мертв в game_data - не создаем
        data = game_data.get_entity_data(mob_id)
        if data and not data.get("is_alive", True):
            self.logger.info(f"Монстр {mob_id} мертв")
            return None

        # Создаем данные
        monster_data = game_data.create_monster_data(
            monster_id=mob_id,
            mob_name=mob_name,
            monster_type=mob_type,
            position=position,
            custom_props=properties,
            map_name=map_name
        )

        # Находим ближайшую зону
        nearest_zone = game_data.find_nearest_zone(position[0], position[1])
        if nearest_zone:
            monster_data["zone_id"] = nearest_zone["id"]
            monster_data["zone_rect"] = nearest_zone["rect"]

        # Сохраняем
        game_data.add_mob(mob_id, monster_data)

        # Создаем визуальный объект
        monster = Creature(
            creature_id=mob_id,
            mob_name=mob_name,
            creature_type=mob_type,
            position=position,
            properties=properties
        )

        # Привязываем к зоне
        if nearest_zone:
            monster.zone_id = nearest_zone["id"]
            monster.zone_rect = nearest_zone["rect"]

        monster_data["map_name"] = map_name

        # Сохраняем
        game_data.add_mob(mob_id, monster_data)

        # Добавляем в менеджер
        self.entities[mob_id] = monster
        self.mob.append(monster)

        self.logger.info(f"{mob_name} создан: {mob_id} на ({position[0]:.0f}, {position[1]:.0f})")
        return monster

    def update_all(self, delta_time: float, player=None, collision_layer=None):
        """Обновляет всех монстров"""
        for monster in self.mob[:]:  # Копия списка для безопасного удаления
            if monster.is_alive:
                monster.update(delta_time, player, collision_layer)
            else:
                self.remove_entity(monster.entity_id)

    def remove_entity(self, entity_id: str):
        """Удаляет сущность"""
        if entity_id in self.entities:
            entity = self.entities[entity_id]

            # Удаляем из списков
            if isinstance(entity, Creature) and entity in self.mob:
                self.mob.remove(entity)

            # Удаляем спрайт
            entity.remove_from_sprite_lists()

            # Удаляем из словаря
            del self.entities[entity_id]

    def draw_debug(self):
        """Отрисовывает отладочную информацию (зоны и радиусы)"""
        from config import constants as C

        if not C.show_area_mode:
            return

        # Рисуем зоны
        for zone_id, zone in game_data.mob_zones.items():
            if zone.get("map_name") != self.current_map_name:
                continue
            x, y, w, h = zone["rect"]
            arcade.draw_rect_filled(
                arcade.rect.XYWH(x + w / 2, y + h / 2, w, h),
                C.MENU_BACKGROUND_COLOR_TRANSLUCENT
            )

            # Название зоны
            arcade.Text(
                f"Zone: {zone_id}",
                x + w / 2, y + h / 2,
                arcade.color.YELLOW, 15,
                anchor_x="center", anchor_y="center"
            ).draw()

        # Рисуем информацию о монстрах
        for monster in self.mob:

            if game_data.get_entity_data(monster.entity_id)["map_name"] != self.current_map_name:
                continue

            if monster.is_alive:
                data = game_data.get_entity_data(monster.entity_id)
                # Радиус агрессии
                if hasattr(monster, 'vision_range'):
                    arcade.draw_circle_outline(
                        monster.center_x, monster.center_y,
                        monster.vision_range,
                        arcade.color.RED, 1
                    )

                # ID и координаты
                arcade.Text(
                    data["id"],
                    monster.center_x, monster.center_y + monster.height+10,
                    arcade.color.WHITE, 15,
                    anchor_x="center"
                ).draw()

                # arcade.Text(
                #     f"({int(monster.center_x)},{int(monster.center_y)})",
                #     monster.center_x, monster.center_y - 10,
                #     arcade.color.CYAN, 15,
                #     anchor_x="center"
                # ).draw()


# Глобальный экземпляр
entity_manager = EntityManager()