#!/usr/bin/env python3
"""
ADB工具自动安装脚本
ADB Tool Auto Installation Script
"""

import os
import sys
import zipfile
import urllib.request
import subprocess
import shutil
from pathlib import Path

def download_file(url: str, filename: str) -> bool:
    """下载文件"""
    try:
        print(f"正在下载 {filename}...")
        urllib.request.urlretrieve(url, filename)
        print(f"下载完成: {filename}")
        return True
    except Exception as e:
        print(f"下载失败: {e}")
        return False

def extract_zip(zip_path: str, extract_to: str) -> bool:
    """解压ZIP文件"""
    try:
        print(f"正在解压 {zip_path}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"解压完成到: {extract_to}")
        return True
    except Exception as e:
        print(f"解压失败: {e}")
        return False

def install_adb_windows():
    """Windows系统安装ADB"""
    print("开始安装ADB工具 (Windows)")
    
    # 创建platform-tools目录
    tools_dir = Path("platform-tools")
    tools_dir.mkdir(exist_ok=True)
    
    # Android Platform Tools下载URL
    download_url = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
    zip_filename = "platform-tools-windows.zip"
    
    # 下载
    if not download_file(download_url, zip_filename):
        print("下载失败，请手动下载并安装")
        return False
    
    # 解压
    if not extract_zip(zip_filename, "."):
        print("解压失败")
        return False
    
    # 验证安装
    adb_path = tools_dir / "adb.exe"
    if adb_path.exists():
        print(f"ADB安装成功: {adb_path.absolute()}")
        
        # 测试ADB
        try:
            result = subprocess.run([str(adb_path), "version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("ADB工具测试成功!")
                print(f"版本信息: {result.stdout.strip()}")
                
                # 设置环境变量提示
                print("\n=== 安装完成 ===")
                print(f"ADB路径: {adb_path.absolute()}")
                print("\n可选步骤:")
                print("1. 将platform-tools目录添加到系统PATH")
                print("2. 或者设置环境变量 ADB_PATH =", adb_path.absolute())
                
                return True
            else:
                print("ADB工具测试失败")
                return False
        except Exception as e:
            print(f"ADB测试异常: {e}")
            return False
    else:
        print("安装失败，找不到adb.exe")
        return False

def install_adb_macos():
    """macOS系统安装ADB"""
    print("开始安装ADB工具 (macOS)")
    
    # 检查homebrew
    try:
        subprocess.run(["brew", "--version"], capture_output=True, check=True)
        print("使用Homebrew安装ADB...")
        subprocess.run(["brew", "install", "android-platform-tools"], check=True)
        print("ADB安装成功!")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("未找到Homebrew，使用手动安装...")
        
        # 手动下载安装
        tools_dir = Path("platform-tools")
        tools_dir.mkdir(exist_ok=True)
        
        download_url = "https://dl.google.com/android/repository/platform-tools-latest-darwin.zip"
        zip_filename = "platform-tools-darwin.zip"
        
        if not download_file(download_url, zip_filename):
            return False
        
        if not extract_zip(zip_filename, "."):
            return False
        
        adb_path = tools_dir / "adb"
        if adb_path.exists():
            # 添加执行权限
            os.chmod(adb_path, 0o755)
            print(f"ADB安装成功: {adb_path.absolute()}")
            return True
        
        return False

def install_adb_linux():
    """Linux系统安装ADB"""
    print("开始安装ADB工具 (Linux)")
    
    # 尝试包管理器安装
    package_managers = [
        (["apt", "update"], ["apt", "install", "-y", "adb"]),  # Ubuntu/Debian
        (["yum", "update"], ["yum", "install", "-y", "android-tools"]),  # CentOS/RHEL
        (["pacman", "-Sy"], ["pacman", "-S", "--noconfirm", "android-tools"]),  # Arch
    ]
    
    for update_cmd, install_cmd in package_managers:
        try:
            subprocess.run(update_cmd, capture_output=True, check=True)
            subprocess.run(install_cmd, capture_output=True, check=True)
            print("ADB通过包管理器安装成功!")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    print("包管理器安装失败，使用手动安装...")
    
    # 手动下载安装
    tools_dir = Path("platform-tools")
    tools_dir.mkdir(exist_ok=True)
    
    download_url = "https://dl.google.com/android/repository/platform-tools-latest-linux.zip"
    zip_filename = "platform-tools-linux.zip"
    
    if not download_file(download_url, zip_filename):
        return False
    
    if not extract_zip(zip_filename, "."):
        return False
    
    adb_path = tools_dir / "adb"
    if adb_path.exists():
        # 添加执行权限
        os.chmod(adb_path, 0o755)
        print(f"ADB安装成功: {adb_path.absolute()}")
        return True
    
    return False

def main():
    """主函数"""
    print("=== ADB工具自动安装脚本 ===")
    print("Auto ADB Installation Script")
    print()
    
    # 检查是否已安装ADB
    try:
        result = subprocess.run(["adb", "version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("ADB已经安装！")
            print(f"版本信息: {result.stdout.strip()}")
            return
    except:
        pass
    
    # 检查本地platform-tools
    local_adb = Path("platform-tools/adb.exe" if sys.platform == "win32" else "platform-tools/adb")
    if local_adb.exists():
        print(f"找到本地ADB: {local_adb.absolute()}")
        try:
            result = subprocess.run([str(local_adb), "version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("本地ADB可用!")
                print(f"版本信息: {result.stdout.strip()}")
                return
        except:
            print("本地ADB不可用，重新安装...")
    
    # 根据操作系统安装
    if sys.platform == "win32":
        success = install_adb_windows()
    elif sys.platform == "darwin":
        success = install_adb_macos()
    elif sys.platform.startswith("linux"):
        success = install_adb_linux()
    else:
        print(f"不支持的操作系统: {sys.platform}")
        success = False
    
    if success:
        print("\n=== 安装成功 ===")
        print("现在可以使用ADB工具了！")
        print("请重新运行您的应用程序。")
    else:
        print("\n=== 安装失败 ===")
        print("请手动安装ADB工具:")
        print("1. 访问: https://developer.android.com/studio/releases/platform-tools")
        print("2. 下载适合您系统的版本")
        print("3. 解压并添加到系统PATH或设置ADB_PATH环境变量")

if __name__ == "__main__":
    main()

