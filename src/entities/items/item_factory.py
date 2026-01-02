from .consumables import HealingPotion, ManaPotion
from .keys import Key
from .base_item import Item

class ItemFactory:
    """Создает предметы по ID"""


    @staticmethod
    def create(item_id: str, count: int = 1, **kwargs) -> Item:
        """Создает предмет по его ID"""

        # Консумаблы
        if item_id == "healing_potion":
            return HealingPotion(count)
        elif item_id == "mana_potion":
            return ManaPotion(count)

        # Ключи
        elif item_id.startswith("key_"):
            key_type = item_id[4:] if "_" in item_id else "basic"
            name = kwargs.get("name", f"Ключ {key_type}")
            return Key(key_id=key_type, name=name)

        # # Золото (специальный случай)
        # elif item_id == "gold":
        #     from .currency import Gold
        #     return Gold(count)

        # По умолчанию - базовый предмет
        else:
            from .base_item import Item
            return Item(
                item_id=item_id,
                name=kwargs.get("name", item_id),
                texture_path=kwargs.get("texture")
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
