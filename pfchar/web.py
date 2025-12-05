"""
There is much jank in here, mostly AI generated with minor hand tweaking.

The state is pseudo-tab based, but things like closing the status dialog causes
other tabs to close as well (possibly due to refreshable UI elements resetting
the whole page?), or having the mouse over expansions while the same expansion
is clicked in other devices still shows the click (but not the action).

This may or may not work for multiple users.
"""

from nicegui import app, ui

from pfchar.char.base import stat_modifier, Save, Statistic
from pfchar.utils import (
    crit_to_string,
    sum_up_dice,
    sum_up_modifiers,
    create_status_effect,
    get_touch_ac,
    get_flat_footed_ac,
    get_total_ac,
    to_attack_string,
)
from pfchar.char.base import Save
from pfchar.premade import YOYU, DORAMAK, CHELLYBEAN

ALL_CHARACTERS = (YOYU, DORAMAK, CHELLYBEAN)
CHARACTERS_BY_NAME = {c.name: c for c in ALL_CHARACTERS}


def get_character():
    """Return the current character based on app.storage.tab selection.
    Falls back to the first character if none is stored or invalid."""
    name = app.storage.tab.get("selected_character")
    return CHARACTERS_BY_NAME.get(name) or ALL_CHARACTERS[0]


def expansion(name: str, default: bool = False):
    key = f"expansion.{name}"
    return ui.expansion(
        name,
        value=app.storage.tab.get(key, default),
        on_value_change=lambda e: app.storage.tab.update({key: e.value}),
    ).classes("w-full")


def header_expansion(name: str, default: bool = False):
    return expansion(name, default=default).props(
        'header-class="bg-secondary text-white"'
    )


# Updates when statuses modify stats
@ui.refreshable
def render_statistics():
    with header_expansion("Statistics"):
        character = get_character()
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
    with header_expansion("Weapons"):
        character = get_character()
        ui.label(f"Base Attack Bonus: {character.base_attack_bonus:+d}")
        if character.main_hand:
            w = character.main_hand
            dmg_str = sum_up_dice(w.damage_bonus(character))
            ui.label(f"Main Hand: {w.name} (Type: {w.type}, Damage: {dmg_str})")
        if character.off_hand:
            w = character.off_hand
            dmg_str = sum_up_dice(w.damage_bonus(character))
            ui.label(f"Off Hand: {w.name} (Type: {w.type}, Damage: {dmg_str})")


def render_items():
    with header_expansion("Items"):
        character = get_character()
        if character.items:
            for item in character.items:
                ui.label(item.name)
        else:
            ui.label("No items equipped")


def render_abilities():
    with header_expansion("Abilities"):
        character = get_character()
        for ability in character.abilities:
            if hasattr(ability.condition, "toggle"):

                def make_handler(ab):
                    def handler(e):
                        ab.condition.toggle()
                        update_combat_sections()

                    return handler

                ui.switch(
                    ability.name,
                    value=ability.condition.enabled,
                    on_change=make_handler(ability),
                )
            else:
                ui.label(ability.name)


def render_feats():
    with header_expansion("Feats"):
        character = get_character()
        for feat in character.feats:
            ui.label(feat.name)


def on_two_handed_change(e):
    character = get_character()
    if not character.toggle_two_handed():
        e.value = character.is_two_handed()
        return
    update_combat_sections()


def make_handler(effect_):
    def handler(e):
        effect_.condition.toggle()
        # only refresh the combat modifiers section
        update_combat_sections()

    return handler


# Make attack/damage section refreshable so computed values update
@ui.refreshable
def render_combat_modifiers():
    character = get_character()
    attack_mods = character.attack_bonus()
    damage_mods = character.damage_bonus()
    critical_bonus = character.critical_bonus()
    ac_bonuses = character.armour_bonuses()
    cmb_breakdown = character.get_cmb()
    cmd_breakdown = character.get_cmd()
    saves_breakdown = character.get_saves()
    attack_string = to_attack_string(attack_mods)
    damage_total_str = sum_up_modifiers(damage_mods)
    cmb_total = sum(cmb_breakdown.values()) if cmb_breakdown else 0
    cmd_total = sum(cmd_breakdown.values()) if cmd_breakdown else 0
    with header_expansion("Combat Modifiers", default=True):
        with ui.element("div").classes(
            "grid grid-cols-1 md:grid-cols-6 gap-2 items-start"
        ):
            ui.switch(
                "Two Handed",
                value=character.is_two_handed(),
                on_change=on_two_handed_change,
            )
            for effect in character.all_effects():
                if hasattr(effect.condition, "toggle"):
                    ui.switch(
                        effect.name,
                        value=effect.condition.enabled,
                        on_change=make_handler(effect),
                    )
            with ui.element("div").classes("flex flex-col"):
                with expansion(f"To Hit {attack_string}").style(
                    "font-weight: bold; text-align: center"
                ):
                    for name, val in attack_mods.items():
                        ui.label(f"• {name}: {val:+d}")
            with ui.element("div").classes("flex flex-col"):
                with expansion(
                    f"Damage {damage_total_str}/{crit_to_string(critical_bonus)}"
                ).style("font-weight: bold; text-align: center"):
                    for name, dice_list in damage_mods.items():
                        ui.label(f"• {name}: {sum_up_dice(dice_list)}")
            with ui.element("div").classes("flex flex-col"):
                total_ac = get_total_ac(ac_bonuses)
                touch_ac = get_touch_ac(ac_bonuses)
                flat_footed_ac = get_flat_footed_ac(ac_bonuses)
                with expansion(
                    f"AC: {total_ac:d} (touch: {touch_ac:d}, flat-footed: {flat_footed_ac:d})"
                ).style("font-weight: bold; text-align: center"):
                    for ac_type, val in ac_bonuses.items():
                        ui.label(
                            f"• {ac_type.value if hasattr(ac_type, 'value') else str(ac_type)}: {val:+d}"
                        )
            with ui.element("div").classes("flex flex-col"):
                with expansion(f"CMB {cmb_total:+d}").style(
                    "font-weight: bold; text-align: center"
                ):
                    for name, val in cmb_breakdown.items():
                        ui.label(f"• {name}: {val:+d}")
            with ui.element("div").classes("flex flex-col"):
                with expansion(f"CMD {cmd_total:+d}").style(
                    "font-weight: bold; text-align: center"
                ):
                    for name, val in cmd_breakdown.items():
                        ui.label(f"• {name}: {val:+d}")
            for save, data in saves_breakdown.items():
                with ui.element("div").classes("flex flex-col"):
                    save_total = sum(data.values())
                    with expansion(f"{save.value} {save_total:+d}").style(
                        "font-weight: bold; text-align: center"
                    ):
                        for name, val in data.items():
                            ui.label(f"• {name}: {val:+d}")


