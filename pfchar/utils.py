from typing import TYPE_CHECKING

from pfchar.char.base import BAB_KEY, ArmorBonus, Effect, Dice, Save, Size, Statistic

if TYPE_CHECKING:
    from pfchar.char.base import CriticalBonus
    from pfchar.char.character import Character


# https://paizo.com/paizo/faq/v5748nruor1fm#v5748eaic9t3f
DAMAGE_PROGRESSION = [
    Dice(num=1, sides=1),
    Dice(num=1, sides=2),
    Dice(num=1, sides=3),
    Dice(num=1, sides=4),
    Dice(num=1, sides=6),
    Dice(num=1, sides=8),
    Dice(num=1, sides=10),
    Dice(num=2, sides=6),
    Dice(num=2, sides=8),
    Dice(num=3, sides=6),
    Dice(num=3, sides=8),
    Dice(num=4, sides=6),
    Dice(num=4, sides=8),
    Dice(num=6, sides=6),
    Dice(num=6, sides=8),
    Dice(num=8, sides=6),
    Dice(num=8, sides=8),
    Dice(num=12, sides=6),
    Dice(num=12, sides=8),
    Dice(num=16, sides=6),
]


def get_size_change(from_size: Size, to_size: Size) -> int:
    sizes = tuple(Size)
    from_index = sizes.index(from_size)
    to_index = sizes.index(to_size)
    return to_index - from_index


def change_size(from_size: Size, size_change: int) -> Size:
    sizes = tuple(Size)
    from_index = sizes.index(from_size)
    to_index = from_index + size_change
    to_index = max(0, min(len(sizes) - 1, to_index))
    return sizes[to_index]


def get_closest_damage_progression_index(damage: Dice) -> int:
    try:
        index = DAMAGE_PROGRESSION.index(damage)
    except ValueError:
        if damage.sides == 6:
            sixes = [
                d for d in DAMAGE_PROGRESSION if d.sides == 6 and d.num < damage.num
            ]
            next_lowest_num = sixes[-1].num
            damage = Dice(num=next_lowest_num, sides=8)
            index = DAMAGE_PROGRESSION.index(damage)
        elif damage.sides == 8:
            eights = [
                d for d in DAMAGE_PROGRESSION if d.sides == 8 and d.num > damage.num
            ]
            next_highest_num = eights[0].num
            damage = Dice(num=next_highest_num, sides=6)
            index = DAMAGE_PROGRESSION.index(damage)
        else:
            sums = [d.num * d.sides for d in DAMAGE_PROGRESSION]
            damage_sum = damage.num * damage.sides
            try:
                s_index = sums.index(damage_sum)
            except ValueError:
                _, s_index = min((abs(s - damage_sum), i) for i, s in enumerate(sums))
            damage = DAMAGE_PROGRESSION[s_index]
            index = DAMAGE_PROGRESSION.index(damage)
    return index


def get_damage_progression(damage: Dice, from_size: Size, to_size: Size) -> Dice:
    size_change = get_size_change(from_size, to_size)
    if size_change == 0:
        return damage

    index = get_closest_damage_progression_index(damage)

    # Increase by a single size step
    offset = -1 if size_change < 0 else 1
    if offset > 0:
        if from_size.value <= Size.SMALL.value or index < DAMAGE_PROGRESSION.index(
            Dice(num=1, sides=6)
        ):
            steps = 1
        else:
            steps = 2
    elif offset < 0:
        if to_size.value <= Size.MEDIUM.value or index <= DAMAGE_PROGRESSION.index(
            Dice(num=1, sides=8)
        ):
            steps = -1
        else:
            steps = -2
    else:
        raise ValueError("Offset must be non-zero")

    new_damage = DAMAGE_PROGRESSION[index + steps]

    # If more size steps are required, recurse
    if abs(size_change) > 1:
        new_size = change_size(from_size, offset)
        return get_damage_progression(new_damage, new_size, to_size)

    return new_damage


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
        string += f" {int(modifier):+d}"

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


def to_attack_string(attack_bonuses: dict[str, int]) -> str:
    attack_bonus = sum(attack_bonuses.values())
    attacks = [attack_bonus]
    bab = attack_bonuses[BAB_KEY]
    while bab > 5:
        bab -= 5
        attacks.append(attack_bonus - (len(attacks) * 5))

    return "/".join(f"{int(attack):+d}" for attack in attacks)


class CustomEffect(Effect):
    def __init__(
        self,
        name: str,
        attack_bonus: int,
        damage_bonus: int,
        statistics: dict[Statistic, int],
        saves: dict[Save, int],
        ac_bonuses: dict[ArmorBonus, int] = None,
        size_change: int = 0,
    ):
        super().__init__(name=name)
        self._attack_bonus = attack_bonus
        self._damage_bonus = damage_bonus
        self._statistics = statistics
        self._saves = saves
        self._ac_bonuses = ac_bonuses or {}
        self._size_change = size_change

    def armour_class_bonus(self, character):
        return self._ac_bonuses.copy()

    def statistic_bonus(self, character, statistic):
        return self._statistics.get(statistic, 0)

    def attack_bonus(self, character: "Character") -> int:
        return self._attack_bonus + super().attack_bonus(character)

    def damage_bonus(self, character: "Character") -> list[Dice]:
        bonus = super().damage_bonus(character)
        if bonus:
            bonus = [
                Dice(num=d.num, sides=d.sides, modifier=d.modifier + self._damage_bonus)
                for d in bonus
            ]
        elif self._damage_bonus:
            bonus.append(Dice(self._damage_bonus))
        return bonus

    def saves_bonuses(self, character: "Character") -> dict[Save, int]:
        return self._saves.copy()

    def size_change(self, character: "Character") -> int:
        return self._size_change


def create_status_effect(
    name: str,
    attack_bonus: int = 0,
    damage_bonus: int = 0,
    statistics: dict[Statistic, int] = None,
    saves: dict[Save, int] = None,
    ac_bonuses: dict[ArmorBonus, int] = None,
    size_change: int = 0,
) -> "Effect":
    return CustomEffect(
        name,
        attack_bonus,
        damage_bonus,
        statistics or {},
        saves or {},
        ac_bonuses or {},
        size_change,
    )


BASE_AC = 10
IGNORE_TOUCH_AC_TYPES = {ArmorBonus.NATURAL, ArmorBonus.ARMOR, ArmorBonus.SHIELD}
IGNORE_FLAT_FOOTED_AC_TYPES = {ArmorBonus.DEXTERITY, ArmorBonus.DODGE}


def get_total_ac(ac_bonuses: dict["ArmorBonus", int]) -> int:
    return BASE_AC + sum(val for val in ac_bonuses.values())


def get_touch_ac(ac_bonuses: dict["ArmorBonus", int]) -> int:
    return BASE_AC + sum(
        val
        for ac_type, val in ac_bonuses.items()
        if ac_type not in IGNORE_TOUCH_AC_TYPES
    )


def get_flat_footed_ac(ac_bonuses: dict["ArmorBonus", int]) -> int:
    return BASE_AC + sum(
        val
        for ac_type, val in ac_bonuses.items()
        if ac_type not in IGNORE_FLAT_FOOTED_AC_TYPES
    )
