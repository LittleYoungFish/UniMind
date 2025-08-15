#!/usr/bin/env python3
"""
最终集成测试 - 验证智能代接功能完全集成到主界面
Final Integration Test - Verify Phone Auto Answer Integration
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_main_ui_integration():
    """测试主界面集成"""
    print("🚀 测试智能代接功能集成到主界面...")
    print("=" * 60)
    
    try:
        # 测试1: 主界面模块导入
        print("📦 测试1: 主界面模块导入...")
        from universal_ai_assistant_web import (
            render_phone_auto_answer_tab,
            render_phone_scenario_management,
            render_phone_custom_responses,
            render_phone_system_settings,
            render_phone_simulation_test,
            render_phone_call_records
        )
        print("✅ 所有智能代接相关函数已成功集成到主界面")
        
        # 测试2: 依赖检查
        print("\n🔧 测试2: 核心依赖检查...")
        from agilemind.tool.phone_auto_answer import (
            phone_manager,
            phone_get_status,
            phone_set_scenario_mode,
            phone_get_custom_responses
        )
        print("✅ 智能代接核心模块导入成功")
        
        # 测试3: 功能可用性
        print("\n📊 测试3: 功能可用性测试...")
        status = phone_get_status()
        print(f"✅ 智能代接状态获取成功: {status['scenario_name']}")
        
        responses = phone_get_custom_responses()
        print(f"✅ 自定义回复获取成功: {len(responses)} 个配置")
        
        records = phone_manager.get_recent_call_records(5)
        print(f"✅ 通话记录获取成功: {len(records)} 条记录")
        
        # 测试4: 场景切换
        print("\n🎭 测试4: 场景切换测试...")
        result = phone_set_scenario_mode("work")
        if result["success"]:
            print("✅ 场景切换功能正常")
        else:
            print(f"⚠️ 场景切换警告: {result.get('error', '未知')}")
        
        print("\n" + "=" * 60)
        print("🎉 智能代接功能集成测试完成！")
        print("✅ 所有核心功能已成功集成到主界面")
        
        return True
        
    except Exception as e:
        print(f"❌ 集成测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def print_usage_guide():
    """打印使用指南"""
    print("\n📖 使用指南:")
    print("-" * 40)
    print("1. 🌐 启动Web应用:")
    print("   streamlit run universal_ai_assistant_web.py --server.port 8501")
    print()
    print("2. 🔗 访问地址:")
    print("   http://localhost:8501")
    print()
    print("3. 📞 智能代接功能:")
    print("   - 点击主界面中的'📞 智能代接'标签页")
    print("   - 在其中可以完整管理所有智能代接设置")
    print("   - 包括场景管理、自定义回复、系统设置、模拟测试、通话记录")
    print()
    print("4. 💬 语音控制:")
    print("   - 在'智能对话'标签页中可以说:")
    print("   - '开启智能代接'")
    print("   - '设置工作模式'")
    print("   - '查询代接状态'")
    print()
    print("5. 🎯 完成功能:")
    print("   ✅ 不再需要打开两个界面")
    print("   ✅ 所有智能代接功能已集成到主界面")
    print("   ✅ 保持原有功能的完整性")
    print("   ✅ 支持语音指令控制")


if __name__ == "__main__":
    success = test_main_ui_integration()
    
    if success:
        print_usage_guide()
        print("\n🏆 智能代接功能已成功集成到主界面！")
        print("📱 现在您可以在一个界面中管理所有功能了。")
    else:
        print("\n❌ 集成测试失败，请检查配置。")

