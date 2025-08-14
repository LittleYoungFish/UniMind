#!/usr/bin/env python3
"""
解析UI布局文件，查找"我的"按钮的位置
"""

import re
import xml.etree.ElementTree as ET

def parse_ui_layout():
    try:
        # 读取UI布局文件
        with open('ui_current.xml', 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("🔍 分析UI布局文件...")
        
        # 查找所有包含文本的元素
        text_elements = []
        
        # 使用正则表达式查找所有text属性不为空的元素
        pattern = r'text="([^"]+)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
        matches = re.findall(pattern, content)
        
        print(f"📋 找到 {len(matches)} 个包含文本的UI元素:")
        print("=" * 60)
        
        for i, (text, x1, y1, x2, y2) in enumerate(matches):
            if text.strip():  # 只显示非空文本
                center_x = (int(x1) + int(x2)) // 2
                center_y = (int(y1) + int(y2)) // 2
                print(f"{i+1:2d}. 文本: '{text}'")
                print(f"    位置: [{x1},{y1}][{x2},{y2}] 中心: ({center_x},{center_y})")
                print()
                
                # 特别标记可能的底部导航元素
                if int(y1) > 1800:  # 底部区域
                    print(f"    ⭐ 底部导航元素!")
                    print()
        
        # 查找可能的"我的"相关元素
        print("\n🎯 查找可能的'我的'按钮:")
        print("=" * 60)
        
        # 查找包含"我"或类似字符的元素
        my_candidates = []
        for text, x1, y1, x2, y2 in matches:
            if '我' in text or 'my' in text.lower() or 'mine' in text.lower():
                center_x = (int(x1) + int(x2)) // 2
                center_y = (int(y1) + int(y2)) // 2
                my_candidates.append((text, center_x, center_y))
        
        if my_candidates:
            for text, x, y in my_candidates:
                print(f"候选: '{text}' 位置: ({x}, {y})")
        else:
            print("❌ 未找到明显的'我的'按钮")
            print("💡 可能需要检查resource-id或content-desc属性")
        
        # 查找底部导航区域的所有可点击元素
        print("\n📱 底部导航区域分析 (Y > 1800):")
        print("=" * 60)
        
        # 查找可点击元素
        clickable_pattern = r'clickable="true"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"[^>]*(?:text="([^"]*)")?'
        clickable_matches = re.findall(clickable_pattern, content)
        
        bottom_clickables = []
        for x1, y1, x2, y2, text in clickable_matches:
            if int(y1) > 1800:  # 底部区域
                center_x = (int(x1) + int(x2)) // 2
                center_y = (int(y1) + int(y2)) // 2
                bottom_clickables.append((text if text else "无文本", center_x, center_y, x1, y1, x2, y2))
        
        bottom_clickables.sort(key=lambda x: x[1])  # 按X坐标排序
        
        for i, (text, cx, cy, x1, y1, x2, y2) in enumerate(bottom_clickables):
            print(f"{i+1}. 文本: '{text}' 中心: ({cx}, {cy}) 边界: [{x1},{y1}][{x2},{y2}]")
        
        # 推荐点击位置
        if bottom_clickables:
            print(f"\n💡 建议的底部导航点击位置:")
            for i, (text, cx, cy, x1, y1, x2, y2) in enumerate(bottom_clickables[-3:]):  # 最右边的3个
                print(f"   位置 {i+1}: ({cx}, {cy}) - '{text}'")
        
    except Exception as e:
        print(f"❌ 解析失败: {str(e)}")

if __name__ == "__main__":
    parse_ui_layout()

