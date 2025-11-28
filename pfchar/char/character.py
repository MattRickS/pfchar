import dataclasses

from pfchar.char.base import CriticalBonus, Dice, Statistic
from pfchar.char.items import Item, Weapon
from pfchar.char.abilities import Ability


@dataclasses.dataclass
class Character:
    name: str = "Character"
    level: int = 1
    statistics: dict[Statistic, int] = dataclasses.field(
        default_factory=lambda: {
            Statistic.STRENGTH: 10,
            Statistic.DEXTERITY: 10,
            Statistic.CONSTITUTION: 10,
            Statistic.INTELLIGENCE: 10,
            Statistic.WISDOM: 10,
            Statistic.CHARISMA: 10,
        }
    )
    base_attack_bonus: int = 0
    main_hand: Weapon | None = None
    off_hand: Weapon | None = None
    items: list[Item] = dataclasses.field(default_factory=list)
    abilities: list[Ability] = dataclasses.field(default_factory=list)
    _two_handed: bool = False

    def can_be_two_handed(self) -> bool:
        return (
            self.main_hand is not None
            and not self.main_hand.is_ranged
            and self.off_hand is None
        )

    def is_two_handed(self) -> bool:
        return self._two_handed and self.can_be_two_handed()

    def toggle_two_handed(self) -> bool:
        if not self.can_be_two_handed():
            return False
        self._two_handed = not self._two_handed
        return True

    def attack_statistic(self) -> Statistic:
        return Statistic.DEXTERITY if self.main_hand.is_ranged else Statistic.STRENGTH

    def attack_bonus(self) -> dict[str, int]:
        modifiers = {
            "Base Attack Bonus": self.base_attack_bonus,
        }
        if self.main_hand and (enchantment := self.main_hand.attack_bonus(self)):
            modifiers["Weapon Enchantment"] = enchantment

        stat = self.attack_statistic()
        modifiers[stat.value] = (self.statistics[stat] - 10) // 2
        modifiers |= {
            item.name: item.attack_bonus(self)
            for item in self.items
            if item.condition(self)
        } | {
            ability.name: ability.attack_bonus(self)
            for ability in self.abilities
            if ability.condition(self)
        }
        return {name: value for name, value in modifiers.items() if value}

    def damage_bonus(self) -> dict[str, list[Dice]]:
        modifiers = {
            self.main_hand.name: self.main_hand.damage_bonus(self),
        }
        if self.off_hand:
            modifiers[self.off_hand.name] = self.off_hand.damage_bonus(self)

        stat = Statistic.STRENGTH
        strength_mod = (self.statistics[stat] - 10) // 2
        if self._two_handed:
            strength_mod = int(strength_mod * 1.5)
        modifiers[stat.value] = [Dice(num=strength_mod)]

        modifiers |= {
            item.name: item.damage_bonus(self)
            for item in self.items
            if item.condition(self)
        } | {
            ability.name: ability.damage_bonus(self)
            for ability in self.abilities
            if ability.condition(self)
        }

        return {name: value for name, value in modifiers.items() if value}

    def critical_bonus(self) -> CriticalBonus:
        bonus = self.main_hand.critical_bonus(self, None)
        for effect in self.items + self.abilities:
            if effect.condition(self):
                bonus = effect.critical_bonus(self, bonus)

        return bonus
