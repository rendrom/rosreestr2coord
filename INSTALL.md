# INSTALL

## MacOS

Установка poetry

```bash
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python

source $HOME/.poetry/env
```

запуск выполнения

```bash
make setup
```

## Windows

### Подготовка окружения

#### Установка poetry

В командной строке Power Shell выполнить:

```bash
(Invoke-WebRequest -Uri https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py
 -UseBasicParsing).Content | python
```

Перезагрузить компьютер, или выйти/зайти.

#### Настройка виртуального окружения

Можно создать виртуальное окружение самостоятельно, активировать его, а затем установить зависимости с помощью poetry

```bash
git clone https://github.com/rendrom/rosreestr2coord
cd ./rosreestr2coord
# создание виртуального окружения
python -m venv ./.env
# активация виртуального окружения Linux and MacOS
. ./.env/bin/activate
# активация виртуального окружения для Windows
. ./.env/Scripts/activate
# установка зависимостей
make.bat setup
```

или же воспользоваться poetry, он всё сделает сам. Команда таже.

```bash
make.bat setup
```
