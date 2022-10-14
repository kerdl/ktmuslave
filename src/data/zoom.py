from __future__ import annotations

from loguru import logger

if __name__ == "__main__":
    import sys
    sys.path.append(".")

from typing import Literal, Optional, Union
from dataclasses import dataclass

from src.svc import common
from src.data import error


COMPLETE   = "🔹"
INCOMPLETE = "🔸"
URL        = "🌐"
ID         = "📍"
PWD        = "🔑"
NONE       = "❓"


FIELDS_EMOJIS = {
    "url": URL,
    "id": ID,
    "pwd": PWD
}
FIELDS_TRANSLATIONS = {
    "url": "Ссылка",
    "id": "ID",
    "pwd": "Пароль"
}

NAME = (
    "{emoji} | {name}"
)
def format_name(emoji: str, name: str):
    return NAME.format(emoji=emoji, name=name)

FIELD = (
    "{emoji} {name}: {value}"
)
def format_field(emoji: str, name: str, value: str):
    return FIELD.format(emoji=emoji, name=name, value=value)

SECTION = (
    "{name}\n"
    "{fields}"
)
def format_section(name: str, fields: list[str]):
    indented_fields = []
    merged_fields = ""

    for field in fields:
        indented_fields.append(f"   ╰ {field}")
    
    merged_fields = "\n".join(indented_fields)

    return SECTION.format(
        name = name,
        fields = merged_fields
    )

NO = "нет"


@dataclass
class Data:
    name: str
    url: Optional[str]
    id: Optional[str]
    pwd: Optional[str]

    @classmethod
    def parse(cls: type[Data], text: str) -> list[Data]:
        from src.parse import zoom
        return zoom.Parser(text).parse()
    
    def format(self) -> str:
        name = self.name
        fmt_name = ""

        # get all class fields except for `name` field
        #         tuple     tuple     generator of tuples       key
        fields = [field for field in self.__dict__.items() if field[0] != "name"]
        fmt_fields = []

        completeness = COMPLETE

        # if some fields are `None`
        if not all([field[1] for field in fields]):
            completeness = INCOMPLETE
        
        fmt_name = format_name(completeness, name)

        for field in fields:
            field_name = field[0]
            field_value = field[1]

            if field_value is not None:
                emoji = FIELDS_EMOJIS.get(field_name)
            else:
                emoji = NONE
            
            translation = FIELDS_TRANSLATIONS.get(field_name)
            
            line = format_field(emoji, translation, field_value or NO)
            
            fmt_fields.append(line)

        return format_section(fmt_name, fmt_fields)

    def __hash__(self):
        return hash(self.name)
    
    def __eq__(self, other):
        return self.name == other


@dataclass
class Entries:
    set: set[Data]
    """
    # The collection of data itself
    """
    selected: Optional[str] = None
    """
    # Name of entry that is currently selected
    - used for selecting an entry from pagination,
    so we know what is being edited right now
    """

    @classmethod
    def default(cls: type[Entries]):
        return cls(set = set())

    def select(self, name: str) -> Data:
        """ ## Mark this name as selected, return its data """

        # if this name not
        # in this container
        if not self.has(name):
            raise error.ZoomNameNotInDatabase(
                "you're trying to select a name "
                "that is not in database"
            )
        
        self.selected = name

        return self.get(name)
    
    def add(
        self, 
        data: Union[Data, set[Data], list[Data]], 
        overwrite: bool = False
    ):
        if isinstance(data, (set, list)):
            for data_obj in data:
                if data_obj in self.set and overwrite:
                    self.set.remove(data_obj)

                self.set.add(data_obj)
        
        elif isinstance(data, Data):
            if data in self.set and overwrite:
                self.set.remove(data)

            self.set.add(data)

    def get(self, name: str) -> Optional[Data]:
        for entry in self.set:
            if entry.name == name:
                return entry

        return None

    def has(self, name: str) -> bool:
        """ ## If `name` in this container """
        return name in self.set

    @property
    def has_something(self) -> bool:
        """ ## If this container has something """
        return len(self.set) > 0

    def remove(self, name: Union[str, set[str]]):
        def remove_with_dummy(name: str):
            """
            ## Make a dummy `Data`, remove with it
            """

            # since Data is compared
            # by the `name` field inside it,
            # we can make a dummy
            # and delete the REAL entry
            # from this FAKE one
            dummy = Data(
                name = n,
                url  = "",
                id   = "",
                pwd  = ""
            )

            self.set.remove(dummy)

        if isinstance(name, set):
            for n in name:
                remove_with_dummy(n)
            
            return None

        if isinstance(name, str):
            remove_with_dummy(name)

            return None
    
    def __len__(self):
        return len(self.set)


