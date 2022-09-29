if __name__ == "__main__":
    import sys
    sys.path.append(".")

from dataclasses import dataclass
from src.conv.pattern import SPACE_NEWLINE
from src.data import ZoomData


@dataclass
class Parser:
    text: str

    def remove_newline_spaces(self, text: str) -> str:
        return SPACE_NEWLINE.sub("\n\n", text)

    def split_sections(self, text: str) -> list[str]: 
        return text.split("\n\n")
    
    def parse_section(self, text: str) -> ZoomData:
        name = ""
        url = ""
        id = ""
        pwd = ""
    
    def parse(self) -> ZoomData:
        self.no_newline_spaces = self.remove_newline_spaces(self.text)
        self.sections = self.split_sections(self.no_newline_spaces)
        self.models: list[ZoomData] = []

        for section in self.sections:
            parsed = self.parse_section(section)

            if parsed is not None:
                self.models.append(parsed)
        
        return self.models


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
    p = Parser(text)
    print(p.parse())
