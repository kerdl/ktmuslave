# Configuring
**ktmuslave** uses 1 configuration file.


## Contents
- [Settings](#settings)
- [Settings example](#settings-example)


## Settings
File: `./data/settings.json`
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
Tokens for running the bot.
You can either use one of them or both.

### `server`
[ktmuscrap](https://github.com/kerdl/ktmuscrap)
server configuration.

#### `server.addr`
Server address.

### `database`
[Redis](https://redis.io/)
database configuration.

#### `database.addr`
Database address.

#### `database.password`
Database password.

### `logging`
Configuration of persisting logs on disk.

#### `logging.enabled`
Is logging ebabled.

#### `logging.dir`
Path to the directory, where the logs
will be saved.

**Example**:
```json
"dir": "./data/log"
```

#### `logging.admins`
IDs of users, who'll get messages about
occured errors.

**Object**:
```json
{
  "id": 0,
  "src": "vk | tg"
}
```

**Example**:
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
URLs to materials that are shown as buttons
in hub.

If URLs are not specified,
the corresponding buttons will be hidden.

#### `urls.schedules`
URL of the "Schedules" ("Расписания") button.

#### `urls.journals`
URL of the "Journals" ("Журналы") button.

#### `urls.materials`
URL of the "Materials" ("Материалы") button.

### `time`
Configuration of time schedule.

Responsible for showing time
in the bot's schedule.
The ranges are searched here
by subject number.

#### `time.schedules`
Time schedules.

**Object**:
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
Mapping the schedule to a day of the week.

**Object**:
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

**Example**:
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


## Settings example
File: `./data/settings.json`
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