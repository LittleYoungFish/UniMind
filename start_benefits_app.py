#!/usr/bin/env python3
"""
联通用户权益领取系统 - 快速启动器
"""

import webbrowser
import time

def main():
    print("🚀 联通用户权益领取系统")
    print("=" * 50)
    print("📱 系统正在启动中...")
    
    # 等待应用完全启动
    time.sleep(2)
    
    # 自动打开浏览器
    url = "http://localhost:8504"
    print(f"🌐 正在打开浏览器: {url}")
    
    try:
        webbrowser.open(url)
        print("✅ 浏览器已打开！")
        print("\n📋 使用说明:")
        print("   1. 确保Android设备已连接并开启USB调试")
        print("   2. 确保设备上已安装中国联通APP")
        print("   3. 在网页界面点击'开始权益领取'")
        print("   4. 根据提示进行交互选择")
        print("\n🔧 如果浏览器未自动打开，请手动访问:")
        print(f"   {url}")
    except Exception as e:
        print(f"❌ 打开浏览器失败: {str(e)}")
        print(f"请手动访问: {url}")

if __name__ == "__main__":
    main()

