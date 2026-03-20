@echo off
title CyberCafe - Servicio
:loop
python C:\cybercafe\main.py
timeout /t 2 /nobreak >nul
goto loop