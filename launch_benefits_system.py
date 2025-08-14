#!/usr/bin/env python3
"""
联通用户权益领取系统快速启动脚本
一键启动交互式Web界面
"""

import subprocess
import sys
import os
import time

def check_requirements():
    """检查系统要求"""
    print("🔍 检查系统要求...")
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("❌ 需要Python 3.7或更高版本")
        return False
    
    # 检查必要的包
    required_packages = ['streamlit']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少必要的包: {', '.join(missing_packages)}")
        print("请运行: pip install streamlit")
        return False
    
    # 检查ADB（优先使用本地adb.exe）
    adb_paths = ['./platform-tools/adb.exe', 'adb']
    adb_found = False
    
    for adb_path in adb_paths:
        try:
            result = subprocess.run([adb_path, 'version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ ADB已找到: {adb_path}")
                adb_found = True
                break
        except FileNotFoundError:
            continue
    
    if not adb_found:
        print("❌ 找不到ADB命令")
        print("💡 解决方案：")
        print("   1. 确保 platform-tools/adb.exe 存在")
        print("   2. 或安装Android SDK并添加到PATH")
        return False
    
    # 检查设备连接（使用找到的ADB路径）
    try:
        # 使用第一个找到的ADB路径
        adb_cmd = next(path for path in adb_paths 
                       if subprocess.run([path, 'version'], capture_output=True).returncode == 0)
        
        result = subprocess.run([adb_cmd, 'devices'], capture_output=True, text=True)
        devices = result.stdout.strip().split('\n')[1:]  # 跳过标题行
        connected_devices = [line for line in devices if line.strip() and 'device' in line]
        
        if connected_devices:
            print(f"✅ 找到 {len(connected_devices)} 台连接的设备")
        else:
            print("⚠️  未找到连接的Android设备")
            print("请确保设备已连接并开启USB调试")
    except Exception as e:
        print(f"⚠️  无法检查设备状态: {str(e)}")
    
    return True

def launch_streamlit():
    """启动Streamlit应用"""
    print("\n🚀 启动联通用户权益领取系统...")
    
    # 检查文件是否存在
    demo_file = "unicom_benefits_interactive_demo.py"
    if not os.path.exists(demo_file):
        print(f"❌ 找不到文件: {demo_file}")
        return False
    
    try:
        # 启动Streamlit
        print("🌐 正在启动Web界面...")
        print("📱 浏览器将自动打开 http://localhost:8501")
        print("💡 如果浏览器未自动打开，请手动访问上述地址")
        print("\n⚠️  注意: 请确保Android设备已连接并安装了联通APP")
        print("🔧 系统将在几秒钟后启动...")
        
        time.sleep(3)
        
        # 启动streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            demo_file,
            "--server.address", "0.0.0.0",
            "--server.port", "8501",
            "--server.headless", "false"
        ])
        
    except KeyboardInterrupt:
        print("\n\n👋 系统已停止")
    except Exception as e:
        print(f"❌ 启动失败: {str(e)}")
        return False
    
    return True

def show_help():
    """显示帮助信息"""
    print("""
📱 联通用户权益领取系统 - 快速启动指南

🎯 功能特性:
  • 自动化优惠券领取
  • 交互式权益超市选择  
  • PLUS会员智能处理
  • 可视化操作界面

🔧 使用前准备:
  1. 连接Android设备并开启USB调试
  2. 确保设备上已安装联通APP
  3. 安装必要的Python依赖包

🚀 启动方式:
  python launch_benefits_system.py

💡 操作步骤:
  1. 在Web界面连接设备
  2. 点击开始权益领取
  3. 根据提示进行选择
  4. 查看执行结果

📞 故障排除:
  • 设备连接问题 → 检查USB调试设置
  • APP启动问题 → 确认联通APP已安装
  • 网络问题 → 检查设备网络连接

📄 详细文档: INTERACTIVE_BENEFITS_INTEGRATION_GUIDE.md
""")

def main():
    """主函数"""
    print("=" * 60)
    print("🎉 联通用户权益领取系统 - 交互式启动器")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        show_help()
        return
    
    # 检查系统要求
    if not check_requirements():
        print("\n❌ 系统要求检查失败，请解决上述问题后重试")
        return
    
    print("\n✅ 系统要求检查通过")
    
    # 启动应用
    if launch_streamlit():
        print("\n🎉 系统启动成功！")
    else:
        print("\n❌ 系统启动失败")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 启动被用户中断")
    except Exception as e:
        print(f"\n❌ 启动异常: {str(e)}")
