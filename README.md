[🇬🇧 English](/README-EN.md)

# KTMU slave

[В VK](https://vk.com/ktmuslave)

[В Telegram](https://t.me/ktmuslave_bot)

Бот для расписания с https://ktmu-sutd.ru/

- все кнопочки, сообщения, этапы, навигация,
форматирование расписания - это всё здесь,
в этом коде
- но помимо этого есть ещё и главный сок - 
сервер-конвертер расписания,
который из сырых таблиц с сайта делает
более удобный для бота формат - JSON.
Без него сам бот - хуйня из-под коня

# Зависит от
[ktmuscrap](https://github.com/kerdl/ktmuscrap) - сам сервер-конвертер,
запускается отдельно от бота. Бот автоматически подключается к нему,
получает последнее конвертированное расписание и ожидает событий обновления.

# sus sus imposto amog sus
В дальнейшем буду добавлять новую хуйню
и исправлять говно, которое написал щас, лишь бы побыстрее закончить

Все запланированные фиксы/фичи в [Issues](https://github.com/kerdl/ktmuslave/issues)

# Як примерно работает

- Недо-база данных (сохранение класса контекстов через pickle, ПОТОМУ ЧТО МНЕ ЩАС ПОЕБАТЬ)

- Взаимодействие с ботом **(Python)**
     - Хранилище данных (текущий этап пользователя, его настройки, данные Zoom и т.д.)
     - Работа в отдельных мессенджерах
          - VK
          - Telegram
     - Условия обработки входящих сообщений (например, игнорить, если бот в беседе и его не упомянули)
     - Навигация
          - Форматирование дЕрЕвА пройденных этапов


          ![wise mystical tree](https://i.kym-cdn.com/photos/images/newsfeed/002/444/748/d04.jpg)
          - Кнопки "назад", "далее"
     - Просмотр больших данных по разделённым страницам (для Zoom данных)
     - Режим первоначальной настройки
          - Ввод группы
          - Простые вопросы по рассылке расписания и его закрепу
     - Режим добавления ссылок на Zoom
          - Форматирование данных в красивый текст
          - Вытаскивание всех данных из большого текста
          - Редактирование и добавление по отдельности
          - Предупреждения о неправильном формате данных
     - Режим просмотра расписания
          - Форматирование расписания в красивый текст с ссылками
          - Изменение настроек
     - Миллион хуйни чтобы удобно работать с расписанием от сервера на Rust
     - Возможность глобально обновлять расписание через кнопку "Обновить"
     - Рассылка при изменении расписания

- Расписание **(Rust)**
     - Скачивание расписания
     - Таймер на обновление каждые **10 минут**
     - Понимание расписания
          - Паттерны для поиска в тексте
               - **Групп** (1кдд69),
               - **Дат** (11.09.02),
               - **Времени** (7:00-8:00),
               - **Преподов** (Ебанько Х.Й.),
               - **Аудиторий** (ауд.69, ауд.69б, ауд.69,78...)
          - Конвертация в **JSON**
               - **Очного** из .docx документа
               (ВИ ОХУЕЛИ?? ПОЧМУ РАНШЕ НА САЙТЕ БЫЛО А ТЕПЕРЬ DOCX??? С\*УКА БЛЯ\*ТЬ 🤬)
                    - Поиск группы в заголовке таблицы
                    - Поиск периода даты этого расписания в заголовке таблицы
                    - Соотношение дней недели с парами
                    - Соотношение пар с номерами, временем пар и днями недели
                    - Вызерание аудитории(-й) из ячейки с конца
                    - Вырезание препода(-ов) из ячейки с конца
                    - Сохранение всей инфы в структуры
               - **Дистанта** из Google-таблиц
                    - Определение базовой даты (когда расписание начинается)
                    - Определение последнего листа с расписанием
                    - Получение всех строк групп
                    - Разделение строки группы по дням недели сверху
                    - Вырезание дат из дней недели сверху
                    - Соотношение предмета (в строке группы) с номером и временем пары (в самом верху)
                    - Вырезание времени и номера пар из ячеек сверху
                    - Вырезание препода из ячейки предмета
                    - Сохранение всей инфы в структуры
               - Объединение расписания (`очное дневное с дистант неделя`, `очное недельное с дистант неделя`)
                    - Проверка, что оба расписания принадлежат одной неделе
                    - Объединение двух структур
                        - Групп
                        - Дней внутри группы
                        - Предметов внутри дня
               - Сравнение расписания
                    - Определение появившихся, удалившихся и изменившихся:
                        - Групп
                        - Дней
                        - Предметов
                        - Данных внутри предмета
     - Интерфейс для связи Rust с Python (API)
          - Получение расписания через GET (при каждом включении бота)
          - Глобальное обновление расписания через POST (при нажатии кнопки "Обновить" в боте)
          - Получение уведомлений о изменениях через WebSocket (для рассылки изменений расписания)
          - Получение глобальных параметров сервера-конвертера (какие ссылки скачивает, какой период обновления)
