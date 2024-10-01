# Конфигурация
**ktmuslave** использует 1 файл конфигурации.


## Содержание
- [Настройки](#настройки)
- [Пример настроек](#пример-настроек)


## Настройки
Файл: `./data/settings.json`
```json
{
  "tokens": {
    "vk": null,
    "tg": null
  },
  "server": {
    "addr": "127.0.0.1:8080"
  },
  "database": {
    "addr": "127.0.0.1:6379",
    "password": null
  },
  "logging": {
    "enabled": false,
    "dir": null,
    "admins": []
  },
  "urls": {
    "schedules": null,
    "journals": null,
    "materials": null
  },
  "time": {
    "schedules": [],
    "mapping": {
      "monday": null,
      "tuesday": null,
      "wednesday": null,
      "thursday": null,
      "friday": null,
      "saturday": null,
      "sunday": null
    }
  }
}
```

### `tokens`
Токены группы для запуска бота.
Можно как один из вариантов, так и оба. 

### `server`
Конфигурация сервера
[ktmuscrap](https://github.com/kerdl/ktmuscrap).

#### `server.addr`
Адрес сервера.

### `database`
Конфигурация базы данных
[Redis](https://redis.io/).

#### `database.addr`
Адрес базы данных.

#### `database.password`
Пароль от базы данных.

### `logging`
Конфигурация сохранения логов на диск.

#### `logging.enabled`
Включено ли логгирование.

#### `logging.dir`
Путь до директории, где будут сохранятся логи.

**Пример**:
```json
"dir": "./data/log"
```

#### `logging.admins`
ID пользователей, которые получат сообщения
о возникших ошибках.

**Объект**:
```json
{
  "id": 0,
  "src": "vk | tg"
}
```

**Пример**:
```json
"admins": [
  {
    "id": 228133769,
    "src": "vk"
  },
  {
    "id": 228133769,
    "src": "tg"
  }
]
```

### `urls`
Ссылки на материалы, показывающиеся
как кнопки в хабе.

Если ссылки отсутствуют,
соответствующие кнопки будут скрыты.

#### `urls.schedules`
Ссылка кнопки "Расписания".

#### `urls.journals`
Ссылка кнопки "Журналы".

#### `urls.materials`
Ссылка кнопки "Материалы".

### `time`
Конфигурация расписания времени.

Отвечает за показ времени
в расписании бота.
Здесь ищется нужный диапазон
по номеру предмета.

#### `time.schedules`
Расписания времени.

**Объект**:
```json
{
  "name": "schedule-name",
  "nums": {
    "1": {
      "start": "00:00:00",
      "end": "01:00:00"
    }
  }
}
```

#### `time.mapping`
Назначение расписания на день недели.

**Объект**:
```json
{
  "monday": null,
  "tuesday": null,
  "wednesday": null,
  "thursday": null,
  "friday": null,
  "saturday": null,
  "sunday": null
}
```

**Пример**:
```json
"time": {
  "schedules": [
    {
      "name": "regular",
      "nums": {
        "1": {
          "start": "08:30:00",
          "end": "09:55:00"
        },
        "2": {
          "start": "10:20:00",
          "end": "11:45:00"
        },
        "3": {
          "start": "12:00:00",
          "end": "13:25:00"
        },
        "4": {
          "start": "13:55:00",
          "end": "15:20:00"
        },
        "5": {
          "start": "15:40:00",
          "end": "17:05:00"
        },
        "6": {
          "start": "17:15:00",
          "end": "18:40:00"
        }
      }
    },
    {
      "name": "saturday",
      "nums": {
        "1": {
          "start": "09:00:00",
          "end": "10:00:00"
        },
        "2": {
          "start": "10:10:00",
          "end": "11:10:00"
        },
        "3": {
          "start": "11:30:00",
          "end": "12:30:00"
        },
        "4": {
          "start": "12:50:00",
          "end": "13:50:00"
        },
        "5": {
          "start": "14:05:00",
          "end": "15:05:00"
        },
        "6": {
          "start": "15:15:00",
          "end": "16:15:00"
        }
      }
    }
  ],
  "mapping": {
    "monday": "regular",
    "tuesday": "regular",
    "wednesday": "regular",
    "thursday": "regular",
    "friday": "regular",
    "saturday": "saturday",
    "sunday": "regular"
  }
}
```


## Пример настроек
Файл: `./data/settings.json`
```json
{
  "tokens": {
    "vk": "vk1.x.XXXXXXXXXXXXXXXXXXXXXX",
    "tg": "0000000000:XXXXXXXXXXXXXXXXXXXXXXXXXX"
  },
  "server": {
    "addr": "127.0.0.1:8080"
  },
  "database": {
    "addr": "127.0.0.1:6379",
    "password": null
  },
  "logging": {
    "enabled": true,
    "dir": "./data/log",
    "admins": [
      {
        "id": "228133769",
        "src": "vk"
      },
      {
        "id": "228133769",
        "src": "tg"
      }
    ]
  },
  "urls": {
    "schedules": "https://drive.google.com/drive/folders/abcdef",
    "journals": "https://drive.google.com/drive/folders/ghijkl",
    "materials": "https://docs.google.com/document/d/mnopqr"
  },
  "time": {
    "schedules": [
      {
        "name": "regular",
        "nums": {
          "1": {
            "start": "08:30:00",
            "end": "09:55:00"
          },
          "2": {
            "start": "10:20:00",
            "end": "11:45:00"
          },
          "3": {
            "start": "12:00:00",
            "end": "13:25:00"
          },
          "4": {
            "start": "13:55:00",
            "end": "15:20:00"
          },
          "5": {
            "start": "15:40:00",
            "end": "17:05:00"
          },
          "6": {
            "start": "17:15:00",
            "end": "18:40:00"
          }
        }
      },
      {
        "name": "saturday",
        "nums": {
          "1": {
            "start": "09:00:00",
            "end": "10:00:00"
          },
          "2": {
            "start": "10:10:00",
            "end": "11:10:00"
          },
          "3": {
            "start": "11:30:00",
            "end": "12:30:00"
          },
          "4": {
            "start": "12:50:00",
            "end": "13:50:00"
          },
          "5": {
            "start": "14:05:00",
            "end": "15:05:00"
          },
          "6": {
            "start": "15:15:00",
            "end": "16:15:00"
          }
        }
      }
    ],
    "mapping": {
      "monday": "regular",
      "tuesday": "regular",
      "wednesday": "regular",
      "thursday": "regular",
      "friday": "regular",
      "saturday": "saturday",
      "sunday": "regular"
    }
  }
}
```