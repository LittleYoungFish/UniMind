#!/usr/bin/env python3
"""
智能代接功能快速测试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """主测试函数"""
    print("🚀 智能代接功能快速测试")
    print("=" * 50)
    
    try:
        # 导入核心模块
        from agilemind.tool.phone_auto_answer import (
            phone_manager,
            phone_toggle_auto_answer,
            phone_set_scenario_mode,
            phone_get_status,
            phone_simulate_call
        )
        
        # 测试基本功能
        print("📱 测试基本功能...")
        
        # 1. 开启智能代接
        result = phone_toggle_auto_answer(True)
        print(f"   开启代接: {'✅' if result['success'] else '❌'}")
        
        # 2. 设置会议模式
        result = phone_set_scenario_mode("meeting")
        print(f"   会议模式: {'✅' if result['success'] else '❌'}")
        
        # 3. 获取状态
        status = phone_get_status()
        print(f"   当前状态: {status['scenario_name']} ({'开启' if status['enabled'] else '关闭'})")
        
        # 4. 模拟来电测试
        print("\n📞 模拟来电测试...")
        result = phone_simulate_call("138-1234-5678", "测试联系人", "meeting")
        if result['success']:
            print(f"   ✅ 来电处理成功 - 耗时: {result.get('duration_seconds', 0):.1f}秒")
        else:
            print(f"   ❌ 来电处理失败: {result.get('error', '未知错误')}")
        
        # 5. 测试主界面集成
        print("\n🖥️ 测试主界面集成...")
        from universal_ai_assistant_web import (
            _is_phone_auto_answer_request,
            handle_phone_auto_answer_request
        )
        
        # 测试请求识别
        test_requests = [
            "开启智能代接",
            "会议模式", 
            "智能代接状态"
        ]
        
        for request in test_requests:
            is_recognized = _is_phone_auto_answer_request(request)
            print(f"   {'✅' if is_recognized else '❌'} '{request}' -> {is_recognized}")
        
        # 6. 测试处理逻辑
        print("\n🎯 测试处理逻辑...")
        result = handle_phone_auto_answer_request("智能代接状态", "test_device")
        if result['success']:
            action = result.get('result', {}).get('action', '未知')
            print(f"   ✅ 状态查询成功: {action}")
        else:
            print(f"   ❌ 状态查询失败: {result.get('error', '未知错误')}")
        
        print("\n🎉 快速测试完成!")
        print("\n📋 功能摘要:")
        final_status = phone_get_status()
        print(f"   🔸 代接状态: {'🟢 开启' if final_status['enabled'] else '🔴 关闭'}")
        print(f"   🔸 当前场景: {final_status['scenario_name']}")
        print(f"   🔸 总通话数: {final_status['total_calls']}")
        print(f"   🔸 可用场景: {len(final_status['available_scenarios'])} 个")
        
        print("\n🚀 启动命令:")
        print("   主界面: streamlit run universal_ai_assistant_web.py")
        print("   专用界面: streamlit run phone_auto_answer_ui.py")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
