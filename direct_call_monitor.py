#!/usr/bin/env python3
"""
直接监控来电的智能代接系统
使用dumpsys telephony.registry实时监控
"""

import subprocess
import time
import threading
import re

class DirectCallMonitor:
    def __init__(self):
        self.adb_path = "./platform-tools/adb.exe"
        self.is_running = False
        self.last_answer_time = 0
        
    def quick_auto_answer(self):
        """快速自动接听"""
        current_time = time.time()
        if current_time - self.last_answer_time < 5:  # 5秒防重复
            return
            
        self.last_answer_time = current_time
        
        print("🚨🚨🚨 立即执行自动接听！🚨🚨🚨")
        
        try:
            # 接听电话
            print("📞 执行接听命令...")
            subprocess.run([self.adb_path, "shell", "input", "keyevent", "5"], 
                         capture_output=True, timeout=2)
            print("✅ 接听命令已发送")
            
            # 等待连接
            time.sleep(2)
            
            # 播放语音回复
            print("🎤 播放语音回复...")
            subprocess.run([
                self.adb_path, "shell", "cmd", "media_session", "dispatch",
                "com.android.tts", "speak", "您好，现在不方便接听电话，请稍后联系，谢谢"
            ], capture_output=True, timeout=3)
            print("✅ 语音回复已发送")
            
            # 等待语音播放完成
            time.sleep(4)
            
            # 挂断电话
            print("📴 执行挂断命令...")
            subprocess.run([self.adb_path, "shell", "input", "keyevent", "6"], 
                         capture_output=True, timeout=2)
            print("✅ 挂断命令已发送")
            
            print("🎉 自动接听流程完成！")
            
        except Exception as e:
            print(f"❌ 自动接听异常: {e}")
    
    def monitor_telephony(self):
        """监控telephony状态"""
        print("🔍 开始监控telephony状态...")
        
        while self.is_running:
            try:
                # 获取当前telephony状态
                result = subprocess.run([
                    self.adb_path, "shell", "dumpsys", "telephony.registry"
                ], capture_output=True, text=True, timeout=3)
                
                if result.returncode == 0:
                    output = result.stdout
                    
                    # 检查是否有来电状态
                    if "mCallState=1" in output:  # 1表示响铃状态
                        print("🔔 检测到来电响铃状态！")
                        threading.Thread(target=self.quick_auto_answer, daemon=True).start()
                    elif "CallState: 1" in output:
                        print("🔔 检测到CallState响铃！")
                        threading.Thread(target=self.quick_auto_answer, daemon=True).start()
                    elif "RINGING" in output.upper():
                        print("🔔 检测到RINGING状态！")
                        threading.Thread(target=self.quick_auto_answer, daemon=True).start()
                
                time.sleep(0.3)  # 快速检查
                
            except Exception as e:
                print(f"❌ 监控异常: {e}")
                time.sleep(1)
    
    def monitor_call_state_prop(self):
        """监控call state属性"""
        print("🔍 开始监控call state属性...")
        last_state = ""
        
        while self.is_running:
            try:
                # 检查gsm.voice.call.state属性
                result = subprocess.run([
                    self.adb_path, "shell", "getprop", "gsm.voice.call.state"
                ], capture_output=True, text=True, timeout=2)
                
                if result.returncode == 0:
                    current_state = result.stdout.strip()
                    
                    if current_state != last_state:
                        print(f"📊 Call State变化: '{last_state}' -> '{current_state}'")
                        
                        # 状态1表示来电
                        if current_state == "1":
                            print("🔔 getprop检测到来电！")
                            threading.Thread(target=self.quick_auto_answer, daemon=True).start()
                    
                    last_state = current_state
                
                time.sleep(0.2)  # 更快的检查频率
                
            except Exception as e:
                print(f"❌ 属性监控异常: {e}")
                time.sleep(1)
    
    def start(self):
        """启动监控"""
        if self.is_running:
            return
            
        self.is_running = True
        
        # 启动多个监控线程
        threading.Thread(target=self.monitor_telephony, daemon=True).start()
        threading.Thread(target=self.monitor_call_state_prop, daemon=True).start()
        
        print("🚀 直接来电监控系统已启动")
        print("📱 请用另一台手机拨打您的电话测试...")
        print("按 Ctrl+C 停止监控")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 停止监控")
            self.is_running = False

def main():
    monitor = DirectCallMonitor()
    monitor.start()

if __name__ == "__main__":
    main()
