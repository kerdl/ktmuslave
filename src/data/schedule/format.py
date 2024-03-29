import datetime
import difflib
from typing import Optional, Union, Literal
from dataclasses import dataclass

from src.svc.common import messages
from src.data.schedule.compare import DetailedChanges, PrimitiveChange
from src.data.schedule import Group, Day, Subject, Format, FORMAT_LITERAL, compare
from src.data.range import Range
from src.data import zoom, TranslatedBaseModel, RepredBaseModel, format as fmt
from src import text


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
    Format.REMOTE: "🛌"
}

LITERAL_FORMAT = {
    Format.FULLTIME: "очко",
    Format.REMOTE: "дристант"
}

WINDOW = "🪟 ОКНО ЕБАТЬ (хотя я бы не стал, тыж нехочеш как сын мияги?)"

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

def teachers(
    tchrs: list[str],
    format: FORMAT_LITERAL,
    entries: set[zoom.Data]
) -> list[str]:
    str_entries = [entry.name.value for entry in entries]

    fmt_teachers: list[str] = []

    for teacher in tchrs:
        matches = difflib.get_close_matches(teacher, str_entries, cutoff=0.8)

        if len(matches) < 1:
            fmt_teachers.append(teacher)
            continue
        
        data: list[str] = []

        first_match = matches[0]
        found_entry = None

        for entry in entries:
            if entry.name.value == first_match:
                found_entry = entry
        
        if format == Format.REMOTE:
            if found_entry.url.value is not None:
                data.append(found_entry.url.value)

            if found_entry.id.value is not None:
                translation = found_entry.__translation__.get("id")
                data.append(f"{translation}: {found_entry.id.value}")

            if found_entry.pwd.value is not None:
                translation = found_entry.__translation__.get("pwd").lower()
                data.append(f"{translation}: {found_entry.pwd.value}")

        if found_entry.notes.value is not None:
            data.append(found_entry.notes.value)

        if len(data) > 0:
            fmt_data = ", ".join(data)
            fmt_teachers.append(f"{teacher} ({fmt_data})")
        else:
            fmt_teachers.append(teacher)
    
    return fmt_teachers

def subject(
    subj: Subject,
    entries: set[zoom.Data],
    rng: Optional[Range[Subject]] = None
) -> str:
    if subj.is_unknown_window():
        if rng is not None:
            num_range = Range(
                start=rng.start.num,
                end=rng.end.num
            )
            time_range = Range(
                start=rng.start.time.start,
                end=rng.end.time.end
            )
            return f"{circle_keycap_num_range(num_range)} {time_range}: {subj.name}"
        
        return f"{circle_keycap_num(subj.num)} {subj.name}"
    
    num     = keycap_num(subj.num)
    time    = str(subj.time)
    name    = subj.name
    tchrs   = teachers(subj.teachers, subj.format, entries)
    cabinet = subj.cabinet

    joined_tchrs = ", ".join(tchrs)

    base = f"{num} {time}: {name}"

    if len(tchrs) > 0:
        base += " "
        base += joined_tchrs
    
    if cabinet is not None:
        base += " "
        base += cabinet
    
    return base

def days(
    days: list[Day],
    entries: set[zoom.Data]
) -> list[str]:
    fmt_days: list[str] = []

    for day in days:
        weekday = day.weekday
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
                    rng.start,
                    entries,
                    rng
                )
                fmt_subjs.append((rng, subj_fmt))

        for subj in day.subjects:
            if (
                subj.is_unknown_window() and
                compare.cmp_subjects(
                    hold, ignored_keys=["raw", "num", "time"]
                )
            ):
                hold.append(subj)
                continue
            else:
                get_holden_ranges()
                format_holden_ranges()
                hold = []

            fmt_subj = subject(subj, entries)
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

                fmt_day = f"{emoji} | {weekday} ({literal_format}) {dt}:"
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

async def group(
    group: Optional[Group],
    entries: list[zoom.Data]
) -> str:
    from src.api.schedule import SCHEDULE_API

    last_update          = await SCHEDULE_API.last_update()
    utc3_last_update     = last_update + datetime.timedelta(hours=3)
    fmt_utc3_last_update = utc3_last_update.strftime("%H:%M:%S, %d.%m.%Y")

    update_period        = await SCHEDULE_API.update_period()

    update_params = messages.format_schedule_footer(
        last_update=fmt_utc3_last_update,
        update_period=update_period
    )

    if group is None or not group.days:
        return (
            f"{messages.format_no_schedule()}\n\n"
            f"{update_params}"
        )

    label = group.raw
    days_str = "\n\n".join(days(group.days, entries))

    return (
        f"📜 {label}\n\n"
        f"{days_str}\n\n"
        f"{update_params}"
    )

@dataclass
class CompareFormatted:
    text: Optional[str]
    has_detailed: bool

def cmp(
    compare: Union[TranslatedBaseModel, RepredBaseModel],
    is_detailed: bool = True
) -> CompareFormatted:
    rows: list[str] = []
    has_detailed = False

    is_translated = isinstance(compare, TranslatedBaseModel)

    for field in compare:
        key = field[0]
        value = field[1]

        if isinstance(value, DetailedChanges):
            local_translation = None if not is_translated else compare.translate(key)
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

                if is_detailed:
                    compared = cmp(changed)
                else:
                    compared = CompareFormatted(text="", has_detailed=False)

                indented_compared = text.indent(compared.text, width = 2, add_dropdown = True)
                
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
                f"{compare.translate(key)}: {PRIMITIVE.format(old, new)}"
            )
    
    return CompareFormatted(text="\n".join(rows), has_detailed=has_detailed)
