#!/usr/bin/env python3
"""
AgileMind 智能代接系统
自动检测来电并执行接听-回复-挂断流程
"""

import subprocess
import time
import os
from datetime import datetime

def get_telephony_state():
    """获取telephony状态"""
    try:
        result = subprocess.run([
            "platform-tools/adb.exe", "shell", "dumpsys", "telephony.registry"
        ], capture_output=True, text=True, timeout=1)
        
        if result.returncode == 0:
            return result.stdout
    except:
        pass
    return ""

def is_incoming_call(telephony_output):
    """检查是否有来电"""
    if not telephony_output:
        return False
    
    # 检查关键指标
    indicators = [
        "mCallState=1",           # 通话状态为1（响铃）
        "CallState: 1",           # 另一种格式
        "call state: 1",          # 小写格式
        "Ringing call state: 1"   # 响铃状态
    ]
    
    for indicator in indicators:
        if indicator in telephony_output:
            return True
    
    return False

def execute_smart_answer():
    """执行智能代接流程"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n🚨 [{timestamp}] 执行智能代接流程...")
    
    try:
        # 1. 立即接听
        print("📞 接听电话...")
        os.system("platform-tools\\adb.exe shell input keyevent 5")
        
        # 2. 短暂等待连接稳定
        time.sleep(1)
        
        # 3. 播放多种提示音
        print("🎤 播放提示音...")
        
        # DTMF拨号音（通话中最有效）
        os.system('platform-tools\\adb.exe shell "service call phone 4 i32 1 i32 50"')
        
        # 系统音效
        os.system('platform-tools\\adb.exe shell "input keyevent KEYCODE_CAMERA"')
        time.sleep(0.3)
        
        # 发送通知
        os.system('platform-tools\\adb.exe shell "cmd notification post -S bigtext -t \'AgileMind智能代接\' \'AutoAnswer\' \'现在不方便接听电话，有重要事情请稍后联系，谢谢！\'"')
        
        # 4. 等待提示完成
        time.sleep(2)
        
        # 5. 挂断电话
        print("📴 挂断电话...")
        os.system("platform-tools\\adb.exe shell input keyevent 6")
        
        print(f"✅ [{timestamp}] 智能代接完成！")
        print("-" * 50)
        
    except Exception as e:
        print(f"❌ 执行异常: {e}")

def main():
    print("🤖 AgileMind 智能代接系统")
    print("=" * 50)
    print("📱 实时监控来电状态...")
    print("📞 自动执行: 接听 → 提示 → 挂断")
    print("🔄 检测频率: 0.5秒/次")
    print("⏰ 防重复: 5秒冷却期")
    print("按 Ctrl+C 停止监控")
    print("-" * 50)
    
    last_call_time = 0
    call_count = 0
    
    while True:
        try:
            # 获取telephony状态
            telephony_output = get_telephony_state()
            
            # 检查是否有来电
            if is_incoming_call(telephony_output):
                current_time = time.time()
                
                # 防重复执行（5秒内只执行一次）
                if current_time - last_call_time > 5:
                    call_count += 1
                    print(f"\n🔔 检测到第 {call_count} 个来电！")
                    execute_smart_answer()
                    last_call_time = current_time
            
            time.sleep(0.5)  # 0.5秒检查一次
            
        except KeyboardInterrupt:
            print(f"\n\n🛑 监控已停止")
            print(f"📊 总共处理了 {call_count} 个来电")
            print("谢谢使用 AgileMind 智能代接系统！")
            break
        except Exception as e:
            print(f"❌ 监控异常: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
