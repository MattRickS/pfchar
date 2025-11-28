import dataclasses
from typing import TYPE_CHECKING

from pfchar.char.base import CriticalBonus, Dice, Effect, WeaponType
from pfchar.char.conditions import EnabledCondition, WeaponTypeCondition

if TYPE_CHECKING:
    from pfchar.char.character import Character


@dataclasses.dataclass
class Ability(Effect):
    pass


@dataclasses.dataclass
class WeaponFocus(Ability):
    def __init__(self, weapon_type: WeaponType):
        super().__init__(name="Weapon Focus")
        self.condition = WeaponTypeCondition(weapon_type)

    def attack_bonus(self, character: "Character") -> int:
        return 1


@dataclasses.dataclass
class WeaponTraining(Ability):
    def __init__(self, weapon_type: WeaponType):
        super().__init__(name="Weapon Training")
        self.condition = WeaponTypeCondition(weapon_type)

    def attack_bonus(self, character: "Character") -> int:
        return 1 + (max(0, character.level - 3) // 4)

    def damage_bonus(self, character: "Character") -> list[Dice]:
        return [Dice(self.attack_bonus(character))]


@dataclasses.dataclass
class PowerAttack(Ability):
    name: str = "Power Attack"
    condition: EnabledCondition = dataclasses.field(default_factory=EnabledCondition)

    def attack_bonus(self, character: "Character") -> int:
        return -(character.base_attack_bonus // 4 + 1)

    def damage_bonus(self, character: "Character") -> list[Dice]:
        value = (character.base_attack_bonus // 4 + 1) * 2
        if character.is_two_handed():
            value = int(value * 1.5)
        return [Dice(num=value)]


@dataclasses.dataclass
class ImprovedCritical(Ability):
    def __init__(self, weapon_type: WeaponType):
        super().__init__(name="Improved Critical")
        self.condition = WeaponTypeCondition(weapon_type)

    def critical_bonus(
        self, character: "Character", critical_bonus: "CriticalBonus"
    ) -> int:
        return CriticalBonus(
            crit_range=21 - (21 - critical_bonus.crit_range) * 2,
            crit_multiplier=critical_bonus.crit_multiplier,
            damage_bonus=critical_bonus.damage_bonus,
        )
