from typing import ClassVar


class Translated:
    __translation__: ClassVar[dict[str, str]]

class Emojized:
    __emojis__: ClassVar[dict[str, str]]