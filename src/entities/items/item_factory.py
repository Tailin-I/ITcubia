from .consumables import HealingPotion, ManaPotion
from .keys import Key
from .base_item import Item
from ...core.resource_manager import resource_manager as rm


class ItemFactory:
    """Создает предметы по ID"""

    @staticmethod
    def create(item_id: str, count: int = 1, **kwargs) -> Item:
        """Создает предмет по его ID"""
        # Консумаблы
        if item_id == "healing_potion":
            texture = rm.load_texture("consumables/potion_red.png")
            return HealingPotion(count=count, texture=texture)
        elif item_id == "mana_potion":
            texture = rm.load_texture("consumables/manacrystal_full.png")
            return ManaPotion(count=count, texture=texture)

        # Ключи
        elif item_id.startswith("key_"):
            texture = rm.load_texture("consumables/key.png")
            key_type = item_id[4:] if "_" in item_id else "basic"
            name = kwargs.get("name", f"Ключ {key_type}")
            return Key(key_id=key_type, name=name, texture=texture)

        # По умолчанию - базовый предмет
        else:
            texture = kwargs.get("texture")
            if not texture:
                # Загружаем дефолтную текстуру
                try:
                    texture = rm.load_texture(f"items/{item_id}.png")
                except:
                    # Если нет текстуры, создаем пустую
                    from arcade import Texture
                    texture = Texture.create_filled(f"default_{item_id}", (32, 32), (128, 128, 128, 255))

            return Item(
                item_id=item_id,
                name=kwargs.get("name", item_id),
                texture=texture
            )

    @staticmethod
    def parse_loot_string(loot_str: str) -> list:
        """
        Парсит строку лута из Tiled: "healing_potion:3,key_door1:1,gold:50"
        Возвращает список предметов
        """
        items = []
        if not loot_str:
            return items

        for item_part in loot_str.split(','):
            item_part = item_part.strip()
            if ':' in item_part:
                item_id, count_str = item_part.split(':')
                try:
                    count = int(count_str)
                    item = ItemFactory.create(item_id.strip(), count)
                    if item:
                        items.append(item)
                except ValueError:
                    print(f"Неверный формат количества: {item_part}")
            else:
                # Если нет количества - 1
                item = ItemFactory.create(item_part.strip(), 1)
                if item:
                    items.append(item)

        return items
