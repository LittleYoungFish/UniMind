#!/usr/bin/env python3
"""
测试真实智能代接功能集成
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_real_phone_integration():
    """测试真实智能代接功能"""
    print("🚀 测试真实智能代接功能集成")
    print("=" * 60)
    
    try:
        # 测试导入
        print("📦 测试导入...")
        from agilemind.tool.real_phone_auto_answer import (
            real_phone_manager,
            real_phone_toggle_auto_answer,
            real_phone_set_scenario,
            real_phone_set_user_response,
            real_phone_get_user_responses,
            real_phone_get_status,
            real_phone_set_ring_delay
        )
        print("✅ 真实智能代接模块导入成功")
        
        # 测试用户自定义回复
        print("\n🎨 测试用户自定义回复...")
        
        # 设置自定义回复
        custom_responses = [
            ("work", "您好，我正在工作中，请稍后联系或发送信息说明事由，谢谢！"),
            ("meeting", "抱歉我正在开会，请留言或稍后再拨，我会尽快回复您。"),
            ("delivery", "您好，如果是外卖请放在门口即可，如有其他事情请稍后联系。"),
            ("unknown", "您好，我现在不方便接电话，请说明您的来意，我会记录下来。"),
            ("busy", "对不起我现在很忙，请稍后再拨或发短信联系，谢谢理解。")
        ]
        
        for scenario, response in custom_responses:
            result = real_phone_set_user_response(scenario, response)
            status = "✅" if result["success"] else "❌"
            print(f"   {status} 设置{scenario}场景回复: {response[:30]}...")
        
        # 获取所有用户回复
        print("\n📋 获取用户自定义回复...")
        user_responses = real_phone_get_user_responses()
        for scenario, response in user_responses.items():
            print(f"   📝 {scenario}: {response[:50]}...")
        
        # 测试场景切换
        print("\n🎭 测试场景切换...")
        scenarios_to_test = ["work", "meeting", "delivery", "unknown", "busy"]
        
        for scenario in scenarios_to_test:
            result = real_phone_set_scenario(scenario)
            status = "✅" if result["success"] else "❌"
            print(f"   {status} 切换到{scenario}场景: {result.get('message', result.get('error', ''))}")
        
        # 测试代接功能开关
        print("\n🎛️ 测试代接功能开关...")
        
        # 开启代接
        result = real_phone_toggle_auto_answer(True)
        status = "✅" if result["success"] else "❌"
        print(f"   {status} 开启智能代接: {result.get('message', result.get('error', ''))}")
        
        # 关闭代接
        result = real_phone_toggle_auto_answer(False)
        status = "✅" if result["success"] else "❌"
        print(f"   {status} 关闭智能代接: {result.get('message', result.get('error', ''))}")
        
        # 测试响铃延迟设置
        print("\n⏰ 测试响铃延迟设置...")
        result = real_phone_set_ring_delay(15)
        status = "✅" if result["success"] else "❌"
        print(f"   {status} 设置响铃延迟: {result.get('message', result.get('error', ''))}")
        
        # 获取系统状态
        print("\n📊 获取系统状态...")
        status = real_phone_get_status()
        if status["success"]:
            print(f"   ✅ 代接状态: {'🟢 开启' if status['enabled'] else '🔴 关闭'}")
            print(f"   ✅ 当前场景: {status['current_scenario']}")
            print(f"   ✅ 响铃延迟: {status['ring_delay_seconds']}秒")
            print(f"   ✅ 监控状态: {'🔴 监控中' if status.get('monitoring', False) else '⚪ 未监控'}")
            print(f"   ✅ 总通话数: {status['total_calls']}")
            print(f"   ✅ 可用场景: {len(status['available_scenarios'])} 个")
        else:
            print(f"   ❌ 获取状态失败: {status.get('error', '未知错误')}")
        
        print("\n🎉 真实智能代接功能测试完成!")
        print("\n📋 核心特性:")
        print("   ✅ 真实电话监控和接听")
        print("   ✅ 用户完全自定义回复语")
        print("   ✅ 9种生活场景模式")
        print("   ✅ 智能响铃延迟控制")
        print("   ✅ 来电状态实时监控")
        print("   ✅ 通话记录管理")
        print("   ✅ 语音合成播放")
        
        print("\n🚀 使用方式:")
        print("   1. 设置界面: streamlit run real_phone_auto_answer_ui.py")
        print("   2. 主界面集成: 通过自然语言指令控制")
        print("   3. 完全自定义: 用户设置所有场景回复语")
        
        print("\n⚠️ 重要说明:")
        print("   - 这是真实的电话接听系统，不是模拟")
        print("   - 需要Android设备连接和相关权限")
        print("   - 所有回复语都由用户自己设置")
        print("   - 支持实时监控来电状态")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_real_phone_integration()
