#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试当前手机屏幕状态
"""

import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目路径
sys.path.append(os.path.abspath('.'))

from agilemind.tool.app_automation_tools import AppAutomationTools

def debug_current_screen():
    """调试当前手机屏幕状态"""
    print("🔍 调试当前手机屏幕状态...")
    
    # 初始化工具
    tools = AppAutomationTools()
    
    # 1. 检查设备连接
    print("\n📱 1. 检查设备连接...")
    try:
        import subprocess
        result = subprocess.run([tools.adb_path, "devices"], capture_output=True, text=True, timeout=5)
        print(f"设备列表: {result.stdout}")
    except Exception as e:
        print(f"❌ 设备检查失败: {e}")
        return
    
    # 2. 获取当前屏幕内容
    print("\n📸 2. 获取当前屏幕内容...")
    screenshot_result = tools.capture_screenshot()
    if screenshot_result.get('success'):
        print(f"✅ 截图成功: {screenshot_result.get('filename')}")
    else:
        print("❌ 截图失败")
    
    # 3. 获取当前UI元素
    print("\n🔍 3. 获取当前UI元素...")
    elements_result = tools.find_elements()
    if elements_result.get('success'):
        elements = elements_result.get('elements', [])
        print(f"✅ 找到 {len(elements)} 个UI元素")
        
        print("\n📋 前20个UI元素:")
        for i, elem in enumerate(elements[:20]):
            text = elem.get('text', '').strip()
            if text:
                print(f"  {i+1}. {text} - 位置{elem.get('bounds', '')}")
        
        # 查找特殊按钮
        skip_buttons = []
        start_buttons = []
        unicom_buttons = []
        balance_buttons = []
        
        for elem in elements:
            text = elem.get('text', '').strip().lower()
            if '跳过' in text:
                skip_buttons.append(elem)
            elif any(keyword in text for keyword in ['开始', '进入', '确定', '开始使用']):
                start_buttons.append(elem)
            elif any(keyword in text for keyword in ['联通', 'unicom', '中国联通']):
                unicom_buttons.append(elem)
            elif any(keyword in text for keyword in ['剩余话费', '话费余额', '余额', '账户余额']):
                if '流量' not in text and '语音' not in text:
                    balance_buttons.append(elem)
        
        print(f"\n🔍 特殊按钮统计:")
        print(f"  跳过按钮: {len(skip_buttons)} 个")
        for btn in skip_buttons:
            print(f"    - {btn.get('text')} - 位置{btn.get('bounds')}")
        
        print(f"  开始/进入按钮: {len(start_buttons)} 个")
        for btn in start_buttons:
            print(f"    - {btn.get('text')} - 位置{btn.get('bounds')}")
        
        print(f"  联通相关按钮: {len(unicom_buttons)} 个")
        for btn in unicom_buttons:
            print(f"    - {btn.get('text')} - 位置{btn.get('bounds')}")
        
        print(f"  话费查询按钮: {len(balance_buttons)} 个")
        for btn in balance_buttons:
            print(f"    - {btn.get('text')} - 位置{btn.get('bounds')}")
        
        # 判断当前状态
        print(f"\n📊 界面状态分析:")
        if skip_buttons:
            print("  🚀 检测到启动页面或广告页面")
        elif balance_buttons:
            print("  ✅ 检测到话费查询界面")
        elif unicom_buttons:
            print("  📱 检测到联通APP主界面")
        else:
            print("  ❓ 无法确定当前界面状态")
    
    else:
        print(f"❌ 获取UI元素失败: {elements_result.get('message')}")

if __name__ == "__main__":
    debug_current_screen()


