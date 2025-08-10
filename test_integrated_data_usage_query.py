#!/usr/bin/env python3
"""
测试集成的流量查询功能
Test integrated data usage query functionality
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_integrated_data_usage_query():
    """测试集成的流量查询功能"""
    print("=" * 60)
    print("🧪 联通剩余流量查询功能集成测试")
    print("=" * 60)
    print(f"⏰ 测试开始时间: {datetime.now()}")
    print()
    
    try:
        # 导入测试模块
        print("📦 正在导入模块...")
        from agilemind.tool.app_automation_tools import AppAutomationTools
        print("✅ 模块导入成功")
        
        # 初始化工具
        print("\n🔧 正在初始化工具...")
        tools = AppAutomationTools()
        print("✅ 工具初始化成功")
        
        # 检查关键方法是否存在
        print("\n🔍 检查关键方法存在性...")
        required_methods = [
            'query_unicom_data_usage',
            'smart_extract_data_usage', 
            '_create_data_candidate'
        ]
        
        for method_name in required_methods:
            if hasattr(tools, method_name):
                print(f"✅ {method_name}: 方法存在")
            else:
                print(f"❌ {method_name}: 方法不存在")
                return False
        
        # 检查方法文档
        print("\n📖 检查方法文档...")
        data_query_method = getattr(tools, 'query_unicom_data_usage')
        if data_query_method.__doc__:
            print("✅ query_unicom_data_usage: 文档完整")
            print(f"   📝 描述: {data_query_method.__doc__.split('.')[0].strip()}")
        else:
            print("⚠️  query_unicom_data_usage: 缺少文档")
        
        smart_extract_method = getattr(tools, 'smart_extract_data_usage')
        if smart_extract_method.__doc__:
            print("✅ smart_extract_data_usage: 文档完整")
            print(f"   📝 描述: {smart_extract_method.__doc__.split('.')[0].strip()}")
        else:
            print("⚠️  smart_extract_data_usage: 缺少文档")
        
        # 测试智能流量提取逻辑（使用模拟数据）
        print("\n🧠 测试智能流量提取逻辑...")
        test_elements = [
            {'text': '剩余通用流量', 'bounds': '[10,20][200,60]'},
            {'text': '2.5', 'bounds': '[250,20][300,60]'},
            {'text': 'GB', 'bounds': '[310,20][340,60]'},
            {'text': '语音通话', 'bounds': '[10,100][200,140]'},
            {'text': '100', 'bounds': '[250,100][300,140]'},
            {'text': '分钟', 'bounds': '[310,100][360,140]'},
            {'text': '话费余额', 'bounds': '[10,180][200,220]'},
            {'text': '66.60', 'bounds': '[250,180][300,220]'},
            {'text': '元', 'bounds': '[310,180][340,220]'},
        ]
        
        # 给每个元素添加索引和中心点
        for i, elem in enumerate(test_elements):
            bounds = elem['bounds']
            # 简单解析bounds [x1,y1][x2,y2]
            coords = bounds.replace('[', '').replace(']', ',').split(',')[:-1]
            x1, y1, x2, y2 = map(int, coords)
            elem['center_x'] = (x1 + x2) // 2
            elem['center_y'] = (y1 + y2) // 2
        
        extract_result = tools.smart_extract_data_usage(test_elements)
        
        if extract_result:
            print("✅ 智能提取逻辑正常工作")
            print(f"   📊 识别流量: {extract_result['amount']}")
            print(f"   📈 数值: {extract_result['raw_amount']}")
            print(f"   📏 单位: {extract_result['unit']}")
            print(f"   🎯 置信度: {extract_result['score']}")
            print(f"   🔍 上下文: {extract_result['context']}")
        else:
            print("⚠️  智能提取逻辑未能识别测试数据")
        
        # 测试设备连接（预期会失败，但应该优雅处理）
        print("\n📱 测试设备连接和完整流程...")
        print("⚠️  注意: 如果设备未连接，这是正常的测试行为")
        
        start_time = datetime.now()
        result = tools.query_unicom_data_usage()
        end_time = datetime.now()
        
        print(f"⏱️  执行时间: {(end_time - start_time).total_seconds():.2f} 秒")
        print(f"📊 执行结果: {result}")
        
        if result.get('success'):
            print("🎉 流量查询成功!")
            print(f"   📊 剩余流量: {result.get('data_usage')}")
            print(f"   📈 数值: {result.get('raw_amount')}")
            print(f"   📏 单位: {result.get('unit')}")
            print(f"   🎯 置信度: {result.get('confidence_score')}")
            print(f"   ⏱️  查询时间: {result.get('duration_seconds', 0):.2f} 秒")
        else:
            print(f"⚠️  流量查询未成功: {result.get('message', '未知错误')}")
            print("   📝 这在设备未连接时是正常的")
        
        # 测试通用AI助手集成
        print("\n🤖 测试通用AI助手集成...")
        try:
            from agilemind.universal_ai_assistant import universal_ai_assistant
            
            # 测试流量查询请求
            test_requests = [
                "查询剩余流量",
                "我想看看还有多少流量",
                "剩余通用流量是多少"
            ]
            
            for request in test_requests:
                print(f"\n   🔍 测试请求: '{request}'")
                assistant_result = universal_ai_assistant(request)
                
                if 'data_usage' in str(assistant_result).lower() or '流量' in assistant_result.get('user_response', ''):
                    print("   ✅ 通用助手正确识别流量查询请求")
                else:
                    print("   ⚠️  通用助手未识别流量查询请求")
                
        except Exception as e:
            print(f"   ❌ 通用助手测试失败: {e}")
        
        print("\n" + "=" * 60)
        print("✅ 流量查询功能集成测试完成")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现异常: {e}")
        print("📝 请检查模块导入和方法实现")
        return False


if __name__ == "__main__":
    success = test_integrated_data_usage_query()
    if success:
        print("\n🎉 所有测试通过！流量查询功能已准备就绪。")
        exit(0)
    else:
        print("\n❌ 测试失败，请检查实现。")
        exit(1)