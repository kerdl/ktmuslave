from __future__ import annotations

import difflib
from typing import (
    Callable,
    Literal,
    Optional,
    Union,
    Any,
    ClassVar,
    TypeVar,
    List,
    TYPE_CHECKING
)
from pydantic import BaseModel, Field as PydField
from urllib.parse import urlparse
from src import data
from src.svc import common
from src.data import error
from src.data import Emojized, Translated, DataWarning, DataField
from src.parse import pattern, zoom, teacher
from src.svc import telegram as tg


T = TypeVar("T")
if TYPE_CHECKING:
    from src.data.settings import MODE_LITERAL


NAME_LIMIT = 30
VALUE_LIMIT = 500


NAME = (
    "{emoji} | {name}"
)
def format_name(emoji: str, name: Union[str, DataField]):
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


class Data(BaseModel, Translated, Emojized):
    name: DataField[str]
    url: DataField[Optional[str]] = PydField(
        default_factory=lambda: DataField(value=None)
    )
    id: DataField[Optional[str]] = PydField(
        default_factory=lambda: DataField(value=None)
    )
    pwd: DataField[Optional[str]] = PydField(
        default_factory=lambda: DataField(value=None)
    )
    host_key: DataField[Optional[str]] = PydField(
        default_factory=lambda: DataField(value=None)
    )
    notes: DataField[Optional[str]] = PydField(
        default_factory=lambda: DataField(value=None)
    )

    __translation__: ClassVar[dict[str, str]] = {
        "name": "Имя",
        "url": "Ссылка",
        "id": "ID",
        "pwd": "Пароль",
        "host_key": "Ключ хоста",
        "notes": "Заметки",
    }
    __emojis__: ClassVar[dict[str, str]] = {
        "name": "🐷",
        "url": "🌐",
        "id": "📍",
        "pwd": "🔑",
        "host_key": "🔒",
        "notes": "📝"
    }
    __keys__: ClassVar[dict[str, str]] = {
        "name": zoom.Key.NAME,
        "url": zoom.Key.URL,
        "id": zoom.Key.ID,
        "pwd": zoom.Key.PWD,
        "host_key": zoom.Key.HOST_KEY,
        "notes": zoom.Key.NOTES
    }

    @classmethod
    def parse(cls: type[Data], text: str) -> list[Data]:
        from src.parse import zoom
        return zoom.Parser(text).group_parse()

    @classmethod
    def tchr_parse(cls: type[Data], text: str) -> list[Data]:
        from src.parse import zoom
        return zoom.Parser(text).teacher_parse()
    
    @staticmethod
    def check_name(name: str) -> list[DataWarning]:
        warns = []

        match = pattern.SHORT_NAME.match(name)

        if not match or match.group() != name:
            warns.append(data.INCORRECT_NAME_FORMAT)

        if not name.endswith("."):
            warns.append(data.NO_DOT_AT_THE_END)

        return warns
    
    @staticmethod
    def check_url(url: str) -> list[DataWarning]:
        warns = []

        if urlparse(url).netloc is None:
            warns.append(data.NOT_AN_URL)

        if (
            data.NOT_AN_URL not in warns 
            and url.replace(" ", "").endswith(("..", "...", "…"))
        ):
            warns.append(data.URL_MAY_BE_CUTTED)
        
        return warns

    @staticmethod
    def check_id(id: str) -> list[DataWarning]:
        warns = []

        if not pattern.ZOOM_ID.search(id.replace(" ", "")):
            warns.append(data.INCORRECT_ID_FORMAT)
        
        if pattern.PUNCTUATION.search(id):
            warns.append(data.HAS_PUNCTUATION)
        
        if pattern.LETTER.search(id):
            warns.append(data.HAS_LETTERS)

        return warns
    
    def check(self, mode: "MODE_LITERAL"):
        from src.data.settings import Mode

        if mode == Mode.GROUP:
            for warn in self.check_name(self.name.value):
                self.name.warnings.append(warn)

        if hasattr(self, "url") and self.url.value is not None:
            for warn in self.check_url(self.url.value):
                self.url.warnings.append(warn)
        
        if hasattr(self, "id") and self.id.value is not None:
            for warn in self.check_id(self.id.value):
                self.id.warnings.append(warn)

    def fields(
        self, 
        filter_: Callable[[tuple[str, Any]], bool] = lambda field: True
    ) -> list[tuple[str, DataField[Optional[str]]]]:
        #        tuple    tuple     generator of tuples       condition
        return [field for field in self.__dict__.items() if filter_(field)]

    def all_fields_are_set(self, mode: "MODE_LITERAL") -> bool:
        from src.data.settings import Mode
        ignored = ["host_key", "notes"]
        return all([field[1].value for field in self.fields() if field[0] not in ignored])

    def all_fields_without_warns(
        self, 
        filter_: Callable[[tuple[str, Any]], bool] = lambda field: field[0] != "name"
    ) -> bool:
        return all([not field[1].has_warnings for field in self.fields(filter_)])

    def completeness_emoji(self, mode: "MODE_LITERAL") -> str:
        completeness = data.Emoji.COMPLETE

        if not self.all_fields_are_set(mode):
            completeness = data.Emoji.INCOMPLETE
        
        return completeness
    
    def name_emoji(
        self,
        mode: "MODE_LITERAL",
        warn_sources: Callable[[Data], list[DataField]] = lambda self: [self.name]
    ) -> str:
        any_warns = any([field.has_warnings for field in warn_sources(self)])

        if any_warns:
            return data.Emoji.WARN
        
        return self.completeness_emoji(mode)

    def choose_emoji(self, key: str, field: DataField) -> str:
        if field.has_warnings:
            return data.Emoji.WARN
        elif field.value is not None:
            return self.__emojis__.get(key)
        else:
            return data.Emoji.NONE

    def format_name(self, mode: "MODE_LITERAL", do_tg_markup: bool = False) -> str:
        emoji = self.name_emoji(mode)

        fmt_name = self.name.format(
            emoji=emoji, 
            name=self.name.value, 
            display_value=False,
            do_tg_markup=do_tg_markup,
            escape_tg_markdown=do_tg_markup
        )

        return fmt_name

    def format_fields(
        self,
        filter_: Callable[[tuple[str, Any]], bool] = (
            lambda field: field[0] != "name"
        ),
        do_tg_markup: bool = False
    ) -> str:
        fmt_fields = []

        for (key, field) in self.fields(filter_):
            emoji = self.choose_emoji(key, field)
            name = self.__translation__.get(key)

            if key == "url":
                fmt = field.format(
                    emoji=emoji,
                    name=name,
                    do_tg_markup=False,
                    escape_tg_markdown=True
                )
            else:
                fmt = field.format(
                    emoji=emoji,
                    name=name,
                    do_tg_markup=do_tg_markup,
                    escape_tg_markdown=do_tg_markup
                )
            fmt_fields.append(fmt)
        
        return "\n".join(fmt_fields)

    def format_fields_with_warns(self, do_tg_markup: bool = False) -> Optional[str]:
        if self.all_fields_without_warns():
            return None
        
        def field_filter(key_field: tuple[str, DataField]) -> bool:
            key = key_field[0]
            value = key_field[1]

            return key != "name" and value.has_warnings
        
        return self.format_fields(field_filter, do_tg_markup)

    def format(
        self,
        mode: "MODE_LITERAL",
        field_filter: Callable[[tuple[str, Any]], bool] = (
            lambda field: field[0] != "name"
        ),
        do_tg_markup: bool = False,
    ) -> str:
        fmt_name = self.format_name(mode)

        fmt_fields = self.format_fields(field_filter, do_tg_markup)
        fmt_fields = common.text.indent(fmt_fields, add_dropdown = True)
        
        return fmt_name + "\n" + fmt_fields

    def format_inline(
        self,
        include_name: bool = False,
        name_prefix: Optional[str] = None,
        only_notes: bool = False,
        do_tg_markup: bool = False,
        return_empty_if_no_data: bool = True
    ) -> str:
        data = []
        if not only_notes:
            if self.url.value is not None:
                if do_tg_markup:
                    data.append(tg.escape_html(self.url.value))
                else:
                    data.append(self.url.value)

            if self.id.value is not None:
                translation = self.__translation__.get("id")
                if do_tg_markup:
                    data.append(f"{translation}: <code>{tg.escape_html(self.id.value)}</code>")
                else:
                    data.append(f"{translation}: {self.id.value}")

            if self.pwd.value is not None:
                translation = self.__translation__.get("pwd").lower()
                if do_tg_markup:
                    data.append(f"{translation}: <code>{tg.escape_html(self.pwd.value)}</code>")
                else:
                    data.append(f"{translation}: {self.pwd.value}")
            
            if self.host_key.value is not None:
                translation = self.__translation__.get("host_key").lower()
                if do_tg_markup:
                    data.append(f"{translation}: <code>{tg.escape_html(self.host_key.value)}</code>")
                else:
                    data.append(f"{translation}: {self.host_key.value}")

        if self.notes.value is not None:
            if do_tg_markup:
                data.append(f"<code>{tg.escape_html(self.notes.value)}</code>")
            else:
                data.append(self.notes.value)

        if not data and return_empty_if_no_data:
            return ""
        
        fmt = ", ".join(data)

        if include_name:
            if name_prefix:
                fmt = f"{name_prefix} {self.name.value} | {fmt}"
            else:
                fmt = f"{self.name.value} | {fmt}"
        
        return fmt

    def dump_list(self) -> list[str]:
        fields: list[str] = []

        for (key, field) in self.fields():
            if field.value is None:
                continue

            parsing_key = self.__keys__.get(key)

            if isinstance(parsing_key, list):
                parsing_key = parsing_key[0]
            if parsing_key is None:
                continue
                
            fmt_field = f"{parsing_key}: {field.value}"
            fields.append(fmt_field)
        
        return fields
    
    def dump_str(self) -> str:
        return "\n".join(self.dump_list())

    def __setattr__(self, __name: str, __value: Any) -> None:
        super().__setattr__(__name, __value)

    def __hash__(self):
        return hash(self.name.value)
    
    def __eq__(self, other):
        return self.name.value == other


