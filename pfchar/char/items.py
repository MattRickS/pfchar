import dataclasses
from typing import TYPE_CHECKING

from pfchar.char.base import CriticalBonus, Dice, Effect, Statistic, WeaponType
from pfchar.char.enchantments import WeaponEnchantment

if TYPE_CHECKING:
    from pfchar.char.character import Character


@dataclasses.dataclass
class Item(Effect):
    pass


@dataclasses.dataclass
class StatisticModifyingItem(Item):
    name: str
    stats: dict[Statistic, int] = dataclasses.field(default_factory=dict)

    def _stat(self, character: "Character", stat: Statistic, mult: float = 1.0) -> int:
        original = character.statistics.get(stat, 10)
        modified = original + self.stats.get(stat, 0)
        return int((((modified - 10) // 2) * mult) - (((original - 10) // 2) * mult))

    def attack_bonus(self, character: "Character") -> int:
        stat = character.attack_statistic()
        return self._stat(character, stat)

    def damage_bonus(self, character: "Character") -> list[Dice]:
        return [
            Dice(
                self._stat(
                    character,
                    Statistic.STRENGTH,
                    mult=1.5 if character.is_two_handed() else 1.0,
                )
            )
        ]


@dataclasses.dataclass(kw_only=True)
class Weapon(Item):
    type: WeaponType
    base_damage: Dice
    critical: CriticalBonus = dataclasses.field(default_factory=CriticalBonus)
    is_ranged: bool = False
    enchantment_modifier: int = 0
    enchantments: list[WeaponEnchantment] = dataclasses.field(default_factory=list)

    def attack_bonus(self, character: "Character") -> int:
        return self.enchantment_modifier

    def damage_bonus(self, character: "Character") -> list[Dice]:
        return [
            Dice(
                self.base_damage.num,
                sides=self.base_damage.sides,
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
