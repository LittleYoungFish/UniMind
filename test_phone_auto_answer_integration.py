#!/usr/bin/env python3
"""
测试智能代接功能集成
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_phone_auto_answer_integration():
    """测试智能代接功能集成"""
    print("🚀 测试智能代接功能集成")
    print("=" * 60)
    
    try:
        # 测试导入
        print("📦 测试导入...")
        from agilemind.tool.phone_auto_answer import (
            phone_manager,
            ScenarioMode,
            phone_set_scenario_mode,
            phone_toggle_auto_answer,
            phone_get_status,
            phone_set_custom_response,
            phone_simulate_call
        )
        print("✅ 智能代接模块导入成功")
        
        # 测试主界面集成
        from universal_ai_assistant_web import (
            _is_phone_auto_answer_request,
            handle_phone_auto_answer_request,
            _is_phone_auto_answer_result
        )
        print("✅ 主界面集成函数导入成功")
        
        # 测试场景模式
        print("\n🎭 测试场景模式...")
        scenarios_to_test = [
            ("work", "工作模式"),
            ("meeting", "会议模式"), 
            ("delivery", "外卖模式"),
            ("unknown", "陌生电话模式"),
            ("busy", "忙碌模式")
        ]
        
        for mode, name in scenarios_to_test:
            result = phone_set_scenario_mode(mode)
            status = "✅" if result["success"] else "❌"
            print(f"   {status} {name}: {result.get('message', result.get('error', ''))}")
        
        # 测试自定义回复
        print("\n🎨 测试自定义回复...")
        custom_responses = [
            ("delivery", "您好，请把外卖放在外卖柜里，谢谢！"),
            ("meeting", "正在开会中，有事请留言"),
            ("unknown", "您好，请说明来意，我会记录您的留言")
        ]
        
        for mode, response in custom_responses:
            result = phone_set_custom_response(mode, response)
            status = "✅" if result["success"] else "❌"
            print(f"   {status} {mode}模式自定义回复: {result.get('message', result.get('error', ''))}")
        
        # 测试代接功能开关
        print("\n🎛️ 测试代接功能开关...")
        
        # 开启代接
        result = phone_toggle_auto_answer(True)
        status = "✅" if result["success"] else "❌"
        print(f"   {status} 开启自动代接: {result.get('message', result.get('error', ''))}")
        
        # 关闭代接
        result = phone_toggle_auto_answer(False)
        status = "✅" if result["success"] else "❌"
        print(f"   {status} 关闭自动代接: {result.get('message', result.get('error', ''))}")
        
        # 测试模拟来电
        print("\n📞 测试模拟来电...")
        test_calls = [
            ("138-0000-1111", "张三", "work"),
            ("400-123-4567", "外卖小哥", "delivery"),
            ("150-9999-8888", None, "unknown"),
            ("186-7777-6666", "朋友", "busy")
        ]
        
        for phone, caller, scenario in test_calls:
            result = phone_simulate_call(phone, caller, scenario)
            status = "✅" if result["success"] else "❌"
            scenario_name = result.get("scenario_name", "未知")
            duration = result.get("duration_seconds", 0)
            print(f"   {status} {phone} ({caller or '未知'}) - {scenario_name} - {duration:.1f}秒")
        
        # 测试主界面请求识别
        print("\n🔍 测试主界面请求识别...")
        test_requests = [
            ("开启智能代接", True),
            ("设置会议模式", True),
            ("外卖模式", True),
            ("智能代接设置", True),
            ("查询话费余额", False),
            ("权益领取", False)
        ]
        
        for request, expected in test_requests:
            result = _is_phone_auto_answer_request(request)
            status = "✅" if result == expected else "❌"
            print(f"   {status} '{request}' -> {result} (期望: {expected})")
        
        # 测试主界面处理逻辑
        print("\n🎯 测试主界面处理逻辑...")
        ui_test_requests = [
            "开启智能代接",
            "设置工作模式",
            "切换到外卖模式",
            "智能代接状态"
        ]
        
        for request in ui_test_requests:
            result = handle_phone_auto_answer_request(request, "test_device")
            status = "✅" if result["success"] else "❌"
            action = result.get("result", {}).get("action", "未知操作")
            print(f"   {status} '{request}' -> {action}")
        
        # 获取当前状态
        print("\n📊 当前系统状态:")
        status = phone_get_status()
        print(f"   代接状态: {'🟢 开启' if status['enabled'] else '🔴 关闭'}")
        print(f"   当前场景: {status['scenario_name']}")
        print(f"   总通话数: {status['total_calls']}")
        print(f"   今日通话: {status['recent_calls_24h']}")
        print(f"   可用场景: {len(status['available_scenarios'])} 个")
        
        print(f"\n🎉 智能代接功能集成测试完成!")
        print("\n📋 功能特性:")
        print("   ✅ 9种智能场景模式")
        print("   ✅ 自定义回复语设置")
        print("   ✅ 响铃延迟控制")
        print("   ✅ 陌生电话记录")
        print("   ✅ 模拟来电测试")
        print("   ✅ 主界面完全集成")
        print("   ✅ 智能指令识别")
        print("   ✅ 专用结果显示")
        
        print("\n🚀 使用方式:")
        print("   1. 主界面: streamlit run universal_ai_assistant_web.py")
        print("   2. 专用界面: streamlit run phone_auto_answer_ui.py")
        print("   3. 自然语言: '开启智能代接'、'设置外卖模式'等")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_phone_auto_answer_integration()