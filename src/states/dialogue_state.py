import arcade
import time

from .base_state import BaseState
from config import constants as C


class DialogueState(BaseState):
    """Диалоговое состояние"""

    def __init__(self, gsm, asset_loader):
        super().__init__("dialogue", gsm, asset_loader)

        self.selected_index = 0
        self.key_cooldown = 0.15
        self.last_key_time = 0

        # Цвета
        self.text_color = C.TEXT_COLOR
        self.main_color = C.UI_MAIN_COLOR
        self.title_color = C.UI_TITLE_COLOR
        self.menu_background_color = C.MENU_BACKGROUND_COLOR_TRANSLUCENT

        # ====РАЗМЕРЫ ОКОН====
        # Главное окно диалога
        self.main_window_x =  C.SCREEN_WIDTH * 0.3
        self.main_window_y = C.SCREEN_HEIGHT // 2
        self.main_window_width = C.SCREEN_WIDTH * 0.4
        self.main_window_height = C.SCREEN_HEIGHT* 0.9

        # Окно ответов игрока
        self.answers_window_x = self.gsm.window.width * 0.75
        self.answers_window_y = self.gsm.window.height * 0.7
        self.answer_window_width = self.gsm.window.width * 0.3
        self.answer_window_height = self.gsm.window.height * 0.5

    def on_enter(self, **kwargs):
        """Вход в меню паузы"""

    def on_exit(self):
        """Выход из меню паузы"""

    def update(self, delta_time):
        pass

    def draw(self):
        """Отрисовка диалога"""
        C.draw_dark_background()

        self._draw_main_dialogue_window()
        self._draw_answers_window()


    def _draw_main_dialogue_window(self):
        """главное окно диалога"""
        # Фон окна
        arcade.draw_rect_filled(
            arcade.rect.XYWH(
                self.main_window_x, self.main_window_y,
                self.main_window_width, self.main_window_height),
            self.menu_background_color
        )

        # Рамка окна
        arcade.draw_rect_outline(
            arcade.rect.XYWH(
                self.main_window_x, self.main_window_y,
                self.main_window_width, self.main_window_height),
            self.main_color, 2
        )

    def _draw_answers_window(self):
            """Окно ответов игрока"""
            # Фон окна
            arcade.draw_rect_filled(
                arcade.rect.XYWH(
                    self.answers_window_x, self.answers_window_y,
                    self.answer_window_width, self.answer_window_height),
                self.menu_background_color
            )

            # Рамка окна
            arcade.draw_rect_outline(
                arcade.rect.XYWH(
                    self.answers_window_x, self.answers_window_y,
                    self.answer_window_width, self.answer_window_height),
                self.main_color, 2
            )

    def handle_key_press(self, key, modifiers):
        """Обработка клавиш в меню паузы"""

        current_time = time.time()
        if current_time - self.last_key_time < self.key_cooldown:
            return

        elif self.gsm.input_manager.get_action("select"):

            self.last_key_time = current_time