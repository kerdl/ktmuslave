# Тур по структуре кода
В некоторых директориях имеется `README.md`,
описывающий предназначение вложенных
файлов и папок.


## Инициализация
Происходит в
[`src.Defs.init_all()`](/src/__init__.py?blame=1#L140).
- Инициализация логгера
- Чтение настроек
- Подключение к Redis и его настройка
- Загрузка обработчиков взаимодействия


## Взаимодействия
Когда пользователь отправляет сообщение
или нажимает на кнопку, это взаимодействие
принимает
[`src.svc.common.router.Router`](/src/svc/common/router.py?blame=1#L146).

Взаимодействия проходят через мидлвари в
[`src.svc.common.middlewares`](/src/svc/common/middlewares.py).
Там взаимодействие логгируется, фильтруется,
к нему загружается запись пользователя
из базы данных и сохраняется после выполнения.

Далее ищется нужный обработчик в
[`src.svc.common.bps`](/src/svc/common/bps).


## Цикл обновлений расписания
Цикл проходит в [`src.api.schedule.ScheduleApi.updates()`](/src/api/schedule.py?blame=1#L168).

Уведомления, приходящие от **ktmuscrap**
обрабатываются и рассылаются при необходимости.


## Еженедельная рассылка
Цикл проходит в
[`src.Defs.weekcast_loop()`](/src/__init__.py?blame=1&L280).


## Тексты сообщений
Тексты находятся в
[`src.svc.common.messages`](/src/svc/common/messages.py).


## Форматирование расписания
Расписания форматируются в
[`src.data.schedule.format.formation()`](/src/data/schedule/format.py?blame=1#L523).

Изменения форматируются в
[`src.data.schedule.format.cmp()`](/src/data/schedule/format.py?blame=1#L605).


## Парсинг сообщений с Zoom
- У групп -
[`src.parse.zoom.Parser.group_parse()`](/src/parse/zoom.py?blame=1#L309)
- У преподов -
[`src.parse.zoom.Parser.teacher_parse()`](/src/parse/zoom.py?blame=1#L330)
