@echo off
set NAME=social-emperors_0.02a
pyinstaller --onefile --add-data "..\..\assets;assets" --add-data "..\..\flash;flash" --add-data "..\..\stub;stub" --add-data "..\..\templates;templates" --paths ..\..\. --workpath .\work --distpath .\dist --specpath .\bundle --noconfirm --name %NAME% ..\server.py
echo Done.
pause>NUL