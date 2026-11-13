@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

echo ========================================
echo Запуск тестов Dependency Visualizer
echo ========================================
echo.

set "PYTHONPATH=%CD%\src"

python -m unittest discover -s tests -p "test_*.py" -v

if errorlevel 1 (
    echo.
    echo Обнаружены ошибки при выполнении тестов!
) else (
    echo.
    echo Все тесты успешно пройдены!
)

echo.
pause
endlocal