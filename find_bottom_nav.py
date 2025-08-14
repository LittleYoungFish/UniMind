#!/usr/bin/env python3
"""
查找底部导航元素，专门针对联通APP
"""

import re
import subprocess

def analyze_bottom_navigation():
    # 先获取新的UI dump
    subprocess.run(['./platform-tools/adb.exe', 'pull', '/sdcard/ui_fresh.xml', './ui_fresh.xml'], capture_output=True)
    
    try:
        with open('ui_fresh.xml', 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("🔍 分析联通APP底部导航...")
        
        # 查找所有在底部区域的可点击元素
        # Y坐标大于1800且高度不超过200的元素可能是底部导航
        pattern = r'clickable="true"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"[^>]*(?:text="([^"]*)")?[^>]*(?:resource-id="([^"]*)")?[^>]*(?:content-desc="([^"]*)")?'
        matches = re.findall(pattern, content)
        
        bottom_elements = []
        for match in matches:
            x1, y1, x2, y2 = int(match[0]), int(match[1]), int(match[2]), int(match[3])
            text = match[4] if len(match) > 4 else ""
            resource_id = match[5] if len(match) > 5 else ""
            content_desc = match[6] if len(match) > 6 else ""
            
            # 底部导航判断条件：Y坐标在屏幕底部且高度合理
            if y1 > 1800 and (y2 - y1) < 200:
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                width = x2 - x1
                height = y2 - y1
                
                bottom_elements.append({
                    'center': (center_x, center_y),
                    'bounds': (x1, y1, x2, y2),
                    'text': text,
                    'resource_id': resource_id,
                    'content_desc': content_desc,
                    'width': width,
                    'height': height
                })
        
        # 按X坐标排序（从左到右）
        bottom_elements.sort(key=lambda x: x['center'][0])
        
        print(f"📱 找到 {len(bottom_elements)} 个底部可点击元素:")
        print("=" * 80)
        
        for i, elem in enumerate(bottom_elements):
            print(f"{i+1:2d}. 中心坐标: {elem['center']}")
            print(f"    边界: [{elem['bounds'][0]},{elem['bounds'][1]}][{elem['bounds'][2]},{elem['bounds'][3]}]")
            print(f"    尺寸: {elem['width']}x{elem['height']}")
            print(f"    文本: '{elem['text']}'")
            print(f"    资源ID: '{elem['resource_id']}'")
            print(f"    内容描述: '{elem['content_desc']}'")
            print()
        
        # 根据联通APP的常见布局，推测导航位置
        print("🎯 底部导航推测:")
        print("=" * 80)
        
        if len(bottom_elements) >= 4:  # 典型的底部导航有4-5个tab
            # 通常联通APP的底部导航从左到右是：首页、服务、权益、营业厅、我的
            nav_names = ["首页", "服务", "权益", "营业厅", "我的"]
            
            for i, elem in enumerate(bottom_elements[-5:]):  # 取最右边的5个元素
                nav_index = len(nav_names) - (len(bottom_elements[-5:]) - i)
                if nav_index >= 0:
                    print(f"推测 {nav_names[nav_index]} 按钮: {elem['center']}")
                    if elem['text']:
                        print(f"  实际文本: '{elem['text']}'")
                    if elem['content_desc']:
                        print(f"  内容描述: '{elem['content_desc']}'")
                    print()
        
        # 提供具体的点击建议
        if bottom_elements:
            print("💡 点击建议:")
            print("=" * 80)
            # 最右边的元素通常是"我的"
            if len(bottom_elements) >= 1:
                rightmost = bottom_elements[-1]
                print(f"「我的」可能位置: {rightmost['center']}")
                
            # 第二右边的可能是"营业厅"，第三右边可能是"权益"等
            if len(bottom_elements) >= 2:
                second_right = bottom_elements[-2]
                print(f"「营业厅」可能位置: {second_right['center']}")
                
            if len(bottom_elements) >= 3:
                third_right = bottom_elements[-3]
                print(f"「权益」可能位置: {third_right['center']}")
                
            if len(bottom_elements) >= 4:
                fourth_right = bottom_elements[-4]
                print(f"「服务」可能位置: {fourth_right['center']}")
                
            if len(bottom_elements) >= 5:
                leftmost = bottom_elements[0]
                print(f"「首页」可能位置: {leftmost['center']}")
        
    except Exception as e:
        print(f"❌ 分析失败: {str(e)}")

if __name__ == "__main__":
    analyze_bottom_navigation()

