@echo off

pyside6-uic form.ui -o form.py
pyside6-rcc res.qrc -o res_rc.py
python main.py

pause