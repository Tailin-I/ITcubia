from .base_item import Item
from ...core.resource_manager import resource_manager as rm
from ...ui.notification_system import notifications as ns


class HealingPotion(Item):
    """Целебное зелье"""

    def __init__(self, count: int = 1, texture=None):
        # Если текстура не передана, загружаем по умолчанию
        if texture is None:
            from ...core.resource_manager import resource_manager as rm
            texture = rm.load_texture("consumables/potion_red.png")

        super().__init__(
            item_id="healing_potion",
            name="Целебное зелье",
            texture=texture
        )
        self.count = count
        self.is_consumable = True
        self.heal_amount = 45
        self.description = f"Восстанавливает {self.heal_amount} здоровья"

    def use(self, user) -> bool:
        if user.health < user.max_health:
            heal_amount = min(self.heal_amount, user.max_health - user.health)
            user.health += heal_amount
            self.count -= 1
            ns.notification(f"+{heal_amount} HP")
            return True  # Предмет израсходован
        ns.notification(f"И так полное здоровье")
        return False


class ManaPotion(Item):
    """Зелье маны"""

    def __init__(self, count: int = 1, texture=None):
        if texture is None:
            from ...core.resource_manager import resource_manager as rm
            texture = rm.load_texture("consumables/manacrystal_full.png")

        super().__init__(
            item_id="mana_potion",
            name="Зелье маны",
            texture=texture
        )
        self.count = count
        self.is_consumable = True
        self.restore_amount = 30
        self.description = f"Восстанавливает {self.restore_amount} маны"

    def use(self, user) -> bool:
        if hasattr(user, 'mana'):
            if user.mana < user.max_mana:
                restore = min(self.restore_amount, user.max_mana - user.mana)
                user.mana += restore
                self.count -= 1
                ns.notification(f"+{restore} маны")
                return True
            ns.notification("И так полная мана")
        return False
