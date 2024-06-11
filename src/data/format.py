from typing import Any


PRIMITIVE_VALUE_REPR = {
    True:  "да",
    False: "нет",
    None:  "н/а"
}

def value_repr(value: Any) -> str:
    from src.data.settings import Mode
    from src.data.schedule import TimeMode
    
    if value == Mode.GROUP:
        return "группа"
    
    if value == Mode.TEACHER:
        return "препод"
    
    if value == TimeMode.ORIGINAL:
        return "ориг."
    
    if value == TimeMode.OVERRIDE:
        return "зам."

    if type(value) == int:
        return value
    
    try:
        hash(value)
    except TypeError:
        return value

    return PRIMITIVE_VALUE_REPR.get(value) or value

def zero_at_start(num: int) -> str:
    return f"0{num}" if len(str(num)) < 2 else str(num)