class Entries(BaseModel):
    list: List[Data] = PydField(
        default_factory=lambda *a, **kw: list(*a, *kw)
    )
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
    def from_list(cls: type[Entries], list: list[Data]):
        return cls(list=list)
    
    @property
    def selected(self) -> Data:
        return self.get(self.selected_name)

    def change_name(self, old: str, new: str) -> None:
        if old not in self.list:
            raise error.ZoomNameNotInDatabase(
                "tried to change inexistent name"
            )
        
        if new in self.list:
            raise error.ZoomNameInDatabase(
                "new name is already in the database"
            )
        
        # get current data from old name
        data = self.get(old)

        # remove it from the actual set
        self.remove(old)

        # change our backup with a new name
        data.name = DataField(value=new)

        # add this backup with changed name back
        self.add(data)

    def select(self, name: str) -> Data:
        """ ## Mark this name as selected, return its data """

        # if this name not
        # in this container
        if not self.has(name):
            raise error.ZoomNameNotInDatabase(
                "tried to select a name "
                "that is not in the database"
            )
        
        self.selected_name = name

        return self.get(name)

    def unselect(self) -> None:
        self.selected_name = None

    def add(
        self, 
        data: Union[Data, list[Data]], 
        overwrite: bool = False
    ):
        if isinstance(data, (set, list)):
            for data_obj in data:
                if data_obj in self.list and overwrite:
                    self.list.remove(data_obj)

                self.list.append(data_obj)
        
        elif isinstance(data, Data):
            if data in self.list and overwrite:
                self.list.remove(data)

            self.list.append(data)

    def add_from_name(self, name: str):
        data = Data(name=DataField[str](value=name))
        self.add(data)

    def get(self, name: str) -> Optional[Data]:
        for entry in self.list:
            if entry.name == name:
                return entry

        return None
    
    def get_approx(self, name: str, as_teacher: bool = True) -> Optional[Data]:
        names = [entry.name.value for entry in self.list]
        
        if as_teacher:
            valid = teacher.validate(name, names)
            return self.get(valid)
        else:
            matches = difflib.get_close_matches(name, names, cutoff=0.8)
            try: return self.get(matches[0])
            except IndexError: return None

    def has(self, name: str) -> bool:
        """ ## If `name` in this container """
        return name in self.list

    @property
    def has_something(self) -> bool:
        """ ## If this container has something """
        return len(self.list) > 0

    def remove(self, name: Union[str, set[str]]):
        if isinstance(name, set):
            for n in name:
                self.list.remove(n)
            
            return None

        if isinstance(name, str):
            self.list.remove(name)

            return None
    
    def format_compact(self, mode: "MODE_LITERAL") -> str:
        names: list[str] = []

        for entry in self.list:
            warns_text: Optional[str] = None

            if not entry.all_fields_without_warns():
                warns_text = entry.format_fields_with_warns()
                warns_text = common.text.indent(warns_text, add_dropdown = True)
            
            name = entry.format_name(mode)

            if warns_text:
                name = name + "\n" + warns_text

            names.append(name)

        return "\n".join(names)

    def clear(self):
        self.list = set()
    
    def dump(self) -> str:
        entries_dumps: list[str] = []

        for entry in self.list:
            dump = entry.dump_str()
            entries_dumps.append(dump)
        
        return "\n\n".join(entries_dumps)
    
    def check_all(self, mode: "MODE_LITERAL"):
        for entry in self.list:
            entry.check(mode)

    def __len__(self):
        return len(self.list)


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


