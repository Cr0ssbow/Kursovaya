@echo off
echo Настройка PostgreSQL для приложения ЧОП Легион...
echo.

echo 1. Проверяем, запущен ли PostgreSQL...
sc query postgresql-x64-16 >nul 2>&1
if %errorlevel% neq 0 (
    echo PostgreSQL не найден. Убедитесь, что PostgreSQL установлен.
    echo Скачайте PostgreSQL с https://www.postgresql.org/download/windows/
    pause
    exit /b 1
)

echo 2. Создаем базу данных...
echo Введите пароль для пользователя postgres:
psql -U postgres -h localhost -c "CREATE DATABASE legion_employees WITH OWNER = postgres ENCODING = 'UTF8';"

if %errorlevel% equ 0 (
    echo База данных legion_employees успешно создана!
) else (
    echo Ошибка создания базы данных или база уже существует.
)

echo.
echo 3. Установка зависимостей Python...
pip install psycopg2-binary python-dotenv

echo.
echo Настройка завершена!
echo Теперь можно запускать приложение: python src/main.py
pause