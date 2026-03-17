#!/bin/bash
# 编译 macOS 版 .dylib
# 用法: ./build_macos.sh

echo "开始编译 macOS 版..."

# 检查 Cython
if ! command -v cython &> /dev/null; then
    echo "安装 Cython..."
    pip install cython
fi

# 编译 Cython
echo "编译 indicators_v2.py..."
cython -3 indicators_v2.py

# 编译 .dylib
echo "编译 .dylib..."
gcc -shared -pthread -fPIC \
    -I$(python -c "import sysconfig; print(sysconfig.get_path('include'))") \
    -o indicators_v2.cpython-$(python3 -c 'import sys; print(f"{sys.version_info.major}{sys.version_info.minor}")')-darwin.so \
    indicators_v2.c

echo "完成!"
ls -la *.so *.dylib 2>/dev/null
