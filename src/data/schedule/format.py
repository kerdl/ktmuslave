import datetime
import difflib
from typing import (
    Optional,
    Union,
    Literal,
    TYPE_CHECKING
)
from dataclasses import dataclass
from src import text, defs
from src.data.range import Range
from src.svc import telegram
from src.svc.common import messages
from src.data.schedule.compare import (
    Changes,
    DetailedChanges,
    PrimitiveChange,
)
from src.data.schedule import (
    Formation,
    Day,
    Subject,
    Attender,
    AttenderKind,
    Format,
    FORMAT_LITERAL,
    compare
)
from src.data.weekday import (
    Weekday,
    WEEKDAY_LITERAL,
    WEEKDAYS
)
from src.data import (
    zoom,
    week,
    TranslatedBaseModel,
    RepredBaseModel,
    format as fmt,
    Emoji
)


if TYPE_CHECKING:
    from src.data.settings import MODE_LITERAL


KEYCAPS = {
    0: "0️⃣",
    1: "1️⃣",
    2: "2️⃣",
    3: "3️⃣",
    4: "4️⃣",
    5: "5️⃣",
    6: "6️⃣",
    7: "7️⃣",
    8: "8️⃣",
    9: "9️⃣",
}

CIRCLE_KEYCAPS = {
    0: "🄌",
    1: "➊",
    2: "➋",
    3: "➌",
    4: "➍",
    5: "➎",
    6: "➏",
    7: "➐",
    8: "➑",
    9: "➒",
}

BIG_EMPTY_BULLET = "○"
BIG_BLACK_BULLET = "●"

CIRCLE_KEYCAPS_RANGE_DASH = "-"

FORMAT_EMOJIS = {
    Format.FULLTIME: "🏫",
    Format.REMOTE: "🛌",
    Format.UNKNOWN: "⚪"
}

LITERAL_FORMAT = {
    Format.FULLTIME: "очко",
    Format.REMOTE: "дристант"
}

FORMATION_LABEL = "📜"

RECOVERED_EMOJI = "♻️"

TODAY_BELOW = "📅 | Сегодня"
WINDOW = "🪟 ОКНО"

# HAHAHAHA PENIS HAHAHAHHAHAHAHAHAHAHHAHAHAHAHA
APPEAR     = "+ {}"
DISAPPEAR  = "− {}"
CHANGE     = "• {}"
PRIMITIVE = "{} → {}"
# ⠀⠀⠀⠀⠀⢰⡿⠋⠁⠀⠀⠈⠉⠙⠻⣷⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⢀⣿⠇⠀⢀⣴⣶⡾⠿⠿⠿⢿⣿⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⣀⣀⣸⡿⠀⠀⢸⣿⣇⠀⠀⠀⠀⠀⠀⠙⣷⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⣾⡟⠛⣿⡇⠀⠀⢸⣿⣿⣷⣤⣤⣤⣤⣶⣶⣿⠇⠀⠀⠀⠀⠀⠀⠀⣀⠀⠀
# ⢀⣿⠀⢀⣿⡇⠀⠀⠀⠻⢿⣿⣿⣿⣿⣿⠿⣿⡏⠀⠀⠀⠀⢴⣶⣶⣿⣿⣿⣆
# ⢸⣿⠀⢸⣿⡇⠀⠀⠀⠀⠀⠈⠉⠁⠀⠀⠀⣿⡇⣀⣠⣴⣾⣮⣝⠿⠿⠿⣻⡟
# ⢸⣿⠀⠘⣿⡇⠀⠀⠀⠀⠀⠀⠀⣠⣶⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠁⠉⠀
# ⠸⣿⠀⠀⣿⡇⠀⠀⠀⠀⠀⣠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠟⠉⠀⠀⠀⠀
# ⠀⠻⣷⣶⣿⣇⠀⠀⠀⢠⣼⣿⣿⣿⣿⣿⣿⣿⣛⣛⣻⠉⠁⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⢸⣿⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀
# ⠀⠀⠀⠀⢸⣿⣀⣀⣀⣼⡿⢿⣿⣿⣿⣿⣿⡿⣿⣿⡿

