import dataclasses
from typing import TYPE_CHECKING

from pfchar.char.base import (
    ArmorBonus,
    CriticalBonus,
    Dice,
    Effect,
    Save,
    Statistic,
    WeaponType,
)
from pfchar.char.enchantments import WeaponEnchantment
from pfchar import utils

if TYPE_CHECKING:
    from pfchar.char.character import Character


@dataclasses.dataclass
class Item(Effect):
    pass


@dataclasses.dataclass
class StatisticModifyingItem(Item):
    name: str
    stats: dict[Statistic, int] = dataclasses.field(default_factory=dict)

    def statistic_bonus(self, character, stat):
        return self.stats.get(stat, 0)


@dataclasses.dataclass(kw_only=True)
class Weapon(Item):
    type: WeaponType
    base_damage: Dice
    critical: CriticalBonus = dataclasses.field(default_factory=CriticalBonus)
    is_ranged: bool = False
    is_light: bool = False
    enchantment_modifier: int = 0
    enchantments: list[WeaponEnchantment] = dataclasses.field(default_factory=list)

    def attack_bonus(self, character: "Character") -> int:
        return self.enchantment_modifier

    def damage_bonus(self, character: "Character") -> list[Dice]:
        base_damage = Dice(
            self.base_damage.num,
            sides=self.base_damage.sides,
        )
        if character.base_size != character.get_size():
            from_size = character.base_size
            to_size = character.get_size()
            base_damage = utils.get_damage_progression(base_damage, from_size, to_size)
        return [
            Dice(
                base_damage.num,
                sides=base_damage.sides,
                modifier=self.enchantment_modifier,
            )
        ] + [
            dice
            for enchantment in self.enchantments
            if enchantment.condition(character)
            for dice in enchantment.damage_bonus(character)
        ]

    def critical_bonus(
        self, character: "Character", critical_bonus: "CriticalBonus"
    ) -> CriticalBonus:
        bonus = self.critical
        for enchantment in self.enchantments:
            if enchantment.condition(character):
                bonus = enchantment.critical_bonus(character, bonus)
        return bonus


@dataclasses.dataclass
class Armour(Item):
    name: str
    armour_bonus: int = 0
    shield_bonus: int = 0
    enhancement_bonus: int = 0
    max_dex_bonus: int = 99
    armor_check_penalty: int = 0
    spell_failure_chance: int = 0
    # Armour type, eg, light, medium, heavy. Affects speed.

    def armour_class_bonus(self, character: "Character") -> dict[ArmorBonus, int]:
        bonuses = {}
        if self.shield_bonus:
            bonuses[ArmorBonus.SHIELD] = self.shield_bonus
            if self.enhancement_bonus:
                bonuses[ArmorBonus.SHIELD_ENHANCEMENT] = self.enhancement_bonus
        if self.armour_bonus:
            bonuses[ArmorBonus.ARMOR] = self.armour_bonus
            if self.enhancement_bonus:
                bonuses[ArmorBonus.ARMOR_ENHANCEMENT] = self.enhancement_bonus
        return bonuses


@dataclasses.dataclass
class ShieldOfTheSun(Armour):
    name: str = "Shield of the Sun"
    shield_bonus: int = 2
    enhancement_bonus: int = 5
    armor_check_penalty: int = -2
    spell_failure_chance: int = 15


@dataclasses.dataclass
class CelestialArmour(Armour):
    name: str = "Celestial Armour"
    armour_bonus: int = 6
    enhancement_bonus: int = 3
    max_dex_bonus: int = 8
    armor_check_penalty: int = -2
    spell_failure_chance: int = 15


@dataclasses.dataclass
class AmuletOfNaturalArmor(Item):
    def __init__(self, bonus: int = 1):
        super().__init__(name=f"Amulet of Natural Armor (+{bonus})")
        self.bonus = bonus

    def armour_class_bonus(self, character: "Character") -> dict[ArmorBonus, int]:
        return {ArmorBonus.NATURAL: self.bonus}


@dataclasses.dataclass
class RingOfProtection(Item):
    def __init__(self, bonus: int = 1):
        super().__init__(name=f"Ring of Protection (+{bonus})")
        self.bonus = bonus

    def armour_class_bonus(self, character: "Character") -> dict[ArmorBonus, int]:
        return {ArmorBonus.DEFLECTION: self.bonus}


@dataclasses.dataclass
class CloakOfResistance(Item):
    def __init__(self, bonus: int = 1):
        super().__init__(name=f"Cloak of Resistance (+{bonus})")
        self.bonus = bonus

    def saves_bonuses(self, character: "Character") -> dict[Save, int]:
        return {save: self.bonus for save in Save}
