"""
There is much jank in here, mostly AI generated with minor hand tweaking.

The state is pseudo-tab based, but things like closing the status dialog causes
other tabs to close as well (possibly due to refreshable UI elements resetting
the whole page?), or having the mouse over expansions while the same expansion
is clicked in other devices still shows the click (but not the action).

This may or may not work for multiple users.
"""

from nicegui import app, ui

from pfchar.char.base import stat_modifier, ArmorBonus, Save, Statistic
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


def render_list(values):
    with ui.list().props("dense").style("font-weight: normal; text-align: left"):
        for val in values:
            ui.item(val)


def render_combat_mod(text: str, values: list[str]):
    with ui.element("div").classes("flex flex-col"):
        with expansion(text).style("font-weight: bold; text-align: center"):
            render_list(values)


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
            render_combat_mod(
                f"To Hit {attack_string}",
                (f"{name}: {val:+d}" for name, val in attack_mods.items()),
            )
            render_combat_mod(
                f"Damage {damage_total_str}/{crit_to_string(critical_bonus)}",
                (
                    f"{name}: {sum_up_dice(dice_list)}"
                    for name, dice_list in damage_mods.items()
                ),
            )
            total_ac = get_total_ac(ac_bonuses)
            touch_ac = get_touch_ac(ac_bonuses)
            flat_footed_ac = get_flat_footed_ac(ac_bonuses)
            render_combat_mod(
                f"AC: {total_ac:d} (touch: {touch_ac:d}, flat-footed: {flat_footed_ac:d})",
                (
                    (
                        (
                            f"{ac_type.value}: {val:+d} (capped)"
                            if (
                                ac_type == ArmorBonus.DEXTERITY
                                and character.is_dex_capped()
                            )
                            else f"{ac_type.value}: {val:+d}"
                        )
                        for ac_type, val in ac_bonuses.items()
                    )
                ),
            )
            render_combat_mod(
                f"CMB {cmb_total:+d}",
                (f"{name}: {val:+d}" for name, val in cmb_breakdown.items()),
            )
            render_combat_mod(
                f"CMD {cmd_total:+d}",
                (f"{name}: {val:+d}" for name, val in cmd_breakdown.items()),
            )
            for save, data in saves_breakdown.items():
                render_combat_mod(
                    f"{save.value} {sum(data.values()):+d}",
                    (f"{name}: {val:+d}" for name, val in data.items()),
                )


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


def _create_enum_entry_section(
    enum_class: type,
    group_options: dict[str, tuple[type]] = None,
    on_change=None,
    default=None,
):
    options = {(s,): s.value for s in enum_class}
    if group_options:
        options.update({v: k for k, v in group_options.items()})

    if default is not None and not isinstance(default, tuple):
        default = (default,)

    with ui.expansion(f"{enum_class.__name__} Modifiers").classes("font-semibold mt-2"):
        entries: dict = {}
        with ui.row():
            enum_select = ui.select(
                options, value=default, label=enum_class.__name__
            ).props("outlined dense")
            enum_value = ui.number(label="Value", value=0).props("outlined dense")

        def add_entry():
            if enum_select.value is None:
                return

            try:
                v = int(enum_value.value or 0)
            except Exception:
                v = 0

            if v == 0:
                return

            entries.update({e: v for e in enum_select.value})
            enum_select.set_value(None)
            enum_value.set_value(0)
            refresh_entries()
            if on_change:
                on_change()

        ui.button(f"Add {enum_class.__name__}", on_click=add_entry).props("dense")
        ui_entries = ui.column().classes("gap-1")

        def refresh_entries():
            ui_entries.clear()
            for s, v in entries.items():
                with ui_entries:
                    with ui.row().classes("items-center justify-between"):
                        ui.label(f"{s.value}: {v:+d}")
                        ui.button(
                            icon="delete",
                            on_click=lambda _, key=s: (
                                entries.pop(key),
                                refresh_entries(),
                            ),
                        ).props("flat color=red dense")

        enum_select.on("keydown.enter", add_entry)
        enum_value.on("keydown.enter", add_entry)

    return entries


