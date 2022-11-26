from __future__ import annotations

from src import data

if __name__ == "__main__":
    import sys
    sys.path.append(".")

from loguru import logger
from typing import Callable, Literal, Optional, Union, Any, ClassVar, TypeVar
from dataclasses import dataclass, field
from urllib.parse import urlparse

from src.svc import common
from src.data import error
from src.data import Emojized, Translated, Warning, Field
from src.parse import pattern


T = TypeVar("T")


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


@dataclass
class Data(Translated, Emojized):
    name: Field[str]
    url: Field[Optional[str]]   = field(default_factory = lambda: Field(None))
    id: Field[Optional[str]]    = field(default_factory = lambda: Field(None))
    pwd: Field[Optional[str]]   = field(default_factory = lambda: Field(None))
    notes: Field[Optional[str]] = field(default_factory = lambda: Field(None))

    __translation__: ClassVar[dict[str, str]] = {
        "name": "Имя",
        "url": "Ссылка",
        "id": "ID",
        "pwd": "Пароль",
        "notes": "Заметки",
    }
    __emojis__: ClassVar[dict[str, str]] = {
        "name": "🐷",
        "url": "🌐",
        "id": "📍",
        "pwd": "🔑",
        "notes": "📝"
    }

    def i_promise_i_will_get_rid_of_this_thing_but_not_now(self):
        try:
            self.notes
        except AttributeError:
            self.notes = Field(None)

    @classmethod
    def parse(cls: type[Data], text: str) -> list[Data]:
        from src.parse import zoom
        return zoom.Parser(text).parse()
    
    @staticmethod
    def check_name(name: str) -> set[Warning]:
        warns = set()

        match = pattern.SHORT_NAME.match(name)

        if not match or match.group() != name:
            warns.add(data.INCORRECT_NAME_FORMAT)

        if not name.endswith("."):
            warns.add(data.NO_DOT_AT_THE_END)

        return warns
    
    @staticmethod
    def check_url(url: str) -> set[Warning]:
        warns = set()

        if urlparse(url).netloc is None:
            warns.add(data.NOT_AN_URL)

        if (
            data.NOT_AN_URL not in warns 
            and url.replace(" ", "").endswith(("..", "...", "…"))
        ):
            warns.add(data.URL_MAY_BE_CUTTED)
        
        return warns

    @staticmethod
    def check_id(id: str) -> set[Warning]:
        warns = set()

        if not pattern.ZOOM_ID.search(id):
            warns.add(data.INCORRECT_ID_FORMAT)
        
        if pattern.PUNCTUATION.search(id):
            warns.add(data.HAS_PUNCTUATION)
        
        if pattern.LETTER.search(id):
            warns.add(data.HAS_LETTERS)

        return warns
    
    def check(self):
        self.name.warnings = self.check_name(self.name.value)

        if hasattr(self, "url") and self.url.value is not None:
            self.url.warnings = self.check_url(self.url.value)
        
        if hasattr(self, "id") and self.id.value is not None:
            self.id.warnings = self.check_id(self.id.value)

    def fields(
        self, 
        filter_: Callable[[tuple[str, Any]], bool] = lambda field: True
    ) -> list[tuple[str, Field[Optional[str]]]]:
        #        tuple    tuple     generator of tuples       condition
        return [field for field in self.__dict__.items() if filter_(field)]

    def all_fields_are_set(self) -> bool:
        ignored = ["notes"]

        return all([field[1].value for field in self.fields() if field[0] not in ignored])

    def all_fields_without_warns(
        self, 
        filter_: Callable[[tuple[str, Any]], bool] = lambda field: field[0] != "name"
    ) -> bool:
        return all([not field[1].has_warnings for field in self.fields(filter_)])

    def completeness_emoji(self) -> str:
        completeness = data.Emoji.COMPLETE

        if not self.all_fields_are_set():
            completeness = data.Emoji.INCOMPLETE
        
        return completeness
    
    def name_emoji(
        self,
        warn_sources: Callable[[Data], list[Field]] = lambda self: [self.name]
    ) -> str:

        any_warns = any([field.has_warnings for field in warn_sources(self)])

        if any_warns:
            return data.Emoji.WARN
        
        return self.completeness_emoji()

    def choose_emoji(self, key: str, field: Field) -> str:
        if field.has_warnings:
            return data.Emoji.WARN
        elif field.value is not None:
            return self.__emojis__.get(key)
        else:
            return data.Emoji.NONE

    def format_name(self) -> str:
        emoji = self.name_emoji()

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

    def __setattr__(self, __name: str, __value: Any) -> None:
        super().__setattr__(__name, __value)

        self.check()

    def __hash__(self):
        return hash(self.name.value)
    
    def __eq__(self, other):
        return self.name.value == other


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

    def change_name(self, old: str, new: str) -> None:
        if old not in self.set:
            raise error.ZoomNameNotInDatabase(
                "you're trying to change inexistent name"
            )
        
        if new in self.set:
            raise error.ZoomNameInDatabase(
                "new name is already in database"
            )
        
        # get current data from old name
        data = self.get(old)

        # remove it from the actual set
        self.remove(old)

        # change our backup with a new name
        data.name = Field(new)

        # add this backup with changed name back
        self.add(data)

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

    def unselect(self) -> None:
        self.selected_name = None

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

    def add_from_name(self, name: str):
        data = Data(name = Field(name))

        self.add(data)

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
        if isinstance(name, set):
            for n in name:
                self.set.remove(n)
            
            return None

        if isinstance(name, str):
            self.set.remove(name)

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

    def clear(self):
        self.set = set()

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

    def confirm_new_entries(self) -> None:
        # add data from `new_entries` to `entries`
        self.entries.add(self.new_entries.set, overwrite = True)
        # clear new entries
        self.new_entries.set.clear()

        self.finish()

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
    if tree.ZOOM.I_MASS in everything.ctx.navigator.trace:
        return focus_to_new_entries(everything)
    
    return focus_to_entries(everything)

def focus_to_entries(everything: common.CommonEverything):
    everything.ctx.settings.zoom.focus(Storage.ENTRIES)

def focus_to_new_entries(everything: common.CommonEverything):
    everything.ctx.settings.zoom.focus(Storage.NEW_ENTRIES)

def unfocus(everything: common.CommonEverything):
    everything.ctx.settings.zoom.unfocus()

def unselect(everything: common.CommonEverything):
    everything.ctx.settings.zoom.focused.unselect()