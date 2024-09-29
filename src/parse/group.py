from . import pattern


def validate(raw: str):
    group_nonword: str = pattern.NON_WORD.sub("", raw)
    group_caps = group_nonword.upper()

    return group_caps