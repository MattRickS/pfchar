from nicegui import ui

from pfchar.char.base import CriticalBonus, Dice, Statistic
from pfchar.char.character import Character
from pfchar.char.enchantments import FlamingBurst
from pfchar.char.items import StatisticModifyingItem, Weapon
from pfchar.char.abilities import (
    PowerAttack,
    WeaponFocus,
    WeaponTraining,
    ImprovedCritical,
)
from pfchar.char.base import WeaponType
from pfchar.utils import (
    crit_to_string,
    sum_up_dice,
    sum_up_modifiers,
    create_status_effect,
)

character = Character(
    name="Yoyu Tekko",
    level=20,
    statistics={
        Statistic.STRENGTH: 19,
        Statistic.DEXTERITY: 14,
        Statistic.CONSTITUTION: 14,
        Statistic.INTELLIGENCE: 12,
        Statistic.WISDOM: 12,
        Statistic.CHARISMA: 10,
    },
    base_attack_bonus=20,
    main_hand=Weapon(
        name="Infernal Forge",
        type=WeaponType.HAMMER,
        critical=CriticalBonus(
            crit_range=20,
            crit_multiplier=3,
        ),
        base_damage=Dice(num=1, sides=8),
        enchantment_modifier=3,
        enchantments=[FlamingBurst()],
    ),
    abilities=[
        PowerAttack(),
        WeaponFocus(WeaponType.HAMMER),
        WeaponTraining(WeaponType.HAMMER),
        ImprovedCritical(WeaponType.HAMMER),
    ],
    items=[
        StatisticModifyingItem(
            name="Belt of Physical Perfection (+6)",
            stats={
                Statistic.STRENGTH: 6,
                Statistic.DEXTERITY: 6,
                Statistic.CONSTITUTION: 6,
            },
        )
    ],
)


def stat_modifier(value: int) -> int:
    return (value - 10) // 2


def render_statistics():
    with ui.expansion("Statistics", value=False):
        with ui.card():
            ui.label("Statistics").style("font-weight: bold; font-size: 1.2rem")
            for stat in [
                Statistic.STRENGTH,
                Statistic.DEXTERITY,
                Statistic.CONSTITUTION,
                Statistic.INTELLIGENCE,
                Statistic.WISDOM,
                Statistic.CHARISMA,
            ]:
                val = character.statistics.get(stat, 10)
                mod = stat_modifier(val)
                ui.label(f"{stat.value}: {val} ({mod:+d})")


# Make weapons section refreshable so it updates when toggles change
@ui.refreshable
def render_weapons():
    with ui.expansion("Weapons", value=False):
        with ui.card():
            ui.label("Weapons").style("font-weight: bold; font-size: 1.2rem")
            ui.label(f"Base Attack Bonus: {character.base_attack_bonus:+d}")
            if character.main_hand:
                w = character.main_hand
                dmg_str = sum_up_dice(w.damage_bonus(character))
                ui.label(f"Main Hand: {w.name} (Type: {w.type}, Damage: {dmg_str})")
            if character.off_hand:
                w = character.off_hand
                dmg_str = sum_up_dice(w.damage_bonus(character))
                ui.label(f"Off Hand: {w.name} (Type: {w.type}, Damage: {dmg_str})")

            def on_two_handed_change(e):
                if not character.toggle_two_handed():
                    e.value = character.is_two_handed()
                    return
                # only refresh the combat modifiers section
                update_combat_sections()

            ui.switch(
                "Two Handed",
                value=character.is_two_handed(),
                on_change=on_two_handed_change,
            )


def render_items():
    with ui.expansion("Items", value=False):
        with ui.card():
            ui.label("Items").style("font-weight: bold; font-size: 1.2rem")
            if character.items:
                for item in character.items:
                    ui.label(item.name)
            else:
                ui.label("No items equipped")


