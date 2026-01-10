import arcade
import time
from .base_state import BaseState
from config import constants as C
from src.entities.items.item_factory import ItemFactory
from ..ui.notification_system import notifications as ns


class InventoryState(BaseState):
    """Инвентарь игрока"""

    def __init__(self, gsm, asset_loader):
        super().__init__("inventory", gsm, asset_loader)

        # Цвета
        self.text_color = C.TEXT_COLOR
        self.main_color = C.UI_MAIN_COLOR
        self.cell_color = (50, 50, 80, 200)
        self.cell_selected_color = (100, 100, 150, 200)
        self.menu_background_color = C.MENU_BACKGROUND_COLOR_TRANSLUCENT

        # Параметры сетки
        self.grid_cols = 6
        self.grid_rows = 5
        self.cell_size = 70
        self.cell_spacing = 10

        # Навигация
        self.selected_index = 0
        self.key_cooldown = 0.15
        self.last_key_time = 0

        # Кэш текстур
        self.texture_cache = {}

    def on_enter(self, **kwargs):
        """Вход в инвентарь"""
        self.selected_index = 0

    def update(self, delta_time):
        pass

    def _get_selected_item(self):
        """Получить выбранный предмет"""
        inventory = self.game_data.player_data["inventory"]
        if 0 <= self.selected_index < len(inventory):
            return inventory[self.selected_index]
        return None

    def _draw_grid(self):
        """Отрисовка сетки инвентаря"""
        inventory = self.game_data.player_data["inventory"]

        # Позиции для отрисовки
        start_x = self.gsm.window.width * 0.80 - self.window_width / 2 + self.cell_spacing
        start_y = self.gsm.window.height // 2 + self.window_height / 2 - self.cell_spacing - self.cell_size * 1.5

        # Рисуем все ячейки
        for i in range(self.grid_rows * self.grid_cols):
            row = i // self.grid_cols
            col = i % self.grid_cols

            x = start_x + col * (self.cell_size + self.cell_spacing) + self.cell_size / 2
            y = start_y - row * (self.cell_size + self.cell_spacing) - self.cell_size / 2

            # Цвет ячейки
            is_selected = (i == self.selected_index)
            has_item = (i < len(inventory))

            if is_selected and has_item:
                color = self.cell_selected_color
            elif has_item:
                color = self.cell_color
            else:
                color = (30, 30, 50, 100)  # Пустая ячейка

            # Рисуем ячейку
            arcade.draw_rect_filled(arcade.rect.XYWH(x, y, self.cell_size, self.cell_size), color)
            arcade.draw_rect_outline(arcade.rect.XYWH(x, y, self.cell_size, self.cell_size),
                                     self.main_color, 1)

            # Рисуем предмет, если он есть
            if has_item:
                item = inventory[i]
                texture = self._get_item_texture(item["id"])
                if texture:
                    arcade.draw_texture_rect(texture,
                                             arcade.rect.XYWH(x, y, self.cell_size - 10, self.cell_size - 10))

                # Количество
                if item["count"] > 1:
                    arcade.Text(str(item["count"]), x + self.cell_size / 2 - 5, y - self.cell_size / 2 + 10,
                                arcade.color.WHITE, 14, anchor_x="right").draw()

    def _draw_item_info(self):
        """Отрисовка информации о предмете"""
        item = self._get_selected_item()
        if not item:
            return

        # Позиция для отображения
        info_y = self.gsm.window.height // 2 - self.window_height *0.6
        center_x = self.gsm.window.width * 0.80

        # Фон
        arcade.draw_rect_filled(arcade.rect.XYWH(center_x, info_y,
                                                 self.window_width - 20, self.cell_size), (40, 40, 60, 200))

        # Название и описание
        arcade.Text(item["name"], center_x, info_y + 15,
                    self.main_color, 18, anchor_x="center", anchor_y="center").draw()
        # Создаем объект предмета, чтобы получить описание
        item_obj = ItemFactory.create(item["id"], 1)
        description = getattr(item_obj, 'description', "Нет описания")

        # Показываем описание под названием
        arcade.Text(description, center_x, info_y - 10,
                    self.text_color, 14, anchor_x="center", anchor_y="center").draw()

    @property
    def window_width(self):
        """Ширина окна"""
        return self.grid_cols * (self.cell_size + self.cell_spacing) + self.cell_spacing * 2

    @property
    def window_height(self):
        """Высота окна"""
        return self.grid_rows * (self.cell_size + self.cell_spacing) + self.cell_size * 1.5

    def draw(self):
        """Основная отрисовка"""
        C.draw_dark_background()

        # Центр окна
        center_x = self.gsm.window.width * 0.80
        center_y = self.gsm.window.height // 2

        # Фон окна
        arcade.draw_rect_filled(arcade.rect.XYWH(center_x, center_y,
                                                 self.window_width, self.window_height), self.menu_background_color)
        arcade.draw_rect_outline(arcade.rect.XYWH(center_x, center_y,
                                                  self.window_width, self.window_height), self.main_color, 3)

        # Заголовок
        arcade.Text("ИНВЕНТАРЬ", center_x, center_y + self.window_height * 0.55,
                    self.main_color, 24, anchor_x="center", align="center").draw()

        # Сетка и информация
        self._draw_grid()
        self._draw_item_info()

        # Статистика и подсказки
        total_items = len(self.game_data.player_data["inventory"])
        arcade.Text(f"Предметов: {total_items}", center_x + self.window_width / 2 - 10,
                    center_y + self.window_height / 2 - 20, self.text_color, 14, anchor_x="right").draw()

    def handle_key_press(self, key, modifiers):
        """Управление инвентарем"""
        current_time = time.time()
        if current_time - self.last_key_time < self.key_cooldown:
            return

        # Закрытие
        if (self.gsm.input_manager.get_action("inventory") or
                self.gsm.input_manager.get_action("escape")):
            self.gsm.pop_overlay()
            self.last_key_time = current_time
            return

        inventory = self.game_data.player_data["inventory"]
        if not inventory:
            return  # Пустой инвентарь

        # Использование предмета
        if self.gsm.input_manager.get_action("select"):
            self._use_item()
            self.last_key_time = current_time
            return

        # Навигация
        total_items = len(inventory)

        if self.gsm.input_manager.get_action("up"):
            new_index = self.selected_index - self.grid_cols
            if new_index >= 0:
                self.selected_index = new_index

        elif self.gsm.input_manager.get_action("down"):
            new_index = self.selected_index + self.grid_cols
            if new_index < total_items:
                self.selected_index = new_index

        elif self.gsm.input_manager.get_action("left"):
            if self.selected_index > 0:
                self.selected_index -= 1

        elif self.gsm.input_manager.get_action("right"):
            if self.selected_index < total_items - 1:
                self.selected_index += 1

        # Корректируем, если вышли за границы
        if self.selected_index >= total_items:
            self.selected_index = max(0, total_items - 1)

        self.last_key_time = current_time

    def _use_item(self):
        """Использовать выбранный предмет"""
        item = self._get_selected_item()
        if not item:
            ns.notification("Нет предмета для использования")
            return

        # Создаем объект предмета через фабрику
        try:
            item_obj = ItemFactory.create(item["id"], item["count"])

            # Пробуем использовать
            if item_obj.use(self.gsm.current_state.player):
                    # Успешное использование - удаляем из инвентаря
                    self.game_data.remove_item(item["id"], 1)
                    ns.notification(f"Использовано: {item['name']}")
            else:
                    ns.notification(f"Не удалось использовать: {item['name']}")

        except Exception as e:
            ns.notification(f"Ошибка: {str(e)[:30]}...")


    def _get_item_texture(self, item_id):
        """Получить текстуру предмета"""
        if item_id in self.texture_cache:
            return self.texture_cache[item_id]

        try:
            item = ItemFactory.create(item_id, 1)
            self.texture_cache[item_id] = item.texture
            return item.texture
        except:
            return None