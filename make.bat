@echo off

rem Exibe todas as tarefas
if "%1" == "" (
echo Available commands:
echo * clean
echo * setup
echo * unit-tests
goto :EOF
)

rem Run cleanup of tmp files
if "%1" == "clean" (
call :clean
goto :EOF
)

rem creates virtual environment and install dependencies
if "%1" == "setup" (
call :setup
goto :EOF
)

rem Run usual unit-tests with coverage
if "%1" == "unit-tests" (
call :unit-tests
goto :EOF
)

rem Run tests against all supported python versions
if "%1" == "tox-tests" (
call :tox-tests
goto :EOF
)

if "%1" == "type-checking" (
call :type-checking
goto :EOF
)

if "%1" == "pep-checking" (
call :pep-checking
goto :EOF
)


:clean
echo executing cleanup ...
del /s /q *.pytest_cache
del /s /q *.log
del /s /q *.coverage
del /s /q *.gz
del /s /q .mypy_cache
rmdir /s /q .tox
rmdir /s /q build
rmdir /s /q dist
rmdir /s /q rosreestr2coord.egg-info
echo done cleaning up
goto :EOF

:setup
echo executing setup...
call poetry build
call poetry install -v
call poetry shell
echo done setting up
goto :EOF

:unit-tests
echo executing unit tests...
call poetry run pytest --cov=rosreestr2coord -o log_cli=true --log-cli-level=INFO tests\
echo done unit testing
goto :EOF

:tox-tests
echo executing tox tests...
call poetry run tox
echo done tox-testing
goto :EOF

:type-checking
echo executing type-checking...
call poetry run mypy --config-file pyproject.toml rosreestr2coord tests\
echo done type-checking
goto :EOF

:pep-checking
echo executing pep-checking...
set "format=^"%%^(path^)s:%%^(row^)d:%%^(col^)d: %%^(text^)s"
call poetry run flake8 --format=%%format%% ./rosreestr2coord
echo done pep-checking
goto :EOF
