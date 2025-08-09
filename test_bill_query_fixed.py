#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复后的话费查询功能测试
解决滑动退出应用的问题
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
    通过语义分析和相邻元素关系找到真正的余额信息
    """
    balance_candidates = []
    
    # 遍历所有元素，查找金额
    for i, elem in enumerate(elements):
        text = elem.get('text', '').strip()
        if not text:
            continue
            
        # 方法1：查找包含完整金额的文本（如"66.60元"）
        money_pattern = r'(\d+(?:\.\d{1,2})?)\s*[元￥¥]'
        money_matches = re.findall(money_pattern, text)
        
        # 方法2：查找纯数字金额（如"66.60"），然后检查相邻元素
        pure_number_pattern = r'^(\d+(?:\.\d{1,2})?)$'
        pure_number_match = re.match(pure_number_pattern, text)
        
        # 处理完整金额文本
        if money_matches:
            for amount in money_matches:
                candidate = create_candidate(amount, text, i, elements, "完整金额文本")
                balance_candidates.append(candidate)
        
        # 处理纯数字金额（重点改进部分）
        elif pure_number_match:
            amount = pure_number_match.group(1)
            candidate = create_candidate(amount, text, i, elements, "纯数字金额")
            
            # 检查相邻元素是否有货币符号
            currency_bonus = 0
            nearby_currency = []
            for j in range(max(0, i-2), min(len(elements), i+3)):  # 检查前后2个元素
                if j != i and j < len(elements):
                    neighbor_text = elements[j].get('text', '').strip()
                    if neighbor_text in ['¥', '￥', '元']:
                        currency_bonus = 80  # 高分奖励
                        nearby_currency.append(f"相邻货币符号: {neighbor_text}")
                        
            candidate['context_score'] += currency_bonus
            candidate['context'].extend(nearby_currency)
            
            # 特别检查：紧密相邻的"剩余话费"标题（重点加分）
            title_proximity_bonus = 0
            for j in range(max(0, i-3), i):  # 检查前3个元素
                if j < len(elements):
                    neighbor_text = elements[j].get('text', '').strip().lower()
                    if '剩余话费' in neighbor_text:
                        distance = i - j
                        if distance == 1:  # 紧挨着
                            title_proximity_bonus = 200
                            candidate['context'].append(f"紧挨着剩余话费标题(距离{distance})")
                        elif distance == 2:  # 中间隔一个元素（可能是货币符号）
                            title_proximity_bonus = 180
                            candidate['context'].append(f"非常接近剩余话费标题(距离{distance})")
                        elif distance == 3:
                            title_proximity_bonus = 120
                            candidate['context'].append(f"接近剩余话费标题(距离{distance})")
                        break
            
            candidate['context_score'] += title_proximity_bonus
            
            # 检查是否在页面顶部位置（通过元素索引判断）
            if i <= 15:  # 前15个元素认为是顶部
                candidate['context_score'] += 40
                candidate['context'].append("位于页面顶部区域")
            
            balance_candidates.append(candidate)
    
    # 按语义得分排序
    balance_candidates.sort(key=lambda x: x['context_score'], reverse=True)
    
    # 输出分析结果
    print(f"\n🧠 智能分析找到 {len(balance_candidates)} 个金额候选:")
    for i, candidate in enumerate(balance_candidates[:5]):  # 显示前5个
        print(f"  {i+1}. {candidate['amount']} (得分: {candidate['context_score']})")
        print(f"     原文: {candidate['element_text']}")
        print(f"     元素位置: 第{candidate['element_index']+1}个")
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

def create_candidate(amount, text, element_index, elements, source_type):
    """创建金额候选"""
    candidate = {
        'amount': f"{amount}元",
        'raw_amount': float(amount),
        'element_text': text,
        'element_index': element_index,
        'context_score': 0,
        'context': [f"来源: {source_type}"]
    }
    
    # 分析当前元素的语义上下文
    text_lower = text.lower()
    
    # 高优先级关键词（明确表示余额）
    high_priority_keywords = ['剩余', '余额', '可用', '账户余额', '话费余额', '当前余额']
    for keyword in high_priority_keywords:
        if keyword in text_lower:
            candidate['context_score'] += 60
            candidate['context'].append(f"包含关键词: {keyword}")
    
    # 中优先级关键词
    medium_priority_keywords = ['话费', '余量', '当前']
    for keyword in medium_priority_keywords:
        if keyword in text_lower:
            candidate['context_score'] += 30
            candidate['context'].append(f"包含关键词: {keyword}")
    
    # 负面关键词（表示不是余额）
    negative_keywords = ['充值', '缴费', '交费', '套餐', '售价', '优惠', '立即', '领取', '券', '福利', '不可使用', '暂不可使用']
    for keyword in negative_keywords:
        if keyword in text_lower:
            candidate['context_score'] -= 50
            candidate['context'].append(f"负面关键词: {keyword}")
    
    # 检查邻近元素的语义上下文（重点增强）
    context_range = 3  # 检查前后3个元素
    for j in range(max(0, element_index-context_range), min(len(elements), element_index+context_range+1)):
        if j == element_index:
            continue
        if j < len(elements):
            neighbor = elements[j]
            neighbor_text = neighbor.get('text', '').strip().lower()
            
            # 高优先级邻近元素
            if any(keyword in neighbor_text for keyword in high_priority_keywords):
                distance_bonus = max(30 - abs(j - element_index) * 10, 10)  # 距离越近分数越高
                candidate['context_score'] += distance_bonus
                candidate['context'].append(f"邻近关键元素(距离{abs(j-element_index)}): {neighbor_text}")
            
            # 中优先级邻近元素
            elif any(keyword in neighbor_text for keyword in medium_priority_keywords):
                distance_bonus = max(20 - abs(j - element_index) * 5, 5)
                candidate['context_score'] += distance_bonus
                candidate['context'].append(f"邻近相关元素(距离{abs(j-element_index)}): {neighbor_text}")
            
            # 负面邻近元素
            elif any(keyword in neighbor_text for keyword in negative_keywords):
                candidate['context_score'] -= 30
                candidate['context'].append(f"邻近负面元素: {neighbor_text}")
    
    # 金额合理性检查
    if 0.01 <= candidate['raw_amount'] <= 9999:  # 合理的话费余额范围
        candidate['context_score'] += 15
        candidate['context'].append("金额在合理范围内")
    else:
        candidate['context_score'] -= 30
        candidate['context'].append("金额可能不合理")
    
    return candidate

def check_if_in_app(elements, app_name="联通"):
    """检查是否还在目标APP内"""
    for elem in elements:
        text = elem.get('text', '').lower()
        if app_name.lower() in text or any(keyword in text for keyword in ['话费', '剩余', '流量', '语音']):
            return True
    return False

def test_bill_query_fixed():
    """修复后的话费查询完整流程"""
    print("🎯 开始修复后的话费查询功能测试...")
    
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
    
    # 2. 直接启动联通APP（不依赖桌面位置）
    print("\n🚀 2. 直接启动联通APP...")
    try:
        import subprocess
        
        # 获取设备ID
        device_result = subprocess.run([tools.adb_path, "devices"], capture_output=True, text=True, timeout=5)
        device_lines = device_result.stdout.strip().split('\n')[1:]  # 跳过第一行标题
        device_id = None
        for line in device_lines:
            if 'device' in line:
                device_id = line.split('\t')[0]
                break
        
        if device_id:
            print(f"📱 检测到设备: {device_id}")
            # 使用monkey命令启动联通APP
            launch_cmd = [tools.adb_path, "-s", device_id, "shell", "monkey", "-p", "com.sinovatech.unicom.ui", "-c", "android.intent.category.LAUNCHER", "1"]
            launch_result = subprocess.run(launch_cmd, capture_output=True, text=True, timeout=10)
            
            if launch_result.returncode == 0:
                print("✅ 联通APP启动成功")
                time.sleep(5)  # 等待APP完全启动
            else:
                print(f"❌ APP启动失败: {launch_result.stderr}")
                # 备用方案：尝试通用启动命令
                print("🔄 尝试备用启动方案...")
                backup_cmd = [tools.adb_path, "-s", device_id, "shell", "am", "start", "-n", "com.sinovatech.unicom.ui/.MainActivity"]
                backup_result = subprocess.run(backup_cmd, capture_output=True, text=True, timeout=10)
                if backup_result.returncode == 0:
                    print("✅ 备用方案启动成功")
                    time.sleep(5)
                else:
                    print(f"❌ 备用方案也失败: {backup_result.stderr}")
                    return False
        else:
            print("❌ 未检测到设备")
            return False
            
    except Exception as e:
        print(f"❌ 启动APP时出错: {e}")
        return False
    
    # 3. 检查是否成功进入APP
    print("\n📋 3. 检查APP是否已启动...")
    new_elements = tools.find_elements()
    if new_elements.get('success'):
        new_elem_list = new_elements.get('elements', [])
        print(f"✅ 新界面有 {len(new_elem_list)} 个元素")
        
        # 检查是否在APP内
        if check_if_in_app(new_elem_list):
            print("✅ 确认已进入联通APP")
            
            # 查找话费查询相关按钮
            print("\n🔍 4. 查找话费查询按钮...")
            balance_buttons = []
            
            for elem in new_elem_list:
                text = elem.get('text', '').strip()
                text_lower = text.lower()
                
                # 精确匹配话费相关按钮
                if any(keyword in text_lower for keyword in ['剩余话费', '话费余额', '余额', '账户余额']):
                    if '流量' not in text_lower and '语音' not in text_lower:  # 排除流量和语音
                        balance_buttons.append(elem)
                        print(f"  🎯 找到话费按钮: {text} - 位置{elem['bounds']}")
            
            if balance_buttons:
                print(f"\n🎯 找到 {len(balance_buttons)} 个话费按钮")
                # 选择最合适的按钮
                best_button = balance_buttons[0]
                print(f"🔥 准备点击: {best_button['text']}")
                
                # 获取点击前的截图
                print("📸 点击前截图...")
                tools.capture_screenshot()
                
                # 精确点击，避免滑动
                print(f"🎯 精确点击位置: ({best_button['center_x']}, {best_button['center_y']})")
                tap_result2 = tools.tap_element(best_button['center_x'], best_button['center_y'])
                
                if tap_result2.get('success'):
                    print("✅ 话费按钮点击成功")
                    
                    # 等待界面响应
                    print("⏳ 等待界面加载...")
                    time.sleep(4)
                    
                    # 获取点击后的截图
                    print("📸 点击后截图...")
                    tools.capture_screenshot()
                    
                    # 检查是否还在APP内
                    print("\n🔍 5. 检查点击后的界面状态...")
                    final_elements = tools.find_elements()
                    if final_elements.get('success'):
                        final_elem_list = final_elements.get('elements', [])
                        print(f"✅ 当前界面有 {len(final_elem_list)} 个元素")
                        
                        # 检查是否还在APP内
                        if check_if_in_app(final_elem_list):
                            print("✅ 确认还在APP内，开始查找话费信息...")
                            
                            # 显示所有文本元素以便调试
                            print("\n📋 当前界面所有文本元素:")
                            for i, elem in enumerate(final_elem_list):
                                text = elem.get('text', '').strip()
                                if text:
                                    print(f"  {i+1}. {text}")
                            
                            # 智能识别剩余话费
                            balance_result = smart_extract_balance(final_elem_list)
                            if balance_result:
                                print(f"\n🎉 成功识别剩余话费: {balance_result['amount']}")
                                print(f"📍 完整信息: {balance_result['context']}")
                                print(f"📊 **最终结果: 您的话费余额为 {balance_result['amount']}**")
                                return balance_result['amount']
                            else:
                                print("\n⚠️ 未能智能识别剩余话费")
                                print("🔍 可能需要进一步的界面导航或等待")
                                
                                # 尝试查找更多金额信息
                                money_texts = []
                                for elem in final_elem_list:
                                    text = elem.get('text', '').strip()
                                    if re.search(r'\d+(?:\.\d{1,2})?\s*[元￥¥]', text):
                                        money_texts.append(text)
                                
                                if money_texts:
                                    print(f"💰 发现以下金额信息: {money_texts}")
                                else:
                                    print("💰 当前界面未发现明确的金额信息")
                        else:
                            print("❌ 应用已退出，点击操作可能触发了意外行为")
                            print("🔧 建议检查点击位置和APP界面设计")
                    else:
                        print("❌ 获取点击后界面失败")
                else:
                    print("❌ 话费按钮点击失败")
            else:
                print("⚠️ 未找到话费查询按钮")
                print("📋 显示当前界面的所有按钮:")
                for elem in new_elem_list:
                    text = elem.get('text', '').strip()
                    if text and len(text) < 20:  # 显示短文本（可能是按钮）
                        print(f"  - {text}")
        else:
            print("❌ 未成功进入APP，可能启动失败")
    else:
        print("❌ 获取APP启动后界面失败")
        return False
    
    print("\n✅ 修复后的话费查询测试完成！")
    return None

if __name__ == "__main__":
    result = test_bill_query_fixed()
    if result:
        print(f"\n🎯 最终查询结果: {result}")
    else:
        print(f"\n⚠️ 查询未完成，请检查日志信息")
