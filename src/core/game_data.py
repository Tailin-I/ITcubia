import json
import logging
import pickle
from ..ui.notification_system import notifications as ns


class GameData:
    """центр всех данных игры"""

    def __init__(self):
        # Данные игрока
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.first_req = 500

        self.player = {

            "position": {"x": 400, "y": 300},

            "level": 1,
            "exp": 0,
            "req_exp": self.first_req,
            "max_health": 40,
            "health": 39,
            "speed": 10,
            "strength": 1

        }

        # Инвентарь игрока (список предметов)
        self.inventory = {
            "items": [],
            "equipped": [],
            "gold": 0
        }

        # Прогресс квестов
        self.quests = {
            "active": [],  # Активные квесты
            "completed": [],  # Завершенные
            "failed": []  # Проваленные
        }

        # Статистика игры
        self.stats = {
            "play_time": 0,
            "enemies_killed": 0,
            "items_collected": 0,
        }

        # Настройки
        self.settings = {
            "volume": 0.7
        }

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

    def export_json(self, filename="savegame_backup.json"):
        """Экспорт в JSON (для отладки)"""
        # Преобразуем в словарь
        export_data = {
            "player": self.player,
            "inventory": self.inventory,
            "quests": self.quests,
            "stats": self.stats,
            "settings": self.settings
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

    # Удобные методы для доступа
    def get_player_position(self):
        return (self.player["position"]["x"],
                self.player["position"]["y"])

    def get_player(self, arg):
        if arg in self.player:
            return self.player[arg]
        return None

    def set_player_position(self, x, y, map_name=None):
        self.player["position"]["x"] = x
        self.player["position"]["y"] = y
        if map_name:
            self.player["position"]["map"] = map_name

    def change_player_stat(self, stat_name: str, operation: str, value: int):
        """
        Изменяет характеристику игрока с различными операциями.

        Args:
            stat_name: Название характеристики ('health', 'strength', 'exp', и т.д.)
            operation: Операция ('set', 'add', 'subtract', 'multiply', 'divide')
            value: Значение для операции
        """
        if stat_name not in self.player:
            self.logger.warning(f"Характеристика '{stat_name}' не найдена")
            return False

        current = self.player[stat_name]

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

            self.player[stat_name] = new_value
            self.logger.debug(f"{stat_name}: {current} -> {new_value} ({operation} {value})")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка изменения {stat_name}: {e}")
            return False

    def _apply_stat_limits(self, stat_name: str, value):
        """Применяет ограничения для характеристик"""
        if stat_name == "health":
            return max(0, min(value, self.player["max_health"]))
        elif stat_name == "max_health":
            return max(1, value)
        elif stat_name in ["strength", "speed", "level"]:
            return max(1, value)
        elif stat_name == "exp":
            # Автоматический уровень при накоплении опыта
            new_exp = max(0, value)
            if new_exp >= self.player["req_exp"]:
                self._level_up()
            return new_exp
        return value

    def _level_up(self):
        """Повышение уровня"""
        self.player["level"] += 1
        self.player["exp"] = self.player["exp"] - self.player["req_exp"]
        self.player["req_exp"] = int(self.player["req_exp"] * 1.5)  # Увеличиваем требуемый опыт

        # Улучшаем характеристики при повышении уровня
        self.player["max_health"] += 12
        self.player["health"] += 12
        self.player["strength"] += 1

        ns.notification("Новый уровень")
        self.logger.info(f"Уровень повышен! Теперь уровень {self.player['level']}")

    def heal(self, amount: int):
        """Восстановление здоровья"""
        ns.notification(f"получено лечение: {amount}")
        return self.change_player_stat("health", "add", amount)

    def take_damage(self, amount: int):
        """Получение урона"""
        ns.notification(f"получен урон: {amount}")
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

    def add_item(self, item_id, count=1):
        """Добавляет предмет в инвентарь"""
        pass


# Глобальный экземпляр (будет один на всю игру)
game_data = GameData()
