@echo off
setlocal
title Home-Assistant-Wiki aktualisieren
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\publish_to_pi.ps1"
if errorlevel 1 (
  echo.
  echo Die Aktualisierung ist fehlgeschlagen. Die Fehlermeldung steht oben.
) else (
  echo.
  echo Das Wiki wurde erfolgreich aktualisiert.
)
echo.
pause
