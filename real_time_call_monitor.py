#!/usr/bin/env python3
"""
实时来电监控工具
Real-time Call Monitor Tool
"""

import sys
import os
import time
import threading
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """主函数"""
    print("📞 真实智能代接系统 - 实时监控")
    print("=" * 50)
    
    try:
        from unimind.tool.real_phone_auto_answer import (
            real_phone_manager,
            real_phone_toggle_auto_answer,
            real_phone_set_scenario,
            real_phone_set_user_response,
            real_phone_get_status
        )
        
        print("✅ 真实智能代接系统已加载")
        
        # 设置测试回复
        test_responses = {
            "work": "您好，我正在工作中，无法接听电话。这是智能代接系统的回复，请稍后再拨。",
            "meeting": "抱歉，我正在开会中，无法接听。请留言或稍后联系，谢谢！",
            "delivery": "您好，如果是外卖请放门口。如有其他事务请稍后联系。"
        }
        
        print("\n🎨 设置测试回复语...")
        for scenario, response in test_responses.items():
            result = real_phone_set_user_response(scenario, response)
            if result["success"]:
                print(f"✅ {scenario}: {response[:30]}...")
        
        while True:
            print("\n" + "="*60)
            print("🚀 真实智能代接测试菜单")
            print("="*60)
            
            # 获取当前状态
            status = real_phone_get_status()
            if status["success"]:
                print(f"📊 当前状态:")
                print(f"   代接功能: {'🟢 开启' if status['enabled'] else '🔴 关闭'}")
                print(f"   当前场景: {status['current_scenario']}")
                print(f"   监控状态: {'🔴 监控中' if status.get('monitoring', False) else '⚪ 未监控'}")
                print(f"   总通话数: {status['total_calls']}")
                print(f"   24H通话: {status['recent_calls_24h']}")
            
            print("\n🎯 选择操作:")
            print("1. 🟢 开启智能代接 (工作模式)")
            print("2. 🟡 开启智能代接 (会议模式)")
            print("3. 🟠 开启智能代接 (外卖模式)")
            print("4. 🔴 关闭智能代接")
            print("5. 📝 查看/编辑回复语")
            print("6. 📊 查看详细状态")
            print("7. 📞 进行真实来电测试")
            print("8. 🚪 退出")
            
            choice = input("\n请选择 (1-8): ").strip()
            
            if choice == "1":
                result1 = real_phone_set_scenario("work")
                result2 = real_phone_toggle_auto_answer(True)
                if result1["success"] and result2["success"]:
                    print("✅ 工作模式智能代接已开启")
                    print("📱 系统正在监控来电，请用另一台手机测试")
                
            elif choice == "2":
                result1 = real_phone_set_scenario("meeting")
                result2 = real_phone_toggle_auto_answer(True)
                if result1["success"] and result2["success"]:
                    print("✅ 会议模式智能代接已开启")
                    print("📱 系统正在监控来电，请用另一台手机测试")
                
            elif choice == "3":
                result1 = real_phone_set_scenario("delivery")
                result2 = real_phone_toggle_auto_answer(True)
                if result1["success"] and result2["success"]:
                    print("✅ 外卖模式智能代接已开启")
                    print("📱 系统正在监控来电，请用另一台手机测试")
                
            elif choice == "4":
                result = real_phone_toggle_auto_answer(False)
                if result["success"]:
                    print("✅ 智能代接已关闭")
                
            elif choice == "5":
                print("\n📝 当前回复语设置:")
                responses = real_phone_manager.get_user_responses()
                for scenario, response in responses.items():
                    print(f"   {scenario}: {response}")
                
                print("\n要修改回复语吗？(y/n)")
                if input().lower() == 'y':
                    scenario = input("场景名称 (work/meeting/delivery): ")
                    if scenario in responses:
                        new_response = input(f"新的{scenario}回复语: ")
                        if new_response.strip():
                            result = real_phone_set_user_response(scenario, new_response.strip())
                            if result["success"]:
                                print("✅ 回复语更新成功")
                
            elif choice == "6":
                status = real_phone_get_status()
                if status["success"]:
                    print("\n📊 详细系统状态:")
                    print(f"   代接功能: {status['enabled']}")
                    print(f"   当前场景: {status['current_scenario']}")
                    print(f"   监控状态: {status.get('monitoring', False)}")
                    print(f"   响铃延迟: {status['ring_delay_seconds']}秒")
                    print(f"   可用场景: {status['available_scenarios']}")
                
            elif choice == "7":
                print("\n📞 准备真实来电测试")
                print("=" * 40)
                
                # 确保系统开启
                status = real_phone_get_status()
                if not status.get("enabled", False):
                    print("⚠️ 智能代接未开启，正在开启...")
                    real_phone_set_scenario("work")
                    real_phone_toggle_auto_answer(True)
                    print("✅ 智能代接已开启")
                
                print("\n🎯 测试步骤:")
                print("1. 用另一台手机拨打您的电话")
                print("2. 观察系统日志输出")
                print("3. 系统应该自动:")
                print("   - 检测到来电")
                print("   - 自动接听")
                print("   - 播放回复语")
                print("   - 自动挂断")
                
                print("\n🔍 期望的日志输出:")
                print("   📱 通话状态变化: idle → ringing")
                print("   📞 检测到来电: [号码]")
                print("   🔄 智能代接已开启，准备自动接听...")
                print("   📞 已接听电话")
                print("   🔊 播放回复: [您的自定义回复]")
                print("   📞 已挂断电话")
                print("   📝 通话记录已保存")
                
                print("\n📱 现在请用另一台手机拨打您的电话进行测试...")
                print("按任意键返回菜单...")
                input()
                
            elif choice == "8":
                # 关闭监控
                real_phone_toggle_auto_answer(False)
                print("👋 再见！智能代接已关闭")
                break
                
            else:
                print("❌ 无效选择，请重试")
                
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，正在退出...")
        try:
            real_phone_toggle_auto_answer(False)
        except:
            pass
        
    except Exception as e:
        print(f"❌ 系统错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()