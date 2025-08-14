#!/usr/bin/env python3
"""
交互式用户权益领取流程综合测试
测试完整的前后端集成功能
"""

import sys
import json
from typing import Dict, Any

# 添加项目路径
sys.path.append('.')
from agilemind.tool.unicom_android_tools import UnicomAndroidTools

def mock_user_interaction_callback(question: str, options: list) -> str:
    """模拟用户交互回调函数"""
    print(f"\n🤔 {question}")
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option}")
    
    while True:
        try:
            choice = input("请输入选择 (数字): ").strip()
            choice_index = int(choice) - 1
            if 0 <= choice_index < len(options):
                selected = options[choice_index]
                print(f"✅ 您选择了: {selected}")
                return selected
            else:
                print("❌ 请输入有效的数字")
        except (ValueError, KeyboardInterrupt):
            print("❌ 请输入有效的数字")

def test_basic_benefits_claim():
    """测试基础权益领取功能"""
    print("=" * 60)
    print("🧪 测试1: 基础权益领取功能")
    print("=" * 60)
    
    try:
        tools = UnicomAndroidTools()
        
        # 连接设备
        print("📱 连接Android设备...")
        connect_result = tools.unicom_android_connect()
        print(f"连接结果: {connect_result}")
        
        if not connect_result["success"]:
            print("❌ 设备连接失败，跳过测试")
            return
        
        # 执行基础权益领取
        print("\n🎯 开始基础权益领取流程...")
        result = tools.unicom_user_benefits_claim(user_interaction_callback=mock_user_interaction_callback)
        
        print(f"\n📊 基础测试结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ 基础测试异常: {str(e)}")

def test_interactive_benefits_claim():
    """测试交互式权益领取功能"""
    print("=" * 60)
    print("🧪 测试2: 交互式权益领取功能")
    print("=" * 60)
    
    try:
        tools = UnicomAndroidTools()
        
        # 连接设备
        print("📱 连接Android设备...")
        connect_result = tools.unicom_android_connect()
        print(f"连接结果: {connect_result}")
        
        if not connect_result["success"]:
            print("❌ 设备连接失败，跳过测试")
            return
        
        # 模拟不同的用户响应场景
        test_scenarios = [
            {
                "name": "场景1: 不消费，不是会员，不申请",
                "responses": {
                    "consumption_choice": "否",
                    "is_plus_member": "否", 
                    "apply_membership": "否"
                }
            },
            {
                "name": "场景2: 不消费，不是会员，申请会员",
                "responses": {
                    "consumption_choice": "否",
                    "is_plus_member": "否",
                    "apply_membership": "是"
                }
            },
            {
                "name": "场景3: 不消费，是会员，选择权益",
                "responses": {
                    "consumption_choice": "否",
                    "is_plus_member": "是",
                    "benefit_choice": "酷狗音乐"
                }
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n🎭 {scenario['name']}")
            print("-" * 40)
            
            result = tools.unicom_user_benefits_claim_interactive(
                user_responses=scenario["responses"]
            )
            
            print(f"结果: {result.get('message', '无消息')}")
            print(f"成功: {result.get('success', False)}")
            
            if result.get("result", {}).get("steps"):
                print("执行步骤:")
                for step in result["result"]["steps"]:
                    print(f"  - {step.get('step', '未知')}: {step.get('choice', step.get('result', {}).get('message', '完成'))}")
            
            if result.get("result", {}).get("interactions"):
                print("需要交互:")
                for interaction in result["result"]["interactions"]:
                    print(f"  - {interaction['question']}")
                    print(f"    选项: {interaction['options']}")
            
            print()
            
    except Exception as e:
        print(f"❌ 交互式测试异常: {str(e)}")

def test_progressive_interaction():
    """测试渐进式交互流程"""
    print("=" * 60)
    print("🧪 测试3: 渐进式交互流程")
    print("=" * 60)
    
    try:
        tools = UnicomAndroidTools()
        
        # 连接设备
        print("📱 连接Android设备...")
        connect_result = tools.unicom_android_connect()
        
        if not connect_result["success"]:
            print("❌ 设备连接失败，跳过测试")
            return
        
        print("\n🔄 开始渐进式交互测试...")
        user_responses = {}
        step_count = 0
        max_steps = 10  # 防止无限循环
        
        while step_count < max_steps:
            step_count += 1
            print(f"\n--- 步骤 {step_count} ---")
            
            result = tools.unicom_user_benefits_claim_interactive(
                user_responses=user_responses
            )
            
            print(f"当前状态: {result.get('message', '无消息')}")
            
            # 检查是否需要用户交互
            interactions = result.get("result", {}).get("interactions", [])
            if not interactions:
                print("✅ 流程完成或无需更多交互")
                break
            
            # 处理每个交互
            for interaction in interactions:
                question = interaction["question"]
                options = interaction["options"]
                key = interaction["key"]
                
                print(f"\n❓ {question}")
                for i, option in enumerate(options, 1):
                    print(f"  {i}. {option}")
                
                # 模拟用户选择 (这里用简单的规则模拟)
                if "消费" in question:
                    choice = "否"
                elif "PLUS会员吗" in question:
                    choice = "否"
                elif "办理PLUS会员" in question:
                    choice = "否"
                elif "选择权益" in question:
                    choice = options[0] if options and options[0] != "暂无可用权益" else "暂无"
                else:
                    choice = options[0] if options else "未知"
                
                user_responses[key] = choice
                print(f"🤖 自动选择: {choice}")
        
        print(f"\n📊 渐进式测试完成，共执行 {step_count} 个步骤")
        print(f"最终用户响应: {json.dumps(user_responses, indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"❌ 渐进式测试异常: {str(e)}")

def main():
    """主测试函数"""
    print("🚀 联通用户权益领取交互式流程综合测试")
    print("=" * 60)
    
    # 选择测试模式
    print("请选择测试模式:")
    print("1. 基础权益领取测试")
    print("2. 交互式权益领取测试") 
    print("3. 渐进式交互流程测试")
    print("4. 运行所有测试")
    
    try:
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == "1":
            test_basic_benefits_claim()
        elif choice == "2":
            test_interactive_benefits_claim()
        elif choice == "3":
            test_progressive_interaction()
        elif choice == "4":
            test_basic_benefits_claim()
            test_interactive_benefits_claim()
            test_progressive_interaction()
        else:
            print("❌ 无效选择")
            
    except KeyboardInterrupt:
        print("\n\n👋 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试异常: {str(e)}")
    
    print("\n✅ 测试完成")

if __name__ == "__main__":
    main()



