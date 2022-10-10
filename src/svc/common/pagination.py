if __name__ == "__main__":
    import sys
    sys.path.append(".")

from typing import Generator, Union, TypeVar

from src.svc.common.keyboard import Keyboard, Button, Color, Payload
from src.svc.common import CommonBotTemplate, messages
from src.data import zoom

T = TypeVar("T")


BULLET = "■"


def chunks(lst: list[T], n: int) -> Generator[list[T], None, None]:
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def from_zoom(
    data: list[zoom.Data], 
    per_page: int = 6, 
    keyboard_width: int = 3
) -> list[CommonBotTemplate]:

    # the output of this function
    msgs = []
    # split whole data into pages
    splitted_chunks = [chunk for chunk in chunks(data, per_page)]

    # iterate for each chunk, a list of zoom data classes
    for (page_num, page) in enumerate(splitted_chunks):
        is_first_page = page_num == 0
        is_last_page = page_num + 1 == len(splitted_chunks)

        # call `format()` on each zoom data and separate them with "\n\n"
        text = "\n\n".join([section.format() for section in page])

        # add page number at the bottom
        text += "\n\n"
        text += messages.format_page_num(
            current = page_num + 1, 
            last = len(splitted_chunks)
        )

        # whole keyboard schema
        kb_schema = []
        # current row
        cur_row = []

        # iterate for each section in current chunk
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

        back_symbol = "←" if not is_first_page else BULLET
        next_symbol = "→" if not is_last_page else BULLET

        back_button = Button(back_symbol, Payload.PAGE_BACK)
        page_button = Button(f"{page_num + 1}", f"{page_num}")
        next_button = Button(next_symbol, Payload.PAGE_NEXT)

        # make a row with navigation
        kb_schema.append([
            back_button, page_button, next_button
        ])

        message = CommonBotTemplate(
            text     = text,
            keyboard = Keyboard(kb_schema)
        )
        msgs.append(message)

    return msgs


if __name__ == "__main__":

    text = """
Корабельникова Мария Александровна
https://us04web.zoom.us/j/78319850724?pwd=OVhpOFRlaGR0TnpDUWkvNDllZEZOZz09
Ид.: 783 1985 0724
Код: 0ENPYx

Малютина Елена Николаевна
https://us04web.zoom.us/j/75701763875?pwd=a1FzM1FiSStqdi93M1kzMzNwYnFKZz09
Ид.: 75701763875
Код: VR46rX

Смолина Татьяна Александровна
https://us04web.zoom.us/j/2266947102?pwd=N25sZFFjWDNDcjNTeTNlM2JNNnpXUT09

Косточко Вера Ивановна
https://zoom.us/j/8347057163?pwd=SzhtRWZKWENjN2JWRDZZZUtZdVJBQT09
Идентификатор: 834 705 7163
Код: h6UJgR

Кудряшова Елена Семеновна
https://us04web.zoom.us/j/75926804537?pwd=NEs3UXN5ZEhlbEJPenhOeEs3dVppZz09
Ид.: 759 2680 4537
Код: 9bXf8B

Мызин
https://us04web.zoom.us/j/9133105800?pwd=bWhnUDQrbEtmUCtBK3F0cjNmaUxiQT09
Код: 4hWim6

Власова Татьяна Ильинична
tana.vlasova.vlas102@gmail.com
https://us04web.zoom.us/j/9695067615?pwd=NkxOdDJrTmJXWnJZUHJ…
Идентификатор
конференции: 969 506 7615
Код доступа: 344kHC

Воистинова Валентина Викторовна
https://us04web.zoom.us/j/74384721321?pwd=VUNrK2tYQ1lBTGpEVkdQTkhhdE5Hdz09
Идентификатор: 743 8472 1321
Код доступа: 5yVLRJ

Подделкова Полина Евгеньевна
https://zoom.us/j/9621085574?pwd=bWFjYU11dExxdkNlQXNKQm1XdncyZz09
Ид.: 962 108 5574
Код: jvLpa5

Фокина Диана Антоновна
https://us04web.zoom.us/j/3088700168?pwd=NEVaMW1hazNzY1g2UVFEL0k2ZG9tdz09

Meeting ID: 308 870 0168

Тимофеева Светлана Константиновна
https://us05web.zoom.us/j/5905709257?pwd=M2swWVoydnBFdGpEVUdSdThNSHIxZz09
Идентификатор: 590 570 9257
Код доступа: j08cqh

Малиновский Денис
https://us02web.zoom.us/j/89700354293

Нуруллин Марат Альбертович
https://us05web.zoom.us/j/83732931265?pwd=TVlNOVpUTktjbzlTL1o4WExPMS91QT09
Идентификатор: 837 3293 1265
Код доступа: M9Ha0s
"""

    data = zoom.Data.parse(text)
    from_zoom(data=data)