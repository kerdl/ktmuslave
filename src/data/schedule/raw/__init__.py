from typing import Literal


class Kind:
    GROUPS = "groups"
    TEACHERS  = "teachers"

KIND_LITERAL = Literal[
    "groups",
    "teachers"
]
