from pfchar.char.base import CriticalBonus, Dice, Save, Statistic
from pfchar.char.character import Character
from pfchar.char.enchantments import FlamingBurst, Merciful, Sneaky
from pfchar.char.items import (
    StatisticModifyingItem,
    Weapon,
    CelestialArmour,
    ShieldOfTheSun,
    AmuletOfNaturalArmor,
    RingOfProtection,
    CloakOfResistance,
    Armour,
    Item,
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

DORAMAK = Character(
    name="Doramak Colegard",
    level=19,
    statistics={
        Statistic.STRENGTH: 16,
        Statistic.DEXTERITY: 12,
        Statistic.CONSTITUTION: 12,
        Statistic.INTELLIGENCE: 10,
        Statistic.WISDOM: 19,
        Statistic.CHARISMA: 12,
    },
    base_attack_bonus=15,
    base_saves={
        Save.FORTITUDE: 12,
        Save.REFLEX: 6,
        Save.WILL: 12,
    },
    main_hand=Weapon(
        name="+2 Adamantine Longsword",
        type=WeaponType.SWORD,
        critical=CriticalBonus(crit_range=19),
        base_damage=Dice(num=1, sides=8),
        enchantment_modifier=2,
        enchantments=[],
    ),
    feats=[],
    items=[
        StatisticModifyingItem(
            name="Headband of Mental Superiority (+6)",
            stats={
                Statistic.WISDOM: 6,
                Statistic.INTELLIGENCE: 6,
                Statistic.CHARISMA: 6,
            },
        ),
        StatisticModifyingItem(
            name="Belt of Giant Strength (+4)",  # From Yoyu
            stats={
                Statistic.STRENGTH: 4,
            },
        ),
        Armour(
            name="+4 Adamantine Full Plate",
            armour_bonus=9,
            enhancement_bonus=4,  # Upgraded
            max_dex_bonus=1,
            armor_check_penalty=-6,
            spell_failure_chance=35,
            # DR 3/-
        ),
        Armour(
            name="+3 Animated Light Shield",
            shield_bonus=1,
            enhancement_bonus=3,  # Upgraded
        ),
        RingOfProtection(bonus=3),  # Upgraded
        CloakOfResistance(bonus=3),  # Upgraded
        AmuletOfNaturalArmor(bonus=2),  # Made
    ],
)


CHELLYBEAN = Character(
    name= "Chellybean Smith",
    level=19,
    statistics={
        Statistic.STRENGTH: 10,
        Statistic.DEXTERITY: 18,
        Statistic.CONSTITUTION: 14,
        Statistic.INTELLIGENCE: 14,
        Statistic.WISDOM: 12,
        Statistic.CHARISMA: 14,
    },
    base_attack_bonus=13,
    base_saves={
        Save.FORTITUDE: 8,
        Save.REFLEX: 17,
        Save.WILL: 7,
    },
    main_hand=Weapon(
        name="+2 Sneaky Merciful Dagger",
        type=WeaponType.DAGGER,
        enchantment_modifier=2,
        critical=CriticalBonus(crit_range=19),
        base_damage=Dice(num=1, sides=3),
        enchantments=[
            Merciful(),
            Sneaky(),
        ]
    ),
    feats=[Dodge()],
    items=[
        Armour(
            name="Sexy Catskin Armour",
            armour_bonus=3,
            armor_check_penalty=0,
        ),
        Armour(
            name="Masterwork Buckler",
            shield_bonus=1,
            armor_check_penalty=0,
        ),
        RingOfProtection(bonus=1),
        StatisticModifyingItem(
            name="Headband of Charisma (+6)",
            stats={
                Statistic.CHARISMA: 6,
            },
        ),
        StatisticModifyingItem(
            name="Belt of Dexterity (+6)",
            stats={
                Statistic.DEXTERITY: 6,
            },
        ),
        Weapon(
            name="Rat Ring",
            type=WeaponType.UNARMED,  # ?
            enchantment_modifier=1,
            base_damage=Dice(num=1, sides=3),
            # Part of a full round action
        ),
        Armour(name="Shirt of Movement"),

        Armour(
            name="Gloomstrider",
            # Unlimited Shadow Jump
        ),
        Item(
            name="Eyeglasses of Doom",
            # Cast doom as a gaze attack.
            # Cast Fear 1/week
            # Continuous Deathwatch
        ),
        Armour(
            name="Gloves of Vembraces Storm",
            # Shadow Blast 1d6/level. half cold, half electric
            # If fail reflex save blinded 1d6/rounds
            # Recharge after 1d6/rounds
        ),
        Item(
            name="Cloak of Shadows",
            # Concealment: 20% miss chance
            # Stealth check +5
            # DR 5/Good
            # Protects from Sunlight
            # Dimlight more darker (bonus negated by darkvision):
            #   - Concealment: 50% miss chance
            #   - Stealth check +10
            # Every attack target must pass DC 17 Will or attack has Feint
            #   - Feint not applicable to creatures that can see through Illusions
        ),
    ],
)