class Container(BaseModel):
    entries: Entries = PydField(default_factory=Entries)
    """
    ## Main database of zoom

    - takes links for schedule here
    """
    new_entries: Entries = PydField(default_factory=Entries)
    """
    ## Temp storage for unconfirmed new entries

    - when user sends a massive message
    with data, we store its entries here,
    and overwrite/add them only when
    user confirms
    """

    is_finished: bool = False
    """
    ## Initial step of adding Zoom was completed

    - used to determine when to display
    `"0"` at the right of `"Add zoom"`
    state
    """
    focused_at: Optional[STORAGE] = None
    """ ## Tells which container to use """
    mode: Optional["MODE_LITERAL"] = None
    """ ## Container mode """


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
        self.entries.add(self.new_entries.list, overwrite = True)
        # clear new entries
        self.new_entries.list.clear()

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
        return Entries.from_list(
            list(set(self.new_entries.list).difference(set(self.entries.list)))
        )

    @property
    def overwriting(self) -> Entries:
        return Entries.from_list(
            list(set(self.entries.list).intersection(set(self.new_entries.list)))
        )

    def finish(self) -> None:
        """ ## Initial step of adding Zoom was completed """
        self.is_finished = True
    
    def focus(self, storage: STORAGE) -> None:
        """ ## Change our focus on `storage` """
        self.focused_at = storage
    
    def unfocus(self) -> None:
        self.focused_at = None

    def check_all(self):
        self.entries.check_all(self.mode)
        self.new_entries.check_all(self.mode)

    @classmethod
    def as_group(cls) -> Container:
        from src.data.settings import Mode
        this = cls()
        this.mode = Mode.GROUP
        return this
    
    @classmethod
    def as_tchr(cls) -> Container:
        from src.data.settings import Mode
        this = cls()
        this.mode = Mode.TEACHER
        return this
    