ZOOM_NAME_PREFIX = Emoji.COMPLETE


def week_bullets_from_bitmap(bitmap: list[bool]) -> str:
    """
    # Format bullet indicator from a bitmap
    ## Example
    ```
    assert week_bullets_from_bitmap([False, False, False]) == "○○○"
    assert week_bullets_from_bitmap([False, True, False]) == "○●○"
    ```
    """
    output = ""
    for bit in bitmap:
        if bit is False:
            output += "○"
        else:
            output += "●"
    
    return output

def week_bullets_from_formation(form: Formation, pos: Range[datetime.date]) -> str:
    bitmap = map(lambda weeked: weeked.week == pos, form.days_weekly_chunked)
    return week_bullets_from_bitmap(bitmap)


def keycap_num(num: int) -> str:
    num_str = str(num)
    output = ""

    for char in num_str:
        char_int = int(char)
        keycap = KEYCAPS.get(char_int)
        output += keycap
    
    return output

def circle_keycap_num(num: int) -> str:
    num_str = str(num)
    output = ""

    for char in num_str:
        char_int = int(char)
        keycap = CIRCLE_KEYCAPS.get(char_int)
        output += keycap
    
    return output

def circle_keycap_num_range(range: Range[int]) -> str:
    if range.start == range.end:
        return circle_keycap_num(range.start)

    start = circle_keycap_num(range.start)
    end = circle_keycap_num(range.end)
    
    return f"{start}{CIRCLE_KEYCAPS_RANGE_DASH}{end}"


def navigation_bullets(count: int, idx: int) -> str:
    output = ""
    
    for i in range(count):
        if i == idx: output += BIG_BLACK_BULLET
        else: output += BIG_EMPTY_BULLET
    
    return output


def date(dt: datetime.date) -> str:
    str_day = fmt.zero_at_start(dt.day)
    str_month = fmt.zero_at_start(dt.month)
    str_year = str(dt.year)

    return f"{str_day}.{str_month}.{str_year}"


def attender_cabinet(
    att: Attender,
    add_recovered_suffix: bool = True,
    do_tg_markup: bool = False
) -> str:
    if att.recovered and add_recovered_suffix:
        att_name = f"{att.name} {RECOVERED_EMOJI}"
    else:
        att_name = att.name
    
    if do_tg_markup:
        att_name = telegram.escape_html(att_name)
    
    primary = telegram.escape_html(
        att.cabinet.primary
    ) if att.cabinet.primary else None
    opposite = telegram.escape_html(
        att.cabinet.opposite
    ) if att.cabinet.opposite else None
    
    if (
        primary and
        opposite and
        not att.cabinet.do_versions_match_complex()
    ):
        if att.kind == AttenderKind.TEACHER:
            return (
                f"{att_name} (у группы - «{primary}», "
                f"у препода - «{opposite}»)"
            )
        if att.kind == AttenderKind.GROUP:
            return (
                f"{att_name} (у препода - «{primary}», "
                f"у группы - «{opposite}»)"
            )
    elif primary:
        return f"{att_name} {primary}"
    elif opposite:
        return f"{att_name} {opposite}" 
    else:
        return att_name

def attenders(
    atts: list[Attender],
    format: FORMAT_LITERAL,
    entries: set[zoom.Data],
    add_recovered_suffix: bool = True,
    do_tg_markup: bool = False,
) -> list[str]:
    str_entries = [entry.name.value for entry in entries]

    fmt_attenders: list[str] = []

    for att in atts:
        matches = difflib.get_close_matches(att.name, str_entries, cutoff=0.8)

        if len(matches) < 1:
            fmt_attenders.append(attender_cabinet(
                att,
                add_recovered_suffix=add_recovered_suffix
            ))
            continue
        
        first_match = matches[0]
        found_entry = None

        for entry in entries:
            if entry.name.value == first_match:
                found_entry = entry
        
        fmt_data = found_entry.format_inline(
            include_name=False,
            only_notes=format == Format.FULLTIME,
            do_tg_markup=do_tg_markup
        )
        
        fmt_att = attender_cabinet(
            att,
            add_recovered_suffix=add_recovered_suffix,
            do_tg_markup=do_tg_markup
        )
        
        if fmt_data:
            fmt_attenders.append(f"{fmt_att} ({fmt_data})")
        else:
            fmt_attenders.append(fmt_att)
    
    return fmt_attenders


