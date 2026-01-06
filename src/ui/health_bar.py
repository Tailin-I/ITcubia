import arcade

from .ui_component import UIComponent


class HealthBar(UIComponent):
    """Горизонтальная шкала здоровья"""

    def __init__(self, entity, x, y, width=200, height=20):
        super().__init__(x, y, width, height)
        self.entity = entity  # Сущность, за которой следим

        # Цвета
        self.bg_color = arcade.color.DARK_SLATE_GRAY
        self.fill_color = arcade.color.RED
        self.border_color = arcade.color.GOLD
        self.border_width = 2

    def draw(self):
        if not self.visible:
            return

        # Фон
        arcade.draw_rect_filled(
            arcade.rect.XYWH(
            self.x, self.y,
            self.width, self.height),
            self.bg_color
        )

        # Заполнение (процент здоровья)
        fill_width = max(0, (self.entity.health / max(self.entity.health, self.entity.max_health) ) * self.width)
        if fill_width > 0:
            arcade.draw_rect_filled(
                arcade.rect.XYWH(
                self.x - self.width / 2 + fill_width / 2, self.y,
                fill_width, self.height),
                self.fill_color
            )

        # Рамка
        arcade.draw_rect_outline(
            arcade.rect.XYWH(
                self.x, self.y,
            self.width, self.height),
            self.border_color, self.border_width
        )

        # Текст (опционально)
        arcade.Text(
            f"HP: {self.entity.health}/{self.entity.max_health}",
            self.x, self.y,
            arcade.color.WHITE, 12,
            anchor_x="center", anchor_y="center"
        ).draw()