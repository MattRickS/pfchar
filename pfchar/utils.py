from typing import TYPE_CHECKING

from pfchar.char.base import Effect, Dice

if TYPE_CHECKING:
    from pfchar.char.base import CriticalBonus


def sum_up_dice(dice_list: list[Dice]) -> str:
    values = []
    modifier = 0
    for dice in dice_list:
        if dice.is_variable():
            modifier += dice.modifier
            values.append(f"{dice.num}d{dice.sides}")
        else:
            modifier += dice.num + dice.modifier

    string = " + ".join(values)
    if modifier:
        string += f" {modifier:+d}"

    return string


def sum_up_modifiers(modifiers: dict[str, list[Dice]]) -> int:
    return sum_up_dice(dice for dice_list in modifiers.values() for dice in dice_list)


def crit_to_string(critical_bonus: "CriticalBonus") -> str:
    crit_range = (
        "20" if critical_bonus.crit_range == 20 else f"{critical_bonus.crit_range}-20"
    )
    string = f"{crit_range}/x{critical_bonus.crit_multiplier}"
    if critical_bonus.damage_bonus:
        string += f" (+{sum_up_dice(critical_bonus.damage_bonus)})"
    return string


class CustomEffect(Effect):
    def __init__(self, name: str, attack_bonus: int, damage_bonus: int):
        super().__init__(name=name)
        self._attack_bonus = attack_bonus
        self._damage_bonus = damage_bonus

    def attack_bonus(self, character: "Character") -> int:
        return self._attack_bonus

    def damage_bonus(self, character: "Character") -> list[Dice]:
        return [Dice(self._damage_bonus)]


def create_status_effect(
    name: str, attack_bonus: int = 0, damage_bonus: int = 0
) -> "Effect":
    return CustomEffect(name, attack_bonus, damage_bonus)