# Make abilities section refreshable so toggles reflect immediately
@ui.refreshable
def render_abilities():
    with ui.expansion("Abilities", value=False):
        with ui.card():
            ui.label("Abilities").style("font-weight: bold; font-size: 1.2rem")
            for ability in character.abilities:
                # Only PowerAttack currently has an EnabledCondition toggle
                if hasattr(ability.condition, "toggle"):

                    def make_handler(ab):
                        def handler(e):
                            ab.condition.toggle()
                            # only refresh the combat modifiers section
                            update_combat_sections()

                        return handler

                    ui.switch(
                        ability.name,
                        value=ability.condition.enabled,
                        on_change=make_handler(ability),
                    )
                else:
                    ui.label(ability.name)


# Make attack/damage section refreshable so computed values update
@ui.refreshable
def render_attack_damage():
    attack_mods = character.attack_bonus()
    damage_mods = character.damage_bonus()
    critical_bonus = character.critical_bonus()

    attack_total = sum(attack_mods.values())
    damage_total_str = sum_up_modifiers(damage_mods)

    with ui.expansion("Combat Modifiers", value=True):
        with ui.card():
            ui.label("Combat Modifiers").style("font-weight: bold; font-size: 1.2rem")
            with ui.row().classes("items-start"):  # two columns
                with ui.column():
                    ui.label("Attack Bonus:")
                    for name, val in attack_mods.items():
                        ui.label(f"• {name}: {val:+d}")
                    ui.separator()
                    ui.label(f"Total Attack Bonus: {attack_total:+d}")
                with ui.column():
                    ui.label("Damage:")
                    for name, dice_list in damage_mods.items():
                        ui.label(f"• {name}: {sum_up_dice(dice_list)}")
                    ui.separator()
                    ui.label(f"Total Damage: {damage_total_str}")
                    ui.label(f"Critical: {crit_to_string(critical_bonus)}")


# Dialog and helpers for status effects
status_dialog = ui.dialog()
with status_dialog:
    with ui.card():
        ui.label("Add Status").style("font-weight: bold; font-size: 1.2rem")
        status_name_input = ui.input("Name")
        status_attack_input = ui.number("Attack Bonus", value=0)
        status_damage_input = ui.number("Damage Bonus", value=0)
        with ui.row():

            def create_status():
                name = status_name_input.value.strip() or "Status"
                attack = int(status_attack_input.value or 0)
                damage = int(status_damage_input.value or 0)
                character.statuses.append(
                    create_status_effect(name, attack_bonus=attack, damage_bonus=damage)
                )
                status_dialog.close()
                render_statuses.refresh()
                update_combat_sections()

            ui.button("Create", on_click=create_status).props("color=primary")
            ui.button("Cancel", on_click=lambda: status_dialog.close())


def open_add_status_dialog():
    status_dialog.open()


def delete_status(index: int):
    if 0 <= index < len(character.statuses):
        del character.statuses[index]
        render_statuses.refresh()
        update_combat_sections()


# Track expansion state of Statuses across refreshes
STATUSES_EXPANDED = False


def update_statuses_expansion(expanded: bool):
    global STATUSES_EXPANDED
    STATUSES_EXPANDED = expanded


@ui.refreshable
def render_statuses():
    # use stored expansion state
    expansion = ui.expansion(
        "Statuses",
        value=STATUSES_EXPANDED,
        on_value_change=lambda e: update_statuses_expansion(e.value),
    )
    with expansion:
        with ui.card():
            ui.label("Statuses").style("font-weight: bold; font-size: 1.2rem")
            if character.statuses:
                for i, status in enumerate(character.statuses):
                    with ui.row().classes("items-center"):
                        ui.label(status.name)
                        ui.button(
                            icon="delete", on_click=lambda _, idx=i: delete_status(idx)
                        ).props("flat color=red")
            else:
                ui.label("No statuses active")
            ui.separator()
            ui.button("Add Status", on_click=open_add_status_dialog).props(
                "color=primary outline"
            )


def update_combat_sections():
    # re-render the computed sections
    render_attack_damage.refresh()


with ui.header():
    ui.label(character.name).style("font-weight: bold; font-size: 1.5rem")

with ui.row():
    with ui.column():
        render_statistics()
        render_weapons()
        render_items()
        render_abilities()
        render_statuses()

render_attack_damage()

ui.run()
