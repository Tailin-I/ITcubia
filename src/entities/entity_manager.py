import logging
import arcade
from typing import Dict, List
from .base_entity import Entity
from .monster import Monster
from ..core.game_data import game_data


class EntityManager:
    """Простой менеджер сущностей"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.entities: Dict[str, Entity] = {}  # Все сущности по ID
        self.monsters: List[Monster] = []  # Только монстры

    def spawn_monster(self, monster_type: str, position, properties=None, scale=1.0) -> Monster:
        """
        Создает монстра.
        position: координаты (x, y) в пикселях
        scale: масштаб спрайта (не влияет на координаты!)
        """
        # Уникальный ID
        monster_id = f"monster_{monster_type}_{len(self.entities)}"

        # Создаем данные
        monster_data = game_data.create_monster_data(
            monster_id=monster_id,
            monster_type=monster_type,
            position=position,
            custom_props=properties
        )

        # Находим ближайшую зону
        nearest_zone = game_data.find_nearest_zone(position[0], position[1])
        if nearest_zone:
            monster_data["zone_id"] = nearest_zone["id"]
            monster_data["zone_rect"] = nearest_zone["rect"]

        # Сохраняем
        game_data.add_monster(monster_id, monster_data)

        # Создаем визуальный объект
        monster = Monster(
            monster_id=monster_id,
            monster_type=monster_type,
            position=position,
            properties=properties,
            scale=scale
        )

        # Привязываем к зоне
        if nearest_zone:
            monster.zone_id = nearest_zone["id"]
            monster.zone_rect = nearest_zone["rect"]

        # Добавляем в менеджер
        self.entities[monster_id] = monster
        self.monsters.append(monster)

        self.logger.info(f"Монстр создан: {monster_id} на ({position[0]:.0f}, {position[1]:.0f})")
        return monster

    def update_all(self, delta_time: float, player=None, collision_layer=None):
        """Обновляет всех монстров"""
        for monster in self.monsters[:]:  # Копия списка для безопасного удаления
            if monster.is_alive:
                monster.update(delta_time, player, collision_layer)
            else:
                self.remove_entity(monster.entity_id)

    def remove_entity(self, entity_id: str):
        """Удаляет сущность"""
        if entity_id in self.entities:
            entity = self.entities[entity_id]

            # Удаляем из списков
            if isinstance(entity, Monster) and entity in self.monsters:
                self.monsters.remove(entity)

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
        for zone_id, zone in game_data.monster_zones.items():
            x, y, w, h = zone["rect"]
            arcade.draw_rect_outline(
                arcade.rect.XYWH(x + w / 2, y + h / 2, w, h),
                arcade.color.YELLOW, 2
            )

            # Название зоны
            arcade.Text(
                f"Zone: {zone_id}",
                x + w / 2, y + h / 2,
                arcade.color.YELLOW, 10,
                anchor_x="center", anchor_y="center"
            ).draw()

        # Рисуем информацию о монстрах
        for monster in self.monsters:
            if monster.is_alive:
                # Радиус агрессии
                if hasattr(monster, 'aggro_range'):
                    arcade.draw_circle_outline(
                        monster.center_x, monster.center_y,
                        monster.aggro_range,
                        arcade.color.RED, 1
                    )

                # ID и координаты
                arcade.Text(
                    f"{monster.entity_id}",
                    monster.center_x, monster.center_y + 15,
                    arcade.color.WHITE, 8,
                    anchor_x="center"
                ).draw()

                arcade.Text(
                    f"({int(monster.center_x)},{int(monster.center_y)})",
                    monster.center_x, monster.center_y - 10,
                    arcade.color.CYAN, 8,
                    anchor_x="center"
                ).draw()


# Глобальный экземпляр
entity_manager = EntityManager()