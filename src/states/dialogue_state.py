import arcade
import time

from .base_state import BaseState
from config import constants as C


class DialogueState(BaseState):
    """Это Диалоговое окно"""

    def __init__(self, gsm, asset_loader):
        super().__init__("dialogue", gsm, asset_loader)

        # Пункты меню паузы
        self.menu_items = [
            {"text": "ПРОДОЛЖИТЬ", "action": "resume"},
            {"text": "НАСТРОЙКИ", "action": "settings"},
            {"text": "В ГЛАВНОЕ МЕНЮ", "action": "main_menu"},
            {"text": "ВЫЙТИ ИЗ ИГРЫ", "action": "exit_game"}
        ]

        self.selected_index = 0
        self.key_cooldown = 0.15
        self.last_key_time = 0

        # Цвета
        self.text_color = C.TEXT_COLOR
        self.main_color = C.UI_MAIN_COLOR
        self.title_color = C.UI_TITLE_COLOR
        self.menu_background_color = C.MENU_BACKGROUND_COLOR
        self.bg_color = C.FOGGING_COLOR

        # Размеры окна меню
        self.window_width = 400
        self.window_height = 400

    def on_enter(self, **kwargs):
        """Вход в меню паузы"""

    def on_exit(self):
        """Выход из меню паузы"""

    def update(self, delta_time):
        pass

    def draw(self):
        """Отрисовка меню паузы ПОВЕРХ игры"""
        # Полупрозрачный тёмный фон
        arcade.draw_rect_filled(
            arcade.rect.LRBT(
                0, self.gsm.window.width,
                0,
                self.gsm.window.height),
            self.bg_color
        )

        # Окно меню (в центре экрана)
        window_x = self.gsm.window.width // 2
        window_y = self.gsm.window.height // 2

        # Фон окна
        arcade.draw_rect_filled(
            arcade.rect.XYWH(
                window_x, window_y,
                self.window_width, self.window_height),
            self.menu_background_color
        )

        # Рамка окна
        arcade.draw_rect_outline(
            arcade.rect.XYWH(
                window_x, window_y,
                self.window_width, self.window_height),
            self.main_color, 3
        )

        # Заголовок
        arcade.Text(
            "ПАУЗА",
            window_x, window_y + 150,
            self.main_color,
            36,
            align="center",
            anchor_x="center",
            anchor_y="center",
            bold=True
        ).draw()

        # Рисуем пункты меню
        self._draw_menu(window_x, window_y)

    def _draw_menu(self, center_x, center_y):
        """Рисует пункты меню паузы"""
        start_y = center_y + 50
        spacing = 60

        for i, item in enumerate(self.menu_items):
            # Выбираем цвет
            if i == self.selected_index:
                color = self.main_color
                font_size = 28
                is_bold = True
            else:
                color = self.text_color
                font_size = 24
                is_bold = False

            # Текст пункта
            arcade.Text(
                item["text"],
                center_x, start_y - i * spacing,
                color,
                font_size,
                align="center",
                anchor_x="center",
                anchor_y="center",
                bold=is_bold
            ).draw()


    def handle_key_press(self, key, modifiers):
        """Обработка клавиш в меню паузы"""
        if not self.gsm.input_manager:
            return

        current_time = time.time()
        if current_time - self.last_key_time < self.key_cooldown:
            return

        # Навигация
        if self.gsm.input_manager.get_action("up"):
            self.selected_index = max(0, self.selected_index - 1)
            self.last_key_time = current_time

        elif self.gsm.input_manager.get_action("down"):
            self.selected_index = min(len(self.menu_items) - 1, self.selected_index + 1)
            self.last_key_time = current_time

        # Выбор (ENTER)
        elif self.gsm.input_manager.get_action("select"):
            self._select_menu_item()
            self.last_key_time = current_time

        # Назад (ESC) - закрыть меню паузы
        elif self.gsm.input_manager.get_action("escape"):
            self._close_pause_menu()
            self.last_key_time = current_time

    def _select_menu_item(self):
        """Обрабатывает выбор пункта"""
        selected = self.menu_items[self.selected_index]

        if selected["action"] == "resume":
            self._close_pause_menu()

        elif selected["action"] == "settings":
            # Открываем настройки как overlay поверх паузы
            self.gsm.push_overlay("settings", is_overlay=True, parent_state="pause_menu")

        elif selected["action"] == "main_menu":
            # Подтверждение выхода в главное меню
            self.gsm.switch_to("lobby")

        elif selected["action"] == "exit_game":
            self.gsm.window.close()

    def _close_pause_menu(self):
        """Закрывает меню паузы (возврат в игру)"""
        self.gsm.pop_overlay()
