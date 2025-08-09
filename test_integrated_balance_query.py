#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试集成后的话费查询功能
已更新为使用合并后的AppAutomationTools方法
"""

import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目路径
sys.path.append(os.path.abspath('.'))

from agilemind.tool.app_automation_tools import AppAutomationTools

def test_integrated_balance_query():
    """测试集成后的话费查询功能"""
    print("🎯 测试集成后的话费查询功能...")
    print("✅ 已使用合并后的AppAutomationTools.query_unicom_balance方法")
    
    # 初始化工具
    tools = AppAutomationTools()
    
    # 调用集成的话费查询方法（现在使用合并后的完整实现）
    result = tools.query_unicom_balance()
    
    # 显示结果
    print(f"\n📋 查询结果:")
    print(f"成功状态: {result.get('success')}")
    print(f"消息: {result.get('message')}")
    
    if result.get('success'):
        print(f"💰 话费余额: {result.get('balance')}")
        print(f"📊 数值: {result.get('raw_amount')} 元")
        print(f"⭐ 置信度: {result.get('confidence_score')}")
        print(f"⏱️ 执行时长: {result.get('duration_seconds', 0):.2f} 秒")
        print(f"🕒 查询时间: {result.get('query_time')}")
        print(f"📍 上下文: {result.get('context')}")
        
        print(f"\n🎉 集成测试成功! 话费余额: {result.get('balance')}")
    else:
        print(f"\n❌ 查询失败: {result.get('message')}")
        if "available_elements" in result:
            print(f"可用元素: {result['available_elements'][:5]}")
        if "available_texts" in result:
            print(f"可用文本: {result['available_texts'][:5]}")
    
    return result

if __name__ == "__main__":
    test_integrated_balance_query()


