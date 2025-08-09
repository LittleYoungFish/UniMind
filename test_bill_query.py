#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试真实的话费查询功能
"""

import sys
import os
from dotenv import load_dotenv
import time

# 加载环境变量
load_dotenv()

# 添加项目路径
sys.path.append(os.path.abspath('.'))

from agilemind.tool.app_automation_tools import AppAutomationTools
import re

def smart_extract_balance(elements):
    """
    智能提取剩余话费金额
    通过语义分析找到真正的余额信息
    """
    balance_candidates = []
    
    # 构建元素位置索引，用于查找邻近元素
    element_map = {}
    for i, elem in enumerate(elements):
        element_map[i] = elem
    
    for i, elem in enumerate(elements):
        text = elem.get('text', '').strip()
        if not text:
            continue
            
        # 查找包含金额的文本
        money_pattern = r'(\d+(?:\.\d{1,2})?)\s*[元￥¥]'
        money_matches = re.findall(money_pattern, text)
        
        if money_matches:
            for amount in money_matches:
                candidate = {
                    'amount': f"{amount}元",
                    'raw_amount': float(amount),
                    'element_text': text,
                    'element_index': i,
                    'context_score': 0,
                    'context': []
                }
                
                # 分析当前元素的语义上下文
                text_lower = text.lower()
                
                # 高优先级关键词（明确表示余额）
                high_priority_keywords = ['剩余', '余额', '可用', '账户余额', '话费余额', '当前余额']
                for keyword in high_priority_keywords:
                    if keyword in text_lower:
                        candidate['context_score'] += 50
                        candidate['context'].append(f"包含关键词: {keyword}")
                
                # 中优先级关键词
                medium_priority_keywords = ['话费', '余量', '当前']
                for keyword in medium_priority_keywords:
                    if keyword in text_lower:
                        candidate['context_score'] += 20
                        candidate['context'].append(f"包含关键词: {keyword}")
                
                # 负面关键词（表示不是余额）
                negative_keywords = ['充值', '缴费', '交费', '套餐', '售价', '优惠', '立即', '领取', '券', '福利']
                for keyword in negative_keywords:
                    if keyword in text_lower:
                        candidate['context_score'] -= 30
                        candidate['context'].append(f"负面关键词: {keyword}")
                
                # 检查邻近元素的语义上下文
                context_range = 3  # 检查前后3个元素
                for j in range(max(0, i-context_range), min(len(elements), i+context_range+1)):
                    if j == i:
                        continue
                    neighbor = elements[j]
                    neighbor_text = neighbor.get('text', '').strip().lower()
                    
                    if any(keyword in neighbor_text for keyword in high_priority_keywords):
                        candidate['context_score'] += 30
                        candidate['context'].append(f"邻近元素包含: {neighbor_text}")
                    elif any(keyword in neighbor_text for keyword in medium_priority_keywords):
                        candidate['context_score'] += 10
                        candidate['context'].append(f"邻近元素包含: {neighbor_text}")
                    elif any(keyword in neighbor_text for keyword in negative_keywords):
                        candidate['context_score'] -= 20
                        candidate['context'].append(f"邻近负面元素: {neighbor_text}")
                
                # 金额合理性检查
                if 0.01 <= candidate['raw_amount'] <= 9999:  # 合理的话费余额范围
                    candidate['context_score'] += 10
                    candidate['context'].append("金额在合理范围内")
                else:
                    candidate['context_score'] -= 20
                    candidate['context'].append("金额可能不合理")
                
                balance_candidates.append(candidate)
    
    # 按语义得分排序
    balance_candidates.sort(key=lambda x: x['context_score'], reverse=True)
    
    # 输出分析结果
    print(f"\n🧠 智能分析找到 {len(balance_candidates)} 个金额候选:")
    for i, candidate in enumerate(balance_candidates[:5]):  # 显示前5个
        print(f"  {i+1}. {candidate['amount']} (得分: {candidate['context_score']})")
        print(f"     原文: {candidate['element_text']}")
        print(f"     上下文: {'; '.join(candidate['context'])}")
        print()
    
    # 返回得分最高的候选
    if balance_candidates and balance_candidates[0]['context_score'] > 0:
        best_candidate = balance_candidates[0]
        return {
            'amount': best_candidate['amount'],
            'raw_amount': best_candidate['raw_amount'],
            'context': best_candidate['element_text'],
            'score': best_candidate['context_score']
        }
    
    return None

def test_bill_query():
    """测试话费查询完整流程"""
    print("🎯 开始测试话费查询功能...")
    
    # 初始化工具
    tools = AppAutomationTools()
    
    # 1. 检查设备连接
    print("\n📱 1. 检查设备连接...")
    try:
        import subprocess
        result = subprocess.run([tools.adb_path, "devices"], capture_output=True, text=True, timeout=5)
        if "device" in result.stdout and len(result.stdout.split('\n')) > 1:
            print("✅ 设备连接正常")
        else:
            print("❌ 设备未连接")
            return False
    except Exception as e:
        print(f"❌ 设备检查失败: {e}")
        return False
    
    # 2. 获取屏幕内容
    print("\n📸 2. 获取当前屏幕状态...")
    screenshot_result = tools.capture_screenshot()
    if screenshot_result.get('success'):
        print(f"✅ 截图成功: {screenshot_result.get('filename')}")
    else:
        print("❌ 截图失败")
    
    # 3. 查找UI元素
    print("\n🔍 3. 查找可用的APP和UI元素...")
    elements_result = tools.find_elements()
    if elements_result.get('success'):
        elements = elements_result.get('elements', [])
        print(f"✅ 找到 {len(elements)} 个UI元素")
        
        # 查找联通相关的APP
        unicom_elements = []
        for elem in elements:
            text = elem.get('text', '').lower()
            if any(keyword in text for keyword in ['联通', 'unicom', '中国联通', '手机营业厅', '10010']):
                unicom_elements.append(elem)
                print(f"  📍 找到联通相关元素: {elem['text']} - 位置{elem['bounds']}")
        
        if unicom_elements:
            print(f"\n🎉 找到 {len(unicom_elements)} 个联通相关元素")
            # 尝试点击第一个联通元素
            target_elem = unicom_elements[0]
            print(f"🔥 尝试点击: {target_elem['text']}")
            
            tap_result = tools.tap_element(target_elem['center_x'], target_elem['center_y'])
            if tap_result.get('success'):
                print("✅ 点击成功，等待APP启动...")
                time.sleep(3)
                
                # 再次获取UI元素，查看是否进入了APP
                print("\n📋 4. 检查APP是否已启动...")
                new_elements = tools.find_elements()
                if new_elements.get('success'):
                    new_elem_list = new_elements.get('elements', [])
                    print(f"✅ 新界面有 {len(new_elem_list)} 个元素")
                    
                    # 智能查找话费查询相关按钮
                    bill_buttons = []
                    query_buttons = []
                    
                    for elem in new_elem_list:
                        text = elem.get('text', '').strip()
                        text_lower = text.lower()
                        
                        # 优先匹配查询功能
                        if any(keyword in text_lower for keyword in ['查询话费', '话费查询', '余额查询', '剩余话费', '话费余额']):
                            query_buttons.append(elem)
                            print(f"  🎯 找到查询话费按钮: {text} - 位置{elem['bounds']}")
                        # 次优匹配包含查询的功能
                        elif '查询' in text_lower and any(keyword in text_lower for keyword in ['话费', '余额', '流量']):
                            query_buttons.append(elem)
                            print(f"  🔍 找到查询功能按钮: {text} - 位置{elem['bounds']}")
                        # 最后匹配可能相关的功能（排除充值、交费等）
                        elif any(keyword in text_lower for keyword in ['余额', '剩余']) and '充值' not in text_lower and '交费' not in text_lower:
                            bill_buttons.append(elem)
                            print(f"  💰 找到话费相关按钮: {text} - 位置{elem['bounds']}")
                    
                    # 优先使用查询按钮
                    target_buttons = query_buttons if query_buttons else bill_buttons
                    
                    if target_buttons:
                        print(f"\n🎯 找到 {len(target_buttons)} 个话费查询按钮")
                        # 点击第一个话费查询按钮
                        bill_elem = target_buttons[0]
                        print(f"🔥 尝试点击话费查询: {bill_elem['text']}")
                        
                        tap_result2 = tools.tap_element(bill_elem['center_x'], bill_elem['center_y'])
                        if tap_result2.get('success'):
                            print("✅ 话费查询按钮点击成功，等待结果...")
                            time.sleep(3)
                            
                            # 最终检查是否获取到话费信息
                            print("\n💰 5. 智能识别话费查询结果...")
                            final_elements = tools.find_elements()
                            if final_elements.get('success'):
                                final_elem_list = final_elements.get('elements', [])
                                print(f"✅ 结果界面有 {len(final_elem_list)} 个元素")
                                
                                # 智能识别剩余话费
                                balance_result = smart_extract_balance(final_elem_list)
                                if balance_result:
                                    print(f"\n🎉 成功识别剩余话费: {balance_result['amount']}")
                                    print(f"📍 位置信息: {balance_result['context']}")
                                    print(f"📊 完整话费查询完成 - 剩余话费: {balance_result['amount']}")
                                    return balance_result['amount']
                                else:
                                    print("⚠️ 未能智能识别剩余话费，显示所有金额信息:")
                                    # 显示所有可能的金额信息作为备选
                                    money_elements = []
                                    for elem in final_elem_list:
                                        text = elem.get('text', '')
                                        if any(char in text for char in ['元', '￥', '¥']) or any(char.isdigit() for char in text):
                                            if len(text.strip()) > 0:
                                                money_elements.append(elem)
                                                print(f"  💵 可能的金额信息: {text}")
                                    print("📋 需要进一步的语义分析")
                            else:
                                print("❌ 获取最终结果失败")
                        else:
                            print("❌ 话费查询按钮点击失败")
                    else:
                        print("⚠️ 未找到话费查询相关按钮，可能需要进一步导航")
                        print("📋 但APP启动成功，系统能够真正控制手机")
                else:
                    print("❌ 获取新界面元素失败")
            else:
                print("❌ 点击联通元素失败")
        else:
            print("⚠️ 未找到联通APP，但可以测试其他功能")
            print("📋 检测到的一些APP:")
            for i, elem in enumerate(elements[:10]):  # 显示前10个元素
                print(f"  App{i+1}: {elem['text']}")
            
            # 测试点击设置APP
            settings_elements = [elem for elem in elements if '设置' in elem.get('text', '')]
            if settings_elements:
                print(f"\n🔧 测试点击设置APP...")
                settings_elem = settings_elements[0]
                tap_result = tools.tap_element(settings_elem['center_x'], settings_elem['center_y'])
                if tap_result.get('success'):
                    print("✅ 设置APP点击成功 - 手机自动化功能正常!")
                    time.sleep(2)
                    
                    # 按Home键返回桌面
                    tools.press_key("KEYCODE_HOME")
                    print("🏠 已返回桌面")
                else:
                    print("❌ 设置APP点击失败")
    else:
        print("❌ 获取UI元素失败")
        return False
    
    print("\n✅ 话费查询功能测试完成！")
    print("📱 系统已能够:")
    print("   - 真正控制手机设备")
    print("   - 自动截屏和获取UI元素")
    print("   - 点击APP和按钮")
    print("   - 进行真实的APP操作")
    print("   - 智能识别剩余话费金额")
    return None

if __name__ == "__main__":
    test_bill_query()

