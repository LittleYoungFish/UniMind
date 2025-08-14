#!/usr/bin/env python3
"""
简化版智能代接系统
直接监控关键状态变化，快速响应
"""

import subprocess
import time
import threading

class SimpleAutoAnswer:
    def __init__(self):
        self.adb_path = "./platform-tools/adb.exe"
        self.is_running = False
        self.last_action_time = 0
        
    def get_call_state(self):
        """快速获取通话状态"""
        try:
            # 使用最快的命令检查通话状态
            result = subprocess.run([
                self.adb_path, "shell", "getprop", "gsm.voice.call.state"
            ], capture_output=True, text=True, timeout=1)
            
            if result.returncode == 0:
                state = result.stdout.strip()
                return state
            return "0"
        except:
            return "0"
    
    def auto_answer_call(self):
        """快速自动接听流程"""
        current_time = time.time()
        
        # 防止重复执行（3秒内只执行一次）
        if current_time - self.last_action_time < 3:
            return
        
        self.last_action_time = current_time
        
        print("🚨 检测到来电，立即执行自动接听！")
        
        try:
            # 1. 快速接听
            print("📞 接听...")
            subprocess.run([self.adb_path, "shell", "input", "keyevent", "5"], 
                         timeout=2, capture_output=True)
            
            # 2. 短暂等待
            time.sleep(1)
            
            # 3. 播放语音（简化版）
            print("🎤 播放回复...")
            subprocess.run([
                self.adb_path, "shell", "cmd", "media_session", "dispatch", 
                "com.android.tts", "speak", "您好，现在不方便接听，请稍后联系"
            ], timeout=3, capture_output=True)
            
            # 4. 等待语音播放
            time.sleep(3)
            
            # 5. 挂断
            print("📴 挂断...")
            subprocess.run([self.adb_path, "shell", "input", "keyevent", "6"], 
                         timeout=2, capture_output=True)
            
            print("✅ 自动接听完成")
            
        except Exception as e:
            print(f"❌ 自动接听失败: {e}")
    
    def monitor_calls(self):
        """监控来电状态"""
        print("🔍 开始监控来电状态...")
        last_state = "0"
        
        while self.is_running:
            try:
                current_state = self.get_call_state()
                
                # 检测到来电状态变化
                if current_state != last_state:
                    print(f"📊 通话状态变化: {last_state} -> {current_state}")
                    
                    # 状态1表示来电响铃
                    if current_state == "1":
                        print("🔔 检测到来电响铃！")
                        # 在单独线程中执行自动接听，避免阻塞监控
                        threading.Thread(target=self.auto_answer_call, daemon=True).start()
                
                last_state = current_state
                time.sleep(0.5)  # 0.5秒检查一次，响应更快
                
            except Exception as e:
                print(f"❌ 监控异常: {e}")
                time.sleep(1)
    
    def start(self):
        """启动监控"""
        if self.is_running:
            return
            
        self.is_running = True
        
        # 启动监控线程
        monitor_thread = threading.Thread(target=self.monitor_calls, daemon=True)
        monitor_thread.start()
        
        print("🚀 简化版智能代接系统已启动")
        print("📱 请拨打电话测试...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 停止监控")
            self.is_running = False

def main():
    auto_answer = SimpleAutoAnswer()
    auto_answer.start()

if __name__ == "__main__":
    main()
