from typing import Any, Callable, Optional
from loguru import logger

from src import defs, text
from src.parse import pattern, zoom as zoom_parse
from src.data.settings import Mode
from src.svc.common import CommonEverything, messages, pagination, bps, Source
from src.svc.common.states import formatter as states_fmt
from src.svc.common.states.tree import ZOOM, Space
from src.svc.common.router import router
from src.svc.common.filters import PayloadFilter, StateFilter, UnionFilter
from src.svc.common import keyboard as kb, template
from src.data import zoom, DataField, error


@router.on_callback(
    StateFilter(ZOOM.IIII_CONFIRM_REMOVE_ALL),
    PayloadFilter(kb.Payload.DUMP_AND_REMOVE_ALL)
)
async def dump_when_removing_all(everything: CommonEverything):
    ctx = everything.ctx
    if ctx.settings.mode == Mode.GROUP:
        storage = ctx.settings.zoom
    elif ctx.settings.mode == Mode.TEACHER:
        storage = ctx.settings.tchr_zoom

    await everything.send_message(
        text=storage.entries.dump(),
        chunker=text.double_newline_chunks
    )

    storage.focused.clear()

    everything.force_send = True

    everything.navigator.jump_back_to_or_append(ZOOM.II_BROWSE)
    return await browse(everything)


@router.on_callback(StateFilter(ZOOM.III_DUMP), PayloadFilter(kb.Payload.DUMP))
async def dump(everything: CommonEverything):
    ctx = everything.ctx
    if ctx.settings.mode == Mode.GROUP:
        storage = ctx.settings.zoom
    elif ctx.settings.mode == Mode.TEACHER:
        storage = ctx.settings.tchr_zoom

    await everything.send_message(
        text=storage.entries.dump(),
        chunker=text.double_newline_chunks
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
        text=answer_text.make(),
        keyboard=answer_keyboard
    )

@router.on_callback(
    UnionFilter((
        StateFilter(ZOOM.II_BROWSE),
    )),
    PayloadFilter(kb.Payload.DUMP)
)
async def to_going_to_dump(everything: CommonEverything):
    everything.navigator.append(ZOOM.III_DUMP)
    return await going_to_dump(everything)


@router.on_callback(PayloadFilter(kb.Payload.REMOVE))
async def remove_entry(everything: CommonEverything):
    ctx = everything.ctx
    if ctx.settings.mode == Mode.GROUP:
        storage = ctx.settings.zoom
    elif ctx.settings.mode == Mode.TEACHER:
        storage = ctx.settings.tchr_zoom
    
    focused = storage.focused
    selected = focused.selected

    if selected is None:
        # usually it should not happen,
        # only in case of rate limit
        return await to_browse(everything)

    focused.remove(selected.name.value)
    everything.navigator.back(trace_it=False)

    if ZOOM.I_MASS in everything.navigator.trace and not focused.has_something:
        return await to_mass(everything)
    else:
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
                text=answer_text.make(),
                keyboard=answer_keyboard
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
                text=answer_text.make(),
                keyboard=answer_keyboard
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
                text=answer_text.make(),
                keyboard=answer_keyboard
            )

        ctx.navigator.jump_back_to(
            ZOOM.II_BROWSE, 
            execute_actions=False
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
            text=answer_text.make(),
            keyboard=answer_keyboard
        )


@router.on_callback(StateFilter(ZOOM.IIII_CONFIRM_CLEAR_ALL), PayloadFilter(kb.Payload.CLEAR))
async def clear_new_entries(everything: CommonEverything):
    ctx = everything.ctx
    if ctx.settings.mode == Mode.GROUP:
        storage = ctx.settings.zoom
    elif ctx.settings.mode == Mode.TEACHER:
        storage = ctx.settings.tchr_zoom

    storage.new_entries.clear()

    ctx.navigator.jump_back_to(ZOOM.I_MASS)
    return await mass(everything)

