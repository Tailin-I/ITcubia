import time

import arcade
from arcade import SpriteList, Camera2D

from .base_state import BaseState
from ..entities import Player
from ..ui.health_bar import HealthBar
from ..ui.notification_system import notifications as ns
from ..ui.vertical_bar import VerticalBar
from ..world.map_loader import MapLoader
from config import constants as C
from src.entities.entity_manager import entity_manager


class GameplayState(BaseState):
    """
    Состояние основной игры.
    Здесь происходит вся игровая логика.
    """

    def __init__(self, gsm, asset_loader):
        super().__init__("game", gsm, asset_loader)

        self.is_paused = False

        self.entity_manager = entity_manager

        # Для FPS
        self.frame_count = 0
        self.fps = 0
        self.fps_timer = time.time()

        self.viewport_width = C.VIEWPORT_WIDTH
        self.viewport_height = C.VIEWPORT_HEIGHT

        self.input_manager = self.gsm.input_manager

        player_scale = self.tile_size / 63  # ≈1.0159 (почти не меняем)

        self.default_camera = Camera2D()
        self.default_camera.viewport = (
            arcade.rect.XYWH(self.gsm.window.width // 2, self.gsm.window.height // 2, self.gsm.window.width,
                             self.gsm.window.height))

        player_textures = self.asset_loader.load_player_sprites()
        self.player = Player(player_textures, self.input_manager, scale=player_scale)
        self.player_list = SpriteList()
        self.player_list.append(self.player)

        self.map_loader = MapLoader()

        # Загружаем Tiled карту
        start_map = "secmap"
        self.map_loader.load(f"maps/{start_map}.tmx")
        self.mobs = arcade.SpriteList()

        # Загружаем монстров для стартовой карты
        for monster in self.entity_manager.mob:
            if monster and monster.is_alive and start_map in monster.entity_id:
                self.mobs.append(monster)

        # Устанавливаем текущую карту
        self.entity_manager.set_current_map(start_map)

        self.map_left = 0
        self.map_bottom = 0
        self.map_right = 0
        self.map_top = 0

        bounds = self.map_loader.get_bounds()
        self.setup_map_limits(bounds["left"], bounds["bottom"], bounds["right"], bounds["top"])

        # Получаем слой коллизий
        self.collision_layer = self.map_loader.get_collision_layer()

        # Камера
        self.camera = arcade.camera.Camera2D()

        self.ui_elements = []

        self.deepseek_bar = VerticalBar(
            x=15,
            y=550,
            width=15,
            height=150,
            bg_color=arcade.color.PURPLE_NAVY,
            fill_color=arcade.color.PURPLE,
            icon_texture=asset_loader.load_ui_texture("deepseek")
        )
        self.ui_elements.append(self.deepseek_bar)

        self.fatigue_bar = VerticalBar(
            x=50,
            y=550,
            width=15,
            height=150,
            bg_color=arcade.color.FRENCH_BEIGE,
            fill_color=arcade.color.BEIGE,
            icon_texture=asset_loader.load_ui_texture("fatigue")
        )
        self.ui_elements.append(self.fatigue_bar)

        self.health_bar = HealthBar(
            self.player,
            x=150,
            y=50,
            width=200,
            height=20
        )
        self.gsm.ui_elements.append(self.health_bar)

        # Устанавливаем начальные значения
        self.deepseek_bar.set_value(75, 100)
        self.fatigue_bar.set_value(30, 100)

        self.select_pressed = False

    def setup_map_limits(self, left, bottom, width, height):
        self.map_left = left
        self.map_bottom = bottom
        self.map_right = left + width
        self.map_top = bottom + height

    def teleport_to(self, x: int, y: int, map: str = None):
        """
        Телепортирует игрока в указанные координаты.
        """
        # Если нужно сменить карту
        if map:
            path = f"maps/{map}.tmx"
            self.logger.info(f"Смена карты: {map}")

            # Устанавливаем текущую карту
            self.entity_manager.set_current_map(map)

            # Загружаем новую карту
            success = self.map_loader.load(path)
            if not success:
                self.logger.error(f"Не удалось загрузить карту: {map}")
                return False

            # Очищаем список монстров для отрисовки
            self.mobs.clear()

            # Получаем монстров для этой карты из EntityManager
            current_map_monsters = self.entity_manager.get_monsters_for_current_map()

            for monster in current_map_monsters:
                if monster and monster.is_alive and self.entity_manager.current_map_name in monster.entity_id:
                    print(f'монстр {monster.entity_id} добавлен на карту {self.entity_manager.current_map_name}')
                    self.mobs.append(monster)

            # Обновляем слой коллизий
            self.collision_layer = self.map_loader.get_collision_layer()

            # Обновляем границы карты для камеры
            bounds = self.map_loader.get_bounds()
            self.setup_map_limits(bounds["left"], bounds["bottom"], bounds["right"], bounds["top"])

        # Устанавливаем позицию игрока
        tile_x = x * self.tile_size
        tile_y = y * self.tile_size

        self.player.center_x = tile_x
        self.player.center_y = tile_y

        # Обновляем данные игрока
        self.game_data.set_player_position(x, y, map)

        target_x = self.player.center_x
        target_y = self.player.center_y

        # Учитываем половину размера экрана, чтобы камера не показывала пустоту за краем
        half_screen_w = self.gsm.window.width / 2
        half_screen_h = self.gsm.window.height / 2

        # Зажимаем камеру между границами карты
        final_x = max(self.map_left + half_screen_w, min(target_x, self.map_right - half_screen_w))
        final_y = max(self.map_bottom + half_screen_h, min(target_y, self.map_top - half_screen_h))

        # ПРИМЕНЕНИЕ (Для мгновенного следования)
        self.camera.position = (final_x, final_y)

        ns.notification(f"Телепорт в ({x}, {y}). карта: {map or 'текущая'}")
        return True

    def on_enter(self, **kwargs):
        """Вызывается при входе в это состояние"""
        # СБРАСЫВАЕМ все флаги при каждом входе!
        self.is_paused = False
        self.is_initialized = True

        # Инициализируем UI
        self._init_ui()

    def on_exit(self):
        """Вызывается при выходе из состояния"""
        # Сбрасываем флаги
        self.is_paused = False
        self.is_initialized = False

        # Сохраняем прогресс, освобождаем ресурсы...

    def on_pause(self):
        """Вызывается при постановке игры на паузу (для overlay)"""
        self.is_paused = True

    def on_resume(self):
        """Вызывается при возобновлении игры"""
        self.is_paused = False

    def update(self, delta_time: float):
        """Обновление игровой логики"""
        if self.is_paused:
            return
        # Обновляем монстров
        for monster in self.mobs:
            if monster.is_alive:
                monster.update(delta_time, self.player, self.collision_layer)
                if monster.collides_with_sprite(self.player):
                    monster.interact(self.player)
                if monster.can_start_dialogue and self.select_pressed:
                    self.gsm.push_overlay("dialogue", npc=monster)
                    monster.can_start_dialogue = False
                    self.select_pressed = False
                    break

        self.entity_manager.update_all(delta_time, self.player, self.collision_layer)

        # Обновляем игрока
        self.player.update(delta_time, collision_layer=self.collision_layer)


        # Обновляем и проверяем события (КОЛЛИЗИИ!)
        if hasattr(self.map_loader, 'event_manager') and self.map_loader.event_manager:
            self.map_loader.event_manager.update(delta_time)
            self.map_loader.event_manager.check_collisions(self.player, self)

        target_x = self.player.center_x
        target_y = self.player.center_y

        # Учитываем половину размера экрана, чтобы камера не показывала пустоту за краем
        half_screen_w = self.gsm.window.width / 2
        half_screen_h = self.gsm.window.height / 2

        # Зажимаем камеру между границами карты
        final_x = max(self.map_left + half_screen_w, min(target_x, self.map_right - half_screen_w))
        final_y = max(self.map_bottom + half_screen_h, min(target_y, self.map_top - half_screen_h))

        # ЕСЛИ НУЖНА ПЛАВНОСТЬ (Lerp):
        self.camera.position = arcade.math.lerp_2d(self.camera.position, (final_x, final_y), 0.3)

        # Обновляем UI
        for ui_element in self.ui_elements:
            ui_element.update(delta_time)

        # Счет FPS
        if C.debug_mode:
            self.frame_count += 1
            current_time = time.time()
            if current_time - self.fps_timer >= 1.0:  # Каждую секунду
                self.fps = self.frame_count
                self.frame_count = 0
                self.fps_timer = current_time

    def draw(self):
        """Отрисовка игры"""
        # Активируем камеру для игрового мира
        self.camera.use()

        # Рисуем карту
        self.map_loader.draw()

        # Рисуем сундуки
        self.map_loader.event_manager.draw()

        self.entity_manager.draw_debug()
        # Рисуем игрока и монстров
        self.player_list.draw()
        self.mobs.draw()
        for monster in self.mobs:
            monster.draw()

        # Переключаемся на UI камеру (полный экран)
        self.default_camera.use()

        # Рисуем UI элементы (здоровье, уведомления и т.д.)
        if C.debug_mode:
            # FPS и координаты
            text = f"x:{int(self.player.center_x // self.tile_size)} y:{int(self.player.center_y // self.tile_size)}"
            arcade.Text(text,
                        self.gsm.window.width - 3 * self.tile_size,
                        self.gsm.window.height - self.tile_size,
                        C.DEEPSEEK_COLOR, 18).draw()

            arcade.Text(f"FPS: {self.fps}",
                        self.gsm.window.width - 3 * self.tile_size,
                        self.gsm.window.height - 0.5 * self.tile_size,
                        C.DEEPSEEK_COLOR, 18).draw()

        # Рисуем UI элементы
        for ui_element in self.ui_elements:
            ui_element.draw()



    def handle_key_press(self, key: int, modifiers: int):
        if not self.input_manager:
            return

        # ESC - открыть меню паузы
        if self.input_manager.get_action("escape"):
            self._open_pause_menu()

        if self.input_manager.get_action("select"):
            self.select_pressed = True

        if self.input_manager.get_action("stats"):
            self.gsm.push_overlay("stats")

        if self.input_manager.get_action("inventory"):
            self.gsm.push_overlay("inventory")

        if C.cheat_mode:
            # F2 - чит-консоль
            if self.input_manager.get_action("cheat_console"):
                self.gsm.push_overlay("cheat_console")


            if self.input_manager.get_action("ghost_mode"):
                C.ghost_mode = not C.ghost_mode
            if self.input_manager.get_action("debug_mode"):
                C.debug_mode = not C.debug_mode
            if self.input_manager.get_action("show_area_mode"):
                C.show_area_mode = not C.show_area_mode
            if self.input_manager.get_action("heal"):
                if self.game_data.has_item("healing_potion"):
                    from src.entities.items.consumables import HealingPotion
                    potion = HealingPotion()
                    if potion.use(self.player):
                        self.game_data.remove_item("healing_potion", 1)
                        ns.notification("Зелье лечения использовано")
                else:
                    ns.notification("Нет зелий лечения")

    def handle_key_release(self, key: int, modifiers: int):
        self.select_pressed = False

    def _init_ui(self):
        """Инициализирует UI элементы"""
        # Пока пусто - добавим позже
        pass

    def _open_pause_menu(self):
        """Открывает меню паузы поверх игры"""
        self.gsm.push_overlay("pause_menu", )
