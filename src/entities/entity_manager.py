import logging
import arcade
from typing import Dict, List
from .base_entity import Entity
from .monster import Monster
from ..core.game_data import game_data


class EntityManager:
    """Менеджер для управления всеми сущностями в игре"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.entities: Dict[str, Entity] = {}  # Все активные сущности
        self.monsters: List[Monster] = []  # Только монстры (для быстрого доступа)
        self.npcs: List[Entity] = []  # Только NPC

    def spawn_monster(self, monster_type: str, position, properties=None, scale=1.0) -> Monster:
        """Создать нового монстра"""
        # Генерируем уникальный ID
        monster_id = f"monster_{monster_type}_{len(self.entities)}"

        # Создаем данные в GameData
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

        # Сохраняем в GameData
        game_data.add_monster(monster_id, monster_data)

        # Создаем визуальный объект
        monster = Monster(
            monster_id=monster_id,
            monster_type=monster_type,
            position=position,
            properties=properties,
            scale=scale
        )

        # Устанавливаем данные зоны
        if nearest_zone:
            monster.zone_id = nearest_zone["id"]
            monster.zone_rect = nearest_zone["rect"]

        # Сохраняем в менеджере
        self.entities[monster_id] = monster
        self.monsters.append(monster)

        self.logger.debug(f"Создан монстр: {monster_id} в зоне {monster.zone_id}")
        return monster

    def spawn_npc(self, npc_type: str, position, properties=None, scale=1.0) -> Entity:
        """Создать NPC (будет реализовано позже)"""
        # Пока заглушка
        pass

    def update_all(self, delta_time: float, player=None, collision_layer=None):
        """Обновить все сущности"""
        for monster in self.monsters[:]:  # Копируем список для безопасного удаления
            if monster.is_alive:
                monster.update(delta_time, player, collision_layer)
            else:
                # Удаляем мертвых монстров
                self.remove_entity(monster.entity_id)

    def remove_entity(self, entity_id: str):
        """Удалить сущность"""
        if entity_id in self.entities:
            entity = self.entities[entity_id]

            # Удаляем из соответствующих списков
            if isinstance(entity, Monster) and entity in self.monsters:
                self.monsters.remove(entity)
            elif entity in self.npcs:
                self.npcs.remove(entity)

            # Удаляем из основного словаря
            del self.entities[entity_id]

            # Удаляем из спрайтовых списков
            entity.remove_from_sprite_lists()

            self.logger.debug(f"Удалена сущность: {entity_id}")

    def get_entity(self, entity_id: str) -> Entity:
        """Получить сущность по ID"""
        return self.entities.get(entity_id)

    def clear_all(self):
        """Очистить все сущности"""
        for entity_id in list(self.entities.keys()):
            self.remove_entity(entity_id)

        self.logger.info("Все сущности очищены")

    def draw_debug(self):
        """Отрисовать отладочную информацию"""
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

        # Рисуем радиусы агрессии монстров
        for monster in self.monsters:
            if monster.is_alive and hasattr(monster, 'aggro_range'):
                # Радиус агрессии
                arcade.draw_circle_outline(
                    monster.center_x, monster.center_y,
                    monster.aggro_range,
                    arcade.color.RED, 1
                )

                # Текущее состояние
                state_color = arcade.color.WHITE
                if hasattr(monster, 'current_state'):
                    if monster.current_state == "chase":
                        state_color = arcade.color.RED
                    # elif monster.current_state == "patrol":
                    #     state_color = arcade.color.GREEN
                    elif monster.current_state == "return":
                        state_color = arcade.color.BLUE

                arcade.Text(
                    f"{monster.current_state if hasattr(monster, 'current_state') else 'idle'}",
                    monster.center_x, monster.center_y - 20,
                    state_color, 10,
                    anchor_x="center"
                ).draw()


# Глобальный экземпляр
entity_manager = EntityManager()