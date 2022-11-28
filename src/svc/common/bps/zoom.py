from typing import Any, Callable, Optional
from loguru import logger

from src import defs, text
from src.parse import pattern
from src.svc.common import CommonEverything, messages, pagination, Ctx, bps
from src.svc.common.states import formatter as states_fmt
from src.svc.common.states.tree import ZOOM, Space
from src.svc.common.router import r
from src.svc.common.filters import PayloadFilter, StateFilter, UnionFilter
from src.svc.common import keyboard as kb
from src.data import zoom, Field, error


@r.on_callback(StateFilter(ZOOM.III_DUMP), PayloadFilter(kb.Payload.DUMP))
async def dump(everything: CommonEverything):
    ctx = everything.ctx

    await everything.send_message(
        text = ctx.settings.zoom.entries.dump(),
        chunker = text.double_newline_chunks
    )

    everything.force_send = True

    return await bps.back(everything)


async def going_to_dump(everything: CommonEverything):
    answer_text = (
        messages.Builder()
                .add(messages.format_dump_explain())
    )
    answer_keyboard = kb.Keyboard([
        [kb.DUMP_BUTTON]
    ])

    return await everything.edit_or_answer(
        text = answer_text.make(),
        keyboard = answer_keyboard
    )

@r.on_callback(StateFilter(ZOOM.II_BROWSE), PayloadFilter(kb.Payload.DUMP))
async def to_going_to_dump(everything: CommonEverything):
    everything.navigator.append(ZOOM.III_DUMP)
    return await going_to_dump(everything)


@r.on_callback(PayloadFilter(kb.Payload.REMOVE))
async def remove_entry(everything: CommonEverything):
    focused = everything.ctx.settings.zoom.focused
    selected = focused.selected

    everything.navigator.jump_back_to(ZOOM.II_BROWSE)

    if selected is None:
        # usually it should not happen,
        # only in case of rate limit
        return await to_browse(everything)

    focused.remove(selected.name.value)

    return await to_browse(everything)

async def set_attribute(
    everything: CommonEverything,
    main_message: str,
    getter: Callable[[], Any],
    setter: Callable[[Any], None],
    nuller: Callable[[], None] = lambda: None,
    limit: Optional[int] = zoom.VALUE_LIMIT,
):
    ctx = everything.ctx

    footer_addition = messages.default_footer_addition(everything)
    answer_keyboard = kb.Keyboard([
        [kb.NULL_BUTTON.only_if(
            ctx.navigator.current != ZOOM.IIII_NAME
            and getter() is not None
        )]
    ])

    if everything.is_from_message:
        message = everything.message

        if not message.text:
            answer_text = (
                messages.Builder()
                        .add(messages.format_no_text())
                        .add(messages.format_current_value(getter()))
                        .add(main_message)
                        .add(footer_addition)
            )

            return await message.answer(
                text     = answer_text.make(),
                keyboard = answer_keyboard
            )
        
        if len(message.text) > limit:
            answer_text = (
                messages.Builder()
                        .add(messages.format_current_value(getter()))
                        .add(main_message)
                        .add(messages.format_value_too_big(limit))
                        .add(footer_addition)
            )

            return await message.answer(
                text     = answer_text.make(),
                keyboard = answer_keyboard
            )

        try:
            setter(", ".join([section for section in message.text.split("\n") if section != ""]))
        except error.ZoomNameInDatabase:
            answer_text = (
                messages.Builder()
                        .add(messages.format_name_in_database())
                        .add(messages.format_current_value(getter()))
                        .add(main_message)
                        .add(footer_addition)
            )

            return await message.answer(
                text     = answer_text.make(),
                keyboard = answer_keyboard
            )

        ctx.navigator.jump_back_to(
            ZOOM.II_BROWSE, 
            execute_actions = False
        )

        return await to_entry(everything)

    if everything.is_from_event:
        event = everything.event

        if event.payload == kb.Payload.NULL:
            nuller()

            return await to_entry(everything)

        answer_text = (
            messages.Builder()
                    .add(messages.format_current_value(getter()))
                    .add(main_message)
                    .add(footer_addition)
        )

        return await event.edit_message(
            text     = answer_text.make(),
            keyboard = answer_keyboard
        )

@r.on_callback(StateFilter(ZOOM.II_BROWSE), PayloadFilter(kb.Payload.CLEAR))
async def clear_new_entries(everything: CommonEverything):
    ctx = everything.ctx

    ctx.settings.zoom.new_entries.clear()

    ctx.navigator.jump_back_to(ZOOM.I_MASS)
    return await mass(everything)