def subject_from_parts(
    num_range: Optional[Range[int]] = None,
    num: Optional[int] = None,
    time_range: Optional[Range[datetime.time]] = None,
    time: Optional[datetime.time] = None,
    name: Optional[str] = None,
    raw: Optional[str] = None
) -> str:
    output = ""
    
    if num_range:
        output += f"{circle_keycap_num_range(num_range)} "
    elif num:
        output += f"{circle_keycap_num(num)} "
    if time_range:
        output += f"{time_range}: "
    elif time:
        output += f"{time}: "
    else:
        output = output.strip()
        output += ": "
        
    output += name if name else raw
        
    return output


def subject(
    subj: Subject,
    entries: set[zoom.Data],
    rng: Optional[Range[Subject]] = None,
    weekday: Optional[WEEKDAY_LITERAL] = None,
    add_recovered_suffix: bool = True,
    do_tg_markup: bool = False
) -> str:
    if subj.is_unknown_window():
        if rng is not None:
            num_range = Range(
                start=rng.start.num,
                end=rng.end.num
            )
            start_time = defs.settings.get_time_for(
                wkd=weekday,
                num=num_range.start
            )
            end_time = defs.settings.get_time_for(
                wkd=weekday,
                num=num_range.end
            )
            time_range = Range(
                start=start_time.start,
                end=end_time.end
            ) if start_time and end_time else None
            
            return subject_from_parts(
                num_range=num_range,
                time_range=time_range,
                name=subj.name,
                raw=subj.raw
            )
        
        time = defs.settings.get_time_for(
            wkd=weekday,
            num=subj.num
        )
        
        return subject_from_parts(
            num=subj.num,
            time=time,
            name=subj.name,
            raw=subj.raw
        )
    
    num = keycap_num(subj.num)
    raw_time = defs.settings.get_time_for(wkd=weekday, num=subj.num)
    time = str(raw_time) if raw_time else ""
    name = subj.name if subj.name else subj.raw
    if do_tg_markup: name = telegram.escape_html(name)
    attenders_ = attenders(
        atts=subj.attenders,
        format=subj.format,
        entries=entries,
        add_recovered_suffix=not subj.recovered,
        do_tg_markup=do_tg_markup
    )

    joined_attenders = ", ".join(attenders_)

    left_base_parts = []
    left_base_parts.append(num)
    if time: left_base_parts.append(time)
    left_base = " ".join(left_base_parts)

    if name:
        base = f"{left_base}: {name}"
    else:
        base = f"{left_base}:"
        
    if subj.recovered and add_recovered_suffix:
        base += " "
        base += RECOVERED_EMOJI

    if len(attenders_) > 0:
        base += " "
        base += joined_attenders
    
    return base


