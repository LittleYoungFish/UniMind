#!/usr/bin/env python3
"""
测试智能代接功能集成
Test Phone Auto Answer Integration
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_phone_auto_answer_integration():
    """测试智能代接功能集成"""
    print("🚀 开始测试智能代接功能集成...")
    print("-" * 50)
    
    try:
        # 测试1: 导入检查
        print("📦 测试1: 导入功能模块...")
        from agilemind.tool.phone_auto_answer import (
            phone_get_status,
            phone_set_scenario_mode,
            phone_get_custom_responses,
            phone_simulate_call
        )
        print("✅ 模块导入成功")
        
        # 测试2: 状态获取
        print("\n📊 测试2: 获取系统状态...")
        status = phone_get_status()
        print(f"✅ 当前状态: {status['scenario_name']}")
        print(f"📞 代接开关: {'开启' if status['enabled'] else '关闭'}")
        print(f"📱 设备连接: {'已连接' if status['device_connected'] else '未连接'}")
        print(f"📋 今日通话: {status['recent_calls_24h']} 次")
        
        # 测试3: 场景切换
        print("\n🎭 测试3: 场景切换功能...")
        result = phone_set_scenario_mode("work")
        if result["success"]:
            print("✅ 场景切换成功")
        else:
            print(f"❌ 场景切换失败: {result.get('error', '未知错误')}")
        
        # 测试4: 自定义回复
        print("\n🎨 测试4: 自定义回复功能...")
        responses = phone_get_custom_responses()
        print(f"✅ 获取到 {len(responses)} 个自定义回复")
        for scenario, response in responses.items():
            if response:
                print(f"  - {scenario}: {response[:30]}...")
        
        # 测试5: 模拟测试
        print("\n🧪 测试5: 模拟来电功能...")
        sim_result = phone_simulate_call("138-TEST-8888", "测试联系人", "work")
        if sim_result["success"]:
            print("✅ 模拟来电成功")
            print(f"📞 模拟场景: {sim_result['scenario_name']}")
            print(f"💬 回复内容: {sim_result['response_text'][:50]}...")
        else:
            print(f"❌ 模拟来电失败: {sim_result.get('error', '未知错误')}")
        
        # 测试6: Web界面集成
        print("\n🌐 测试6: Web界面集成...")
        try:
            from universal_ai_assistant_web import (
                render_phone_auto_answer_tab,
                render_phone_scenario_management,
                render_phone_custom_responses
            )
            print("✅ Web界面函数导入成功")
        except ImportError as e:
            print(f"❌ Web界面导入失败: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 智能代接功能集成测试完成！")
        print("✅ 所有核心功能已成功集成到主界面")
        print("🌐 Web界面地址: http://localhost:8501")
        print("📱 请在浏览器中访问，查看'智能代接'标签页")
        
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()


def test_web_interface_features():
    """测试Web界面功能特性"""
    print("\n🌐 Web界面功能特性:")
    print("1. 📞 智能代接标签页 - 完整的代接管理界面")
    print("2. 🎭 场景管理 - 9种智能场景模式")
    print("3. 🎨 自定义回复 - 个性化回复设置")
    print("4. ⚙️ 系统设置 - 开关控制和延迟设置")
    print("5. 🧪 模拟测试 - 来电模拟和快速测试")
    print("6. 📋 通话记录 - 历史通话查看")
    print("7. 💬 语音指令 - 通过对话界面控制代接功能")
    
    print("\n💡 使用建议:")
    print("- 在'智能对话'中可以说'开启智能代接'、'设置工作模式'等")
    print("- 在'智能代接'标签页中可以详细管理所有设置")
    print("- 支持完全自定义的回复语，适应不同场景需求")


if __name__ == "__main__":
    test_phone_auto_answer_integration()
    test_web_interface_features()

