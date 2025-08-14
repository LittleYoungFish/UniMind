#!/usr/bin/env python3
"""
测试集成后的主流程权益领取功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agilemind.tool.unicom_android_tools import UnicomAndroidTools

def test_integrated_benefits():
    """测试集成后的权益领取流程"""
    print("🚀 测试集成后的权益领取流程")
    print("=" * 60)
    
    # 创建工具实例
    tools = UnicomAndroidTools()
    
    # 测试用户响应（模拟用户选择）
    user_responses = {
        "consumption_choice": "否",  # 不在权益超市消费
        "is_plus_member": "是",      # 是PLUS会员
        "benefit_choice": "流量包"   # 选择流量包权益
    }
    
    # 执行交互式权益领取流程
    print("\n📱 开始执行交互式权益领取流程...")
    result = tools.unicom_user_benefits_claim_interactive(user_responses)
    
    print(f"\n🎯 执行结果:")
    print(f"   成功: {result['success']}")
    print(f"   消息: {result['message']}")
    
    if result.get('result'):
        steps = result['result'].get('steps', [])
        print(f"\n📋 执行步骤 ({len(steps)} 步):")
        for i, step in enumerate(steps, 1):
            step_name = step.get('step', '未知步骤')
            step_result = step.get('result', {})
            step_success = step_result.get('success', False)
            step_message = step_result.get('message', '无消息')
            
            status = "✅" if step_success else "❌"
            print(f"   {i}. {status} {step_name}: {step_message}")
            
            # 如果是领取优惠券步骤，显示详细信息
            if step_name == "claim_coupons" and step_success:
                claimed_coupons = step_result.get('claimed_coupons', [])
                if claimed_coupons:
                    print(f"      🎫 领取的优惠券: {', '.join(claimed_coupons)}")
        
        interactions = result['result'].get('interactions', [])
        if interactions:
            print(f"\n💬 需要的交互 ({len(interactions)} 个):")
            for interaction in interactions:
                print(f"   ❓ {interaction.get('question', '未知问题')}")
                print(f"      选项: {', '.join(interaction.get('options', []))}")
    
    print(f"\n🎉 测试完成!")
    return result

if __name__ == "__main__":
    test_integrated_benefits()
