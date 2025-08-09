#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试真实的手机操作功能
"""

import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目路径
sys.path.append(os.path.abspath('.'))

from agilemind.tool.app_automation_tools import AppAutomationTools

def test_real_device_operations():
    """测试真实设备操作"""
    print("开始测试真实设备操作...")
    
    # 初始化工具
    tools = AppAutomationTools()
    
    # 1. 测试设备连接（通过ADB命令检查）
    print("\n1. 测试设备连接...")
    try:
        import subprocess
        result = subprocess.run([tools.adb_path, "devices"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            devices_output = result.stdout.strip()
            print(f"ADB设备列表:\n{devices_output}")
            if "device" in devices_output and len(devices_output.split('\n')) > 1:
                print("✅ 检测到连接的设备")
            else:
                print("❌ 没有连接的设备，请确保：")
                print("   - 手机已连接USB并开启调试模式")
                print("   - 已允许USB调试权限")
                return False
        else:
            print(f"❌ ADB命令失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 设备连接检查失败: {str(e)}")
        return False
    
    # 2. 测试截屏功能
    print("\n2. 测试截屏功能...")
    screenshot_result = tools.capture_screenshot()
    print(f"截屏结果: {screenshot_result}")
    
    # 3. 测试获取屏幕内容
    print("\n3. 测试获取屏幕内容...")
    screen_content = tools.get_screen_content()
    print(f"屏幕内容获取: {screen_content.get('success')}")
    if screen_content.get('success'):
        content = screen_content.get('content', {})
        print(f"截图路径: {content.get('screenshot_path')}")
        print(f"OCR可用: {content.get('has_ocr')}")
        if content.get('has_ocr'):
            ocr_text = content.get('ocr_text', '')[:200]  # 显示前200字符
            print(f"OCR文本预览: {ocr_text}...")
    
    # 4. 测试UI元素查找
    print("\n4. 测试UI元素查找...")
    elements_result = tools.find_elements()
    print(f"UI元素查找: {elements_result.get('success')}")
    if elements_result.get('success'):
        elements = elements_result.get('elements', [])
        print(f"检测到 {len(elements)} 个界面元素")
        # 显示前几个元素作为示例
        for i, elem in enumerate(elements[:5]):
            print(f"  元素{i+1}: {elem.get('text', '无文本')} - {elem.get('bounds', '无位置')}")
    
    # 5. 测试简单的点击操作（点击屏幕中心，通常比较安全）
    print("\n5. 测试点击操作（点击屏幕中心）...")
    tap_result = tools.tap_element(540, 960)  # 1080x1920屏幕的中心
    print(f"点击结果: {tap_result}")
    
    print("\n✅ 测试完成！如果看到真实的点击操作（屏幕中心可能会点击某个元素），说明修复成功！")
    return True

if __name__ == "__main__":
    test_real_device_operations()
