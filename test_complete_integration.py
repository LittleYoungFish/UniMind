#!/usr/bin/env python3
"""
测试完整的集成流程
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agilemind.tool.unicom_android_tools import UnicomAndroidTools

def test_complete_flow():
    """测试完整的权益领取流程"""
    print("🚀 测试完整的权益领取流程")
    print("=" * 60)
    
    tools = UnicomAndroidTools()
    
    print("📱 步骤1: 测试首次调用（无用户响应）")
    result1 = tools.unicom_user_benefits_claim_interactive()
    
    print(f"✅ 首次调用结果:")
    print(f"   成功: {result1['success']}")
    print(f"   消息: {result1['message']}")
    
    if result1.get('result'):
        steps = result1['result'].get('steps', [])
        print(f"\n📋 执行的步骤 ({len(steps)} 步):")
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
        
        interactions = result1['result'].get('interactions', [])
        if interactions:
            print(f"\n💬 需要的交互 ({len(interactions)} 个):")
            for interaction in interactions:
                print(f"   ❓ {interaction.get('question', '未知问题')}")
                print(f"      选项: {', '.join(interaction.get('options', []))}")
                print(f"      键: {interaction.get('key', '未知键')}")
    
    print(f"\n" + "="*60)
    print("📱 步骤2: 测试用户选择后的调用")
    
    # 模拟用户选择
    user_responses = {
        "consumption_choice": "否",  # 不在权益超市消费
    }
    
    result2 = tools.unicom_user_benefits_claim_interactive(user_responses)
    
    print(f"✅ 第二次调用结果:")
    print(f"   成功: {result2['success']}")
    print(f"   消息: {result2['message']}")
    
    if result2.get('result'):
        steps = result2['result'].get('steps', [])
        print(f"\n📋 执行的步骤 ({len(steps)} 步):")
        for i, step in enumerate(steps, 1):
            step_name = step.get('step', '未知步骤')
            step_result = step.get('result', {})
            choice = step.get('choice', '')
            step_success = step_result.get('success', False) if step_result else True
            step_message = step_result.get('message', '完成') if step_result else choice
            
            status = "✅" if step_success else "❌"
            print(f"   {i}. {status} {step_name}: {step_message}")
        
        interactions = result2['result'].get('interactions', [])
        if interactions:
            print(f"\n💬 需要的交互 ({len(interactions)} 个):")
            for interaction in interactions:
                print(f"   ❓ {interaction.get('question', '未知问题')}")
                print(f"      选项: {', '.join(interaction.get('options', []))}")
                print(f"      键: {interaction.get('key', '未知键')}")
    
    print(f"\n🎉 完整流程测试完成!")
    
    # 验证关键点
    print(f"\n🔍 验证关键点:")
    if result1['success'] and result1.get('result', {}).get('steps'):
        steps = result1['result']['steps']
        
        # 检查是否成功启动APP
        launch_step = next((s for s in steps if s['step'] == 'launch_app'), None)
        if launch_step and launch_step['result']['success']:
            print("   ✅ APP启动成功")
        else:
            print("   ❌ APP启动失败")
        
        # 检查是否成功进入我的页面
        my_step = next((s for s in steps if s['step'] == 'navigate_to_my_page'), None)
        if my_step and my_step['result']['success']:
            print("   ✅ 成功进入我的页面")
        else:
            print("   ❌ 进入我的页面失败")
        
        # 检查是否成功领取优惠券
        coupon_step = next((s for s in steps if s['step'] == 'claim_coupons'), None)
        if coupon_step and coupon_step['result']['success']:
            claimed_count = len(coupon_step['result'].get('claimed_coupons', []))
            print(f"   ✅ 成功领取优惠券 ({claimed_count} 张)")
        else:
            print("   ❌ 领取优惠券失败")
        
        # 检查是否成功进入服务页面
        service_step = next((s for s in steps if s['step'] == 'navigate_to_service_page'), None)
        if service_step and service_step['result']['success']:
            print("   ✅ 成功进入服务页面")
        else:
            print("   ❌ 进入服务页面失败")
    
    return result1, result2

if __name__ == "__main__":
    test_complete_flow()
