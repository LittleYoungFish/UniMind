#!/usr/bin/env python3
"""
超极速智能代接系统
只检测关键信号，立即响应
"""

import subprocess
import time
import os

class UltraFastAnswer:
    def __init__(self):
        self.adb = "platform-tools\\adb.exe"  # Windows路径
        self.last_action = 0
        
    def instant_commands(self):
        """立即执行所有命令"""
        current_time = time.time()
        if current_time - self.last_action < 3:
            return
        self.last_action = current_time
        
        print("🚨 立即执行接听+回复+挂断序列！")
        
        # 连续快速执行命令
        os.system(f"{self.adb} shell input keyevent 5")  # 接听
        os.system(f'{self.adb} shell cmd media_session dispatch com.android.tts speak "不方便接听请稍后联系"')  # 回复
        time.sleep(1)
        os.system(f"{self.adb} shell input keyevent 6")  # 挂断
        
        print("✅ 执行完成")
    
    def check_audio_mode(self):
        """检查音频模式变化（来电时音频模式会改变）"""
        try:
            result = subprocess.run([
                "platform-tools/adb.exe", "shell", "dumpsys", "audio"
            ], capture_output=True, text=True, timeout=1)
            
            if "MODE_IN_CALL" in result.stdout or "STREAM_RING" in result.stdout:
                return True
        except:
            pass
        return False
    
    def check_call_activity(self):
        """检查是否有通话相关的Activity"""
        try:
            result = subprocess.run([
                "platform-tools/adb.exe", "shell", "dumpsys", "activity", "top"
            ], capture_output=True, text=True, timeout=1)
            
            if any(keyword in result.stdout.lower() for keyword in 
                  ["incall", "dialer", "phone", "call"]):
                return True
        except:
            pass
        return False
    
    def monitor(self):
        """多重检测监控"""
        print("🚀 超极速智能代接启动")
        print("📱 请拨打电话测试...")
        
        while True:
            try:
                # 方法1：检查音频模式
                if self.check_audio_mode():
                    print("🔔 音频模式检测到来电！")
                    self.instant_commands()
                    continue
                
                # 方法2：检查Activity
                if self.check_call_activity():
                    print("🔔 Activity检测到来电！")
                    self.instant_commands()
                    continue
                
                time.sleep(0.2)  # 快速循环
                
            except KeyboardInterrupt:
                print("\n🛑 停止监控")
                break
            except:
                time.sleep(0.1)

def main():
    answer = UltraFastAnswer()
    answer.monitor()

if __name__ == "__main__":
    main()
