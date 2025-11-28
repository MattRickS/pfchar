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

    def critical_bonus(
        self, character: "Character", critical_bonus: "CriticalBonus"
    ) -> CriticalBonus:
        return critical_bonus

    def attack_bonus(self, character: "Character") -> int:
        return 0

    @abc.abstractmethod
    def damage_bonus(self, character: "Character") -> list[Dice]:
        return []
