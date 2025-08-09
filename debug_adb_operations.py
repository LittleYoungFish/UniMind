#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试ADB操作问题
"""

import subprocess
import os
import time

def test_adb_commands():
    """测试不同的ADB命令执行方式"""
    adb_path = "./platform-tools/adb.exe"
    
    print("测试1: 直接运行ADB版本检查")
    try:
        result = subprocess.run([adb_path, "version"], capture_output=True, text=True, timeout=10)
        print(f"返回码: {result.returncode}")
        print(f"输出: {result.stdout}")
        print(f"错误: {result.stderr}")
    except Exception as e:
        print(f"异常: {e}")
    
    print("\n测试2: 点击操作 - 使用列表参数")
    try:
        result = subprocess.run([adb_path, "shell", "input", "tap", "100", "100"], 
                              capture_output=True, text=True, timeout=10)
        print(f"返回码: {result.returncode}")
        print(f"输出: {result.stdout}")
        print(f"错误: {result.stderr}")
    except Exception as e:
        print(f"异常: {e}")
    
    print("\n测试3: 点击操作 - 使用shell=True")
    try:
        cmd = f'"{adb_path}" shell input tap 200 200'
        print(f"执行命令: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        print(f"返回码: {result.returncode}")
        print(f"输出: {result.stdout}")
        print(f"错误: {result.stderr}")
    except Exception as e:
        print(f"异常: {e}")
    
    print("\n测试4: UI Automator Dump")
    try:
        result = subprocess.run([adb_path, "shell", "uiautomator", "dump", "/sdcard/ui_dump.xml"], 
                              capture_output=True, text=True, timeout=15)
        print(f"返回码: {result.returncode}")
        print(f"输出: {result.stdout}")
        print(f"错误: {result.stderr}")
    except Exception as e:
        print(f"异常: {e}")
    
    print("\n测试5: 拉取UI文件")
    try:
        result = subprocess.run([adb_path, "pull", "/sdcard/ui_dump.xml", "."], 
                              capture_output=True, text=True, timeout=10)
        print(f"返回码: {result.returncode}")
        print(f"输出: {result.stdout}")
        print(f"错误: {result.stderr}")
        
        # 检查文件是否存在
        if os.path.exists("ui_dump.xml"):
            print("UI文件成功下载")
            with open("ui_dump.xml", "r", encoding="utf-8") as f:
                content = f.read()[:500]  # 读取前500字符
                print(f"文件内容预览: {content}")
        else:
            print("UI文件下载失败")
    except Exception as e:
        print(f"异常: {e}")

if __name__ == "__main__":
    test_adb_commands()

