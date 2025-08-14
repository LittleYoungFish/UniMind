#!/usr/bin/env python3
"""
测试高速智能代接系统
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """测试高速智能代接"""
    print("⚡ 高速智能代接系统测试")
    print("=" * 50)
    
    try:
        from agilemind.tool.real_phone_auto_answer import (
            real_phone_manager,
            real_phone_toggle_auto_answer,
            real_phone_set_scenario,
            real_phone_set_user_response,
            real_phone_get_status
        )
        
        print("✅ 高速智能代接系统已加载")
        
        # 设置测试回复
        test_response = "您好，这是智能代接测试。我现在无法接听电话，请稍后再拨，谢谢。"
        result = real_phone_set_user_response("work", test_response)
        if result["success"]:
            print(f"✅ 设置工作场景回复: {test_response[:30]}...")
        
        # 设置为工作模式
        result = real_phone_set_scenario("work")
        if result["success"]:
            print("✅ 场景设置为工作模式")
        
        # 开启智能代接
        result = real_phone_toggle_auto_answer(True)
        if result["success"]:
            print("✅ 高速智能代接已开启")
        
        # 获取状态
        status = real_phone_get_status()
        if status["success"]:
            print(f"\n📊 系统状态:")
            print(f"   ⚡ 检测频率: 每0.2秒")
            print(f"   📱 代接状态: {'🟢 开启' if status['enabled'] else '🔴 关闭'}")
            print(f"   🎭 当前场景: {status['current_scenario']}")
            print(f"   🔍 监控状态: {'🔴 高速监控中' if status.get('monitoring', False) else '⚪ 未监控'}")
        
        print(f"\n⚡ 优化说明:")
        print(f"   🚀 检测频率提升至每0.2秒")
        print(f"   ⚡ 使用最快的ADB命令")
        print(f"   📞 检测到响铃立即处理（不使用线程）")
        print(f"   🔊 简化TTS播放流程")
        print(f"   📴 播放完成立即挂断")
        
        print(f"\n📞 测试指引:")
        print(f"   1. 用另一台手机拨打您的电话")
        print(f"   2. 系统应该在响铃后立即接听")
        print(f"   3. 播放测试回复语音")
        print(f"   4. 播放完成后自动挂断")
        
        print(f"\n🔍 观察要点:")
        print(f"   - 是否能检测到 '📱 通话状态变化: idle → ringing'")
        print(f"   - 是否显示 '🔔 检测到来电响铃'")
        print(f"   - 是否显示 '⚡ 智能代接已开启，立即处理来电'")
        print(f"   - 是否显示 '✅ 快速智能代接完成！'")
        
        input("\n🚀 系统已准备就绪，请拨打测试电话，然后按回车键结束...")
        
        # 关闭监控
        real_phone_toggle_auto_answer(False)
        print("👋 测试结束，智能代接已关闭")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
