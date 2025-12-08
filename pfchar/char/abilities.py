import dataclasses
from typing import TYPE_CHECKING

from pfchar.char.base import CriticalBonus, Effect, WeaponType
from pfchar.char.conditions import WeaponTypeCondition

if TYPE_CHECKING:
    from pfchar.char.character import Character


@dataclasses.dataclass
class Ability(Effect):
    pass


@dataclasses.dataclass
class DeadlyCritical(Ability):
    def __init__(self, weapon_type: WeaponType):
        super().__init__(name="Deadly Critical")
        self.condition = WeaponTypeCondition(weapon_type)

    def critical_bonus(
        self, character: "Character", critical_bonus: "CriticalBonus"
    ) -> int:
        return CriticalBonus(
            crit_range=critical_bonus.crit_range,
            crit_multiplier=critical_bonus.crit_multiplier + 1,
            damage_bonus=critical_bonus.damage_bonus,
        )


@dataclasses.dataclass
class WeaponsMastery(Ability):
    def __init__(self, weapon_type: WeaponType):
        super().__init__(name="Weapons Mastery")
        self.condition = WeaponTypeCondition(weapon_type)

    def critical_bonus(
        self, character: "Character", critical_bonus: "CriticalBonus"
    ) -> int:
        return CriticalBonus(
            crit_range=critical_bonus.crit_range,
            crit_multiplier=critical_bonus.crit_multiplier + 1,
            damage_bonus=critical_bonus.damage_bonus,
        )
