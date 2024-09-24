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

WINDOW = "🪟 ОКНО ЕБАТЬ"

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

def date(dt: datetime.date) -> str:
    str_day = fmt.zero_at_start(dt.day)
    str_month = fmt.zero_at_start(dt.month)
    str_year = str(dt.year)

    return f"{str_day}.{str_month}.{str_year}"

def attender_cabinet(att: Attender) -> str:
    if (
        att.cabinet.primary and
        att.cabinet.opposite and
        not att.cabinet.do_versions_match_complex()
    ):
        if att.kind == AttenderKind.TEACHER:
            return (
                f"{att.name} (у группы - \"{att.cabinet.primary}\", "
                f"у препода - \"{att.cabinet.opposite}\")"
            )
        if att.kind == AttenderKind.GROUP:
            return (
                f"{att.name} (у препода - \"{att.cabinet.primary}\", "
                f"у группы - \"{att.cabinet.opposite}\")"
            )
    elif att.cabinet.primary:
        return f"{att.name} {att.cabinet.primary}"
    elif att.cabinet.opposite:
        return f"{att.name} {att.cabinet.opposite}" 
    else:
        return att.name

def attenders(
    atts: list[Attender],
    format: FORMAT_LITERAL,
    entries: set[zoom.Data],
    do_tg_markup: bool = False
) -> list[str]:
    str_entries = [entry.name.value for entry in entries]

    fmt_attenders: list[str] = []

    for att in atts:
        matches = difflib.get_close_matches(att.name, str_entries, cutoff=0.8)

        if len(matches) < 1:
            fmt_attenders.append(attender_cabinet(att))
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
        
        if fmt_data:
            fmt_attenders.append(f"{attender_cabinet(att)} ({fmt_data})")
        else:
            fmt_attenders.append(attender_cabinet(att))
    
    return fmt_attenders

def subject(
    subj: Subject,
    entries: set[zoom.Data],
    rng: Optional[Range[Subject]] = None,
    do_tg_markup: bool = False,
    weekday: Optional[WEEKDAY_LITERAL] = None
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
            
            fmt = ""
            fmt += f"{circle_keycap_num_range(num_range)} "
            if time_range:
                fmt += f"{time_range}: "
            else:
                fmt = fmt.strip()
                fmt += ": "
            fmt += subj.name
                
            return fmt
        
        return f"{circle_keycap_num(subj.num)} {subj.name}"
    
    num = keycap_num(subj.num)
    raw_time = defs.settings.get_time_for(wkd=weekday, num=subj.num)
    time = str(raw_time) if raw_time else ""
    name = subj.name
    attenders_ = attenders(
        atts=subj.attenders,
        format=subj.format,
        entries=entries,
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

    if len(attenders_) > 0:
        base += " "
        base += joined_attenders
    
    return base

def days(
    days: list[Day],
    entries: set[zoom.Data],
    do_tg_markup: bool = False
) -> list[str]:
    fmt_days: list[str] = []

    for day in days:
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
                    do_tg_markup=do_tg_markup,
                    weekday=weekday
                )
                fmt_subjs.append((rng, subj_fmt))

        for subj in day.subjects:
            if (
                subj.is_unknown_window() and
                compare.cmp_subjects(
                    hold, ignored_keys=["num"]
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
                do_tg_markup=do_tg_markup,
                weekday=weekday
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

        for (subj, fmt) in fmt_subjs:
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
                
                if emoji:
                    fmt_day += f"{emoji} | "
                if weekday:
                    fmt_day += f"{weekday} "
                if literal_format:
                    fmt_day += f"({literal_format}) "
                if dt:
                    fmt_day += dt
                
                fmt_day = fmt_day.strip()
                fmt_day += ":"
                    
                fmt = text.indent(fmt, add_dropdown = True)

                rows.append(fmt_day)
                rows.append(fmt)
            else:
                fmt = text.indent(fmt, add_dropdown = True)
                rows.append(fmt)


            if subj_end is None:
                last_num = subj.num
            else:
                last_num = subj_end.num
        
        fmt_days.append("\n".join(rows))
    
    return fmt_days

async def formation(
    form: Optional[Formation],
    entries: list[zoom.Data],
    mode: "MODE_LITERAL",
    do_tg_markup: bool = False
) -> str:
    from src.data.settings import Mode

    last_update = await defs.schedule.get_last_update()
    utc3_last_update = (
        last_update + datetime.timedelta(hours=3)
    ) if last_update else None
    fmt_utc3_last_update = (
        utc3_last_update.strftime("%H:%M:%S, %d.%m.%Y")
    ) if utc3_last_update else None

    update_period = await defs.schedule.get_update_period()

    update_params = messages.format_schedule_footer(
        last_update=fmt_utc3_last_update,
        update_period=update_period
    )

    if form is None or not form.days:
        if mode == Mode.GROUP:
            return (
                f"{messages.format_no_schedule()}\n\n"
                f"{update_params}"
            )
        elif mode == Mode.TEACHER:
            return (
                f"{messages.format_tchr_no_schedule()}\n\n"
                f"{update_params}"
            )

    label = form.raw
    days_str = "\n\n".join(days(
        form.days,
        entries,
        do_tg_markup
    ))

    if mode == Mode.GROUP:
        return (
            f"📜 {label}\n\n"
            f"{days_str}\n\n"
            f"{update_params}"
        )
    elif mode == Mode.TEACHER:
        fmt_entries = "\n".join([
            entry.format_inline(
                include_name=True,
                name_prefix=ZOOM_NAME_PREFIX,
                only_notes=False,
                do_tg_markup=do_tg_markup
            ) for entry in entries
        ])

        msg = ""
        msg += f"📜 {label}\n\n"
        msg += f"{days_str}\n\n"
        if fmt_entries:
            msg += f"{fmt_entries}\n\n"
        msg += f"{update_params}"

        return msg

@dataclass
class CompareFormatted:
    text: Optional[str]
    has_detailed: bool

def cmp(
    model: Union[TranslatedBaseModel, RepredBaseModel],
    do_detailed: bool = True
) -> CompareFormatted:
    rows: list[str] = []
    has_detailed = False

    is_translated = isinstance(model, TranslatedBaseModel)

    for field in model:
        key = field[0]
        value = field[1]

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
                    compared = cmp(changed)
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
    
    return CompareFormatted(text="\n".join(rows), has_detailed=has_detailed)
