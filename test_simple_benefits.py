#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的权益领取测试脚本
Simplified Benefits Claim Test Script
"""

import sys
import os
import time
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agilemind.tool.unicom_android_tools import UnicomAndroidTools


def simple_user_interaction(question: str, options: list) -> str:
    """简单的用户交互模拟"""
    print(f"\n📋 {question}")
    print(f"选项: {', '.join(options)}")
    
    # 自动选择逻辑
    if "消费" in question:
        return "否"
    elif "PLUS会员" in question and "办理" in question:
        return "否"  
    elif "PLUS会员" in question:
        return "是"
    else:
        return options[0] if options else "是"


def test_benefits_workflow():
    """测试权益领取流程"""
    print("🎁 简化权益领取测试")
    print("=" * 50)
    
    # 初始化工具
    tools = UnicomAndroidTools()
    
    # 连接设备
    print("🔍 连接设备...")
    device_id = "9HTOC6AEHQYL4HAM"
    connect_result = tools.unicom_android_connect(device_id)
    if not connect_result["success"]:
        print(f"❌ 连接失败: {connect_result['message']}")
        return False
    
    print(f"✅ 设备连接成功: {device_id}")
    
    # 启动联通APP
    print("\n🚀 启动联通APP...")
    launch_result = tools.unicom_launch_app("unicom_app")
    if not launch_result["success"]:
        print(f"❌ APP启动失败: {launch_result['message']}")
        return False
    
    print("✅ 联通APP启动成功")
    time.sleep(5)  # 等待APP完全加载
    
    # 截图看当前状态
    print("\n📸 截取当前屏幕...")
    screen_result = tools.unicom_get_screen_content("unicom_app")
    if screen_result["success"]:
        print(f"✅ 截图成功: {screen_result['screenshot_path']}")
    
    # 尝试点击底部导航
    print("\n📱 尝试点击底部导航...")
    
    # 点击底部"我的"按钮 (大概位置)
    success, output = tools._execute_adb_command('shell input tap 540 1800')
    if success:
        print("✅ 点击底部导航位置")
        time.sleep(3)
    
    # 再次截图
    screen_result = tools.unicom_get_screen_content("unicom_app")
    if screen_result["success"]:
        print(f"📸 导航后截图: {screen_result['screenshot_path']}")
    
    # 尝试查找UI元素
    print("\n🔍 查找UI元素...")
    elements_to_find = ["我的", "领券中心", "服务", "权益", "PLUS"]
    
    for element in elements_to_find:
        find_result = tools.unicom_find_element_by_text(element)
        if find_result["success"] and find_result.get("found"):
            print(f"✅ 找到元素: {element}")
        else:
            print(f"❌ 未找到元素: {element}")
    
    # 测试完整的权益领取流程
    print("\n🎁 执行完整权益领取流程...")
    try:
        result = tools.unicom_user_benefits_claim(simple_user_interaction)
        if result["success"]:
            print("✅ 权益领取流程执行成功")
            print(f"📋 执行步骤数: {len(result.get('results', []))}")
            
            for i, step in enumerate(result.get('results', []), 1):
                step_name = step["step"]
                step_success = step["result"]["success"]
                status = "✅" if step_success else "❌"
                print(f"   {i}. {status} {step_name}")
        else:
            print(f"❌ 权益领取流程失败: {result['message']}")
    except Exception as e:
        print(f"❌ 执行异常: {e}")
    
    print("\n📊 测试完成")
    return True


def main():
    """主函数"""
    try:
        test_benefits_workflow()
    except KeyboardInterrupt:
        print("\n🛑 测试被中断")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")


if __name__ == "__main__":
    main()
