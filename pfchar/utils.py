from typing import TYPE_CHECKING

from pfchar.char.base import ACType, Effect, Dice, Save, Statistic

if TYPE_CHECKING:
    from pfchar.char.base import CriticalBonus
    from pfchar.char.character import Character


def sum_up_dice(dice_list: list[Dice]) -> str:
    values = []
    modifier = 0
    for dice in dice_list:
        if dice.is_variable():
            modifier += dice.modifier
            values.append(f"{dice.num}d{dice.sides}")
        else:
            modifier += dice.num + dice.modifier

    string = "+".join(values)
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
    def __init__(
        self,
        name: str,
        attack_bonus: int,
        damage_bonus: int,
        statistics: dict[Statistic, int],
        saves: dict[Save, int],
    ):
        super().__init__(name=name)
        self._attack_bonus = attack_bonus
        self._damage_bonus = damage_bonus
        self._statistics = statistics
        self._saves = saves

    def statistic_bonus(self, character, statistic):
        return self._statistics.get(statistic, 0)

    def attack_bonus(self, character: "Character") -> int:
        return self._attack_bonus + super().attack_bonus(character)

    def damage_bonus(self, character: "Character") -> list[Dice]:
        bonus = super().damage_bonus(character)
        if bonus:
            bonus[0].modifier += self._damage_bonus
        elif self._damage_bonus:
            bonus.append(Dice(self._damage_bonus))
        return bonus

    def saves_bonuses(self, character: "Character") -> dict[Save, int]:
        return self._saves.copy()


def create_status_effect(
    name: str,
    attack_bonus: int = 0,
    damage_bonus: int = 0,
    statistics: dict[Statistic, int] = None,
    saves: dict[Save, int] = None,
) -> "Effect":
    return CustomEffect(name, attack_bonus, damage_bonus, statistics or {}, saves or {})


BASE_AC = 10
IGNORE_TOUCH_AC_TYPES = {ACType.NATURAL, ACType.ARMOR, ACType.SHIELD}
IGNORE_FLAT_FOOTED_AC_TYPES = {ACType.DEXTERITY, ACType.DODGE}


def get_total_ac(ac_bonuses: dict["ACType", int]) -> int:
    return BASE_AC + sum(val for val in ac_bonuses.values())


def get_touch_ac(ac_bonuses: dict["ACType", int]) -> int:
    return BASE_AC + sum(
        val
        for ac_type, val in ac_bonuses.items()
        if ac_type not in IGNORE_TOUCH_AC_TYPES
    )


def get_flat_footed_ac(ac_bonuses: dict["ACType", int]) -> int:
    return BASE_AC + sum(
        val
        for ac_type, val in ac_bonuses.items()
        if ac_type not in IGNORE_FLAT_FOOTED_AC_TYPES
    )
