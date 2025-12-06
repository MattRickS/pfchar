import dataclasses

from pfchar.char.base import (
    BAB_KEY,
    stat_modifier,
    ArmorBonus,
    CriticalBonus,
    Dice,
    Effect,
    Save,
    Size,
    Statistic,
)
from pfchar.char.feats import Feat, WeaponFinesse
from pfchar.char.items import Item, Weapon
from pfchar.char.abilities import Ability


@dataclasses.dataclass
class Character:
    name: str = "Character"
    level: int = 1
    size: Size = Size.MEDIUM
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
    base_saves: dict[Save, int] = dataclasses.field(default_factory=dict)
    main_hand: Weapon | None = None
    off_hand: Weapon | None = None
    feats: list[Feat] = dataclasses.field(default_factory=list)
    items: list[Item] = dataclasses.field(default_factory=list)
    abilities: list[Ability] = dataclasses.field(default_factory=list)
    statuses: list[Effect] = dataclasses.field(default_factory=list)
    _two_handed: bool = False

    def all_effects(self) -> list[Effect]:
        return self.abilities + self.feats + self.statuses + self.items

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

    def has_feat(self, feat_type: type[Feat]) -> bool:
        return any(isinstance(feat, feat_type) for feat in self.feats)

    def attack_statistic(self) -> Statistic:
        return (
            Statistic.DEXTERITY
            if (
                self.main_hand.is_ranged
                or (self.has_feat(WeaponFinesse) and self.main_hand.is_light)
            )
            else Statistic.STRENGTH
        )

    def modified_statistic(self, stat: Statistic) -> int:
        original = self.statistics.get(stat, 10)
        modified = original + sum(
            effect.statistic_bonus(self, stat) for effect in self.all_effects()
        )
        return modified

    def attack_bonus(self) -> dict[str, int]:
        modifiers = {
            BAB_KEY: self.base_attack_bonus,
        }
        if self.main_hand and (enchantment := self.main_hand.attack_bonus(self)):
            modifiers["Weapon Enchantment"] = enchantment

        stat = self.attack_statistic()
        modifiers[stat.value] = stat_modifier(self.statistics[stat])
        modifiers |= {
            effect.name: effect.attack_bonus(self)
            for effect in self.all_effects()
            if effect.condition(self)
        }
        return {name: value for name, value in modifiers.items() if value}

    def damage_bonus(self) -> dict[str, list[Dice]]:
        modifiers = {
            self.main_hand.name: self.main_hand.damage_bonus(self),
        }
        if self.off_hand:
            modifiers[self.off_hand.name] = self.off_hand.damage_bonus(self)

        stat = Statistic.STRENGTH
        strength_mod = stat_modifier(self.statistics[stat])
        if self._two_handed:
            strength_mod = int(strength_mod * 1.5)
        modifiers[stat.value] = [Dice(num=strength_mod)]

        modifiers |= {
            effect.name: effect.damage_bonus(self)
            for effect in self.all_effects()
            if effect.condition(self)
        }
        return {name: value for name, value in modifiers.items() if value}

    def critical_bonus(self) -> CriticalBonus:
        bonus = self.main_hand.critical_bonus(self, None)
        for effect in self.all_effects():
            if effect.condition(self):
                bonus = effect.critical_bonus(self, bonus)

        return bonus

    def armour_bonuses(self) -> dict[ArmorBonus, int]:
        bonuses = {ac_type: 0 for ac_type in ArmorBonus}
        bonuses[ArmorBonus.SIZE] = -self.size.value

        max_dex_bonus = 99
        for effect in self.all_effects():
            max_dex_bonus = min(max_dex_bonus, getattr(effect, "max_dex_bonus", 99))
            ac_bonuses = effect.armour_class_bonus(self)

            # All penalties are added, not just the highest.
            if enhancement_bonus := ac_bonuses.pop(ArmorBonus.PENALTY, 0):
                bonuses[ArmorBonus.PENALTY] += enhancement_bonus

            for ac_type, value in ac_bonuses.items():
                bonuses[ac_type] = max(bonuses[ac_type], value)

        bonuses[ArmorBonus.DEXTERITY] = min(
            stat_modifier(self.modified_statistic(Statistic.DEXTERITY)), max_dex_bonus
        )

        return {ac_type: value for ac_type, value in bonuses.items() if value}

    def is_dex_capped(self) -> bool:
        # For some reason the dex cap only applies to AC otherwise would just modify
        # modified_statistic() for DEX.
        max_dex_bonus = 99
        for effect in self.all_effects():
            max_dex_bonus = min(max_dex_bonus, getattr(effect, "max_dex_bonus", 99))
        return (
            stat_modifier(self.modified_statistic(Statistic.DEXTERITY)) > max_dex_bonus
        )

    def get_cmb(self) -> dict[str, int]:
        statistic = (
            Statistic.DEXTERITY
            if self.size.value <= Size.TINY.value
            else Statistic.STRENGTH
        )
        modifiers = {
            BAB_KEY: self.base_attack_bonus,
            # TODO: Inconsistency - attack/damage use unmodified stats, but CMD uses modified.
            #       Either stat is always modified or stat modifying items are always separate line items.
            #       The former is much more straightforward, and likely more accurate.
            statistic.value: stat_modifier(self.modified_statistic(statistic)),
            "Size": self.size.value,
        }
        return {name: value for name, value in modifiers.items() if value}

    def get_cmd(self) -> dict[str, int]:
        ac_bonuses = self.armour_bonuses()
        applicable_ac_types = {
            ac_type: val
            for ac_type, val in ac_bonuses.items()
            if ac_type
            in (
                ArmorBonus.DEFLECTION,
                ArmorBonus.DODGE,
                ArmorBonus.INSIGHT,
                ArmorBonus.LUCK,
                ArmorBonus.MORALE,
                ArmorBonus.PROFANE,
                ArmorBonus.SACRED,
                ArmorBonus.PENALTY,
            )
        }
        modifiers = {
            "Base CMD": 10,
            BAB_KEY: self.base_attack_bonus,
            Statistic.STRENGTH.value: stat_modifier(
                self.modified_statistic(Statistic.STRENGTH)
            ),
            Statistic.DEXTERITY.value: stat_modifier(
                self.modified_statistic(Statistic.DEXTERITY)
            ),
            "Size": self.size.value,
            **applicable_ac_types,
        }
        return {name: value for name, value in modifiers.items() if value}

    def get_saves(self) -> dict[Save, dict[str, int]]:
        mapping = {
            Save.FORTITUDE: Statistic.CONSTITUTION,
            Save.REFLEX: Statistic.DEXTERITY,
            Save.WILL: Statistic.WISDOM,
        }
        saves = {
            save: {
                "Base": value,
                mapping[save].value: stat_modifier(
                    self.modified_statistic(mapping[save])
                ),
            }
            for save, value in self.base_saves.items()
        }

        for effect in self.all_effects():
            if effect.condition(self):
                for save, value in effect.saves_bonuses(self).items():
                    saves[save][effect.name] = value

        return saves
