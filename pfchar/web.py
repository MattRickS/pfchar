from nicegui import app, ui

from pfchar.char.base import stat_modifier, CriticalBonus, Dice, Save, Statistic
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

yoyu = Character(
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

someone_else = Character(
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
all_characters = (yoyu, someone_else)
CHARACTER = None
CHARACTERS_BY_NAME = {c.name: c for c in all_characters}
STATUS_DIALOG = None


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
        for stat in Statistic:
            value = CHARACTER.statistics.get(stat, 10)
            modifier = stat_modifier(value)
            modified_value = CHARACTER.modified_statistic(stat)
            modified_modifier = stat_modifier(modified_value)
            if modified_value != value:
                ui.label(
                    f"{stat.value}: {value} ({modifier:+d}) -> {modified_value} ({modified_modifier:+d})"
                )
            else:
                ui.label(f"{stat.value}: {value} ({modifier:+d})")


def render_weapons():
    with header_expansion("Weapons"):
        ui.label(f"Base Attack Bonus: {CHARACTER.base_attack_bonus:+d}")
        if CHARACTER.main_hand:
            w = CHARACTER.main_hand
            dmg_str = sum_up_dice(w.damage_bonus(CHARACTER))
            ui.label(f"Main Hand: {w.name} (Type: {w.type}, Damage: {dmg_str})")
        if CHARACTER.off_hand:
            w = CHARACTER.off_hand
            dmg_str = sum_up_dice(w.damage_bonus(CHARACTER))
            ui.label(f"Off Hand: {w.name} (Type: {w.type}, Damage: {dmg_str})")


def render_items():
    with header_expansion("Items"):
        if CHARACTER.items:
            for item in CHARACTER.items:
                ui.label(item.name)
        else:
            ui.label("No items equipped")


def render_abilities():
    with header_expansion("Abilities"):
        for ability in CHARACTER.abilities:
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


def render_feats():
    with header_expansion("Feats"):
        for feat in CHARACTER.feats:
            ui.label(feat.name)


def on_two_handed_change(e):
    if not CHARACTER.toggle_two_handed():
        e.value = CHARACTER.is_two_handed()
        return
    # only refresh the combat modifiers section
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
    attack_mods = CHARACTER.attack_bonus()
    damage_mods = CHARACTER.damage_bonus()
    critical_bonus = CHARACTER.critical_bonus()
    ac_bonuses = CHARACTER.armour_bonuses()
    cmb_breakdown = CHARACTER.get_cmb()
    cmd_breakdown = CHARACTER.get_cmd()
    saves_breakdown = CHARACTER.get_saves()

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
                value=CHARACTER.is_two_handed(),
                on_change=on_two_handed_change,
            )

            for effect in CHARACTER.all_effects():
                # Only PowerAttack currently has an EnabledCondition toggle
                if hasattr(effect.condition, "toggle"):

                    ui.switch(
                        effect.name,
                        value=effect.condition.enabled,
                        on_change=make_handler(effect),
                    )

            # Attack Column
            with ui.element("div").classes("flex flex-col"):
                with expansion(f"To Hit {attack_string}").style(
                    "font-weight: bold; text-align: center"
                ):
                    for name, val in attack_mods.items():
                        ui.label(f"• {name}: {val:+d}")
            # Damage Column
            with ui.element("div").classes("flex flex-col"):
                with expansion(
                    f"Damage {damage_total_str}/{crit_to_string(critical_bonus)}"
                ).style("font-weight: bold; text-align: center"):
                    for name, dice_list in damage_mods.items():
                        ui.label(f"• {name}: {sum_up_dice(dice_list)}")
            # AC Column
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
            # CMB Column
            with ui.element("div").classes("flex flex-col"):
                # ui.label(f"CMB {cmb_total:+d}").style("font-weight: bold; text-align: center")
                with expansion(f"CMB {cmb_total:+d}").style(
                    "font-weight: bold; text-align: center"
                ):
                    for name, val in cmb_breakdown.items():
                        ui.label(f"• {name}: {val:+d}")
            # CMD Column
            with ui.element("div").classes("flex flex-col"):
                with expansion(f"CMD {cmd_total:+d}").style(
                    "font-weight: bold; text-align: center"
                ):
                    for name, val in cmd_breakdown.items():
                        ui.label(f"• {name}: {val:+d}")
            # Saves Column
            for save, data in saves_breakdown.items():
                with ui.element("div").classes("flex flex-col"):
                    save_total = sum(data.values())
                    with expansion(f"{save.value} {save_total:+d}").style(
                        "font-weight: bold; text-align: center"
                    ):
                        for name, val in data.items():
                            ui.label(f"• {name}: {val:+d}")


def open_add_status_dialog():
    global STATUS_DIALOG
    if STATUS_DIALOG is None:
        STATUS_DIALOG = create_status_dialog()
    STATUS_DIALOG.open()


def delete_status(index: int):
    if 0 <= index < len(CHARACTER.statuses):
        del CHARACTER.statuses[index]
        render_statuses.refresh()
        update_combat_sections()


@ui.refreshable
def render_statuses():
    with header_expansion("Statuses"):
        if CHARACTER.statuses:
            for i, status in enumerate(CHARACTER.statuses):
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
    global CHARACTER
    # swap current character by name
    for c in all_characters:
        if c.name == name:
            CHARACTER = c
            break
    else:
        CHARACTER = all_characters[0]
    # store per tab (requires client connection)
    try:
        app.storage.tab["selected_character"] = name
    except Exception:
        pass
    # rerender page
    render_page.refresh()


def create_status_dialog():
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
            # per-save modifiers
            ui.label("Save Modifiers").style("margin-top: 0.5rem")
            save_inputs: dict[Save, any] = {}
            with ui.row().classes("gap-4"):
                for save in Save:
                    save_inputs[save] = ui.number(save.value, value=0)
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
                        status_name_input.props(
                            'error error-message="Name is required"'
                        )
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
                        for inp in save_inputs.values():
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
                    saves_dict = {}
                    for save, inp in save_inputs.items():
                        try:
                            v = int(inp.value or 0)
                        except Exception:
                            v = 0
                        if v:
                            saves_dict[save] = v
                    CHARACTER.statuses.append(
                        create_status_effect(
                            name,
                            attack_bonus=attack,
                            damage_bonus=damage,
                            statistics=stats_dict,
                            saves=saves_dict,
                        )
                    )
                    # reset dialog inputs after successful add
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
            for inp in save_inputs.values():
                inp.on("change", clear_warning)

    return status_dialog


@ui.page("/")
async def page():
    global CHARACTER
    await ui.context.client.connected()

    # Restore selection from tab storage
    selected_name = app.storage.tab.get("selected_character")
    if not (CHARACTER := CHARACTERS_BY_NAME.get(selected_name)):
        CHARACTER = all_characters[0]
        selected_name = CHARACTER.name

    # Handle tab changes
    def handle_tab_change(e):
        if e.value:
            on_character_change(e.value)

    # Tabs for characters
    with ui.header():
        with ui.tabs(value=selected_name, on_change=handle_tab_change) as tabs:
            for c in all_characters:
                ui.tab(c.name)

    # Panels (optional visual grouping)
    with ui.tab_panels(tabs, value=selected_name) as panels:
        for c in all_characters:
            with ui.tab_panel(c.name):
                pass  # content is global; page re-renders on selection change

    # Initial render with default
    render_page()


ui.run()
