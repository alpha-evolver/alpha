#!/bin/bash
# Build macOS .dylib
# Usage: ./build_macos.sh

echo "Starting macOS build..."

# Check Cython
if ! command -v cython &> /dev/null; then
    echo "Installing Cython..."
    pip install cython
fi

# Compile Cython
echo "Compiling indicators_v2.py..."
cython -3 indicators_v2.py

# Compile .dylib
echo "Compiling .dylib..."
gcc -shared -pthread -fPIC \
    -I$(python -c "import sysconfig; print(sysconfig.get_path('include'))") \
    -o indicators_v2.cpython-$(python3 -c 'import sys; print(f"{sys.version_info.major}{sys.version_info.minor}")')-darwin.so \
    indicators_v2.c

echo "Done!"
ls -la *.so *.dylib 2>/dev/null
