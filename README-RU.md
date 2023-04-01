[🇬🇧 English](/README.md)

Работает в продакшене:
<p float="left">
  <a title="VK" href="https://vk.com/ktmuslave">
    <img alt="VK" src="https://upload.wikimedia.org/wikipedia/commons/f/f3/VK_Compact_Logo_%282021-present%29.svg" width=35>
  </a>
  <a title="Telegram" href="https://t.me/ktmuslave_bot">
    <img alt="Telegram" src="https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg" width=35>
  </a>
</p>

# KTMU slave
### Бот для расписания с https://ktmu-sutd.ru/

- Как для [VK](https://vk.com/ktmuslave), так и [Telegram](https://t.me/ktmuslave_bot) с одной кодбазой используя свою реализацию хэндлеров
- Простая пошаговая регистрация
- Простое постраничное изменяемое хранилище на каждого пользователя для Zoom данных преподов, чтобы отображать данные в расписании
- Рассылка при изменении расписания с детальным сравнением, с ответом на прошлое сообщение и закреп в чате по желанию
- Возможность самостоятельно обновить расписание глобально, если кто-то заметил изменения между 10 минутным периодом автообновления
- Прочие полезные ссылки в сообщении с расписанием: **оригинальные расписания**, **материалы преподов** и **журналы**

## Что насчёт парсинга?
[**ktmuscrap**](https://github.com/kerdl/ktmuscrap) - HTTP REST API сервер-парсер написанный на 🚀НЕВЕРОЯТНО БЫСТРОЙ ХИТОВОЙ ВИДЕОИГРЕ - RUST🚀

Сервер запускается на локалке, предоставляя простой API для этого бота с такими фичами, как:
- получение **дневного** или **недельного** расписания в виде JSON как **полностью**, так и **для определённой группы чтоб 🚀СОХРАНИТЬ ДОП. МИЛЛИСЕКУНДУ🚀**
- ручное обновление POST запросом, если юзер нажал кнопку **Обновить**
- получение обновлений с помощью WebSocket, где отправляются все детальные изменения расписания

Больше в [README **ktmuscrap**](https://github.com/kerdl/ktmuscrap/blob/master/README.md) 😮😮😮😮

## Улучшения
[Issues](https://github.com/kerdl/ktmuslave/issues) - самый **ЦЕННЫЙ©** и **ПРОВЕРЕННЫЙ®** источник запланированных улучшений (так как это моё портфолио и я хочу выглядеть ответственным) этой непопулярной хуйни

## Все фичи
- [**База данных Redis**](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/__init__.py#L41-L87)
  - [Стейты навигации юзера](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/states/tree.py)
  - [Настройки юзера](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/data/settings.py#L17-L22)
  - [Хранилище Zoom данных юзера](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/data/zoom.py#L472-L499)
  - [Другое незначительное говно чтоб бот работал](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/router.py)
- [**Кастомный роутер для хендлеров VK и Telegram**](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/router.py)
  - Декораторы, чтоб хендлеры регались автоматически ([🎍 декораторы](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/router.py#L37-L74))
  - Фильтры, например чтоб хендлер выполнялся только при колбэке ([🚽 базовые фильтры](https://github.com/kerdl/ktmuslave/blob/master/src/svc/common/filters.py))
  - Роутер, проверяет все фильтры и выполняет хендлер который прошёл все проверки ([⚙️ реализация](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/router.py#L103-L165))
  - Хендлеры регистрации (ты новичок), чтоб поставить изначальные настройки типа твоей группы, хочешь ли ты рассылку и добавить Zoom данные ([⚙️ хендлеры](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/bps/init.py))
  - Хендлеры хаба (ты уже смешарик), чтоб смотреть расписание, полезные ссылки и изменять настройки ([⚙️ хендлеры](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/bps/hub.py))
  - Хендлеры Zoom данных (ты добавляешь Zoom преподов), чтоб добавить препода, ссылку, ID, пароль и заметки к нему ([⚙️ хендлеры](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/bps/zoom.py))
- [**Навигация**](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/navigator.py)
  - Кнопки Назад и Далее ([➕ авто добавление кнопок](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/keyboard.py#L270-L280), [⚙️ реализация кнопки Назад](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/bps/__init__.py#L83-L86))
  - Форматирование этапов во время регистраци, чтоб юзер знал насколько это затянется ([🖌️ форматтер](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/states/formatter.py#L38-L145))
  - Распределение больших данных по страницам для Zoom данных в нашем случае ([⚙️ реализация](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/pagination.py#L54-L165))
- [**Хранилище Zoom**](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/data/zoom.py)
  - Возможность добавить/изменить/удалить запись вручную ([⛏️ выбор записи](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/bps/zoom.py#L418-L429), [✏️ изменение поля записи](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/bps/zoom.py#L65-L155))
  - Возможность добавить много записей из одного сообщения пользователя ([🤓 парсер сообщения](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/parse/zoom.py#L223-L234))
  - Предупреждения насчёт возможно неправильном формате данных ([✔️ проверки](https://github.com/kerdl/ktmuslave/blob/master/src/data/zoom.py#L149-L156), [⚠️ всевозможные предупреждения](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/data/__init__.py#L123-L156))
  - Возможность дампа всех данных в текст, который можно загрузить в другом чате ([💾 кнопка дампа](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/bps/zoom.py#L452), [💥 что происходит при нажатии](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/bps/zoom.py#L15-L26))
  - Куча кросивого форматирования текста ([🖌️ форматтер](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/data/zoom.py#L244-L255))
- **Расписание**
  - Рассылка при любых изменениях, полученных с WebSocket сервера ([🔄 луп событий](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/api/schedule.py#L310-L365))
  - Форматирование изменений, какой день, предмет и данные внутри него изменились ([🖌️ форматтер](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/data/schedule/format.py#L245-L315))
  - Ответ на предыдущее сообщение с расписанием чтоб быстро посмотреть историю расписания ([↩️ условия ответа](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/__init__.py#L208-L226))
  - Возможность вручную начать глобальное обновление расписания, если кто-то заметил изменения между 10 минутным периодом автообновления ([🔄 кнопка обновления](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/bps/hub.py#L114), [💥 что происходит при нажатии](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/svc/common/bps/hub.py#L20-L59))
  - Куча кросивого форматирования текста ([🖌️ форматтер](https://github.com/kerdl/ktmuslave/blob/b8c733216cb7c889a9ee21f4d7a20439639d82d2/src/data/schedule/format.py#L208-L238))
- **Другое**
  - Уведомление админа бота в случае рейза какого-либо исключения ([⚙️ реализация](https://github.com/kerdl/ktmuslave/blob/e7990a044526435c49471ed8be06871ce0c50384/src/__init__.py#L61-L75))
