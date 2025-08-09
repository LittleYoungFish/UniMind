#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试UI元素解析问题
"""

import subprocess
import os
import re
import xml.etree.ElementTree as ET

def debug_ui_parsing():
    """调试UI解析过程"""
    adb_path = "./platform-tools/adb.exe"
    
    print("1. 执行UI Dump...")
    try:
        # 执行UI dump
        result = subprocess.run([adb_path, "shell", "uiautomator", "dump", "/sdcard/ui_dump.xml"], 
                              capture_output=True, text=True, timeout=15)
        print(f"UI Dump返回码: {result.returncode}")
        print(f"输出: {result.stdout}")
        if result.stderr:
            print(f"错误: {result.stderr}")
        
        # 拉取文件
        result = subprocess.run([adb_path, "pull", "/sdcard/ui_dump.xml", "."], 
                              capture_output=True, text=True, timeout=10)
        print(f"Pull返回码: {result.returncode}")
        print(f"Pull输出: {result.stdout}")
        if result.stderr:
            print(f"Pull错误: {result.stderr}")
        
    except Exception as e:
        print(f"UI Dump异常: {e}")
        return
    
    # 检查文件
    ui_files = []
    for filename in ["ui_dump.xml", "ui_dump.xm"]:
        if os.path.exists(filename):
            ui_files.append(filename)
            print(f"找到UI文件: {filename} (大小: {os.path.getsize(filename)} 字节)")
    
    if not ui_files:
        print("❌ 没有找到UI dump文件")
        return
    
    # 分析第一个找到的文件
    ui_file = ui_files[0]
    print(f"\n2. 分析UI文件: {ui_file}")
    
    try:
        with open(ui_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print(f"文件内容长度: {len(content)} 字符")
        print(f"文件内容预览:")
        print("=" * 50)
        print(content[:500] + ("..." if len(content) > 500 else ""))
        print("=" * 50)
        
        # 方法1: 使用正则表达式解析
        print("\n3. 正则表达式解析:")
        node_pattern = r'<node[^>]*text="([^"]*)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"[^>]*/?>'
        matches = re.findall(node_pattern, content)
        print(f"正则匹配到 {len(matches)} 个节点")
        
        for i, match in enumerate(matches[:10]):  # 只显示前10个
            node_text, x1, y1, x2, y2 = match
            print(f"  节点{i+1}: 文本='{node_text}', 位置=[{x1},{y1}][{x2},{y2}]")
        
        # 方法2: 更宽松的正则表达式
        print("\n4. 宽松正则表达式解析:")
        loose_pattern = r'<node[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"[^>]*/?>'
        loose_matches = re.findall(loose_pattern, content)
        print(f"宽松正则匹配到 {len(loose_matches)} 个有位置的节点")
        
        # 方法3: XML解析
        print("\n5. XML解析:")
        try:
            root = ET.fromstring(content)
            all_nodes = root.findall('.//node')
            print(f"XML解析找到 {len(all_nodes)} 个node节点")
            
            clickable_nodes = 0
            text_nodes = 0
            for node in all_nodes[:10]:  # 只检查前10个
                text = node.get('text', '')
                bounds = node.get('bounds', '')
                clickable = node.get('clickable', 'false')
                content_desc = node.get('content-desc', '')
                resource_id = node.get('resource-id', '')
                
                if text:
                    text_nodes += 1
                if clickable == 'true':
                    clickable_nodes += 1
                    
                if text or content_desc or (clickable == 'true' and bounds != '[0,0][0,0]'):
                    print(f"  有用节点: text='{text}', desc='{content_desc}', id='{resource_id}', bounds='{bounds}', clickable={clickable}")
            
            print(f"总计: 有文本节点={text_nodes}, 可点击节点={clickable_nodes}")
            
        except Exception as e:
            print(f"XML解析失败: {e}")
        
        # 检查是否是锁屏/黑屏状态
        print("\n6. 状态检查:")
        if 'com.android.systemui' in content:
            print("⚠️  检测到系统UI，可能在锁屏状态")
        if 'launcher' in content.lower():
            print("📱 检测到桌面launcher")
        if len(all_nodes) == 1 and all_nodes[0].get('bounds') == '[0,0][0,0]':
            print("⚠️  只有一个空节点，可能界面未正确加载")
        
    except Exception as e:
        print(f"文件分析异常: {e}")
    
    finally:
        # 清理文件
        for filename in ui_files:
            try:
                os.remove(filename)
                print(f"清理文件: {filename}")
            except:
                pass

if __name__ == "__main__":
    debug_ui_parsing()

