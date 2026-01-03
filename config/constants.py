import arcade

# РАЗМЕР ТАЙЛОВ
ORIGINAL_TILE_SIZE = 70  # Оригинальный размер тайлов
TILE_SIZE = 64  # Желаемый размер тайлов
SCALE_FACTOR = TILE_SIZE / ORIGINAL_TILE_SIZE

# ПАРАМЕТРЫ ОКНА
SCREEN_WIDTH = 1440
SCREEN_HEIGHT = 900

VIEWPORT_WIDTH = SCREEN_WIDTH  # Фиксированная ширина обзора
VIEWPORT_HEIGHT = SCREEN_HEIGHT  # Фиксированная высота обзора

SCREEN_TITLE = "IT-Кубия"

# ЦВЕТА
TEXT_COLOR = arcade.color.LIGHT_GRAY
MENU_BACKGROUND_COLOR = (15,21,65)# Тёмно-синий
MENU_BACKGROUND_COLOR_TRANSLUCENT = (15,21,65, 70)# Тёмно-синий
UI_MAIN_COLOR = arcade.color.GOLD
UI_TITLE_COLOR = arcade.color.CYAN
UI_SUBTITLE_COLOR = arcade.color.LIGHT_BLUE
FOGGING_COLOR = (0, 0, 0, 200)  # Полупрозрачный чёрный

DEEPSEEK_COLOR = (76, 106, 253)
DEEPSEEK_COLOR_TRANSLUCENT = (76, 106, 253, 70)


cheat_mode = True
debug_mode = False

# # Текст оповещений
# text_to_draw = []
# remove_text_timer = 4