async def confirm_clear_new_entries(everything: CommonEverything):
    answer_text = (
        messages.Builder()
            .add(messages.format_remove_confirmation(removal_type="очистить"))
    )
    answer_keyboard = kb.Keyboard([
        [kb.CLEAR_BUTTON]
    ])

    return await everything.edit_or_answer(
        text=answer_text.make(),
        keyboard=answer_keyboard,
    )

@router.on_callback(StateFilter(ZOOM.II_BROWSE), PayloadFilter(kb.Payload.CLEAR))
async def to_confirm_clear_new_entries(everything: CommonEverything):
    everything.ctx.navigator.append(ZOOM.IIII_CONFIRM_CLEAR_ALL)
    return await confirm_clear_new_entries(everything)


@router.on_callback(StateFilter(ZOOM.IIII_CONFIRM_REMOVE_ALL), PayloadFilter(kb.Payload.REMOVE_ALL))
async def remove_entries(everything: CommonEverything):
    ctx = everything.ctx
    if ctx.settings.mode == Mode.GROUP:
        storage = ctx.settings.zoom
    elif ctx.settings.mode == Mode.TEACHER:
        storage = ctx.settings.tchr_zoom

    storage.entries.clear()

    ctx.navigator.jump_back_to(ZOOM.II_BROWSE)
    return await browse(everything)

async def confirm_remove_entries(everything: CommonEverything):
    ctx = everything.ctx
    is_init_space = Space.INIT in ctx.navigator.spaces
    is_hub_space = Space.HUB in ctx.navigator.spaces
    
    answer_text = (
        messages.Builder()
            .add(messages.format_remove_confirmation(removal_type="удалить"))
            .add_if(messages.format_you_can_dump_entries_before_removal(), not is_init_space)
    )
    answer_keyboard = kb.Keyboard([
        [kb.DUMP_AND_REMOVE_ALL_BUTTON.only_if(not is_init_space)],
        [kb.REMOVE_ALL_BUTTON]
    ])

    return await everything.edit_or_answer(
        text=answer_text.make(),
        keyboard=answer_keyboard,
    )

@router.on_callback(StateFilter(ZOOM.II_BROWSE), PayloadFilter(kb.Payload.REMOVE_ALL))
async def to_confirm_remove_entries(everything: CommonEverything):
    everything.ctx.navigator.append(ZOOM.IIII_CONFIRM_REMOVE_ALL)
    return await confirm_remove_entries(everything)


@router.on_callback(
    StateFilter(ZOOM.I_MASS_CHECK), 
    PayloadFilter(kb.Payload.CONFIRM)
)
async def confirm_mass_add(everything: CommonEverything):
    ctx = everything.ctx
    if ctx.settings.mode == Mode.GROUP:
        storage = ctx.settings.zoom
    elif ctx.settings.mode == Mode.TEACHER:
        storage = ctx.settings.tchr_zoom

    is_init_space = Space.INIT in ctx.navigator.spaces
    is_hub_space = Space.HUB in ctx.navigator.spaces

    # move everything from `new_entries` to `entries`
    storage.confirm_new_entries()

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
    if ctx.settings.mode == Mode.GROUP:
        storage = ctx.settings.zoom
    elif ctx.settings.mode == Mode.TEACHER:
        storage = ctx.settings.tchr_zoom

    adding = storage.adding
    overwriting = storage.overwriting

    answer_text = (
        messages.Builder()
            .add(messages.format_zoom_mass_adding_overview(adding, overwriting, storage.mode))
    )
    answer_keyboard = kb.Keyboard([
        [kb.CONFIRM_BUTTON]
    ])

    return await everything.edit_or_answer(
        text=answer_text.make(),
        keyboard=answer_keyboard,
    )

@router.on_callback(StateFilter(ZOOM.II_BROWSE), PayloadFilter(kb.Payload.ADD_ALL))
async def to_mass_check(everything: CommonEverything):
    everything.navigator.append(ZOOM.I_MASS_CHECK)
    return await mass_check(everything)

