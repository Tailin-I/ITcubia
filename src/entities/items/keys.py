from .base_item import Item
from ...core.resource_manager import resource_manager as rm
from ...ui.notification_system import notifications as ns



class Key(Item):
    """Ключ для открытия дверей/сундуков"""

    def __init__(self, key_id: str = "basic_key", name: str = "Старый ключ"):
        super().__init__(
            item_id=f"key_{key_id}",
            name=name,
            texture_path=rm.get_resource_path("consumables/key.png")

        )
        self.is_stackable = False
        self.is_key_item = True
        self.key_id = key_id  # Какой замок открывает
        self.description = f"Ключ для замка '{key_id}'"

    def use(self, user) -> bool:
        ns.notification(f"🔑 Ключ '{self.key_id}' нельзя просто так использовать")
        return False  # Ключи не расходуются при использовании
