#!/usr/bin/env python3
"""
最快速的智能代接系统
极简设计，立即响应
"""

import subprocess
import time

def execute_fast(cmd):
    """快速执行命令，不等待结果"""
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass

def check_call_state():
    """最快速检查通话状态"""
    try:
        result = subprocess.run([
            "./platform-tools/adb.exe", "shell", "getprop", "gsm.voice.call.state"
        ], capture_output=True, text=True, timeout=0.5)
        return result.stdout.strip()
    except:
        return "0"

def instant_answer():
    """立即接听，不等待任何结果"""
    print("🚨 立即接听！")
    
    # 立即发送接听命令，不等待
    execute_fast(["./platform-tools/adb.exe", "shell", "input", "keyevent", "5"])
    
    # 立即发送TTS命令，不等待
    execute_fast([
        "./platform-tools/adb.exe", "shell", "cmd", "media_session", "dispatch",
        "com.android.tts", "speak", "不方便接听请稍后联系"
    ])
    
    # 2秒后发送挂断命令
    time.sleep(2)
    execute_fast(["./platform-tools/adb.exe", "shell", "input", "keyevent", "6"])
    
    print("✅ 快速接听完成")

def main():
    print("🚀 超快速智能代接系统")
    print("📱 请拨打电话测试...")
    
    last_state = "0"
    last_answer_time = 0
    
    while True:
        try:
            current_state = check_call_state()
            current_time = time.time()
            
            # 检测到来电且距离上次处理超过3秒
            if current_state == "1" and current_time - last_answer_time > 3:
                print(f"🔔 检测到来电！状态: {current_state}")
                instant_answer()
                last_answer_time = current_time
            
            # 显示状态变化
            if current_state != last_state:
                print(f"📊 状态: {last_state} -> {current_state}")
                last_state = current_state
            
            time.sleep(0.1)  # 极快检查频率
            
        except KeyboardInterrupt:
            print("\n🛑 停止监控")
            break
        except:
            time.sleep(0.1)

if __name__ == "__main__":
    main()