@router.on_everything(StateFilter(ZOOM.IIII_NOTES))
async def notes(everything: CommonEverything):
    if everything.ctx.settings.mode == Mode.GROUP:
        storage = everything.ctx.settings.zoom
    elif everything.ctx.settings.mode == Mode.TEACHER:
        storage = everything.ctx.settings.tchr_zoom

    def getter():
        return storage.focused.selected.notes.value

    def setter(value: Any):
        storage.focused.selected.notes = DataField(value=value)
        storage.focused.selected.check(storage.mode)

    def nuller():
        storage.focused.selected.notes = DataField(value=None)

    main_message = None
    if everything.ctx.settings.mode == Mode.GROUP:
        main_message = messages.format_enter_notes()
    elif everything.ctx.settings.mode == Mode.TEACHER:
        main_message = messages.format_thcr_enter_notes()

    return await set_attribute(
        everything=everything,
        main_message=main_message,
        getter=getter,
        setter=setter,
        nuller=nuller,
    )

@router.on_callback(StateFilter(ZOOM.III_ENTRY), PayloadFilter(kb.Payload.NOTES))
async def to_notes(everything: CommonEverything):
    everything.navigator.append(ZOOM.IIII_NOTES)
    return await notes(everything)

@router.on_everything(StateFilter(ZOOM.IIII_HOST_KEY))
async def host_key(everything: CommonEverything):
    if everything.ctx.settings.mode == Mode.GROUP:
        storage = everything.ctx.settings.zoom
    elif everything.ctx.settings.mode == Mode.TEACHER:
        storage = everything.ctx.settings.tchr_zoom
    
    def getter():
        return storage.focused.selected.host_key.value

    def setter(value: Any):
        storage.focused.selected.host_key = DataField(value=value)
        storage.focused.selected.check(storage.mode)

    def nuller():
        storage.focused.selected.host_key = DataField(value=None)

    return await set_attribute(
        everything=everything,
        main_message=messages.format_enter_host_key(
            do_markup=everything.is_from_tg_generally
        ),
        getter=getter,
        setter=setter,
        nuller=nuller,
    )

@router.on_callback(StateFilter(ZOOM.III_ENTRY), PayloadFilter(kb.Payload.HOST_KEY))
async def to_host_key(everything: CommonEverything):
    everything.navigator.append(ZOOM.IIII_HOST_KEY)
    return await host_key(everything)

@router.on_everything(StateFilter(ZOOM.IIII_PWD))
async def pwd(everything: CommonEverything):
    if everything.ctx.settings.mode == Mode.GROUP:
        storage = everything.ctx.settings.zoom
    elif everything.ctx.settings.mode == Mode.TEACHER:
        storage = everything.ctx.settings.tchr_zoom
    
    def getter():
        return storage.focused.selected.pwd.value

    def setter(value: Any):
        storage.focused.selected.pwd = DataField(value=value)
        storage.focused.selected.check(storage.mode)

    def nuller():
        storage.focused.selected.pwd = DataField(value=None)

    return await set_attribute(
        everything=everything,
        main_message=messages.format_enter_pwd(
            do_markup=everything.is_from_tg_generally
        ),
        getter=getter,
        setter=setter,
        nuller=nuller,
    )

@router.on_callback(StateFilter(ZOOM.III_ENTRY), PayloadFilter(kb.Payload.PWD))
async def to_pwd(everything: CommonEverything):
    everything.navigator.append(ZOOM.IIII_PWD)
    return await pwd(everything)


@router.on_everything(StateFilter(ZOOM.IIII_ID))
async def id_(everything: CommonEverything):
    if everything.ctx.settings.mode == Mode.GROUP:
        storage = everything.ctx.settings.zoom
    elif everything.ctx.settings.mode == Mode.TEACHER:
        storage = everything.ctx.settings.tchr_zoom
    
    def getter():
        return storage.focused.selected.id.value

    def setter(value: Any):
        storage.focused.selected.id = DataField(value=value)
        storage.focused.selected.check(storage.mode)

    def nuller():
        storage.focused.selected.id = DataField(value=None)

    return await set_attribute(
        everything=everything,
        main_message=messages.format_enter_id(
            do_markup=everything.is_from_tg_generally
        ),
        getter=getter,
        setter=setter,
        nuller=nuller,
    )