@r.on_callback(StateFilter(ZOOM.II_BROWSE), PayloadFilter(kb.Payload.REMOVE_ALL))
async def remove_entries(everything: CommonEverything):
    ctx = everything.ctx

    ctx.settings.zoom.entries.clear()

    return await browse(everything)

@r.on_callback(
    StateFilter(ZOOM.I_MASS_CHECK), 
    PayloadFilter(kb.Payload.CONFIRM)
)
async def confirm_mass_add(everything: CommonEverything):
    ctx = everything.ctx

    is_init_space = Space.INIT in ctx.navigator.spaces
    is_hub_space = Space.HUB in ctx.navigator.spaces

    # move everything from `new_entries` to `entries`
    ctx.settings.zoom.confirm_new_entries()

    if is_init_space:
        # jump back to space that is different from current one
        ctx.navigator.space_jump_back()
    elif is_hub_space:
        ctx.navigator.jump_back_to(ZOOM.II_BROWSE)
        ctx.navigator.jump_back_to(ZOOM.II_BROWSE)

    # get module for current space
    space = bps.get_module_space(ctx.navigator.space)

    # get handler for current state
    handler = space.STATE_MAP.get(ctx.navigator.current)
    # call this handler
    return await handler(everything)


async def mass_check(everything: CommonEverything):
    ctx = everything.ctx

    adding = ctx.settings.zoom.adding
    overwriting = ctx.settings.zoom.overwriting

    answer_text = (
        messages.Builder()
                .add(messages.format_zoom_mass_adding_overview(adding, overwriting))
    )
    answer_keyboard = kb.Keyboard([
        [kb.CONFIRM_BUTTON]
    ])

    return await everything.edit_or_answer(
        text     = answer_text.make(),
        keyboard = answer_keyboard,
    )

@r.on_callback(StateFilter(ZOOM.II_BROWSE), PayloadFilter(kb.Payload.ADD_ALL))
async def to_mass_check(everything: CommonEverything):
    everything.navigator.append(ZOOM.I_MASS_CHECK)
    return await mass_check(everything)

@r.on_everything(StateFilter(ZOOM.IIII_NOTES))
async def notes(everything: CommonEverything):
    def getter():
        return everything.ctx.settings.zoom.focused.selected.notes.value

    def setter(value: Any):
        everything.ctx.settings.zoom.focused.selected.notes = Field(value)

    def nuller():
        everything.ctx.settings.zoom.focused.selected.notes = Field(None)

    return await set_attribute(
        everything   = everything,
        main_message = messages.format_enter_notes(),
        getter       = getter,
        setter       = setter,
        nuller       = nuller,
    )

@r.on_callback(StateFilter(ZOOM.III_ENTRY), PayloadFilter(kb.Payload.NOTES))
async def to_notes(everything: CommonEverything):
    everything.navigator.append(ZOOM.IIII_NOTES)
    return await notes(everything)
    
@r.on_everything(StateFilter(ZOOM.IIII_PWD))
async def pwd(everything: CommonEverything):

    def getter():
        return everything.ctx.settings.zoom.focused.selected.pwd.value

    def setter(value: Any):
        everything.ctx.settings.zoom.focused.selected.pwd = Field(value)

    def nuller():
        everything.ctx.settings.zoom.focused.selected.pwd = Field(None)

    return await set_attribute(
        everything   = everything,
        main_message = messages.format_enter_pwd(),
        getter       = getter,
        setter       = setter,
        nuller       = nuller,
    )

@r.on_callback(StateFilter(ZOOM.III_ENTRY), PayloadFilter(kb.Payload.PWD))
async def to_pwd(everything: CommonEverything):
    everything.navigator.append(ZOOM.IIII_PWD)
    return await pwd(everything)


@r.on_everything(StateFilter(ZOOM.IIII_ID))
async def id_(everything: CommonEverything):

    def getter():
        return everything.ctx.settings.zoom.focused.selected.id.value

    def setter(value: Any):
        everything.ctx.settings.zoom.focused.selected.id = Field(value)

    def nuller():
        everything.ctx.settings.zoom.focused.selected.id = Field(None)

    return await set_attribute(
        everything   = everything,
        main_message = messages.format_enter_id(),
        getter       = getter,
        setter       = setter,
        nuller       = nuller,
    )