def days(
    day_list: list[Day],
    entries: set[zoom.Data],
    add_recovered_suffix: bool = True,
    do_tg_markup: bool = False
) -> list[str]:
    today = datetime.date.today()
    fmt_days: list[str] = []

    for day in day_list:
        weekday = Weekday.from_index(day.date.weekday())
        dt = date(day.date)

        hold: list[Subject] = []
        holden_ranges: list[Range[Subject]] = []
        fmt_subjs: list[tuple[Union[Subject, Range[Subject]], str]] = []

        def get_holden_ranges():
            nonlocal holden_ranges

            ranges = []
            start = None
            end = None
            prev: Subject = None

            for holden in hold:
                if prev is None:
                    prev = holden
                    start = holden
                    continue
                
                if prev.num == holden.num - 1:
                    prev = holden
                    continue

                end = prev
                ranges.append(Range(start=start, end=end))

                start = holden
                end = None

                prev = holden
            
            if end is None and len(hold) > 0:
                end = hold[-1]

            if start is not None and end is not None:
                ranges.append(Range(start=start, end=end))

            holden_ranges = ranges

        def format_holden_ranges():
            for rng in holden_ranges:
                subj_fmt = subject(
                    subj=rng.start,
                    entries=entries,
                    rng=rng,
                    weekday=weekday,
                    add_recovered_suffix=add_recovered_suffix and not day.recovered,
                    do_tg_markup=do_tg_markup,
                )
                fmt_subjs.append((rng, subj_fmt))

        for subj in day.subjects:
            if (
                subj.is_unknown_window() and
                compare.cmp_subjects(
                    hold + [subj], ignored_keys=["num"]
                )
            ):
                hold.append(subj)
                continue
            else:
                get_holden_ranges()
                format_holden_ranges()
                hold = []

            fmt_subj = subject(
                subj=subj,
                entries=entries,
                weekday=weekday,
                add_recovered_suffix=add_recovered_suffix and not day.recovered,
                do_tg_markup=do_tg_markup
            )
            fmt_subjs.append((
                subj,
                fmt_subj
            ))
        
        if len(hold) > 0:
            get_holden_ranges()
            format_holden_ranges()
            hold = []
        
        rows: list[str] = []

        last_format = None
        last_num = None

        for (subj, output) in fmt_subjs:
            subj_end = None

            if isinstance(subj, Range):
                subj_end = subj.end
                subj = subj.start                

            emoji = FORMAT_EMOJIS.get(subj.format)
            literal_format = LITERAL_FORMAT.get(subj.format)

            is_duplicate_num = last_num == subj.num if last_num else None
            normally_predicted_num = last_num + 1 if last_num else None

            if last_num is not None and (
                not is_duplicate_num and (normally_predicted_num != subj.num)
            ):
                fmt_window = text.indent(WINDOW, add_dropdown = True)
                rows.append(fmt_window)

            if last_format != subj.format:
                last_format = subj.format

                if len(rows) > 0:
                    rows[-1] += "\n"

                fmt_day = ""
                
                if day.date == today:
                    fmt_day += TODAY_BELOW + "\n"
                if emoji:
                    fmt_day += f"{emoji} | "
                if weekday:
                    fmt_day += f"{weekday} "
                if literal_format:
                    fmt_day += f"({literal_format}) "
                if dt:
                    fmt_day += f"{dt} "
                if day.recovered and add_recovered_suffix:
                    fmt_day += RECOVERED_EMOJI
                
                fmt_day = fmt_day.strip()
                fmt_day += ":"
                    
                output = text.indent(output, add_dropdown = True)

                rows.append(fmt_day)
                rows.append(output)
            else:
                output = text.indent(output, add_dropdown = True)
                rows.append(output)


            if subj_end is None:
                last_num = subj.num
            else:
                last_num = subj_end.num
        
        fmt_days.append("\n".join(rows))
    
    return fmt_days


