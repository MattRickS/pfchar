from pfchar.char.base import CriticalBonus, Dice, Save, Statistic
from pfchar.char.character import Character
from pfchar.char.enchantments import FlamingBurst
from pfchar.char.items import (
    StatisticModifyingItem,
    Weapon,
    CelestialArmour,
    ShieldOfTheSun,
    AmuletOfNaturalArmor,
    RingOfProtection,
    CloakOfResistance,
)
from pfchar.char.feats import (
    Dodge,
    PowerAttack,
    WeaponFocus,
    WeaponTraining,
    ImprovedCritical,
)
from pfchar.char.base import WeaponType
from pfchar.char.base import Save

YOYU = Character(
    name="Yoyu Tekko",
    level=19,
    statistics={
        Statistic.STRENGTH: 19,
        Statistic.DEXTERITY: 14,
        Statistic.CONSTITUTION: 14,
        Statistic.INTELLIGENCE: 12,
        Statistic.WISDOM: 12,
        Statistic.CHARISMA: 10,
    },
    base_attack_bonus=19,
    base_saves={
        Save.FORTITUDE: 11,
        Save.REFLEX: 6,
        Save.WILL: 6,
    },
    main_hand=Weapon(
        name="Infernal Forge",
        type=WeaponType.HAMMER,
        critical=CriticalBonus(
            crit_range=20,
            crit_multiplier=3,
        ),
        base_damage=Dice(num=1, sides=8),
        enchantment_modifier=3,
        # TODO: Critical enhancement bonus from Deadly Critical affects the
        #       burst damage, but weapon is calculated first _including_ effects.
        enchantments=[FlamingBurst()],
    ),
    feats=[
        PowerAttack(),
        WeaponFocus(WeaponType.HAMMER),
        WeaponTraining(WeaponType.HAMMER),
        ImprovedCritical(WeaponType.HAMMER),
        Dodge(),
    ],
    items=[
        StatisticModifyingItem(
            name="Belt of Physical Perfection (+6)",
            stats={
                Statistic.STRENGTH: 6,
                Statistic.DEXTERITY: 6,
                Statistic.CONSTITUTION: 6,
            },
        ),
        CelestialArmour(),
        ShieldOfTheSun(),
        AmuletOfNaturalArmor(bonus=3),
        RingOfProtection(bonus=2),
        CloakOfResistance(bonus=5),
    ],
)

SOMEONE_ELSE = Character(
    name="Someone Else",
    level=19,
    statistics={
        Statistic.STRENGTH: 13,
        Statistic.DEXTERITY: 18,
        Statistic.CONSTITUTION: 14,
        Statistic.INTELLIGENCE: 12,
        Statistic.WISDOM: 14,
        Statistic.CHARISMA: 14,
    },
    base_attack_bonus=13,
    base_saves={
        Save.FORTITUDE: 9,
        Save.REFLEX: 6,
        Save.WILL: 8,
    },
    main_hand=Weapon(
        name="Some Dagger",
        type=WeaponType.DAGGER,
        critical=CriticalBonus(crit_range=19),
        base_damage=Dice(num=1, sides=6),
        enchantment_modifier=2,
        enchantments=[],
    ),
    feats=[
        Dodge(),
    ],
    items=[
        StatisticModifyingItem(
            name="Headband of Charisma (+6)",
            stats={
                Statistic.CHARISMA: 6,
            },
        ),
        RingOfProtection(bonus=2),
        CloakOfResistance(bonus=3),
    ],
)