def create_status_dialog():
    status_dialog = ui.dialog()
    expanded = getattr(app.storage.tab, "statuses_expanded", True)

    with status_dialog:
        with ui.card().style("width: 75vw; max-width: 75vw"):
            ui.label("Add Status").classes("text-xl font-bold text-center")

            # Basic inputs
            name_input = ui.input("Name").props("outlined clearable").classes("w-full")
            with ui.row():
                status_attack_input = ui.number(label="Attack Bonus", value=0).props(
                    "outlined dense"
                )
                status_damage_input = ui.number(label="Damage Bonus", value=0).props(
                    "outlined dense"
                )

            def clear_warning(_=None):
                warn_label.text = ""
                warn_label.visible = False
                name_input.props("error=false error-message=")

            # Enum entry sections: Statistics, Saves, AC Bonuses
            ui.separator()
            stat_entries = _create_enum_entry_section(
                Statistic,
                group_options={
                    "All": tuple(Statistic),
                    "Physical": (
                        Statistic.STRENGTH,
                        Statistic.DEXTERITY,
                        Statistic.CONSTITUTION,
                    ),
                    "Mental": (
                        Statistic.INTELLIGENCE,
                        Statistic.WISDOM,
                        Statistic.CHARISMA,
                    ),
                },
                default=Statistic.STRENGTH,
                on_change=clear_warning,
            )
            ui.separator()
            save_entries = _create_enum_entry_section(
                Save,
                group_options={"All": tuple(Save)},
                default=Save.FORTITUDE,
                on_change=clear_warning,
            )
            ui.separator()
            ac_entries = _create_enum_entry_section(
                ArmorBonus, default=ArmorBonus.DEFLECTION, on_change=clear_warning
            )

            warn_label = (
                ui.label("").classes("text-red-600").style("min-height: 1.5rem")
            )
            warn_label.visible = False

            def validate_unique_name(name: str) -> bool:
                character = get_character()
                return name and all(s.name != name for s in character.statuses)

            def has_non_default_values() -> bool:
                if int(status_attack_input.value or 0) != 0:
                    return True
                if int(status_damage_input.value or 0) != 0:
                    return True
                if stat_entries or save_entries or ac_entries:
                    return True
                return False

            name_input.on("input", clear_warning)
            status_attack_input.on("change", clear_warning)
            status_damage_input.on("change", clear_warning)

            def submit(_=None):
                name = (name_input.value or "").strip()
                if not name:
                    name_input.props('error=true error-message="Name is required"')
                    warn_label.text = "Please provide a status name."
                    warn_label.visible = True
                    return
                if not validate_unique_name(name):
                    name_input.props('error=true error-message="Name must be unique"')
                    warn_label.text = "Status name must be unique."
                    warn_label.visible = True
                    return
                if not has_non_default_values():
                    warn_label.text = "At least one non-default value is required."
                    warn_label.visible = True
                    return

                character = get_character()
                new_status = create_status_effect(
                    name=name,
                    attack_bonus=status_attack_input.value,
                    damage_bonus=status_damage_input.value,
                    statistics=stat_entries,
                    saves=save_entries,
                    ac_bonuses=ac_entries,
                )
                character.statuses.append(new_status)

                status_dialog.close()
                render_statuses.refresh()
                update_combat_sections()
                app.storage.tab["statuses_expanded"] = expanded

            def cancel(_=None):
                status_dialog.close()

            # Enter key submits
            name_input.on("keydown.enter", submit)
            status_attack_input.on("keydown.enter", submit)
            status_damage_input.on("keydown.enter", submit)

            with ui.row().classes("justify-end gap-2"):
                ui.button("Cancel", on_click=cancel).props("flat color=grey")
                ui.button("Create", on_click=submit).props("color=primary")

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