@router.on_callback(StateFilter(ZOOM.III_ENTRY), PayloadFilter(kb.Payload.ID))
async def to_id(everything: CommonEverything):
    everything.navigator.append(ZOOM.IIII_ID)
    return await id_(everything)


@router.on_everything(StateFilter(ZOOM.IIII_URL))
async def url(everything: CommonEverything):
    if everything.ctx.settings.mode == Mode.GROUP:
        storage = everything.ctx.settings.zoom
    elif everything.ctx.settings.mode == Mode.TEACHER:
        storage = everything.ctx.settings.tchr_zoom
    
    def getter():
        return storage.focused.selected.url.value

    def setter(value: Any):
        storage.focused.selected.url = DataField(value=value)
        storage.focused.selected.check(storage.mode)

    def nuller():
        storage.focused.selected.url = DataField(value=None)

    return await set_attribute(
        everything=everything,
        main_message=messages.format_enter_url(
            do_markup=everything.is_from_tg_generally
        ),
        getter=getter,
        setter=setter,
        nuller=nuller,
    )

@router.on_callback(StateFilter(ZOOM.III_ENTRY), PayloadFilter(kb.Payload.URL))
async def to_url(everything: CommonEverything):
    everything.navigator.append(ZOOM.IIII_URL)
    return await url(everything)


@router.on_message(StateFilter(ZOOM.IIII_NAME))
async def name(everything: CommonEverything):
    if everything.ctx.settings.mode == Mode.GROUP:
        storage = everything.ctx.settings.zoom
        main_message = messages.format_enter_name(
            do_markup=everything.is_from_tg_generally
        )
    elif everything.ctx.settings.mode == Mode.TEACHER:
        storage = everything.ctx.settings.tchr_zoom
        main_message = messages.format_tchr_enter_name(
            do_markup=everything.is_from_tg_generally
        )

    def getter():
        focused = storage.focused
        if focused.selected is None:
            return None

        return storage.focused.selected.name.value

    def setter(value: Any):
        focused = storage.focused

        if focused.selected is None:
            # user tries to add a new entry
            focused.add_from_name(value)
            focused.select(value)

            storage.finish()

            return None

        old = focused.selected.name.value
        focused.change_name(old, value)
        # select this backup
        focused.select(value)

        storage.focused.selected.check(storage.mode)

    return await set_attribute(
        everything=everything,
        main_message=main_message,
        getter=getter,
        setter=setter,
        limit=zoom.NAME_LIMIT
    )

@router.on_callback(StateFilter(ZOOM.III_ENTRY), PayloadFilter(kb.Payload.NAME))
async def to_name(everything: CommonEverything):
    everything.navigator.append(ZOOM.IIII_NAME)
    return await name(everything)

@router.on_everything(StateFilter(ZOOM.III_ENTRY))
async def entry(everything: CommonEverything):
    ignored_keys = []
    field_filter = lambda field: field[0] not in ["name"]
    if everything.ctx.settings.mode == Mode.GROUP:
        storage = everything.ctx.settings.zoom
        ignored_keys = ["host_key"]
        field_filter = lambda field: field[0] not in ["name", "host_key"]
    elif everything.ctx.settings.mode == Mode.TEACHER:
        storage = everything.ctx.settings.tchr_zoom

    selected = storage.focused.selected

    answer_text = (
        messages.Builder()
            .add(selected.format(
                mode=everything.ctx.settings.mode,
                field_filter=field_filter,
                do_tg_markup=everything.is_from_tg_generally
            ))
            .add(messages.format_press_buttons_to_change())
    )
    answer_keyboard = kb.Keyboard.from_dataclass(
        dataclass=selected,
        ignored_keys=ignored_keys,
        footer=[[kb.REMOVE_BUTTON]]
    )

    await everything.edit_or_answer(
        text=answer_text.make(),
        keyboard=answer_keyboard
    )

