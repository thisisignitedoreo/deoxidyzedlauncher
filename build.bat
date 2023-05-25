@echo off

pyinstaller -w -F -y --noupx --clean -n DeoxidyzedLauncher -i assets/icon.ico main.py

pause