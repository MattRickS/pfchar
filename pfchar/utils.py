from typing import TYPE_CHECKING

from pfchar.char.base import Dice

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
