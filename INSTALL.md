# Windows

## Подготовка окружения

### Установка poetry

В командной строке Power Shell выполнить:

```bash
(Invoke-WebRequest -Uri https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py
 -UseBasicParsing).Content | python
```

Перезагрузить компьютер, или или выйти/зайти.

### Настройка виртуального окружения
Можно создать виртуальное окружение самостоятельнор, активировать его, а затем установить зависимости с помощью poetry

```bash
git clone https://github.com/rendrom/rosreestr2coord
cd ./rosreestr2coord
# создание виртуального окружения
python -v venv ./.env # or py -3 -v venv ./.env
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