@r.on_callback(StateFilter(ZOOM.III_ENTRY), PayloadFilter(kb.Payload.ID))
async def to_id(everything: CommonEverything):
    everything.navigator.append(ZOOM.IIII_ID)
    return await id_(everything)


@r.on_everything(StateFilter(ZOOM.IIII_URL))
async def url(everything: CommonEverything):

    def getter():
        return everything.ctx.settings.zoom.focused.selected.url.value

    def setter(value: Any):
        everything.ctx.settings.zoom.focused.selected.url = Field(value)

    def nuller():
        everything.ctx.settings.zoom.focused.selected.url = Field(None)

    return await set_attribute(
        everything   = everything,
        main_message = messages.format_enter_url(),
        getter       = getter,
        setter       = setter,
        nuller       = nuller,
    )

@r.on_callback(StateFilter(ZOOM.III_ENTRY), PayloadFilter(kb.Payload.URL))
async def to_url(everything: CommonEverything):
    everything.navigator.append(ZOOM.IIII_URL)
    return await url(everything)


@r.on_message(StateFilter(ZOOM.IIII_NAME))
async def name(everything: CommonEverything):
    ctx = everything.ctx

    def getter():
        focused = ctx.settings.zoom.focused

        if focused.selected is None:
            return None

        return ctx.settings.zoom.focused.selected.name.value

    def setter(value: Any):
        focused = ctx.settings.zoom.focused

        if focused.selected is None:
            # user tries to add a new entry
            focused.add_from_name(value)
            focused.select(value)

            ctx.settings.zoom.finish()

            return None

        old = focused.selected.name.value

        focused.change_name(old, value)

        # select this backup
        focused.select(value)

    return await set_attribute(
        everything   = everything,
        main_message = messages.format_enter_name(),
        getter       = getter,
        setter       = setter,
        limit        = zoom.NAME_LIMIT
    )

@r.on_callback(StateFilter(ZOOM.III_ENTRY), PayloadFilter(kb.Payload.NAME))
async def to_name(everything: CommonEverything):
    everything.navigator.append(ZOOM.IIII_NAME)
    return await name(everything)


async def entry(everything: CommonEverything):
    ctx = everything.ctx
    
    selected = ctx.settings.zoom.focused.selected

    answer_text = (
        messages.Builder()
                .add(selected.format())
                .add(messages.format_press_buttons_to_change())
    )
    answer_keyboard = kb.Keyboard.from_dataclass(
        dataclass = selected,
        footer=[[kb.REMOVE_BUTTON]]
    )

    await everything.edit_or_answer(
        text     = answer_text.make(),
        keyboard = answer_keyboard
    )

async def to_entry(everything: CommonEverything):
    everything.navigator.jump_back_to_or_append(ZOOM.III_ENTRY)
    return await entry(everything)

@r.on_callback(StateFilter(ZOOM.II_BROWSE), PayloadFilter(kb.Payload.ADD_INIT))
async def add_init_entry(everything: CommonEverything):
    return await to_name(everything)


@r.on_callback(
    StateFilter(ZOOM.II_BROWSE),
    lambda every: every.event.payload != kb.Payload.ADD_HUB
)
async def browse(
    everything: CommonEverything, 
    text_footer: Optional[str] = None
):
    ctx = everything.ctx
    has_entries = ctx.settings.zoom.entries.has_something
    has_new_entries = ctx.settings.zoom.new_entries.has_something

    is_init_space = Space.INIT in ctx.navigator.spaces
    is_hub_space = Space.HUB in ctx.navigator.spaces

    if everything.is_from_event:
        # try to check if user selected an entry in list
        event = everything.event
        payload = event.payload

        related_to_entry = ctx.settings.zoom.has(payload)

        if related_to_entry:
            # user really selected someone
            ctx.settings.zoom.focused.select(payload)

            return await to_entry(everything)

    if ctx.settings.zoom.is_focused_on_new_entries:
        # user came here from adding mass zoom data
        ctx.pages.list = pagination.from_zoom(
            data = ctx.settings.zoom.new_entries.set,
            text_footer = text_footer,
            keyboard_footer = [
                [kb.CLEAR_BUTTON.only_if(has_new_entries), kb.ADD_ALL_BUTTON], 
                [kb.BACK_BUTTON],
            ],
        )
    elif ctx.settings.zoom.is_focused_on_entries:
        # user came here to view current active entries
        ctx.pages.list = pagination.from_zoom(
            data = ctx.settings.zoom.entries.set,
            text_footer = text_footer,
            keyboard_footer = [
                [
                    kb.ADD_INIT_BUTTON.only_if(is_init_space),
                    kb.ADD_HUB_BUTTON.only_if(is_hub_space),
                    kb.REMOVE_ALL_BUTTON.only_if(has_entries)
                ], 
                [kb.DUMP_BUTTON.only_if(has_entries)],
                [kb.BACK_BUTTON],
            ],
        )

    return await everything.edit_or_answer(
        text     = ctx.pages.current.text,
        keyboard = ctx.pages.current.keyboard,
    )