def focus_auto(everything: common.CommonEverything):
    from src.svc.common.states import tree
    from src.data.settings import Mode

    # if "adding mass zoom" state in trace
    if tree.ZOOM.I_MASS in everything.ctx.navigator.trace:
        if everything.ctx.settings.mode == Mode.GROUP:
            return focus_to_new_entries(everything)
        elif everything.ctx.settings.mode == Mode.TEACHER:
            return focus_to_tchr_new_entries(everything)
    
    if everything.ctx.settings.mode == Mode.GROUP:
        return focus_to_entries(everything)
    elif everything.ctx.settings.mode == Mode.TEACHER:
        return focus_to_tchr_entries(everything)

def focus_to_entries(everything: common.CommonEverything):
    everything.ctx.settings.zoom.focus(Storage.ENTRIES)

def focus_to_new_entries(everything: common.CommonEverything):
    everything.ctx.settings.zoom.focus(Storage.NEW_ENTRIES)

def focus_to_tchr_entries(everything: common.CommonEverything):
    everything.ctx.settings.tchr_zoom.focus(Storage.ENTRIES)

def focus_to_tchr_new_entries(everything: common.CommonEverything):
    everything.ctx.settings.tchr_zoom.focus(Storage.NEW_ENTRIES)

def unfocus(everything: common.CommonEverything):
    from src.data.settings import Mode
    if everything.ctx.settings.mode == Mode.GROUP:
        everything.ctx.settings.zoom.unfocus()
    if everything.ctx.settings.mode == Mode.TEACHER:
        everything.ctx.settings.tchr_zoom.unfocus()
    

def unselect(everything: common.CommonEverything):
    if everything.ctx.settings.zoom.focused is None:
        everything.ctx.settings.zoom.focus(Storage.ENTRIES)

    everything.ctx.settings.zoom.focused.unselect()
