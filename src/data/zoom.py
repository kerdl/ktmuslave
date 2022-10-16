from __future__ import annotations

from src import data

if __name__ == "__main__":
    import sys
    sys.path.append(".")

from loguru import logger
from typing import Callable, Literal, Optional, Union, Any, ClassVar, TypeVar
from dataclasses import dataclass, field

from src.svc import common
from src.data import Repred, error
from src.data import Emojized, Translated, Warning, Field


T = TypeVar("T")


COMPLETE   = "🔹"
INCOMPLETE = "🔸"
NONE       = "❓"
WARN       = "❗"

NAME = (
    "{emoji} | {name}"
)
def format_name(emoji: str, name: Union[str, Field]):
    if isinstance(name, str):
        return NAME.format(emoji = emoji, name = name)

    return NAME.format(
        emoji = emoji, 
        name  = name.__repr_name__()
    )

SECTION = (
    "{name}\n"
    "{fields}"
)
def format_section(name: str, fields: list[str]):
    indented_fields = []
    merged_fields = ""

    for field in fields:
        indented_field = common.text.indent(field, add_dropdown = True)
        indented_fields.append(indented_field)
    
    merged_fields = "\n".join(indented_fields)

    return SECTION.format(
        name = name,
        fields = merged_fields
    )

NO = "нет"


@dataclass
class Data(Translated, Emojized):
    name: Field[str]
    url: Field[Optional[str]]
    id: Field[Optional[str]]
    pwd: Field[Optional[str]]

    __translation__: ClassVar[dict[str, str]] = {
        "name": "Имя",
        "url": "Ссылка",
        "id": "ID",
        "pwd": "Пароль",
    }
    __emojis__: ClassVar[dict[str, str]] = {
        "name": "🐷",
        "url": "🌐",
        "id": "📍",
        "pwd": "🔑",
    }

    @classmethod
    def parse(cls: type[Data], text: str) -> list[Data]:
        from src.parse import zoom
        return zoom.Parser(text).parse()
    
    def fields(
        self, 
        filter_: Callable[[tuple[str, Any]], bool] = lambda field: True
    ) -> list[tuple[str, Field[Optional[str]]]]:
        #        tuple    tuple     generator of tuples       condition
        return [field for field in self.__dict__.items() if filter_(field)]

    def all_fields_are_set(self) -> bool:
        return all([field[1].value for field in self.fields()])

    def all_fields_without_warns(
        self, 
        filter_: Callable[[tuple[str, Any]], bool] = lambda field: field[0] != "name"
    ) -> bool:
        return all([not field[1].has_warnings for field in self.fields(filter_)])

    def completeness_emoji(self) -> str:
        completeness = COMPLETE

        if not self.all_fields_are_set():
            completeness = INCOMPLETE
        
        return completeness

    def choose_emoji(self, key: str, field: Field) -> str:
        if field.has_warnings:
            return WARN
        elif field.value is not None:
            return self.__emojis__.get(key)
        else:
            return NONE

    def format_name(
        self, 
        warn_sources: Callable[[Data], list[Field]] = lambda self: [self.name]
    ) -> str:
        emoji = self.completeness_emoji()

        has_warn_sources = warn_sources(self)
        any_warns_in_sources = any([
            field.has_warnings for field in warn_sources(self)
        ])

        if has_warn_sources and any_warns_in_sources:
            emoji = WARN

        fmt_name = self.name.format(
            emoji         = emoji, 
            name          = self.name.value, 
            display_value = False
        )

        return fmt_name

    def format_fields(
        self,
        filter_: Callable[[tuple[str, Any]], bool] = (
            lambda field: field[0] != "name"
        )
    ) -> str:
        fmt_fields = []

        for (key, field) in self.fields(filter_):
            emoji = self.choose_emoji(key, field)
            name = self.__translation__.get(key)

            fmt = field.format(emoji, name)
            fmt_fields.append(fmt)
        
        return "\n".join(fmt_fields)

    def format_fields_with_warns(self) -> Optional[str]:
        if self.all_fields_without_warns():
            return None
        
        def field_filter(key_field: tuple[str, Field]) -> bool:
            key = key_field[0]
            value = key_field[1]

            return key != "name" and value.has_warnings
        
        return self.format_fields(field_filter)

    def format(
        self,
        field_filter: Callable[[tuple[str, Any]], bool] = (
            lambda field: field[0] != "name"
        )
    ) -> str:
        fmt_name = self.format_name()

        fmt_fields = self.format_fields(field_filter)
        fmt_fields = common.text.indent(fmt_fields, add_dropdown = True)
        
        return fmt_name + "\n" + fmt_fields

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
    selected_name: Optional[str] = None
    """
    # Name of entry that is currently selected
    - used for selecting an entry from pagination,
    so we know what is being edited right now
    """

    @classmethod
    def default(cls: type[Entries]):
        return cls(set = set())

    @classmethod
    def from_set(cls: type[Entries], set: set[Data]):
        return cls(set = set)
    
    @property
    def selected(self) -> Data:
        return self.get(self.selected_name)

    def select(self, name: str) -> Data:
        """ ## Mark this name as selected, return its data """

        # if this name not
        # in this container
        if not self.has(name):
            raise error.ZoomNameNotInDatabase(
                "you're trying to select a name "
                "that is not in database"
            )
        
        self.selected_name = name

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
                name = data.Field(n),
                url  = data.Field(""),
                id   = data.Field(""),
                pwd  = data.Field("")
            )

            self.set.remove(dummy)

        if isinstance(name, set):
            for n in name:
                remove_with_dummy(n)
            
            return None

        if isinstance(name, str):
            remove_with_dummy(name)

            return None
    
    def format_compact(self) -> str:
        names: list[str] = []

        for entry in self.set:
            warns_text: Optional[str] = None

            if not entry.all_fields_without_warns():
                warns_text = entry.format_fields_with_warns()
                warns_text = common.text.indent(warns_text, add_dropdown = True)
            
            name = entry.format_name()

            if warns_text:
                name = name + "\n" + warns_text

            names.append(name)

        return "\n".join(names)

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

    @property
    def adding(self) -> Entries:
        return Entries.from_set(
            self.new_entries.set.difference(self.entries.set)
        )

    @property
    def overwriting(self) -> Entries:
        return Entries.from_set(
            self.entries.set.intersection(self.new_entries.set)
        )

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