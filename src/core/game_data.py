import logging
import pickle
from typing import Dict

from ..ui.notification_system import notifications as ns
from config import constants as C


class GameData:
    """центр всех данных игры"""

    def __init__(self):
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.base_req_exp = 500

        # Данные игрока
        self.player_data = {
            "id": "player",
            "name": "Игрок",
            "type": "player",
            "position": {"x": 10, "y": 20},
            "level": 1,
            "exp": 0,
            "req_exp": self.base_req_exp,
            "health": 39,
            "max_health": 400,
            "strength": 1,
            "speed": 10,
            # Инвентарь
            "inventory": [
                {'id': 'healing_potion', 'name': 'Целебное зелье', 'count': 1, 'stackable': True},
            ],
            "equipment": {
                "weapon": None,
                "accessory_1": None,
                "accessory_2": None,
                "accessory_3": None
            }
        }

        # Данные монстров (загружаются из Tiled)
        self.mobs_data = {}

        # Данные зон для монстров
        self.mob_zones = {}

        # Шаблоны монстров (дефолтные значения)
        self.mob_templates = {
            "bug": {
                "health": 20,
                "max_health": 20,
                "damage": 1,
                "speed": 1,
                "vision_range": 200,
                "behavior": "aggressive",
                "chase_speed": 3,
                "loot_table": [],
                "scale": 1
            },
            "npc": {
                "health": 100,

                "max_health": 100,
                "damage": 1,
                "speed": 1,
                "vision_range": 150,
                "behavior": "passive",
                "chase_speed": 2,
                "loot_table": [],
                "scale": 1,
                "can_dialogue": True,  # <-- может разговаривать
                "initial_topic": "greeting"
            }
        }

    def get_entity_data(self, entity_id):
        """Получить данные любой сущности"""
        if entity_id == "player":
            return self.player_data
        elif entity_id in self.mobs_data:
            return self.mobs_data[entity_id]

    def update_entity_data(self, entity_id, updates):
        """Обновить данные сущности"""
        data = self.get_entity_data(entity_id)
        if data:
            data.update(updates)
            # Здесь можно триггерить события

    def add_mob(self, mob_id, monster_data):
        """Добавить монстра"""
        self.mobs_data[mob_id] = monster_data

    def remove_mob(self, mob_id):
        """Удалить монстра"""
        if mob_id in self.mobs_data:

            del self.mobs_data[mob_id]



    def save_to_file(self, filename="savegame.dat"):
        """Сохраняем в бинарный файл"""
        # Можно использовать pickle или собственный бинарный формат
        with open(filename, 'wb') as f:
            pickle.dump(self.__dict__, f)  # Сохраняем ВСЕ данные класса

    def load_from_file(self, filename="savegame.dat"):
        """Загружаем из файла"""
        try:
            with open(filename, 'rb') as f:
                data = pickle.load(f)
                self.__dict__.update(data)  # Обновляем все данные

        except FileNotFoundError:
            self.logger.warning("Файл сохранения не найден, используем значения по умолчанию")

    # Удобные методы для доступа
    def get_player_position(self):
        return (self.player_data["position"]["x"] * C.TILE_SIZE,
                self.player_data["position"]["y"] * C.TILE_SIZE)

    def get_player(self, arg):
        if arg in self.player_data:
            return self.player_data[arg]
        return None

    def set_player_position(self, x, y, map_name=None):
        self.player_data["position"]["x"] = x * C.TILE_SIZE
        self.player_data["position"]["y"] = y * C.TILE_SIZE
        if map_name:
            self.player_data["position"]["map"] = map_name

    def change_player_stat(self, stat_name: str, operation: str, value: int):
        """
        Изменяет характеристику игрока с различными операциями.

        Args:
            stat_name: Название характеристики ('health', 'strength', 'exp', и т.д.)
            operation: Операция ('set', 'add', 'subtract', 'multiply', 'divide')
            value: Значение для операции
        """
        if stat_name not in self.player_data:
            self.logger.warning(f"Характеристика '{stat_name}' не найдена")
            return False

        current = self.player_data[stat_name]

        try:
            if operation == "set":
                new_value = value
            elif operation == "add":
                new_value = current + value
            elif operation == "subtract":
                new_value = current - value
            elif operation == "multiply":
                new_value = current * value
            elif operation == "divide":
                new_value = current / value if value != 0 else current
            else:
                self.logger.warning(f"Неизвестная операция: {operation}")
                return False

            # Применяем ограничения для разных характеристик
            new_value = self._apply_stat_limits(stat_name, new_value)

            self.player_data[stat_name] = new_value
            self.logger.debug(f"{stat_name}: {current} -> {new_value} ({operation} {value})")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка изменения {stat_name}: {e}")
            return False

    def _apply_stat_limits(self, stat_name: str, value):
        """Применяет ограничения для характеристик"""
        if stat_name == "health":
            return max(0, min(value, self.player_data["max_health"]))
        elif stat_name == "max_health":
            return max(1, value)
        elif stat_name in ["strength", "speed", "level"]:
            return max(1, value)
        elif stat_name == "exp":
            # Автоматический уровень при накоплении опыта
            new_exp = max(0, value)
            if new_exp >= self.player_data["req_exp"]:
                self._level_up()
            return new_exp
        return value

    def _level_up(self):
        """Повышение уровня"""
        self.player_data["level"] += 1
        self.player_data["exp"] = self.player_data["exp"] - self.player_data["req_exp"]
        self.player_data["req_exp"] = int(self.player_data["req_exp"] * 1.5)  # Увеличиваем требуемый опыт

        # Улучшаем характеристики при повышении уровня
        self.player_data["max_health"] += 12
        self.player_data["health"] += 12
        self.player_data["strength"] += 1

        ns.notification("Новый уровень")
        self.logger.info(f"Уровень повышен! Теперь уровень {self.player_data['level']}")

    def heal(self, amount: int):
        """Восстановление здоровья"""
        ns.notification(f"получено лечение: {amount}")
        return self.change_player_stat("health", "add", amount)

    def take_damage(self, amount: int):
        """Получение урона"""
        return self.change_player_stat("health", "subtract", amount)

    def add_exp(self, amount: int):
        """Добавление опыта"""
        ns.notification(f"+{amount} exp")
        return self.change_player_stat("exp", "add", amount)

    def increase_strength(self, amount: int = 1):
        """Увеличение силы"""
        return self.change_player_stat("strength", "add", amount)

    def increase_max_health(self, amount: int):
        """Увеличение максимального здоровья"""
        success = self.change_player_stat("max_health", "add", amount)
        if success:
            # Также увеличиваем текущее здоровье
            self.change_player_stat("health", "add", amount)
        return success

    def add_mob_zone(self, zone_id, zone_data):
        """Добавить зону для монстров"""
        self.mob_zones[zone_id] = zone_data

    def get_monster_zone(self, zone_id):
        """Получить зону по ID"""
        return self.mob_zones.get(zone_id)

    def find_nearest_zone(self, x, y, max_distance=1000):
        """Находит ближайшую зону к точке"""
        nearest_zone = None
        min_distance = float('inf')

        for zone_id, zone in self.mob_zones.items():
            zone_x, zone_y, zone_w, zone_h = zone["rect"]

            # Центр зоны
            center_x = zone_x + zone_w / 2
            center_y = zone_y + zone_h / 2

            # Расстояние до центра зоны
            distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5

            if distance < min_distance and distance <= max_distance:
                min_distance = distance
                nearest_zone = zone.copy()
                nearest_zone["id"] = zone_id

        return nearest_zone

    def create_monster_data(self, monster_id, mob_name, monster_type, position, custom_props: Dict=None,  map_name=None, scale=1):
        """Создать данные монстра с учетом дефолтных и кастомных свойств"""
        # Копируем шаблон для этого типа
        monster_data = self.mob_templates[monster_type].copy()

        # Добавляем обязательные поля
        monster_data.update({
            "id": monster_id,
            "type": monster_type,
            "name": mob_name,
            "position": {"x": position[0], "y": position[1]},
            "is_alive": True,
            "zone_id": None,  # Будет установлено позже
            "custom_properties": custom_props or {},
            "map_name": map_name
        })

        # Перезаписываем свойствами из Tiled
        if custom_props:
            for key, value in custom_props.items():
                if key in monster_data:
                    print(key, value)
                    monster_data[key] = value

            if "health" not in custom_props.keys():
                monster_data["health"] = monster_data["max_health"]

        return monster_data

    def add_item(self, item_id: str, name: str = None, count: int = 1, stackable: bool = True):
        """Добавляет предмет в инвентарь игрока"""
        inventory = self.player_data["inventory"]
        ns.notification(f"+{count} {name}")
        # Ищем уже существующий предмет
        if stackable:
            for item in inventory:
                if item["id"] == item_id:
                    item["count"] += count
                    return True

        # Если предмет не найден или не стакаемый - добавляем новый
        inventory.append({
            "id": item_id,
            "name": name or item_id,
            "count": count,
            "stackable": stackable,
            "type": "item"  # Тип для категоризации
        })


        return True

    def remove_item(self, item_id: str, count: int = 1):
        """Удаляет предмет из инвентаря"""
        inventory = self.player_data["inventory"]

        for i, item in enumerate(inventory):
            if item["id"] == item_id:
                if item["stackable"]:
                    item["count"] -= count
                    if item["count"] <= 0:
                        inventory.pop(i)
                else:
                    inventory.pop(i)
                return True
        return False

    def get_item_count(self, item_id: str) -> int:
        """Возвращает количество предметов в инвентаре"""
        for item in self.player_data["inventory"]:
            if item["id"] == item_id:
                return item["count"]
        return 0

    def has_item(self, item_id: str, min_count: int = 1) -> bool:
        """Проверяет наличие предмета в инвентаре"""
        return self.get_item_count(item_id) >= min_count

    def get_inventory_size(self) -> int:
        """Возвращает текущее количество занятых слотов"""
        return len(self.player_data["inventory"])

    def get_total_inventory_capacity(self) -> int:
        """Возвращает общее количество слотов (бесконечный инвентарь)"""
        return int(float('inf'))  # Бесконечный инвентарь

    def can_add_item(self, item_id: str, stackable: bool = True) -> bool:
        """Проверяет, можно ли добавить предмет"""
        # В бесконечном инвентаре всегда можно добавить
        return True


# Глобальный экземпляр (будет один на всю игру)
game_data = GameData()
