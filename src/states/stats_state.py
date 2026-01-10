import arcade
from .base_state import BaseState
from config import constants as C


class StatsState(BaseState):
    """Меню характеристик """

    def __init__(self, gsm, asset_loader):
        super().__init__("stats", gsm, asset_loader)

        self.level = None
        self.exp = None
        self.req_exp = None
        self.speed = None
        self.strength = None

        # Цвета
        self.text_color = C.TEXT_COLOR
        self.main_color = C.UI_MAIN_COLOR
        self.title_color = C.UI_TITLE_COLOR
        self.menu_background_color = C.MENU_BACKGROUND_COLOR_TRANSLUCENT

        # Размеры окна меню
        self.window_width = self.gsm.window.width // 2
        self.window_height = self.gsm.window.height // 2

    def on_enter(self, **kwargs):
        self.level = self._get_player("level")
        self.exp = self._get_player("exp")
        self.req_exp = self._get_player("req_exp")
        self.speed = self._get_player("speed")
        self.strength = self._get_player("strength")

    def _get_player(self, arg):
        return str(self.game_data.get_player(arg))

    def on_exit(self):
        """Выход из меню паузы"""

    def update(self, delta_time):
        pass

    def draw(self):
        """Отрисовка меню паузы ПОВЕРХ игры"""
        C.draw_dark_background()

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
            "Характеристики",
            window_x, window_y * 1.45,
            self.main_color,
            30,
            align="center",
            anchor_x="center",
            anchor_y="center",
            bold=True
        ).draw()

        arcade.Text(
            f"Уровень: {self.level}",
            window_x * 0.55, window_y * 1.34,
            self.text_color,
            20
        ).draw()

        arcade.Text(
            f"Опыт: {self.exp}/{self.req_exp}",
            window_x * 0.55, window_y * 1.25,
            self.text_color,
            20
        ).draw()

    def handle_key_press(self, key, modifiers):
        """Обработка клавиш в меню паузы"""

        if self.gsm.input_manager.get_action("stats"):
            self.gsm.pop_overlay()

        elif self.gsm.input_manager.get_action("escape"):
            self.gsm.pop_overlay()
