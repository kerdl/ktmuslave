# Запуск
**ktmuslave** работает на Windows и Linux.

Доступна виртуализация через Docker.


## Содержание
- [Docker под Debian-based Linux](#docker-под-debian-based-linux)
- [Windows](#windows)
- [Debian-based Linux](#debian-based-linux)


## Docker под Debian-based Linux
1. Установи Docker по
[инструкции для твоей платформы](https://docs.docker.com/engine/install/)
2. Установи **git**
```console
sudo apt update && sudo apt install git -y
```
3. Склонируй репозиторий
```console
git clone https://github.com/kerdl/ktmuslave
```
4. Перейди в директорию
```console
cd ktmuslave
```
5. Создай папки
```console
mkdir -p data/docker/ktmuscrap/schedule/
mkdir -p data/docker/ktmuslave/
```
6. Создай и заполни конфигурационные файлы
`index.json` ([пример](https://github.com/kerdl/ktmuscrap/blob/yr2024/doc/ru/configuring.md#пример-расписаний),
[документация](https://github.com/kerdl/ktmuscrap/blob/yr2024/doc/ru/configuring.md#расписания))
и
`settings.json` ([пример](/doc/ru/configuring.md#пример-настроек),
[документация](/doc/ru/configuring.md#настройки))
```console
nano data/docker/ktmuscrap/schedule/index.json
nano data/docker/ktmuslave/settings.json
```
7. Запусти
```console
sudo docker compose -f docker-compose.yml up --build -d
```


## Windows
1. Установи
[Python 3.12](https://www.python.org/downloads/release/python-3127/)
2. Установи и запусти
[Redis](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/install-redis-on-windows/)
с модулями
[RedisJSON](https://github.com/RedisJSON/RedisJSON)
и
[RediSearch](https://github.com/RediSearch/RediSearch)
3. Установи и запусти
[ktmuscrap](https://github.com/kerdl/ktmuscrap/blob/yr2024/doc/ru/running.md#windows)
4. Скачай и распакуй репозиторий,
либо воспользуйся **git**
```console
git clone https://github.com/kerdl/ktmuslave
```
5. Перейди в директорию с кодом или открой там **cmd**:
```console
cd ktmuslave-yr2024
```
или
```console
cd ktmuslave
```
6. Создай виртуальное окружение
```console
python3.12 -m venv .venv
```
7. Переключись на виртуальное окружение
```console
.venv\Scripts\activate
```
8. Установи зависимости
```console
pip3.12 install -r requirements.txt
```
9. Создай папку `data` и файл `settings.json` в ней
```console
mkdir data
copy NUL data\settings.json
```
10. Заполни файл `settings.json`
([пример](/doc/ru/configuring.md#пример-настроек),
[документация](/doc/ru/configuring.md#настройки))
9. Запусти
```console
python src
```


## Debian-based Linux
1. Установи
[Python 3.12](https://wiki.crowncloud.net/?How_to_Install_Python_3_12_on_Debian_12)
2. Установи и запусти
[Redis](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/install-redis-on-linux/)
с модулями
[RedisJSON](https://github.com/RedisJSON/RedisJSON)
и
[RediSearch](https://github.com/RediSearch/RediSearch)
3. Установи и запусти
[ktmuscrap](https://github.com/kerdl/ktmuscrap/blob/yr2024/doc/ru/running.md#debian-based-linux)
4. Установи **git**
```console
sudo apt update && sudo apt install git -y
```
5. Склонируй репозиторий
```console
git clone https://github.com/kerdl/ktmuslave
```
6. Перейди в директорию
```console
cd ktmuslave
```
7. Создай виртуальное окружение
```console
python3.12 -m venv .venv
```
8. Переключись на виртуальное окружение
```console
.venv/bin/activate
```
9. Установи зависимости
```console
pip3.12 install -r requirements.txt
```
10. Создай папку `data`
```console
mkdir data
```
11. Создай и заполни конфигурационный файл
`settings.json` ([пример](/doc/ru/configuring.md#пример-настроек),
[документация](/doc/ru/configuring.md#настройки))
```console
nano data/settings.json
```
12. Запусти
```console
python src
```