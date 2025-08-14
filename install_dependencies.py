#!/usr/bin/env python3
"""
联通用户权益领取系统 - 依赖安装脚本
自动安装必要的依赖包，无需adb-shell
"""

import subprocess
import sys
import os

def install_package(package_name):
    """安装Python包"""
    try:
        print(f"📦 安装 {package_name}...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", package_name
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {package_name} 安装成功")
            return True
        else:
            print(f"❌ {package_name} 安装失败:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ 安装 {package_name} 时出现异常: {str(e)}")
        return False

def check_and_install_streamlit():
    """检查并安装Streamlit"""
    try:
        import streamlit
        print("✅ Streamlit 已安装")
        return True
    except ImportError:
        print("📥 Streamlit 未安装，正在安装...")
        return install_package("streamlit")

def check_adb():
    """检查ADB可用性"""
    print("\n🔍 检查ADB...")
    
    # 检查本地adb.exe
    if os.path.exists("./platform-tools/adb.exe"):
        print("✅ 找到本地 ADB: ./platform-tools/adb.exe")
        return True
    
    # 检查系统PATH中的adb
    try:
        result = subprocess.run(['adb', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 找到系统 ADB")
            return True
    except FileNotFoundError:
        pass
    
    print("⚠️  未找到ADB")
    print("💡 解决方案:")
    print("   1. platform-tools/adb.exe 已包含在项目中")
    print("   2. 或者安装Android SDK并添加到系统PATH")
    return False

def main():
    """主安装函数"""
    print("🚀 联通用户权益领取系统 - 依赖安装")
    print("=" * 50)
    
    success = True
    
    # 检查Python版本
    print(f"🐍 Python版本: {sys.version}")
    if sys.version_info < (3, 7):
        print("❌ 需要Python 3.7或更高版本")
        return False
    
    # 安装Streamlit
    if not check_and_install_streamlit():
        success = False
    
    # 检查ADB
    if not check_adb():
        print("⚠️  ADB检查未通过，但可以继续使用本地ADB")
    
    print("\n" + "=" * 50)
    if success:
        print("✅ 依赖安装完成！")
        print("\n🎯 下一步:")
        print("   python launch_benefits_system.py")
        
        # 询问是否立即启动
        try:
            choice = input("\n是否立即启动系统？ (y/n): ").lower().strip()
            if choice in ['y', 'yes', '是']:
                print("\n🚀 启动系统...")
                os.system("python launch_benefits_system.py")
        except KeyboardInterrupt:
            print("\n👋 用户取消")
    else:
        print("❌ 部分依赖安装失败")
        print("请检查网络连接并重试")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 安装被用户中断")
    except Exception as e:
        print(f"\n❌ 安装过程中出现异常: {str(e)}")



