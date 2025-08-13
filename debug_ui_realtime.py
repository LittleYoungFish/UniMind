#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时UI调试工具
Real-time UI Debug Tool
"""

import sys
import os
import time
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agilemind.tool.unicom_android_tools import UnicomAndroidTools


def debug_current_ui():
    """调试当前UI状态"""
    print("🔍 实时UI调试工具")
    print("=" * 50)
    
    # 初始化工具
    tools = UnicomAndroidTools()
    
    # 连接设备
    print("📱 连接设备...")
    device_id = "9HTOC6AEHQYL4HAM"
    connect_result = tools.unicom_android_connect(device_id)
    if not connect_result["success"]:
        print(f"❌ 连接失败: {connect_result['message']}")
        return
    
    print(f"✅ 设备连接成功: {device_id}")
    
    while True:
        print("\n" + "="*50)
        print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
        
        try:
            # 1. 截图
            print("📸 截取屏幕...")
            screenshot_path = tools._capture_screenshot()
            if screenshot_path:
                print(f"✅ 截图保存: {screenshot_path}")
            else:
                print("❌ 截图失败")
            
            # 2. 获取UI dump
            print("📋 获取UI结构...")
            success, output = tools._execute_adb_command('shell uiautomator dump /sdcard/ui_dump.xml')
            if success:
                success, xml_content = tools._execute_adb_command('shell cat /sdcard/ui_dump.xml')
                if success:
                    print("✅ UI结构获取成功")
                    
                    # 分析关键元素
                    key_elements = ["我的", "服务", "领券中心", "权益超市", "PLUS会员", "领取"]
                    found_elements = []
                    
                    for element in key_elements:
                        if element in xml_content:
                            found_elements.append(element)
                    
                    if found_elements:
                        print(f"🎯 找到元素: {', '.join(found_elements)}")
                    else:
                        print("❌ 未找到关键元素")
                    
                    # 显示当前焦点窗口
                    success, focus_output = tools._execute_adb_command('shell dumpsys window windows | grep -E "mCurrentFocus"')
                    if success:
                        print(f"🔎 当前焦点: {focus_output.strip()}")
                    
                    # 显示当前活动
                    success, activity_output = tools._execute_adb_command('shell dumpsys activity activities | grep -E "mResumedActivity"')
                    if success:
                        print(f"📱 当前活动: {activity_output.strip()}")
                else:
                    print("❌ UI内容读取失败")
            else:
                print("❌ UI dump失败")
            
            # 3. 检查特定UI元素的坐标
            if xml_content:
                import re
                # 查找所有文本元素及其坐标
                text_pattern = r'text="([^"]*)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
                matches = re.findall(text_pattern, xml_content)
                
                if matches:
                    print("\n🎯 可点击的文本元素:")
                    for text, x1, y1, x2, y2 in matches[:10]:  # 只显示前10个
                        if text.strip():  # 只显示非空文本
                            center_x = (int(x1) + int(x2)) // 2
                            center_y = (int(y1) + int(y2)) // 2
                            print(f"   '{text}' -> 坐标: ({center_x}, {center_y})")
            
            # 4. 等待用户操作
            print("\n⌨️ 操作选项:")
            print("1. 点击底部'我的' (540, 1800)")
            print("2. 点击底部'服务' (540, 1600)")
            print("3. 点击屏幕中央 (540, 800)")
            print("4. 向上滑动")
            print("5. 向下滑动")
            print("6. 返回键")
            print("7. 刷新状态")
            print("0. 退出")
            
            choice = input("\n请选择操作 (0-7): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                success, output = tools._execute_adb_command('shell input tap 540 1800')
                print(f"点击'我的': {'成功' if success else '失败'}")
                time.sleep(2)
            elif choice == "2":
                success, output = tools._execute_adb_command('shell input tap 540 1600')
                print(f"点击'服务': {'成功' if success else '失败'}")
                time.sleep(2)
            elif choice == "3":
                success, output = tools._execute_adb_command('shell input tap 540 800')
                print(f"点击中央: {'成功' if success else '失败'}")
                time.sleep(2)
            elif choice == "4":
                success, output = tools._execute_adb_command('shell input swipe 500 800 500 400 500')
                print(f"向上滑动: {'成功' if success else '失败'}")
                time.sleep(1)
            elif choice == "5":
                success, output = tools._execute_adb_command('shell input swipe 500 400 500 800 500')
                print(f"向下滑动: {'成功' if success else '失败'}")
                time.sleep(1)
            elif choice == "6":
                success, output = tools._execute_adb_command('shell input keyevent KEYCODE_BACK')
                print(f"返回键: {'成功' if success else '失败'}")
                time.sleep(1)
            elif choice == "7":
                print("🔄 刷新状态...")
                continue
            else:
                print("❌ 无效选择")
                continue
                
        except KeyboardInterrupt:
            print("\n🛑 调试被中断")
            break
        except Exception as e:
            print(f"\n❌ 调试异常: {e}")
            time.sleep(1)
    
    print("\n👋 调试结束")


if __name__ == "__main__":
    debug_current_ui()