class Storage:
    """
    ## Tells which container to use

    - when user sends a callback
    with some entry name, we're not sure
    from which container this name is

    - so on each state, we change
    our focus

    - this focus should always
    be set to `None` when we exit
    `"Zoom adding"` zone

    ## In example

    - if user is currently
    adding mass data from big message,
    we focus on temp `new_entries` storage

    - else if user wants to see all
    active entries, we focus on `entries`
    storage
    """
    ENTRIES     = "entries"
    NEW_ENTRIES = "new_entries"

STORAGE = Literal["entries", "new_entries"]


@dataclass
class Container:
    entries: Entries
    """
    ## Main database of zoom

    - takes links for schedule here
    """
    new_entries: Entries
    """
    ## Temp storage for unconfirmed new entries

    - when user sends a massive message
    with data, we store its entries here,
    and overwrite/add them only when
    user confirms
    """

    is_finished: bool
    """
    ## Initial step of adding Zoom was completed

    - used to determine when to display
    `"0"` at the right of `"Add zoom"`
    state
    """
    focused_at: Optional[STORAGE]
    """ ## Tells which container to use """

    @classmethod
    def default(cls: type[Container]) -> Container:
        return cls(
            entries     = Entries.default(), 
            new_entries = Entries.default(),
            is_finished = False,
            focused_at  = None
        )
    
    @property
    def is_focused_on_entries(self) -> bool:
        return self.focused_at == Storage.ENTRIES
    
    @property
    def is_focused_on_new_entries(self) -> bool:
        return self.focused_at == Storage.NEW_ENTRIES

    @property
    def focused(self) -> Entries:
        if self.is_focused_on_entries:
            return self.entries
        if self.is_focused_on_new_entries:
            return self.new_entries

    def has(self, name: str) -> bool:
        """ ## If `name` is in some container """

        # list of all results
        # that `has()` returned
        # for each container
        contain_results: list[bool] = []

        containers = [
            self.entries,
            self.new_entries
        ]

        for container in containers:
            # check if this container
            # has this `name`
            result = container.has(name)
            # append this result to
            # all results
            contain_results.append(result)
        
        # return if ANY container
        # had this name
        return any(contain_results)

    def finish(self) -> None:
        """ ## Initial step of adding Zoom was completed """
        self.is_finished = True
    
    def focus(self, storage: STORAGE) -> None:
        """ ## Change our focus on `storage` """
        self.focused_at = storage
    
    def unfocus(self) -> None:
        self.focused_at = None

def focus_auto(everything: common.CommonEverything):
    from src.svc.common.states import tree

    # if "adding mass zoom" state in trace
    if tree.Zoom.I_MASS in everything.ctx.navigator.trace:
        return focus_to_new_entries(everything)
    
    return focus_to_entries(everything)

def focus_to_entries(everything: common.CommonEverything):
    logger.info("focus_to_entries")
    everything.ctx.settings.zoom.focus(Storage.ENTRIES)

def focus_to_new_entries(everything: common.CommonEverything):
    logger.info("focus_to_new_entries")
    everything.ctx.settings.zoom.focus(Storage.NEW_ENTRIES)

def unfocus(everything: common.CommonEverything):
    logger.info("unfocus")
    everything.ctx.settings.zoom.unfocus()