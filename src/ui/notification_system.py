import arcade
from config import constants as C


class NotificationSystem:
    """система оповещений"""

    def __init__(self, max_messages=6):
        self.messages = []  # список сообщений
        self.timers = []  # таймеры для каждого сообщения
        self.max_messages = max_messages

    def notification(self, text: str, duration: float = 4.0):
        """Добавить новое оповещение"""
        self.messages.append(text)
        self.timers.append(duration)

        # Удаляем старые если слишком много
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
            self.timers.pop(0)

    def update(self, delta_time: float):
        """Обновить таймеры"""
        for i in range(len(self.timers) - 1, -1, -1):
            self.timers[i] -= delta_time
            if self.timers[i] <= 0:
                self.messages.pop(i)
                self.timers.pop(i)

    def draw(self, x: int, y: int):
        """Нарисовать все оповещения"""
        for i, text in enumerate(self.messages):
            # Прозрачность при исчезновении
            alpha = min(255, int(self.timers[i] * 255))
            color = (*C.DEEPSEEK_COLOR, alpha)

            arcade.Text(
                text,
                x,
                y - i * 17,
                color,
                15
            ).draw()

    def clear(self):
        """Очистить все оповещения"""
        self.messages.clear()
        self.timers.clear()

notifications = NotificationSystem()