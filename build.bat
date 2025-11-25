@echo off
echo Сборка exe файла...
pyinstaller build.spec --clean --noconfirm
echo Готово! Exe файл находится в папке dist/
pause