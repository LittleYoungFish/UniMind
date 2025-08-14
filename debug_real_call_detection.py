#!/usr/bin/env python3
"""
实时调试来电检测
"""

import subprocess
import time
import threading
import os

def continuous_monitor():
    """持续监控所有可能的来电信号"""
    print("🔍 开始持续监控来电信号...")
    print("请在另一台手机拨打您的电话，观察输出变化")
    print("按 Ctrl+C 停止监控")
    
    adb_path = "./platform-tools/adb.exe"
    last_telecom_tail = ""
    last_telephony_state = ""
    last_audio_mode = ""
    
    try:
        while True:
            print(f"\n{'='*60}")
            print(f"⏰ {time.strftime('%H:%M:%S')} - 检查状态")
            
            # 1. 检查telecom最新事件
            try:
                result = subprocess.run([adb_path, "shell", "dumpsys", "telecom"], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    current_tail = '\n'.join(lines[-10:])  # 最后10行
                    
                    if current_tail != last_telecom_tail:
                        print("📋 Telecom 最新事件:")
                        for line in lines[-10:]:
                            if line.strip() and any(keyword in line for keyword in 
                                ['RING', 'CALL', 'incoming', 'SET_', 'START_', 'STOP_']):
                                print(f"   {line.strip()}")
                        last_telecom_tail = current_tail
            except Exception as e:
                print(f"❌ Telecom检查失败: {e}")
            
            # 2. 检查telephony registry
            try:
                result = subprocess.run([adb_path, "shell", "dumpsys", "telephony.registry"], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'mCallState' in line:
                            if line != last_telephony_state:
                                print(f"📱 Telephony状态变化: {line.strip()}")
                                last_telephony_state = line
                            break
            except Exception as e:
                print(f"❌ Telephony检查失败: {e}")
            
            # 3. 检查音频模式
            try:
                result = subprocess.run([adb_path, "shell", "dumpsys", "audio"], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'Mode :' in line or 'MODE_' in line:
                            if line != last_audio_mode:
                                print(f"🔊 Audio模式变化: {line.strip()}")
                                last_audio_mode = line
                            break
            except Exception as e:
                print(f"❌ Audio检查失败: {e}")
            
            # 4. 检查通话属性
            try:
                result = subprocess.run([adb_path, "shell", "getprop", "gsm.voice.call.state"], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    state = result.stdout.strip()
                    if state and state != "0":  # 0是空闲状态
                        print(f"📞 GSM通话状态: {state}")
            except Exception as e:
                print(f"❌ GSM状态检查失败: {e}")
            
            # 5. 检查活动应用
            try:
                result = subprocess.run([adb_path, "shell", "dumpsys", "activity", "activities"], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'dialer' in line.lower() or 'phone' in line.lower() or 'call' in line.lower():
                            if 'mResumedActivity' in line or 'mFocusedActivity' in line:
                                print(f"📱 电话相关活动: {line.strip()}")
                                break
            except Exception as e:
                print(f"❌ Activity检查失败: {e}")
            
            time.sleep(1)  # 每秒检查一次
            
    except KeyboardInterrupt:
        print("\n\n🛑 监控已停止")

def test_adb_connectivity():
    """测试ADB连接"""
    print("🔧 测试ADB连接...")
    adb_path = "./platform-tools/adb.exe"
    
    try:
        result = subprocess.run([adb_path, "devices"], capture_output=True, text=True, timeout=5)
        print("ADB设备列表:")
        print(result.stdout)
        
        if "device" in result.stdout:
            print("✅ ADB连接正常")
            return True
        else:
            print("❌ 没有检测到连接的设备")
            return False
    except Exception as e:
        print(f"❌ ADB连接测试失败: {e}")
        return False

def main():
    """主函数"""
    print("📞 实时来电检测调试工具")
    print("=" * 50)
    
    if not test_adb_connectivity():
        print("请确保Android设备已连接并开启USB调试")
        return
    
    print("\n选择测试模式:")
    print("1. 持续监控所有来电信号")
    print("2. 检查当前状态")
    print("3. 退出")
    
    choice = input("请选择 (1-3): ").strip()
    
    if choice == "1":
        continuous_monitor()
    elif choice == "2":
        print("📊 当前状态检查...")
        # 这里可以添加单次状态检查
    elif choice == "3":
        print("👋 退出")
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main()
