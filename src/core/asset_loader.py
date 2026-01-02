from ..core.resource_manager import resource_manager


class AssetLoader:
    """Загружает игровые ресурсы"""

    def __init__(self):
        self.rm = resource_manager

    def load_player_sprites(self):
        """Загружает спрайты игрока"""
        textures = self.rm.load_spritesheet(
            "player/player_move.png",
            size=(63, 63),
            columns=8,
            count=8,
        )
        return {
            "up": [textures[0], textures[1]],
            "down": [textures[2], textures[3]],
            "left": [textures[4], textures[5]],
            "right": [textures[6], textures[7]]
        }

    def load_background(self, name):
        """Загружает фоновую текстуру"""
        path = f"backgrounds/{name}.png"
        return self.rm.load_texture(path)

    def load_ui_texture(self, name):
        """Загружает текстуру для UI - используем кеш ResourceManager"""
        path = f"ui/{name}.png"
        return self.rm.load_texture(path)

    def load_sound(self, name):
        """Загружает звуковой файл"""
        path = f"sounds/{name}.wav"
        return self.rm.load_sound(path)
