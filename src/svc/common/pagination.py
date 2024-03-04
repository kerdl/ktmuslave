from __future__ import annotations

if __name__ == "__main__":
    import sys
    sys.path.append(".")

from typing import Generator, Union, TypeVar, Optional
from dataclasses import dataclass
from pydantic import BaseModel, Field as PydField

from src.svc.common.keyboard import BACK_BUTTON, Keyboard, Button, Color, Payload
from src.svc.common.template import CommonBotTemplate, MetadataKeys
from src.svc.common import error, messages
from src.data import zoom

T = TypeVar("T")


BULLET = "■"


def chunks(lst: list[T], n: int) -> Generator[list[T], None, None]:
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

class Container(BaseModel):
    list: list[CommonBotTemplate] = PydField(default_factory=list)
    """ ## List of pages, containing messsage templates """
    current_num: int = 0
    """ ## On which page number user is currently on """


    def keep_num_in_range(self) -> None:
        last_page_index = len(self.list) - 1

        if last_page_index < self.current_num:
            self.current_num = last_page_index

    @property
    def current(self):
        """ ## Current page """
        if len(self.list) < 1:
            raise error.NoPages(
                "no pages in container, can't return current page"
            )

        self.keep_num_in_range()

        return self.list[self.current_num]

def from_zoom(
    data: Union[list[zoom.Data], set[zoom.Data]], 
    per_page: int = 4, 
    text_footer: Optional[str] = None,
    keyboard_width: int = 2,
    keyboard_header: list[list[Button]] = [[]],
    keyboard_footer: list[list[Button]] = [[BACK_BUTTON]]
) -> list[CommonBotTemplate]:
    if isinstance(data, set):
        data = list(data)

    # the output of this function
    msgs = []
    # split whole data into pages
    pages = [page for page in chunks(data, per_page)]

    is_single_page = len(pages) < 2

    if len(pages) < 1:
        pages = [[]]

    page_num_names_map: dict[int, list[str]] = {}

    # iterate for each chunk, a list of zoom data classes
    for (page_num, page) in enumerate(pages):
        this_page_names = [entry.name.value for entry in page]
        page_num_names_map[page_num] = this_page_names

        is_first_page = page_num == 0
        is_last_page = page_num + 1 == len(pages)

        if len(page) > 0:
            # call `format()` on each zoom data and separate them with "\n\n"
            text = "\n\n".join([section.format() for section in page])
        else:
            text = messages.format_empty_page()

        # add page number at the bottom
        text += "\n\n"
        text += messages.format_page_num(
            current = page_num + 1, 
            last = len(pages)
        )

        # add custom text footer
        if text_footer is not None:
            text += "\n\n"
            text += text_footer

        # whole keyboard schema
        kb_schema = []
        # current row
        cur_row = []

        # append keyboard header
        for row in keyboard_header:
            kb_schema.append(row)

        if not is_single_page:
            back_symbol = "←" if not is_first_page else BULLET
            next_symbol = "→" if not is_last_page else BULLET

            back_button = Button(text=back_symbol, callback=Payload.PAGE_BACK)
            next_button = Button(text=next_symbol, callback=Payload.PAGE_NEXT)

            # make a row with navigation
            kb_schema.append([
                back_button, 
                #page_button, 
                next_button
            ])

        # iterate for each section in current page (2D array)
        #                  [..., ...]         [ [..., ...], [..., ...] ]
        for (section_i, section) in enumerate(page):
            is_last_section = section_i + 1 == len(page)

            name_emoji = section.name_emoji(
                warn_sources = lambda entry: [
                    entry.name,
                    entry.url,
                    entry.id,
                    entry.pwd
                ]
            )

            button = Button(
                text     = f"{name_emoji} {section.name.__repr_name__()}", 
                callback = section.name.__repr_name__(),
                color    = Color.BLUE
            )

            cur_row.append(button)

            # if current row is equal to max keyboard width 
            # or it's the last section
            if len(cur_row) == keyboard_width or is_last_section:
                # append this row to whole schema
                kb_schema.append(cur_row)
                # clean current row
                cur_row = []

        for row in keyboard_footer:
            if not row:
                continue

            kb_schema.append(row)

        message = CommonBotTemplate(
            text     = text,
            keyboard = Keyboard(kb_schema, add_back=False),
            metadata = {MetadataKeys.PAGE_NUM_NAMES_MAP: page_num_names_map}
        )
        msgs.append(message)

    return msgs


if __name__ == "__main__":

    text = """"""

    data = zoom.Data.parse(text)
    from_zoom(data=data)