async def to_entry(everything: CommonEverything):
    everything.navigator.jump_back_to_or_append(ZOOM.III_ENTRY)
    return await entry(everything)

@router.on_callback(StateFilter(ZOOM.II_BROWSE), PayloadFilter(kb.Payload.ADD_INIT))
async def add_init_entry(everything: CommonEverything):
    return await to_name(everything)



@router.on_everything(
    StateFilter(ZOOM.II_BROWSE),
    lambda every: every.event.payload != kb.Payload.ADD_HUB if every.is_from_event else True
)
async def browse(
    everything: CommonEverything, 
    text_footer: Optional[str] = None,
    is_first_call: bool = True,
    is_jump_call: bool = False,
):
    ctx = everything.ctx
    if ctx.settings.mode == Mode.GROUP:
        storage = ctx.settings.zoom
    elif ctx.settings.mode == Mode.TEACHER:
        storage = ctx.settings.tchr_zoom

    has_entries = storage.entries.has_something
    has_new_entries = storage.new_entries.has_something

    is_init_space = Space.INIT in ctx.navigator.spaces
    is_hub_space = Space.HUB in ctx.navigator.spaces
    
    quick_lookup_hint = (
        messages.format_entry_quick_lookup()
    ) if len(storage.entries.list) > 0 else None

    if everything.is_from_event:
        # try to check if user selected an entry in list
        event = everything.event
        payload = event.payload

        related_to_entry = storage.has(payload)

        if related_to_entry:
            # user really selected someone
            storage.focused.select(payload)
            return await to_entry(everything)

    # if used used jump by number or entry name
    if (
        everything.is_from_message and
        not zoom_parse.Key.is_relevant_in_text(everything.message.text) and
        not is_jump_call
    ):
        number = pattern.NUMBER.match(everything.message.text)
        if number:
            try: number = int(number.group())
            except ValueError: number = None
        
        requested_entry = None
        if number is None:
            requested_entry = storage.focused.get_approx(
                everything.message.text,
                as_teacher=ctx.is_group_mode
            )
        else:
            if number > 0:
                everything.ctx.pages.current_num = number - 1
            else:
                everything.ctx.pages.current_num = number
            return await browse(everything, is_jump_call=True)
        
        if requested_entry:
            storage.focused.selected_name = requested_entry.name.value

            # jump to the page where the entry is located
            for page in everything.ctx.pages.list:
                if page.metadata is None:
                    continue

                page_num_names_map: dict[int, list[str]] = page.metadata.get(
                    template.MetadataKeys.PAGE_NUM_NAMES_MAP
                )

                if page_num_names_map is None:
                    continue

                for (page_num, page_map) in page_num_names_map.items():
                    if requested_entry.name.value in page_map:
                        everything.ctx.pages.current_num = page_num

            return await to_entry(everything)

    if storage.is_focused_on_new_entries and not is_jump_call:
        # user came here from adding mass zoom data
        if everything.is_from_message and is_first_call:
            return await mass(everything)
        
        ctx.pages.list = pagination.from_zoom(
            data=storage.new_entries.list,
            mode=ctx.settings.mode,
            text_footer=text_footer if text_footer else quick_lookup_hint,
            keyboard_footer=[
                [kb.CLEAR_BUTTON.only_if(has_new_entries), kb.ADD_ALL_BUTTON], 
                [kb.BACK_BUTTON],
            ],
            do_tg_markup=everything.is_from_tg_generally
        )
    elif storage.is_focused_on_entries and not is_jump_call:
        # user came here to view current active entries
        ctx.pages.list = pagination.from_zoom(
            data=storage.entries.list,
            mode=ctx.settings.mode,
            text_footer=text_footer if text_footer else quick_lookup_hint,
            keyboard_footer=[
                [
                    kb.ADD_INIT_BUTTON.only_if(is_init_space),
                    kb.ADD_HUB_BUTTON.only_if(is_hub_space),
                    kb.REMOVE_ALL_BUTTON.only_if(has_entries)
                ], 
                [kb.DUMP_BUTTON.only_if(has_entries and not is_init_space)],
                [kb.BACK_BUTTON],
            ],
            do_tg_markup=everything.is_from_tg_generally
        )

    return await everything.edit_or_answer(
        text=ctx.pages.current.text,
        keyboard=ctx.pages.current.keyboard,
    )

