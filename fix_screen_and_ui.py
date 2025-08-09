#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复屏幕状态和UI获取问题
"""

import subprocess
import time
import os
import xml.etree.ElementTree as ET

def fix_screen_and_ui():
    """修复屏幕状态并获取UI元素"""
    adb_path = "./platform-tools/adb.exe"
    
    print("🔧 开始修复屏幕状态和UI获取...")
    
    # 1. 唤醒屏幕
    print("\n1. 唤醒屏幕...")
    try:
        # 按下电源键唤醒屏幕
        result = subprocess.run([adb_path, "shell", "input", "keyevent", "KEYCODE_WAKEUP"], 
                              capture_output=True, text=True, timeout=5)
        print(f"唤醒屏幕结果: {result.returncode}")
        
        # 等待屏幕响应
        time.sleep(2)
        
        # 滑动解锁（向上滑动）
        result = subprocess.run([adb_path, "shell", "input", "swipe", "540", "1500", "540", "800"], 
                              capture_output=True, text=True, timeout=5)
        print(f"滑动解锁结果: {result.returncode}")
        
        time.sleep(2)
        
    except Exception as e:
        print(f"唤醒屏幕异常: {e}")
    
    # 2. 启动桌面/launcher
    print("\n2. 启动桌面...")
    try:
        # 按Home键回到桌面
        result = subprocess.run([adb_path, "shell", "input", "keyevent", "KEYCODE_HOME"], 
                              capture_output=True, text=True, timeout=5)
        print(f"回到桌面结果: {result.returncode}")
        
        time.sleep(3)  # 等待桌面加载
        
    except Exception as e:
        print(f"启动桌面异常: {e}")
    
    # 3. 重新获取UI
    print("\n3. 重新获取UI结构...")
    ui_elements = get_ui_elements(adb_path)
    
    if ui_elements:
        print(f"✅ 成功获取到 {len(ui_elements)} 个UI元素:")
        for i, elem in enumerate(ui_elements[:10]):  # 显示前10个
            print(f"  元素{i+1}: '{elem['text']}' - {elem['bounds']}")
        
        # 4. 尝试查找并启动联通APP
        print("\n4. 查找联通相关APP...")
        unicom_keywords = ["联通", "unicom", "中国联通", "沃", "话费", "流量"]
        found_unicom = False
        
        for elem in ui_elements:
            text = elem['text'].lower()
            for keyword in unicom_keywords:
                if keyword.lower() in text:
                    print(f"🎯 找到联通相关元素: '{elem['text']}' 位置: {elem['bounds']}")
                    found_unicom = True
                    
                    # 尝试点击启动
                    try:
                        result = subprocess.run([adb_path, "shell", "input", "tap", 
                                               str(elem['center_x']), str(elem['center_y'])], 
                                              capture_output=True, text=True, timeout=5)
                        print(f"点击联通APP结果: {result.returncode}")
                        time.sleep(5)  # 等待APP启动
                        
                        # 重新获取UI看是否进入了APP
                        new_ui = get_ui_elements(adb_path)
                        if new_ui and len(new_ui) > len(ui_elements):
                            print("✅ 成功启动联通APP，获取到更多UI元素")
                            return new_ui
                        
                    except Exception as e:
                        print(f"点击联通APP失败: {e}")
                    break
            if found_unicom:
                break
        
        if not found_unicom:
            # 5. 如果没找到联通APP，尝试启动其他常见APP来测试
            print("\n5. 未找到联通APP，尝试启动其他APP进行测试...")
            common_apps = [
                "com.android.settings",  # 设置
                "com.android.contacts",  # 联系人
                "com.android.dialer",    # 拨号
            ]
            
            for package in common_apps:
                try:
                    print(f"尝试启动: {package}")
                    result = subprocess.run([adb_path, "shell", "monkey", "-p", package, 
                                           "-c", "android.intent.category.LAUNCHER", "1"], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        print(f"✅ 成功启动 {package}")
                        time.sleep(3)
                        
                        test_ui = get_ui_elements(adb_path)
                        if test_ui and len(test_ui) > 5:
                            print(f"✅ 获取到 {len(test_ui)} 个UI元素，APP界面正常")
                            return test_ui
                        
                except Exception as e:
                    print(f"启动 {package} 失败: {e}")
                    continue
        
        return ui_elements
        
    else:
        print("❌ 仍未获取到有效的UI元素")
        return []

def get_ui_elements(adb_path):
    """获取UI元素"""
    try:
        # UI dump
        result = subprocess.run([adb_path, "shell", "uiautomator", "dump", "/sdcard/ui_dump.xml"], 
                              capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            print(f"UI dump失败: {result.stderr}")
            return []
        
        # Pull文件
        result = subprocess.run([adb_path, "pull", "/sdcard/ui_dump.xml", "."], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print(f"Pull文件失败: {result.stderr}")
            return []
        
        # 解析UI
        ui_file = None
        for filename in ["ui_dump.xml", "ui_dump.xm"]:
            if os.path.exists(filename):
                ui_file = filename
                break
        
        if not ui_file:
            print("UI文件不存在")
            return []
        
        elements = []
        with open(ui_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 使用XML解析
        root = ET.fromstring(content)
        all_nodes = root.findall('.//node')
        
        for node in all_nodes:
            text = node.get('text', '')
            bounds = node.get('bounds', '')
            clickable = node.get('clickable', 'false')
            content_desc = node.get('content-desc', '')
            
            # 解析bounds
            if bounds and bounds != '[0,0][0,0]':
                # 从 [x1,y1][x2,y2] 格式提取坐标
                import re
                match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
                if match:
                    x1, y1, x2, y2 = map(int, match.groups())
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2
                    
                    # 只保留有意义的元素
                    if text or content_desc or clickable == 'true':
                        elements.append({
                            'text': text or content_desc,
                            'bounds': bounds,
                            'center_x': center_x,
                            'center_y': center_y,
                            'clickable': clickable == 'true'
                        })
        
        # 清理文件
        try:
            os.remove(ui_file)
        except:
            pass
        
        return elements
        
    except Exception as e:
        print(f"获取UI元素异常: {e}")
        return []

if __name__ == "__main__":
    result = fix_screen_and_ui()
    print(f"\n🎉 修复完成! 最终获取到 {len(result)} 个UI元素")

