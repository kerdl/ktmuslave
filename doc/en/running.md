# Running
**ktmuslave** works on Windows and Linux.

Virtualization through Docker is available.



## Contents
- [Docker on Debian-based Linux](#docker-on-debian-based-linux)
- [Windows](#windows)
- [Debian-based Linux](#debian-based-linux)


## Docker on Debian-based Linux
1. Install Docker using
[instructions for your platform](https://docs.docker.com/engine/install/)
2. Install **git**
```console
sudo apt update && sudo apt install git -y
```
3. Clone the repo
```console
git clone https://github.com/kerdl/ktmuslave
```
4. Go to the directory
```console
cd ktmuslave
```
5. Create folders
```console
mkdir -p data/docker/ktmuscrap/schedule/
mkdir -p data/docker/ktmuslave/
```
6. Create and fill in the configuration files
`index.json` ([example](https://github.com/kerdl/ktmuscrap/blob/yr2024/doc/en/configuring.md#schedules-example),
[documentation](https://github.com/kerdl/ktmuscrap/blob/yr2024/doc/en/configuring.md#schedules))
```console
nano data/docker/ktmuscrap/schedule/index.json
nano data/docker/ktmuslave/settings.json
```
7. Run
```console
sudo docker compose -f docker-compose.yml up --build -d
```


## Windows
1. Install
[Python 3.12](https://www.python.org/downloads/release/python-3127/)
2. Install and run
[Redis](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/install-redis-on-windows/)
with
[RedisJSON](https://github.com/RedisJSON/RedisJSON)
and
[RediSearch](https://github.com/RediSearch/RediSearch)
modules.
3. Install and run
[ktmuscrap](https://github.com/kerdl/ktmuscrap/blob/yr2024/doc/en/running.md#windows)
4. Download and unpack the repo,
or use **git**
```console
git clone https://github.com/kerdl/ktmuslave
```
5. Go to the code directory or open a **cmd** there
```console
cd ktmuslave-yr2024
```
or
```console
cd ktmuslave
```
6. Create venv
```console
python3.12 -m venv .venv
```
7. Switch to venv
```console
.venv\Scripts\activate
```
8. Install dependencies
```console
pip3.12 install -r requirements.txt
```
9. Create `data` folder and a `settings.json` file in it
```console
mkdir data
copy NUL data\settings.json
```
10. Fill in the `settings.json` file
([example](/doc/en/configuring.md#settings-example), 
[documentation](/doc/en/configuring.md#settings))
9. Run
```console
python src
```


## Debian-based Linux
1. Install
[Python 3.12](https://wiki.crowncloud.net/?How_to_Install_Python_3_12_on_Debian_12)
2. Install and run
[Redis](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/install-redis-on-linux/)
with
[RedisJSON](https://github.com/RedisJSON/RedisJSON)
and
[RediSearch](https://github.com/RediSearch/RediSearch)
modules
3. Install and run
[ktmuscrap](https://github.com/kerdl/ktmuscrap/blob/yr2024/doc/en/running.md#debian-based-linux)
4. Install **git**
```console
sudo apt update && sudo apt install git -y
```
5. Clone the repo
```console
git clone https://github.com/kerdl/ktmuslave
```
6. Go to the directory
```console
cd ktmuslave
```
7. Create venv
```console
python3.12 -m venv .venv
```
8. Switch to venv
```console
.venv/bin/activate
```
9. Install dependencies
```console
pip3.12 install -r requirements.txt
```
10. Create `data` folder
```console
mkdir data
```
11. Create and fill in the configuration file
`settings.json`
([example](/doc/en/configuring.md#settings-example),
[documentation](/doc/en/configuring.md#settings))
```console
nano data/settings.json
```
12. Run
```console
python src
```