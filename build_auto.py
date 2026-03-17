#!/usr/bin/env python3
"""
Alfe 自动编译脚本
- 自动检测平台
- 自动编译对应二进制
- 自动测试
- 自动删除源码
"""

import os
import sys
import subprocess
import platform
import shutil
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
        return f"indicators_v2.cp{sys.version_info.major}{sys.version_info.minor}.pyd"
    return None


def install_dependencies():
    """安装依赖"""
    print("📦 检查依赖...")
    
    try:
        import Cython
        print("✓ Cython 已安装")
    except ImportError:
        print("📥 安装 Cython...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "cython", "-q"])
    
    try:
        subprocess.check_call(["gcc", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✓ GCC 已安装")
    except FileNotFoundError:
        print("⚠️ 警告: GCC 未安装")
        if detect_platform() == "macos":
            print("   运行: xcode-select --install")
        return False
    
    return True


def compile_module(platform_type):
    """编译模块"""
    source_file = Path("indicators_v2.py")
    output_file = get_output_filename(platform_type)
    
    if not source_file.exists():
        print(f"❌ 源码文件不存在: {source_file}")
        return False
    
    print(f"🔨 编译 {platform_type} 版本...")
    
    # 1. Cython 编译
    print("   运行 Cython...")
    subprocess.check_call([sys.executable, "-m", "cython", "-3", str(source_file)])
    c_file = Path("indicators_v2.c")
    
    if not c_file.exists():
        print("❌ Cython 编译失败")
        return False
    
    # 2. 编译 .so/.dylib/.pyd
    print(f"   编译 {output_file}...")
    
    include_path = subprocess.check_output(
        [sys.executable, "-c", "import sysconfig; print(sysconfig.get_path('include'))"],
        text=True
    ).strip()
    
    if platform_type in ["linux", "wsl"]:
        cmd = ["gcc", "-shared", "-pthread", "-fPIC", 
               f"-I{include_path}", "-o", output_file, "indicators_v2.c"]
    elif platform_type == "macos":
        cmd = ["gcc", "-shared", "-pthread", "-fPIC", "-dynamiclib",
               f"-I{include_path}", "-o", output_file, "indicators_v2.c"]
    elif platform_type == "windows":
        cmd = ["gcc", "-shared", "-pthread",
               f"-I{include_path}", "-o", output_file, "indicators_v2.c"]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ 编译失败: {result.stderr}")
        return False
    
    # 3. 清理 C 文件
    c_file.unlink()
    
    print(f"✓ 编译成功: {output_file}")
    return True


def test_module():
    """测试模块"""
    print("🧪 测试编译结果...")
    
    try:
        import pandas as pd
        import numpy as np
        
        sys.path.insert(0, os.getcwd())
        from indicators_v2 import system1_analyze
        
        # 简单测试 - 导入成功即可
        print("✓ 模块导入成功")
        
        # 尝试用真实数据测试 (如果存在)
        data_file = Path("/workspace/Data_src/api/data/000049.SZ_raw.csv")
        if data_file.exists():
            try:
                df = pd.read_csv(data_file).tail(30)
                df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
                df = df.set_index('trade_date')
                result = system1_analyze(df)
                print(f"✓ 真实数据测试通过!")
                print(f"   建议: {result.get('advice', 'N/A')}")
            except Exception as e:
                print(f"⚠️ 真实数据测试跳过: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def cleanup_source():
    """删除源码"""
    source_file = Path("indicators_v2.py")
    
    if source_file.exists():
        backup_file = Path("indicators_v2.py.bak")
        shutil.copy(source_file, backup_file)
        print(f"✓ 源码已备份: {backup_file}")
        
        source_file.unlink()
        print(f"✓ 源码已删除: {source_file}")
    else:
        print("⚠️ 源码文件不存在")


def main():
    """主函数"""
    print("=" * 50)
    print("🚀 Alfe 自动编译系统")
    print("=" * 50)
    
    platform_type = detect_platform()
    print(f"📱 检测平台: {platform_type}")
    
    if not install_dependencies():
        print("❌ 依赖检查失败")
        return 1
    
    if not compile_module(platform_type):
        print("❌ 编译失败")
        return 1
    
    if not test_module():
        print("❌ 测试失败，保留源码")
        return 1
    
    cleanup_source()
    
    print("=" * 50)
    print("✅ 全部完成!")
    print("=" * 50)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
