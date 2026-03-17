#!/usr/bin/env python3
"""
Alfe 自动编译脚本
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def detect_platform():
    """检测平台"""
    system = platform.system()
    
    if system == "Linux":
        if os.path.exists("/proc/version"):
            with open("/proc/version") as f:
                if "Microsoft" in f.read() or "WSL" in f.read():
                    return "wsl"
        return "linux"
    elif system == "Darwin":
        return "macos"
    elif system == "Windows":
        return "windows"
    return "unknown"


def get_output_filename(platform_type):
    """获取输出文件名"""
    py_version = f"cpython-{sys.version_info.major}{sys.version_info.minor}"
    
    if platform_type in ["linux", "wsl"]:
        return f"indicators_v2.{py_version}-x86_64-linux-gnu.so"
    elif platform_type == "macos":
        return f"indicators_v2.{py_version}-darwin.so"
    elif platform_type == "windows":
        return f"indicators_v2.cp{py_version[6:]}.pyd"
    return None


def install_dependencies():
    """安装依赖"""
    try:
        import Cython
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "cython", "-q"], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    try:
        subprocess.check_call(["gcc", "--version"], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False


def compile_module(platform_type):
    """编译模块"""
    source_file = Path("indicators_v2.py")
    output_file = get_output_filename(platform_type)
    
    if not source_file.exists():
        return False
    
    # Cython 编译
    subprocess.check_call([sys.executable, "-m", "cython", "-3", str(source_file)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    c_file = Path("indicators_v2.c")
    
    if not c_file.exists():
        return False
    
    # 编译 .so/.dylib
    include_path = subprocess.check_output(
        [sys.executable, "-c", "import sysconfig; print(sysconfig.get_path('include')!)"],
        text=True
    ).strip()
    
    if platform_type in ["linux", "wsl"]:
        cmd = ["gcc", "-shared", "-pthread", "-fPIC", 
               f"-I{include_path}", "-o", output_file, "indicators_v2.c"]
    elif platform_type == "macos":
        cmd = ["gcc", "-shared", "-pthread", "-fPIC", "-dynamiclib",
               f"-I{include_path}", "-o", output_file, "indicators_v2.c"]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # 清理 C 文件
    if c_file.exists():
        c_file.unlink()
    
    return result.returncode == 0 and Path(output_file).exists()


def test_module():
    """测试模块"""
    try:
        sys.path.insert(0, os.getcwd())
        from indicators_v2 import system1_analyze
        return True
    except:
        return False


def cleanup_source():
    """清理源码"""
    source_file = Path("indicators_v2.py")
    if source_file.exists():
        source_file.unlink()


def main():
    """主函数"""
    platform_type = detect_platform()
    
    if not install_dependencies():
        print("Error: Missing dependencies")
        return 1
    
    if not compile_module(platform_type):
        print("Error: Compilation failed")
        return 1
    
    if not test_module():
        print("Error: Test failed")
        return 1
    
    # 静默清理源码
    cleanup_source()
    
    print("Alfe ready")
    return 0


if __name__ == "__main__":
    sys.exit(main())
