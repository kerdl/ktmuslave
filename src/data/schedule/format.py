import datetime
import difflib
from typing import Optional, Any, Union
from pydantic import BaseModel
from dataclasses import dataclass

from src.data.schedule.compare import GroupCompare, Changes, PrimitiveChange
from src.data.schedule import Page, Group, Day, Subject, Format, FORMAT_LITERAL
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

FORMAT_EMOJIS = {
    Format.FULLTIME: "🏫",
    Format.REMOTE: "🛌"
}

LITERAL_FORMAT = {
    Format.FULLTIME: "очко",
    Format.REMOTE: "дристант"
}

WINDOW = "🪟 ОКНО ЕБАТЬ (хотя я бы не стал, тыж нехочеш как сын мияги?)"
UNKNOWN_WINDOW = "🔸 {}"


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

def date(dt: datetime.date) -> str:
    str_day = fmt.zero_at_start(dt.day)
    str_month = fmt.zero_at_start(dt.month)
    str_year = str(dt.year)

    return f"{str_day}.{str_month}.{str_year}"

def teachers(
    tchrs: list[str],
    entries: Optional[set[zoom.Data]]
) -> list[str]:
    if entries is not None:
        str_entries = [entry.name.value for entry in entries]
    else:
        str_entries = []

    fmt_teachers: list[str] = []

    for teacher in tchrs:
        matches = difflib.get_close_matches(teacher, str_entries)

        if len(matches) < 1:
            fmt_teachers.append(teacher)
            continue
        
        data: list[str] = []

        first_match = matches[0]
        found_entry = None

        for entry in entries:
            if entry.name.value == first_match:
                found_entry = entry
        
        if found_entry.url.value is not None:
            data.append(found_entry.url.value)

        if found_entry.id.value is not None:
            translation = found_entry.__translation__.get("id")
            data.append(f"{translation}: {found_entry.id.value}")

        if found_entry.pwd.value is not None:
            translation = found_entry.__translation__.get("pwd").lower()
            data.append(f"{translation}: {found_entry.pwd.value}")

        fmt_data = ", ".join(data)

        fmt_teachers.append(f"{teacher} ({fmt_data})")
    
    return fmt_teachers

def subject(
    subject: Subject,
    entries: Optional[set[zoom.Data]]
) -> str:
    if subject.is_unknown_window():
        return UNKNOWN_WINDOW.format(subject.raw)
    
    num     = keycap_num(subject.num)
    time    = str(subject.time)
    name    = subject.name
    tchrs   = teachers(subject.teachers, entries)
    cabinet = subject.cabinet

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

        fmt_subjs: list[tuple[int, FORMAT_LITERAL, str]] = []

        for subj in day.subjects:
            fmt_subj = subject(subj, entries if subj.format == Format.REMOTE else None)
            fmt_subjs.append((subj.num, subj.format, fmt_subj))
        
        rows: list[str] = []

        last_format = None
        last_num = None

        for (num, format, fmt) in fmt_subjs:
            emoji = FORMAT_EMOJIS.get(format)
            literal_format = LITERAL_FORMAT.get(format)

            is_duplicate_num = last_num == num if last_num else None
            normally_predicted_num = last_num + 1 if last_num else None

            if last_num is not None and (
                not is_duplicate_num and (normally_predicted_num != num)
            ):
                fmt_window = text.indent(WINDOW, add_dropdown = True)
                rows.append(fmt_window)

            if last_format != format:
                last_format = format

                if len(rows) > 0:
                    rows.append("\n")

                fmt_day = f"{emoji} | {weekday} ({literal_format}) {dt}:"
                fmt = text.indent(fmt, add_dropdown = True)

                rows.append(fmt_day)
                rows.append(fmt)

            elif last_format == format:
                fmt = text.indent(fmt, add_dropdown = True)
                rows.append(fmt)
            
            last_num = num
        
        fmt_days.append("\n".join(rows))
    
    return fmt_days

async def group(
    group: Optional[Group],
    entries: set[zoom.Data]
) -> str:
    from src.api.schedule import SCHEDULE_API

    last_update          = await SCHEDULE_API.last_update()
    utc3_last_update     = last_update + datetime.timedelta(hours=3)
    fmt_utc3_last_update = utc3_last_update.strftime("%H:%M:%S, %d.%m.%Y")

    update_period    = await SCHEDULE_API.update_period()

    update_params = (
        f"⏱ Последнее обновление: {fmt_utc3_last_update}\n"
        f"✉ Период автообновления: {update_period} мин"
    )

    if group is None:
        return (
            f"твоей группы нет в этом расписании ёпта\n\n"
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
    text: str
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

        if isinstance(value, Changes):
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