async def to_browse(
    everything: CommonEverything, 
    text_footer: Optional[str] = None,
    first_call: bool = True
):
    if everything.navigator.current != ZOOM.II_BROWSE:
        everything.navigator.append(ZOOM.II_BROWSE)

    return await browse(everything, text_footer, first_call)

@router.on_everything(
    UnionFilter((
        StateFilter(ZOOM.I_MASS),
        StateFilter(ZOOM.II_BROWSE)
    )),
    lambda every: every.event.payload != kb.Payload.ADD_HUB if every.event is not None else True,
    lambda every: every.event.payload != kb.Payload.CONTINUE if every.event is not None else True,
)
async def mass(everything: CommonEverything):
    ctx = everything.ctx
    if ctx.settings.mode == Mode.GROUP:
        storage = ctx.settings.zoom
    elif ctx.settings.mode == Mode.TEACHER:
        storage = ctx.settings.tchr_zoom

    if ZOOM.I_MASS not in ctx.navigator.trace:
        return None

    if everything.is_from_event:
        # user came to this state from button
        event = everything.event

        footer_addition = messages.default_footer_addition(everything)
        has_new_entries = storage.new_entries.has_something

        if ctx.settings.mode == Mode.GROUP:
            answer_text = (
                messages.Builder()
                    .add(messages.format_send_zoom_data())
                    .add(messages.format_zoom_data_format(
                        do_escape=everything.is_from_tg_generally
                    ))
                    .add(messages.format_zoom_example(
                        do_markup=everything.is_from_tg_generally
                    ))
                    .add(messages.format_mass_zoom_data_explain())
                    .add(footer_addition)
            )
        elif ctx.settings.mode == Mode.TEACHER:
            answer_text = (
                messages.Builder()
                    .add(messages.format_send_zoom_data())
                    .add(messages.format_tchr_zoom_data_format(
                        do_escape=everything.is_from_tg_generally
                    ))
                    .add(messages.format_tchr_zoom_example(
                        do_markup=everything.is_from_tg_generally
                    ))
                    .add(messages.format_mass_zoom_data_explain())
                    .add(footer_addition)
            )
        
        answer_keyboard = kb.Keyboard().assign_next(
            kb.CONTINUE_BUTTON.only_if(has_new_entries)
        )

        await event.edit_message(
            text=answer_text.make(),
            keyboard=answer_keyboard,
        )

    elif everything.is_from_message:
        # user sent a message with links
        message = everything.message

        text = message.text or ""
        # get text from all forwarded messages
        forwards_text = message.forwards_text

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
                .rm_prev_chars(1)
                .add(messages.format_entry_quick_lookup())
                .add(footer_addition)
        )

        # parse from text
        if ctx.settings.mode == Mode.GROUP:
            parsed = zoom.Data.parse(text)
        elif ctx.settings.mode == Mode.TEACHER:
            parsed = zoom.Data.tchr_parse(text)

        # if no data found in text
        # and user didn't added anything yet
        if len(parsed) < 1 and ctx.navigator.current != ZOOM.II_BROWSE:
            answer_text = (
                messages.Builder()
                    .add(messages.format_doesnt_contain_zoom())
                    .add(footer_addition)
            )
            answer_keyboard = kb.Keyboard()

            return await message.answer(
                text=answer_text.make(),
                keyboard=answer_keyboard
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
            storage.new_entries.add(parsed, overwrite=True)

        return await to_browse(everything, text_footer.make(), first_call=False)

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