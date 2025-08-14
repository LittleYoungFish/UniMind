#!/usr/bin/env python3
"""
测试改进后的来电检测功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_improved_call_detection():
    """测试改进后的来电检测"""
    print("🚀 测试改进后的真实智能代接系统")
    print("=" * 60)
    
    try:
        # 导入改进后的模块
        from agilemind.tool.real_phone_auto_answer import (
            real_phone_manager,
            real_phone_toggle_auto_answer,
            real_phone_set_scenario,
            real_phone_set_user_response,
            real_phone_get_status
        )
        
        print("✅ 改进后的智能代接模块导入成功")
        
        # 设置测试回复
        print("\n🎨 设置测试回复...")
        test_response = "您好，这是智能代接测试，我现在无法接听电话，请稍后再拨。"
        result = real_phone_set_user_response("work", test_response)
        if result["success"]:
            print(f"✅ 测试回复设置成功: {test_response[:30]}...")
        else:
            print(f"❌ 测试回复设置失败: {result.get('error')}")
        
        # 设置为工作场景
        result = real_phone_set_scenario("work")
        if result["success"]:
            print("✅ 场景设置为工作模式")
        
        # 开启智能代接
        print("\n🎛️ 开启智能代接...")
        result = real_phone_toggle_auto_answer(True)
        if result["success"]:
            print("✅ 智能代接已开启")
        else:
            print(f"❌ 开启智能代接失败: {result.get('error')}")
        
        # 获取当前状态
        status = real_phone_get_status()
        if status["success"]:
            print(f"\n📊 当前系统状态:")
            print(f"   🔘 代接状态: {'🟢 开启' if status['enabled'] else '🔴 关闭'}")
            print(f"   🔘 当前场景: {status['current_scenario']}")
            print(f"   🔘 监控状态: {'🔴 监控中' if status.get('monitoring', False) else '⚪ 未监控'}")
            print(f"   🔘 响铃延迟: {status['ring_delay_seconds']}秒")
        
        print("\n🎯 测试说明:")
        print("1. 系统现在使用改进的检测逻辑")
        print("2. 检测频率提高到每0.5秒一次")
        print("3. 使用多种方法检测来电状态")
        print("4. 支持多线程处理来电")
        
        print("\n📞 测试步骤:")
        print("1. 用另一台手机拨打您的电话")
        print("2. 观察控制台日志输出")
        print("3. 系统应该:")
        print("   - 检测到来电状态变化")
        print("   - 显示'检测到来电'信息")
        print("   - 自动接听并播放回复")
        print("   - 自动挂断电话")
        
        print("\n⚠️ 重要提醒:")
        print("- 确保Android设备已连接且开启USB调试")
        print("- 确保设备有电话和音频权限")
        print("- 系统现在会真实接听和挂断电话")
        print("- 请用测试号码进行验证")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_improved_call_detection()
