import dataclasses
from typing import TYPE_CHECKING

from pfchar.char.base import ArmorBonus, CriticalBonus, Dice, Effect, WeaponType
from pfchar.char.conditions import EnabledCondition, WeaponTypeCondition

if TYPE_CHECKING:
    from pfchar.char.character import Character


class Feat(Effect):
    pass


class Dodge(Feat):
    def __init__(self, name: str = "Dodge"):
        super().__init__(name=name)

    def armour_class_bonus(self, character: "Character") -> dict[ArmorBonus, int]:
        return {ArmorBonus.DODGE: 1}


@dataclasses.dataclass
class WeaponFocus(Feat):
    def __init__(self, weapon_type: WeaponType):
        super().__init__(name="Weapon Focus")
        self.condition = WeaponTypeCondition(weapon_type)

    def attack_bonus(self, character: "Character") -> int:
        return 1


@dataclasses.dataclass
class WeaponTraining(Feat):
    def __init__(self, weapon_type: WeaponType):
        super().__init__(name="Weapon Training")
        self.condition = WeaponTypeCondition(weapon_type)

    def attack_bonus(self, character: "Character") -> int:
        return 1 + (max(0, character.level - 3) // 4)

    def damage_bonus(self, character: "Character") -> list[Dice]:
        return [Dice(self.attack_bonus(character))]


@dataclasses.dataclass
class PowerAttack(Feat):
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
class ImprovedCritical(Feat):
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


@dataclasses.dataclass
class WeaponFinesse(Feat):
    def __init__(self):
        super().__init__(name="Weapon Finesse")
