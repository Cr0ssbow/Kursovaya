@echo off
echo Запуск PostgreSQL и создание базы данных...

echo 1. Запуск службы PostgreSQL...
net start postgresql-x64-16

echo 2. Создание базы данных legion_employees...
createdb -U postgres legion_employees

echo 3. Запуск приложения...
cd src
python main.py

pause