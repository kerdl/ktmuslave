from typing import Any, Callable, Optional
from loguru import logger

from src import defs
from src.parse import pattern
from src.svc.common import CommonEverything, messages, pagination, Ctx, bps
from src.svc.common.states import formatter as states_fmt
from src.svc.common.states.tree import Zoom
from src.svc.common.router import r
from src.svc.common.filters import PayloadFilter, StateFilter, UnionFilter
from src.svc.common import keyboard as kb
from src.data import zoom, Field, error


@r.on_callback(PayloadFilter(kb.Payload.REMOVE))
async def remove_entry(everything: CommonEverything):
    focused = everything.ctx.settings.zoom.focused
    selected = focused.selected

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
):
    ctx = everything.ctx

    footer_addition = messages.default_footer_addition(everything)
    answer_keyboard = kb.Keyboard([
        [kb.NULL_BUTTON.only_if(
            ctx.navigator.current != Zoom.IIII_NAME
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

        try:
            setter(message.text)
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
            Zoom.II_BROWSE, 
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

@r.on_callback(StateFilter(Zoom.II_BROWSE), PayloadFilter(kb.Payload.CLEAR))
async def clear_new_entries(everything: CommonEverything):
    ctx = everything.ctx

    ctx.settings.zoom.new_entries.clear()

    ctx.navigator.jump_back_to(Zoom.I_MASS)
    return await mass(everything)

@r.on_callback(StateFilter(Zoom.II_BROWSE), PayloadFilter(kb.Payload.REMOVE_ALL))
async def remove_entries(everything: CommonEverything):
    ctx = everything.ctx

    ctx.settings.zoom.entries.clear()

    return await browse(everything)

@r.on_callback(
    StateFilter(Zoom.I_MASS_CHECK), 
    PayloadFilter(kb.Payload.CONFIRM)
)
async def confirm_mass_add(everything: CommonEverything):
    ctx = everything.ctx

    # move everything from `new_entries` to `entries`
    ctx.settings.zoom.confirm_new_entries()
    # jump back to space that is different from current one
    ctx.navigator.space_jump_back()

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

@r.on_callback(StateFilter(Zoom.II_BROWSE), PayloadFilter(kb.Payload.ADD_ALL))
async def to_mass_check(everything: CommonEverything):
    everything.navigator.append(Zoom.I_MASS_CHECK)
    return await mass_check(everything)


@r.on_everything(StateFilter(Zoom.IIII_PWD))
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

@r.on_callback(StateFilter(Zoom.III_ENTRY), PayloadFilter(kb.Payload.PWD))
async def to_pwd(everything: CommonEverything):
    everything.navigator.append(Zoom.IIII_PWD)
    return await pwd(everything)


@r.on_everything(StateFilter(Zoom.IIII_ID))
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

@r.on_callback(StateFilter(Zoom.III_ENTRY), PayloadFilter(kb.Payload.ID))
async def to_id(everything: CommonEverything):
    everything.navigator.append(Zoom.IIII_ID)
    return await id_(everything)


@r.on_everything(StateFilter(Zoom.IIII_URL))
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

@r.on_callback(StateFilter(Zoom.III_ENTRY), PayloadFilter(kb.Payload.URL))
async def to_url(everything: CommonEverything):
    everything.navigator.append(Zoom.IIII_URL)
    return await url(everything)


@r.on_message(StateFilter(Zoom.IIII_NAME))
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
    )

@r.on_callback(StateFilter(Zoom.III_ENTRY), PayloadFilter(kb.Payload.NAME))
async def to_name(everything: CommonEverything):
    everything.navigator.append(Zoom.IIII_NAME)
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
    everything.navigator.jump_back_to_or_append(Zoom.III_ENTRY)
    return await entry(everything)


@r.on_callback(StateFilter(Zoom.II_BROWSE), PayloadFilter(kb.Payload.ADD))
async def add_entry(everything: CommonEverything):
    return await to_name(everything)


@r.on_callback(StateFilter(Zoom.II_BROWSE))
async def browse(
    everything: CommonEverything, 
    text_footer: Optional[str] = None
):
    ctx = everything.ctx
    has_entries = ctx.settings.zoom.entries.has_something
    has_new_entries = ctx.settings.zoom.new_entries.has_something

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
                [kb.BACK_BUTTON]
            ],
        )
    elif ctx.settings.zoom.is_focused_on_entries:
        # user came here to view current active entries
        ctx.pages.list = pagination.from_zoom(
            data = ctx.settings.zoom.entries.set,
            text_footer = text_footer,
            keyboard_footer = [
                [kb.ADD_BUTTON, kb.REMOVE_ALL_BUTTON.only_if(has_entries)], 
                [kb.BACK_BUTTON]
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
    everything.navigator.jump_back_to_or_append(Zoom.II_BROWSE)

    #if everything.navigator.current != Zoom.II_BROWSE:
    #    everything.navigator.append(Zoom.II_BROWSE)

    return await browse(everything, text_footer)


@r.on_everything(
    UnionFilter((
        StateFilter(Zoom.I_MASS),
        StateFilter(Zoom.II_BROWSE)
    ))
)
async def mass(everything: CommonEverything):
    ctx = everything.ctx

    if Zoom.I_MASS not in ctx.navigator.trace:
        return None

    if everything.is_from_event:
        # user came to this state from button
        event = everything.event

        footer_addition = messages.default_footer_addition(everything)
        has_new_entries = ctx.settings.zoom.new_entries.has_something

        answer_text = (
            messages.Builder()
                    .add(messages.format_zoom_data_format())
                    .add(messages.format_send_zoom_data(everything.src, everything.is_group_chat))
                    .add(footer_addition)
        )
        answer_keyboard = kb.Keyboard.default().assign_next(kb.NEXT_BUTTON.only_if(has_new_entries))

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
        if len(parsed) < 1 and ctx.navigator.current != Zoom.II_BROWSE:
            answer_text = (
                messages.Builder()
                        .add(messages.format_zoom_data_format())
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
        elif len(parsed) < 1 and ctx.navigator.current == Zoom.II_BROWSE:
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
    everything.navigator.append(Zoom.I_MASS)
    return await mass(everything)


STATE_MAP = {
    Zoom.I_MASS: mass,
    Zoom.II_BROWSE: browse,
    Zoom.III_ENTRY: entry,
    Zoom.IIII_NAME: name,
    Zoom.IIII_URL: url,
    Zoom.IIII_ID: id_,
    Zoom.IIII_PWD: pwd,
    Zoom.I_MASS_CHECK: mass_check,
}