async def to_browse(
    everything: CommonEverything, 
    text_footer: Optional[str] = None
):
    if everything.navigator.current != ZOOM.II_BROWSE:
        everything.navigator.append(ZOOM.II_BROWSE)

    #if everything.navigator.current != Zoom.II_BROWSE:
    #    everything.navigator.append(Zoom.II_BROWSE)

    return await browse(everything, text_footer)


@r.on_everything(
    UnionFilter((
        StateFilter(ZOOM.I_MASS),
        StateFilter(ZOOM.II_BROWSE)
    )),
    lambda every: every.event.payload != kb.Payload.ADD_HUB if every.event is not None else True,
    lambda every: every.event.payload != kb.Payload.CONTINUE if every.event is not None else True,
)
async def mass(everything: CommonEverything):
    ctx = everything.ctx

    if ZOOM.I_MASS not in ctx.navigator.trace:
        return None

    if everything.is_from_event:
        # user came to this state from button
        event = everything.event

        footer_addition = messages.default_footer_addition(everything)
        has_new_entries = ctx.settings.zoom.new_entries.has_something

        answer_text = (
            messages.Builder()
                    .add(messages.format_send_zoom_data())
                    .add(messages.format_zoom_data_format())
                    .add(messages.format_mass_zoom_data_explain())
                    .add(footer_addition)
        )
        answer_keyboard = kb.Keyboard.default().assign_next(
            kb.CONTINUE_BUTTON.only_if(has_new_entries)
        )

        await event.edit_message(
            text        = answer_text.make(),
            keyboard    = answer_keyboard,
        )

    elif everything.is_from_message:
        # user sent a message with links
        message = everything.message

        text = message.text or ""
        # get text from all forwarded messages
        forwards_text = message.forwards_text

        # of there is some text in forwards
        if forwards_text is not None:
            text += "\n\n"
            text += forwards_text

        # addition about if user
        # should mention or reply
        # so bot notices his message
        footer_addition = messages.default_footer_addition(everything)

        # text that'll be shown
        # at the bottom of browser,
        # may contain the `footer_addition`
        text_footer = (
            messages.Builder()
                    .add(messages.format_you_can_add_more())
                    .add(footer_addition)
        )

        # parse from text
        parsed = zoom.Data.parse(text)

        # if no data found in text
        # and user didn't added anything yet
        if len(parsed) < 1 and ctx.navigator.current != ZOOM.II_BROWSE:
            answer_text = (
                messages.Builder()
                        .add(messages.format_zoom_data_format())
                        .add(messages.format_mass_zoom_data_explain())
                        .add(messages.format_doesnt_contain_zoom())
                        .add(footer_addition)
            )
            answer_keyboard = kb.Keyboard.default()

            return await message.answer(
                text     = answer_text.make(),
                keyboard = answer_keyboard
            )
        # elif no data found in text
        # but user already added something
        elif len(parsed) < 1 and ctx.navigator.current == ZOOM.II_BROWSE:
            text_footer = (
                messages.Builder()
                        .add(messages.format_doesnt_contain_zoom())
                        .add(footer_addition)
            )

        if len(parsed) > 0:
            # add everything parsed
            ctx.settings.zoom.new_entries.add(parsed, overwrite=True)

        return await to_browse(everything, text_footer.make())

async def to_mass(everything: CommonEverything):
    everything.navigator.append(ZOOM.I_MASS)
    return await mass(everything)


STATE_MAP = {
    ZOOM.I_MASS: mass,
    ZOOM.II_BROWSE: browse,
    ZOOM.III_ENTRY: entry,
    ZOOM.IIII_NAME: name,
    ZOOM.IIII_URL: url,
    ZOOM.IIII_ID: id_,
    ZOOM.IIII_PWD: pwd,
    ZOOM.I_MASS_CHECK: mass_check,
}