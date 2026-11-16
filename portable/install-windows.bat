@echo off
rem Install LakeMark on this Windows computer, from the USB stick: double-click this file.
rem
rem Makes Documents\LakeMark, laid out like the LakeMark folder on the stick:
rem
rem     lakemark.exe     the program
rem     output\          the web pages you export
rem     system\          settings, and a folder for each club
rem
rem and puts LakeMark on the desktop and in the Start menu. A new installation gets the clubs
rem from the stick. If this computer already has LakeMark data, only the program is replaced:
rem the data on the computer is left alone, as it may be newer than the stick's.
rem Run it again from a newer stick to update the program.

setlocal
set "stick=%~dp0"
if not exist "%stick%lakemark.exe" goto no_program

rem Documents may have been moved, to OneDrive say: ask Windows where it is.
set "docs="
for /f "usebackq delims=" %%d in (`powershell -NoProfile -Command "[Environment]::GetFolderPath('MyDocuments')"`) do set "docs=%%d"
if not defined docs set "docs=%USERPROFILE%\Documents"
set "LAKEMARK=%docs%\LakeMark"

echo Installing LakeMark in %LAKEMARK%
echo.
if not exist "%LAKEMARK%\system" mkdir "%LAKEMARK%\system"
if not exist "%LAKEMARK%\output" mkdir "%LAKEMARK%\output"
copy /y "%stick%lakemark.exe" "%LAKEMARK%\lakemark.exe" >nul || goto cannot_copy
if exist "%stick%system\README.txt" copy /y "%stick%system\README.txt" "%LAKEMARK%\system\" >nul

if exist "%LAKEMARK%\system\properties.xml" goto keep_data
xcopy "%stick%system" "%LAKEMARK%\system" /e /i /q /y >nul || goto cannot_copy
if exist "%LAKEMARK%\system\start-linux.sh" del "%LAKEMARK%\system\start-linux.sh"
echo Copied the settings and the clubs from the stick.
goto shortcuts

:keep_data
echo This computer already has LakeMark data: it is left as it is, and only the program
echo is updated. To bring a club over from the stick, use File, Import club.

:shortcuts
powershell -NoProfile -Command "$shell = New-Object -ComObject WScript.Shell; foreach ($folder in 'Desktop', 'Programs') { $link = $shell.CreateShortcut([Environment]::GetFolderPath($folder) + '\LakeMark.lnk'); $link.TargetPath = $env:LAKEMARK + '\lakemark.exe'; $link.WorkingDirectory = $env:LAKEMARK; $link.Save() }"
if errorlevel 1 (echo Could not make the shortcuts: start LakeMark from the LakeMark folder in Documents.) else (echo Put LakeMark on the desktop and in the Start menu.)

echo.
echo Done. Start LakeMark from the desktop. You can unplug the stick: the computer has its
echo own copy now, and the results you enter there stay on the computer.
echo.
choice /m "Start LakeMark now"
if errorlevel 2 goto end
start "" "%LAKEMARK%\lakemark.exe"
goto end

:no_program
echo Cannot find lakemark.exe beside this file. Run install-windows.bat from the LakeMark
echo folder on the stick.
pause
goto end

:cannot_copy
echo Could not copy the files to %LAKEMARK%.
echo If LakeMark is running, close it and try again.
pause

:end
endlocal
