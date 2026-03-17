@echo off
REM 编译 Windows 版 .pyd
REM 用法: build_windows.bat

echo 开始编译 Windows 版...

REM 安装 Cython
pip install cython

REM 编译 Cython
echo 编译 indicators_v2.py...
cython -3 indicators_v2.py

REM 编译 .pyd
echo 编译 .pyd...
set PYTHON_INCLUDE=C:\Python310\include
gcc -shared -pthread -shared ^
    -I%PYTHON_INCLUDE% ^
    -o indicators_v2.cp310.pyd ^
    indicators_v2.c

echo 完成!
dir *.pyd
pause
