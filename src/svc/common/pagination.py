from __future__ import annotations

if __name__ == "__main__":
    import sys
    sys.path.append(".")

from typing import Generator, Union, TypeVar, Optional
from dataclasses import dataclass

from src.svc.common.keyboard import BACK_BUTTON, Keyboard, Button, Color, Payload
from src.svc import common
from src.data import zoom

T = TypeVar("T")


BULLET = "■"


def chunks(lst: list[T], n: int) -> Generator[list[T], None, None]:
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

@dataclass
class Container:
    list: list[common.CommonBotTemplate]
    """ ## List of pages, containing messsage templates """
    current_num: int
    """ ## On which page number user is currently on """

    @classmethod
    def default(cls: type[Container]):
        return cls([], 0)
    
    @property
    def current(self):
        """ ## Current page """
        return self.list[self.current_num]

def from_zoom(
    data: Union[list[zoom.Data], set[zoom.Data]], 
    per_page: int = 6, 
    text_footer: Optional[str] = None,
    keyboard_width: int = 2,
    keyboard_header: list[Button] = [],
    keyboard_footer: list[Button] = [BACK_BUTTON]
) -> list[common.CommonBotTemplate]:

    if isinstance(data, set):
        data = list(data)

    # the output of this function
    msgs = []
    # split whole data into pages
    pages = [page for page in chunks(data, per_page)]

    is_single_page = len(pages) < 2

    # iterate for each chunk, a list of zoom data classes
    for (page_num, page) in enumerate(pages):
        is_first_page = page_num == 0
        is_last_page = page_num + 1 == len(pages)

        # call `format()` on each zoom data and separate them with "\n\n"
        text = "\n\n".join([section.format() for section in page])

        # add page number at the bottom
        text += "\n\n"
        text += common.messages.format_page_num(
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
        kb_schema.append(keyboard_header)

        if not is_single_page:
            back_symbol = "←" if not is_first_page else BULLET
            next_symbol = "→" if not is_last_page else BULLET

            back_button = Button(back_symbol, Payload.PAGE_BACK)
            #page_button = Button(f"{page_num + 1}", f"{page_num}")
            next_button = Button(next_symbol, Payload.PAGE_NEXT)

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

            button = Button(
                text     = section.name, 
                callback = section.name,
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

        kb_schema.append(keyboard_footer)

        message = common.CommonBotTemplate(
            text     = text,
            keyboard = Keyboard(kb_schema, add_back=False)
        )
        msgs.append(message)

    return msgs


if __name__ == "__main__":

    text = """"""

    data = zoom.Data.parse(text)
    from_zoom(data=data)