@echo off
REM Build Windows .pyd
REM Usage: build_windows.bat

echo Starting Windows build...

REM Install Cython
pip install cython

REM Compile Cython
echo Compiling indicators_v2.py...
cython -3 indicators_v2.py

REM Compile .pyd
echo Compiling .pyd...
set PYTHON_INCLUDE=C:\Python310\include
gcc -shared -pthread -shared ^
    -I%PYTHON_INCLUDE% ^
    -o indicators_v2.cp310.pyd ^
    indicators_v2.c

echo Done!
dir *.pyd
pause
