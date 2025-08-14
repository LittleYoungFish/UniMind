#!/usr/bin/env python3
"""
准确的智能代接系统
只在真正检测到来电时才执行
"""

import subprocess
import time
import os

class AccurateAutoAnswer:
    def __init__(self):
        self.adb = "platform-tools\\adb.exe"
        self.last_action = 0
        self.last_state = "0"
        
    def get_call_state(self):
        """获取准确的通话状态"""
        try:
            result = subprocess.run([
                "platform-tools/adb.exe", "shell", "getprop", "gsm.voice.call.state"
            ], capture_output=True, text=True, timeout=1)
            
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return "0"
    
    def instant_answer(self):
        """执行快速接听"""
        current_time = time.time()
        if current_time - self.last_action < 5:  # 5秒防重复
            return
        self.last_action = current_time
        
        print("🚨 执行自动接听！")
        
        try:
            # 1. 接听电话
            print("📞 接听...")
            os.system(f"{self.adb} shell input keyevent 5")
            
            # 2. 等待1秒
            time.sleep(1)
            
            # 3. 使用简单的TTS方式
            print("🎤 播放回复...")
            # 尝试不同的TTS方法
            os.system(f'{self.adb} shell "echo \'现在不方便接听\' | cmd media_session"')
            
            # 4. 等待2秒让语音播放
            time.sleep(2)
            
            # 5. 挂断电话
            print("📴 挂断...")
            os.system(f"{self.adb} shell input keyevent 6")
            
            print("✅ 自动接听完成")
            
        except Exception as e:
            print(f"❌ 执行失败: {e}")
    
    def monitor(self):
        """精确监控通话状态变化"""
        print("🚀 准确智能代接系统启动")
        print("📱 当前监控通话状态变化...")
        print("📊 状态说明: 0=无通话, 1=来电响铃, 2=通话中")
        
        while True:
            try:
                current_state = self.get_call_state()
                
                # 只有状态发生变化时才打印
                if current_state != self.last_state:
                    print(f"📊 通话状态变化: {self.last_state} -> {current_state}")
                    
                    # 只有从0变为1时才表示真正的来电
                    if self.last_state == "0" and current_state == "1":
                        print("🔔 检测到新来电！")
                        self.instant_answer()
                    
                    self.last_state = current_state
                
                time.sleep(0.3)  # 检查频率
                
            except KeyboardInterrupt:
                print("\n🛑 停止监控")
                break
            except Exception as e:
                print(f"❌ 监控异常: {e}")
                time.sleep(1)

def main():
    answer = AccurateAutoAnswer()
    answer.monitor()

if __name__ == "__main__":
    main()
