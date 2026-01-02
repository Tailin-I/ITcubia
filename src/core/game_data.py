import json
import logging
import pickle

class GameData:
    """центр всех данных игры"""

    def __init__(self):
        # Данные игрока
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")


        self.player = {
            "health": 100,
            "position": {"x": 400, "y": 300},

            "level": 1,
            "experience": 0
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
            "deaths": 0
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

    def set_player_position(self, x, y, map_name=None):
        self.player["position"]["x"] = x
        self.player["position"]["y"] = y
        if map_name:
            self.player["position"]["map"] = map_name

    def add_item(self, item_id, count=1):
        """Добавляет предмет в инвентарь"""
        pass


# Глобальный экземпляр (будет один на всю игру)
game_data = GameData()

