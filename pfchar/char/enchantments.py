from typing import TYPE_CHECKING

from pfchar.char.base import CriticalBonus, Dice, Effect

if TYPE_CHECKING:
    from pfchar.char.character import Character


class WeaponEnchantment(Effect):
    def __init__(self, name: str, damage_dice: list[Dice] | None = None):
        super().__init__(name=name)
        self._damage_dice = damage_dice or []

    def damage_bonus(self, character: "Character") -> list[Dice]:
        return self._damage_dice


class FlamingBurst(WeaponEnchantment):
    def __init__(self):
        super().__init__(
            name="Flaming Burst",
            damage_dice=[Dice(num=1, sides=6)],
        )

    def critical_bonus(self, character: "Character", critical_bonus) -> CriticalBonus:
        return CriticalBonus(
            crit_range=critical_bonus.crit_range,
            crit_multiplier=critical_bonus.crit_multiplier,
            damage_bonus=(
                critical_bonus.damage_bonus
                + [Dice(num=critical_bonus.crit_multiplier - 1, sides=10)]
            ),
        )

class Merciful(WeaponEnchantment):
    def __init__(self):
        super().__init__(
            name="Merciful",
            damage_dice=[Dice(num=1, sides=6)]
        )

class Sneaky(WeaponEnchantment):
    def __init__(self):
        super().__init__(
            name="Sneaky",
            damage_dice=[Dice(num=7, sides=6)]
        )
