#!/usr/bin/env python3
"""
调试来电检测功能
Debug Call Detection
"""

import subprocess
import time
import sys
import os

def check_adb_connection():
    """检查ADB连接"""
    try:
        result = subprocess.run(["./platform-tools/adb.exe", "devices"], 
                              capture_output=True, text=True, timeout=5)
        print("ADB设备列表:")
        print(result.stdout)
        return "device" in result.stdout
    except Exception as e:
        print(f"ADB连接检查失败: {e}")
        return False

def get_call_state():
    """获取通话状态"""
    try:
        # 方法1: 使用telephony.registry
        cmd1 = ["./platform-tools/adb.exe", "shell", "dumpsys", "telephony.registry"]
        result1 = subprocess.run(cmd1, capture_output=True, text=True, timeout=10)
        
        print("=== Telephony Registry 输出 ===")
        lines = result1.stdout.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['call', 'phone', 'state', 'ring']):
                print(line.strip())
        
        # 方法2: 使用audio
        cmd2 = ["./platform-tools/adb.exe", "shell", "dumpsys", "audio"]
        result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=10)
        
        print("\n=== Audio 状态 ===")
        lines = result2.stdout.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['call', 'ring', 'phone']):
                print(line.strip())
        
        # 方法3: 直接检查通话状态
        cmd3 = ["./platform-tools/adb.exe", "shell", "getprop", "gsm.voice.call.state"]
        result3 = subprocess.run(cmd3, capture_output=True, text=True, timeout=5)
        print(f"\n=== GSM Voice Call State ===")
        print(f"gsm.voice.call.state: {result3.stdout.strip()}")
        
        # 方法4: 检查电话应用状态
        cmd4 = ["./platform-tools/adb.exe", "shell", "dumpsys", "telecom"]
        result4 = subprocess.run(cmd4, capture_output=True, text=True, timeout=10)
        
        print("\n=== Telecom 状态 ===")
        lines = result4.stdout.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['call', 'state', 'active', 'ring']):
                print(line.strip())
        
    except Exception as e:
        print(f"获取通话状态失败: {e}")

def monitor_call_states():
    """持续监控通话状态"""
    print("开始监控通话状态...")
    print("请在另一台设备拨打您的电话进行测试")
    print("按 Ctrl+C 停止监控")
    
    last_state = None
    
    try:
        while True:
            # 简化的状态检测
            try:
                # 检查音频状态
                cmd = ["./platform-tools/adb.exe", "shell", "dumpsys", "audio", "|", "grep", "-i", "mode"]
                result = subprocess.run(["./platform-tools/adb.exe", "shell", "dumpsys", "audio"], 
                                      capture_output=True, text=True, timeout=5)
                
                # 查找关键状态
                audio_output = result.stdout
                current_state = "IDLE"
                
                if "MODE_IN_CALL" in audio_output:
                    current_state = "IN_CALL"
                elif "MODE_RINGTONE" in audio_output:
                    current_state = "RINGING"
                elif "MODE_IN_COMMUNICATION" in audio_output:
                    current_state = "COMMUNICATION"
                
                # 检查通话状态变化
                if current_state != last_state:
                    timestamp = time.strftime("%H:%M:%S")
                    print(f"[{timestamp}] 状态变化: {last_state} → {current_state}")
                    
                    if current_state == "RINGING":
                        print("🔔 检测到来电！")
                        # 这里应该触发自动接听逻辑
                    elif current_state == "IN_CALL":
                        print("📞 通话中...")
                    elif current_state == "IDLE" and last_state in ["RINGING", "IN_CALL"]:
                        print("📴 通话结束")
                    
                    last_state = current_state
                
                # 更详细的检测
                if "RINGING" in audio_output or "ringtone" in audio_output.lower():
                    print(f"[{time.strftime('%H:%M:%S')}] 🔔 可能有来电 - Audio输出包含铃声相关信息")
                
            except Exception as e:
                print(f"监控异常: {e}")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n监控已停止")

def test_call_commands():
    """测试通话相关命令"""
    print("=== 测试通话相关ADB命令 ===")
    
    commands = [
        ("检查电话应用", ["./platform-tools/adb.exe", "shell", "pm", "list", "packages", "|", "grep", "phone"]),
        ("检查通话权限", ["./platform-tools/adb.exe", "shell", "pm", "list", "permissions", "|", "grep", "PHONE"]),
        ("检查音频焦点", ["./platform-tools/adb.exe", "shell", "dumpsys", "audio", "|", "head", "-20"]),
    ]
    
    for desc, cmd in commands:
        try:
            if "|" in " ".join(cmd):
                # 处理管道命令
                base_cmd = cmd[:cmd.index("|")]
                result = subprocess.run(base_cmd, capture_output=True, text=True, timeout=10)
            else:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            print(f"\n{desc}:")
            print(result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
            
        except Exception as e:
            print(f"{desc} 失败: {e}")

def main():
    """主函数"""
    print("📞 来电检测调试工具")
    print("=" * 40)
    
    # 检查ADB连接
    if not check_adb_connection():
        print("❌ 请确保Android设备已连接并开启USB调试")
        return
    
    print("✅ ADB连接正常")
    
    while True:
        print("\n选择操作:")
        print("1. 获取当前通话状态")
        print("2. 持续监控通话状态")
        print("3. 测试通话相关命令")
        print("4. 退出")
        
        choice = input("请输入选择 (1-4): ").strip()
        
        if choice == "1":
            get_call_state()
        elif choice == "2":
            monitor_call_states()
        elif choice == "3":
            test_call_commands()
        elif choice == "4":
            break
        else:
            print("无效选择，请重试")

if __name__ == "__main__":
    main()