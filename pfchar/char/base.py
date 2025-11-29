import abc
import dataclasses
import enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pfchar.char.character import Character


class WeaponType(enum.StrEnum):
    SWORD = "Sword"
    AXE = "Axe"
    BOW = "Bow"
    HAMMER = "Hammer"


class Statistic(enum.StrEnum):
    STRENGTH = "Strength"
    DEXTERITY = "Dexterity"
    CONSTITUTION = "Constitution"
    INTELLIGENCE = "Intelligence"
    WISDOM = "Wisdom"
    CHARISMA = "Charisma"


def stat_modifier(value: int) -> int:
    return (value - 10) // 2


@dataclasses.dataclass
class Dice:
    num: int
    sides: int = 1
    modifier: int = 0
    # type

    def is_variable(self) -> bool:
        return self.sides > 1


class Condition:
    def __call__(self, character: "Character") -> bool:
        raise NotImplementedError


class NullCondition(Condition):
    def __call__(self, character: "Character") -> bool:
        return True


@dataclasses.dataclass(frozen=True)
class CriticalBonus:
    crit_range: int = 20
    crit_multiplier: int = 2
    damage_bonus: list[Dice] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Effect:
    name: str
    condition: Condition = dataclasses.field(default_factory=NullCondition)

    def statistic_bonus(self, character: "Character", statistic: Statistic) -> int:
        return 0

    def statistic_modifier_bonus(
        self, character: "Character", statistic: Statistic, mult: float = 1.0
    ) -> int:
        original = character.statistics.get(statistic, 10)
        modified = original + self.statistic_bonus(character, statistic)
        return int((stat_modifier(modified) * mult) - (stat_modifier(original) * mult))

    def critical_bonus(
        self, character: "Character", critical_bonus: "CriticalBonus"
    ) -> CriticalBonus:
        return critical_bonus

    def attack_bonus(self, character: "Character") -> int:
        statistic = character.attack_statistic()
        return self.statistic_modifier_bonus(character, statistic)

    @abc.abstractmethod
    def damage_bonus(self, character: "Character") -> list[Dice]:
        bonus = self.statistic_modifier_bonus(
            character,
            Statistic.STRENGTH,
            mult=1.5 if character.is_two_handed() else 1.0,
        )
        if bonus:
            return [Dice(bonus)]
        return []