def formation(
    form: Optional[Formation],
    week_pos: Range[datetime.date],
    entries: list[zoom.Data],
    mode: "MODE_LITERAL",
    do_tg_markup: bool = False,
    is_group_chat: bool = False,
    add_quick_lookup_hint: bool = True
) -> str:
    from src.data.settings import Mode

    last_update = defs.schedule.get_last_update()
    utc3_last_update = (
        last_update + datetime.timedelta(hours=3)
    ) if last_update else None
    fmt_utc3_last_update = (
        utc3_last_update.strftime("%H:%M:%S, %d.%m.%Y")
    ) if utc3_last_update else None

    quick_lookup_hint = None
    
    if add_quick_lookup_hint:
        quick_lookup_hint = messages.format_schedule_quick_lookup_hint()
        if is_group_chat and do_tg_markup:
            quick_lookup_hint = messages.format_schedule_quick_lookup_replying_hint()
        if is_group_chat and not do_tg_markup:
            quick_lookup_hint = messages.format_schedule_quick_lookup_mentioning_hint()

    update_period = defs.schedule.get_update_period()
    update_params = messages.format_schedule_update_info(
        last_update=fmt_utc3_last_update,
        update_period=update_period
    )
    
    week_bullets = week_bullets_from_formation(form=form, pos=week_pos)

    if form is None or not form.days:
        warning_message = messages.format_no_schedule()
        
        if mode == Mode.TEACHER:
            warning_message = messages.format_no_schedule()
        
        return (
            messages.Builder()
                .add(warning_message) 
                .add(quick_lookup_hint)
                .add(update_params)
                .make()
        )

    label = form.name if form.name else form.raw
    if form.recovered:
        label += " "
        label += RECOVERED_EMOJI
    filtered_days = form.get_week(week_pos) or []
    days_str = "\n\n".join(days(
        day_list=filtered_days,
        entries=entries,
        add_recovered_suffix=not form.recovered,
        do_tg_markup=do_tg_markup
    ))

    fmt_entries = None
    if mode == Mode.TEACHER:
        fmt_entries = "\n".join([
            entry.format_inline(
                include_name=True,
                name_prefix=ZOOM_NAME_PREFIX,
                only_notes=False,
                do_tg_markup=do_tg_markup
            ) for entry in entries
        ])

    return (
        messages.Builder()
            .add(f"{FORMATION_LABEL} {label}") 
            .add(days_str)
            .add(quick_lookup_hint)
            .add(update_params)
            .add(week_bullets)
            .make()
    )


@dataclass
class CompareFormatted:
    text: Optional[str]
    has_detailed: bool


def cmp(
    model: Union[TranslatedBaseModel, RepredBaseModel],
    do_detailed: bool = True,
    ignored_fields: list[str] = []
) -> CompareFormatted:
    rows: list[str] = []
    has_detailed = False

    is_translated = isinstance(model, TranslatedBaseModel)

    for field in model:
        key = field[0]
        value = field[1]
        
        if key in ignored_fields:
            continue

        if isinstance(value, (Changes, DetailedChanges)):
            local_translation = None if not is_translated else model.translate(key)
            local_rows: list[str] = []

            for appeared in value.appeared:
                repr_name = appeared

                if isinstance(appeared, RepredBaseModel):
                    repr_name = appeared.repr_name

                local_rows.append(APPEAR.format(repr_name))

            for disappeared in value.disappeared:
                repr_name = disappeared

                if isinstance(disappeared, RepredBaseModel):
                    repr_name = disappeared.repr_name

                local_rows.append(DISAPPEAR.format(repr_name))

            if len(local_rows) > 0 and local_translation is not None:
                local_rows_joined = ", ".join(local_rows)
                rows.append(f"{local_translation}: {local_rows_joined}")
            elif len(local_rows) > 0:
                for row in local_rows:
                    rows.append(row)

            for changed in value.changed:
                has_detailed = True

                if do_detailed:
                    compared = cmp(
                        model=changed,
                        do_detailed=do_detailed,
                        ignored_fields=ignored_fields
                    )
                else:
                    compared = CompareFormatted(text="", has_detailed=False)

                indented_compared = text.indent(compared.text, width=1, add_dropdown=True)
                
                name = changed
                
                if isinstance(changed, RepredBaseModel):
                    name = changed.repr_name

                if compared.text == "":
                    formatted = CHANGE.format(name)
                else:
                    formatted = f"{CHANGE.format(name)}\n{indented_compared}"

                rows.append(formatted)

        elif isinstance(value, PrimitiveChange):
            old = fmt.value_repr(value.old)
            new = fmt.value_repr(value.new)

            rows.append(
                f"{model.translate(key)}: {PRIMITIVE.format(old, new)}"
            )
            
        elif isinstance(value, TranslatedBaseModel):
            compared = cmp(
                model=value,
                do_detailed=do_detailed,
                ignored_fields=ignored_fields
            )
            rows.append(compared.text)
    
    return CompareFormatted(text="\n".join(rows), has_detailed=has_detailed)
