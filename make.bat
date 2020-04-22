@echo off

rem Exibe todas as tarefas
if "%1" == "" (
echo Available commands:
echo * clean
echo * setup
echo * unit-tests
goto :EOF
)

rem Execute cleanup of tmp files
if "%1" == "clean" (
call :clean
goto :EOF
)

rem Execute poetry setup
if "%1" == "setup" (
call :setup
goto :EOF
)

rem Execute unit-tests
if "%1" == "unit-tests" (
call :unit-tests
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
call poetry run pytest --cov=rosreestr2coord -o log_cli=true --log-cli-level=INFO tests/
echo done unit testing
goto :EOF
