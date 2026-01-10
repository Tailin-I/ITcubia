class CreatureConfig:
    """Конфигурация для всех существ"""

    # Размеры спрайтов для каждого типа существ
    SPRITE_SIZES = {
        "алина": (63, 63),
        "артемий": (16, 16),
        "bug": (16, 16),  # Или какой размер у жука?
        "default": (64, 64)
    }

    # Скорость анимации для каждого типа
    ANIMATION_SPEEDS = {
        "алина": 0.4,
        "артемий": 0.5,
        "bug": 0.6,
        "default": 0.4
    }

    @classmethod
    def get_sprite_size(cls, creature_name: str):
        """Получить размер спрайта для существа"""
        print(f"размер {creature_name}: {cls.SPRITE_SIZES.get(creature_name, cls.SPRITE_SIZES['default'])}")
        return cls.SPRITE_SIZES.get(creature_name, cls.SPRITE_SIZES["default"])

    @classmethod
    def get_animation_speed(cls, creature_name: str):
        """Получить скорость анимации"""
        return cls.ANIMATION_SPEEDS.get(creature_name, cls.ANIMATION_SPEEDS["default"])