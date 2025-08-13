#!/usr/bin/env python3
"""
提取所有"立即领取"按钮的坐标
"""

import re

# 读取UI dump文件
with open('./ui_current.xml', 'r', encoding='utf-8') as f:
    ui_content = f.read()

# 正则表达式匹配"立即领取"按钮及其坐标
pattern = r'text="立即领取".*?bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
matches = re.findall(pattern, ui_content, re.DOTALL)

print("找到的立即领取按钮坐标：")
claim_buttons = []
for i, match in enumerate(matches, 1):
    x1, y1, x2, y2 = map(int, match)
    # 计算中心点坐标
    center_x = (x1 + x2) // 2
    center_y = (y1 + y2) // 2
    claim_buttons.append((center_x, center_y))
    print(f"{i}. 坐标范围: [{x1},{y1}][{x2},{y2}] -> 中心点: ({center_x}, {center_y})")

print(f"\n共找到 {len(claim_buttons)} 个立即领取按钮")
print("\n点击坐标列表：")
for i, (x, y) in enumerate(claim_buttons, 1):
    print(f"({x}, {y})  # 第{i}个按钮")