def open_add_status_dialog():
    status_dialog = create_status_dialog()
    status_dialog.open()


def delete_status(index: int):
    character = get_character()
    if 0 <= index < len(character.statuses):
        del character.statuses[index]
        render_statuses.refresh()
        update_combat_sections()


@ui.refreshable
def render_statuses():
    with header_expansion("Statuses"):
        character = get_character()
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
    render_combat_modifiers.refresh()


# Page renderer to rebuild sections for current character
@ui.refreshable
def render_page():
    # rebuild all sections for the selected global `character`
    with ui.row():
        with ui.column().style("gap: 0.1rem; width: 100%"):
            render_statistics()
            render_weapons()
            render_items()
            render_abilities()
            render_feats()
            render_statuses()
            render_combat_modifiers()


def on_character_change(name: str):
    # swap current character by name and store selection per tab
    if name in CHARACTERS_BY_NAME:
        app.storage.tab["selected_character"] = name
    else:
        app.storage.tab["selected_character"] = ALL_CHARACTERS[0].name
    render_page.refresh()


def create_status_dialog():
    status_dialog = ui.dialog()
    with status_dialog:
        with ui.card():
            ui.label("Add Status").style("font-weight: bold; font-size: 1.2rem")
            status_name_input = ui.input("Name").props("clearable")
            status_attack_input = ui.number("Attack Bonus", value=0)
            status_damage_input = ui.number("Damage Bonus", value=0)
            ui.label("Statistic Modifiers").style("margin-top: 0.5rem")
            stat_inputs: dict[Statistic, any] = {}
            with ui.column():
                for stat in Statistic:
                    stat_inputs[stat] = ui.number(stat.value, value=0)
            ui.label("Save Modifiers").style("margin-top: 0.5rem")
            save_inputs: dict[Save, any] = {}
            with ui.row().classes("gap-4"):
                for save in Save:
                    save_inputs[save] = ui.number(save.value, value=0)
            warn_label = ui.label("At least one non-name value is required.").style(
                "color: #b00020"
            )
            warn_label.visible = False
            with ui.row():

                def create_status():
                    name = (status_name_input.value or "").strip()
                    if not name:
                        warn_label.visible = False
                        status_name_input.props(
                            'error error-message="Name is required"'
                        )
                        return
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
                        for inp in save_inputs.values():
                            try:
                                if int(inp.value or 0) != 0:
                                    non_default = True
                                    break
                            except Exception:
                                continue
                    if not non_default:
                        warn_label.visible = True
                        return
                    warn_label.visible = False
                    character = get_character()
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
                    saves_dict = {}
                    for save, inp in save_inputs.items():
                        try:
                            v = int(inp.value or 0)
                        except Exception:
                            v = 0
                        if v:
                            saves_dict[save] = v
                    character.statuses.append(
                        create_status_effect(
                            name,
                            attack_bonus=attack,
                            damage_bonus=damage,
                            statistics=stats_dict,
                            saves=saves_dict,
                        )
                    )
                    status_name_input.value = ""
                    status_name_input.props('error=false error-message=""')
                    status_attack_input.value = 0
                    status_damage_input.value = 0
                    for inp in stat_inputs.values():
                        inp.value = 0
                    for inp in save_inputs.values():
                        inp.value = 0
                    status_dialog.close()
                    render_statuses.refresh()
                    update_combat_sections()

                ui.button("Create", on_click=create_status).props("color=primary")
                ui.button("Cancel", on_click=lambda: status_dialog.close())

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
            for inp in save_inputs.values():
                inp.on("change", clear_warning)
    return status_dialog


@ui.page("/")
async def page():
    await ui.context.client.connected()
    selected_name = app.storage.tab.get("selected_character")
    if selected_name not in CHARACTERS_BY_NAME:
        selected_name = ALL_CHARACTERS[0].name

    def handle_tab_change(e):
        if e.value:
            on_character_change(e.value)

    with ui.header():
        with ui.tabs(value=selected_name, on_change=handle_tab_change):
            for c in ALL_CHARACTERS:
                ui.tab(c.name)
    render_page()


ui.run()
