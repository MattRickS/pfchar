from typing import TYPE_CHECKING

from pfchar.char.base import Condition, WeaponType

if TYPE_CHECKING:
    from pfchar.char.character import Character


class EnabledCondition(Condition):
    def __init__(self, enabled: bool = False):
        self.enabled = enabled

    def __call__(self, character: "Character") -> bool:
        return self.enabled

    def toggle(self):
        self.enabled = not self.enabled


class WeaponTypeCondition(Condition):
    def __init__(self, weapon_type: WeaponType):
        self.weapon_type = weapon_type

    def __call__(self, character: "Character") -> bool:
        main_hand = character.main_hand
        return main_hand is not None and main_hand.type == self.weapon_type
