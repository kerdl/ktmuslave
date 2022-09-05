class State:
    name: str
    emoji: str


class InitMain(State):
    name = "Категорически приветствую"
    emoji = "🚽"

class HubMain(State):
    name = "Главная"
    emoji = "🚽"

class HubSettings(State):
    name = "Настройки"
    emoji = "🚽"

class Group(State):
    name = "Группа"
    emoji = "🚽"

class UnknownGroup(State):
    name = "Неизвестная группа"
    emoji = "🚽"

class ScheduleBroadcast(State):
    name = "Рассылка расписания"
    emoji = "🚽"

class ShouldPin(State):
    name = "Закреп расписания"
    emoji = "🚽"

class InitFinish(State):
    name = "ФИНААААЛ СУЧКИ"
    emoji = "🚽"