from nicegui import ui

from pfchar.char.base import stat_modifier, CriticalBonus, Dice, Statistic
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


EXPANSION = {}


def expansion(name: str, default: bool = False):
    return ui.expansion(
        name,
        value=EXPANSION.get(name, default),
        on_value_change=lambda e: EXPANSION.update({name: e.value}),
    )


# Updates when statuses modify stats
@ui.refreshable
def render_statistics():
    with expansion("Statistics"):
        with ui.card():
            ui.label("Statistics").style("font-weight: bold; font-size: 1.2rem")
            for stat in Statistic:
                value = character.statistics.get(stat, 10)
                modifier = stat_modifier(value)
                modified_value = character.modified_statistic(stat)
                modified_modifier = stat_modifier(modified_value)
                if modified_value != value:
                    ui.label(
                        f"{stat.value}: {value} ({modifier:+d}) -> {modified_value} ({modified_modifier:+d})"
                    )
                else:
                    ui.label(f"{stat.value}: {value} ({modifier:+d})")


def render_weapons():
    with expansion("Weapons"):
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
    with expansion("Items"):
        with ui.card():
            ui.label("Items").style("font-weight: bold; font-size: 1.2rem")
            if character.items:
                for item in character.items:
                    ui.label(item.name)
            else:
                ui.label("No items equipped")


def render_abilities():
    with expansion("Abilities"):
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

    with expansion("Combat Modifiers", default=True):
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
        status_name_input = ui.input("Name").props("clearable")
        status_attack_input = ui.number("Attack Bonus", value=0)
        status_damage_input = ui.number("Damage Bonus", value=0)
        # per-stat modifiers
        ui.label("Statistic Modifiers").style("margin-top: 0.5rem")
        stat_inputs: dict[Statistic, any] = {}
        with ui.column():
            for stat in Statistic:
                stat_inputs[stat] = ui.number(stat.value, value=0)
        # warning message area
        warn_label = ui.label("At least one non-name value is required.").style(
            "color: #b00020"
        )
        warn_label.visible = False
        with ui.row():

            def create_status():
                name = (status_name_input.value or "").strip()
                # require non-empty name
                if not name:
                    warn_label.visible = False
                    status_name_input.props('error error-message="Name is required"')
                    return
                # check if any non-default fields are provided
                non_default = bool(int(status_attack_input.value or 0)) or bool(
                    int(status_damage_input.value or 0)
                )
                if not non_default:
                    for inp in stat_inputs.values():
                        try:
                            if int(inp.value or 0) != 0:
                                non_default = True
                                break
                        except Exception:
                            continue
                if not non_default:
                    # show warning and block submission
                    warn_label.visible = True
                    return
                warn_label.visible = False

                attack = int(status_attack_input.value or 0)
                damage = int(status_damage_input.value or 0)
                stats_dict = {}
                for stat, inp in stat_inputs.items():
                    try:
                        v = int(inp.value or 0)
                    except Exception:
                        v = 0
                    if v:
                        stats_dict[stat] = v
                character.statuses.append(
                    create_status_effect(
                        name,
                        attack_bonus=attack,
                        damage_bonus=damage,
                        statistics=stats_dict,
                    )
                )
                # reset dialog inputs after successful add
                status_name_input.value = ""
                status_name_input.props('error=false error-message=""')
                status_attack_input.value = 0
                status_damage_input.value = 0
                for inp in stat_inputs.values():
                    inp.value = 0
                status_dialog.close()
                render_statuses.refresh()
                update_combat_sections()

            ui.button("Create", on_click=create_status).props("color=primary")
            ui.button("Cancel", on_click=lambda: status_dialog.close())

        # clear error/warning when user types or changes values
        def clear_name_error(_):
            status_name_input.props('error=false error-message=""')
            warn_label.visible = False

        status_name_input.on("input", clear_name_error)

        def clear_warning(_):
            warn_label.visible = False

        status_attack_input.on("change", clear_warning)
        status_damage_input.on("change", clear_warning)
        for inp in stat_inputs.values():
            inp.on("change", clear_warning)


def open_add_status_dialog():
    status_dialog.open()


def delete_status(index: int):
    if 0 <= index < len(character.statuses):
        del character.statuses[index]
        render_statuses.refresh()
        update_combat_sections()


@ui.refreshable
def render_statuses():
    with expansion("Statuses"):
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
    render_statistics.refresh()
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
