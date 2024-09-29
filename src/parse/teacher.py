import difflib
from typing import Optional
from . import pattern


def validate(raw: str, reference: list[str]) -> Optional[str]:
    teacher = pattern.TEACHER.search(raw)
    if teacher is not None:
        teacher: str = teacher.group()
        if not teacher.endswith("."):
            teacher += "."
        
        return teacher
    
    teacher_case_ignored = pattern.TEACHER_CASE_IGNORED.search(raw)
    if teacher_case_ignored is not None:
        teacher_case_ignored: str = teacher_case_ignored.group()
        last_name = pattern.TEACHER_LAST_NAME_CASE_IGNORED.search(
            teacher_case_ignored
        )
        rest = teacher_case_ignored[:last_name.pos]
        rest = rest.upper()
        last_name = last_name.group().capitalize()
        return f"{last_name} {rest}"
    
    teacher_no_dots_case_ignored = pattern.TEACHER_NO_DOTS_CASE_IGNORED.search(raw)
    if teacher_no_dots_case_ignored is not None:
        teacher_no_dots_case_ignored: str = teacher_no_dots_case_ignored.group()
        last_name = pattern.TEACHER_LAST_NAME_CASE_IGNORED.search(
            teacher_no_dots_case_ignored
        )
        rest = teacher_no_dots_case_ignored[last_name.end():]
        rest = rest.strip()
        rest = rest.upper()
        last_name = last_name.group().capitalize()
        dotted_rest = ""

        for char in rest:
            dotted_rest += f"{char}." 
        
        return f"{last_name} {dotted_rest}"
    
    teacher_last_name_case_ignored = pattern.TEACHER_LAST_NAME_CASE_IGNORED.search(raw)
    if teacher_last_name_case_ignored is not None:
        teacher_last_name_case_ignored: str = teacher_last_name_case_ignored.group()
        capitalized = teacher_last_name_case_ignored.capitalize()

        last_name_short_map = {}
        for ref in reference:
            short = ref.split(" ")[0] if " " in ref else ref
            last_name_short_map[short] = ref

        matches = difflib.get_close_matches(
            capitalized,
            [short for short in last_name_short_map.keys()],
            cutoff=0.8
        )
        if len(matches) < 1:
            return None

        first_match = matches[0]
        return last_name_short_map[first_match]
    
    return None