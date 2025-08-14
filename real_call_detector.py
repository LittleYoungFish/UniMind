#!/usr/bin/env python3
"""
真实来电实时检测器
基于logcat实时监听系统事件
"""

import subprocess
import threading
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class RealTimeCallDetector:
    """实时来电检测器"""
    
    def __init__(self):
        self.adb_path = "./platform-tools/adb.exe"
        self.is_monitoring = False
        self.detection_callbacks = []
        self.last_call_time = 0
        self.call_cooldown = 10  # 10秒冷却时间，防止重复处理
        
    def add_callback(self, callback):
        """添加检测回调"""
        self.detection_callbacks.append(callback)
    
    def start_monitoring(self):
        """开始实时监控"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        
        # 启动多个监控线程
        threading.Thread(target=self._monitor_logcat_phone, daemon=True).start()
        threading.Thread(target=self._monitor_logcat_audio, daemon=True).start()
        threading.Thread(target=self._monitor_activity, daemon=True).start()
        
        print("🔍 实时来电监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        print("🛑 实时来电监控已停止")
    
    def _monitor_logcat_phone(self):
        """监控电话相关日志"""
        try:
            cmd = [self.adb_path, "shell", "logcat", "-T", "1", "*:V", "|", "grep", "-i", "phone"]
            process = subprocess.Popen([self.adb_path, "shell", "logcat", "-T", "1", "*:V"],
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     text=True,
                                     bufsize=1)
            
            while self.is_monitoring:
                line = process.stdout.readline()
                if line:
                    line = line.strip()
                    # 检查电话相关事件
                    if any(keyword in line.lower() for keyword in 
                          ['incoming call', 'phone_state', 'call_state', 'ringing', 'telephony']):
                        print(f"📱 电话日志: {line}")
                        self._trigger_callbacks("phone_log", line)
                        
        except Exception as e:
            print(f"❌ 电话日志监控失败: {e}")
    
    def _monitor_logcat_audio(self):
        """监控音频相关日志"""
        try:
            process = subprocess.Popen([self.adb_path, "shell", "logcat", "-T", "1", "*:V"],
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     text=True,
                                     bufsize=1)
            
            while self.is_monitoring:
                line = process.stdout.readline()
                if line:
                    line = line.strip()
                    # 检查音频相关事件
                    if any(keyword in line.lower() for keyword in 
                          ['audio_mode', 'ringtone', 'mode_in_call', 'audio focus']):
                        print(f"🔊 音频日志: {line}")
                        self._trigger_callbacks("audio_log", line)
                        
        except Exception as e:
            print(f"❌ 音频日志监控失败: {e}")
    
    def _monitor_activity(self):
        """监控活动变化"""
        last_activity = ""
        
        while self.is_monitoring:
            try:
                result = subprocess.run([self.adb_path, "shell", "dumpsys", "activity", "top"],
                                      capture_output=True, text=True, timeout=2)
                
                if result.returncode == 0:
                    current_activity = ""
                    for line in result.stdout.split('\n'):
                        if 'ACTIVITY' in line and any(keyword in line.lower() for keyword in 
                                                    ['dialer', 'phone', 'call', 'incall']):
                            current_activity = line.strip()
                            break
                    
                    if current_activity and current_activity != last_activity:
                        print(f"📱 电话活动变化: {current_activity}")
                        self._trigger_callbacks("activity_change", current_activity)
                        last_activity = current_activity
                
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ 活动监控失败: {e}")
                time.sleep(2)
    
    def _trigger_callbacks(self, event_type, data):
        """触发回调"""
        for callback in self.detection_callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                print(f"❌ 回调执行失败: {e}")

def on_call_detected(event_type, data):
    """来电检测回调"""
    print(f"🔔 检测到事件: {event_type}")
    print(f"📄 数据: {data}")
    
    # 更精准地检测来电状态
    incoming_keywords = ['incoming call', 'call_state_ringing', 'phone_state_ringing', 'isringing=true']
    ringing_keywords = ['ringing call state: 1', 'call state: 1', 'callstate 1']
    
    data_lower = data.lower()
    
    # 检测真正的来电状态
    if any(keyword in data_lower for keyword in incoming_keywords + ringing_keywords):
        print("⚡ 检测到真实来电，触发智能代接处理！")
        handle_incoming_call()
    elif 'ringing' in data_lower and ('true' in data_lower or 'call' in data_lower):
        print("⚡ 检测到响铃状态，触发智能代接处理！")
        handle_incoming_call()

def handle_incoming_call():
    """处理来电的完整流程"""
    import time
    
    try:
        print("🚀 开始智能代接流程...")
        
        # 防重复处理检查
        current_time = time.time()
        if not hasattr(handle_incoming_call, 'last_call_handled'):
            handle_incoming_call.last_call_handled = 0
        
        if current_time - handle_incoming_call.last_call_handled < 10:  # 10秒冷却
            print("⏰ 冷却时间内，忽略重复来电事件")
            return
        
        handle_incoming_call.last_call_handled = current_time
        
        # 1. 接听电话 (keyevent 5)
        print("📞 步骤1: 接听来电...")
        try:
            result = subprocess.run(["./platform-tools/adb.exe", "shell", "input", "keyevent", "5"],
                                  capture_output=True, text=True, timeout=5)
            print(f"📞 接听命令返回码: {result.returncode}")
            if result.stdout:
                print(f"📞 接听命令输出: {result.stdout}")
            if result.stderr:
                print(f"📞 接听命令错误: {result.stderr}")
                
            if result.returncode == 0:
                print("✅ 成功发送接听命令")
            else:
                print(f"❌ 接听命令失败，返回码: {result.returncode}")
        except Exception as e:
            print(f"❌ 执行接听命令异常: {e}")
        
        # 2. 等待连接稳定
        print("⏱️ 步骤2: 等待连接稳定...")
        time.sleep(3)
        
        # 3. 播放语音回复
        print("🎤 步骤3: 播放语音回复...")
        response_text = "您好，我现在不方便接听电话，有重要事情请稍后联系，谢谢！"
        
        try:
            # 使用TTS播放回复
            tts_result = subprocess.run([
                "./platform-tools/adb.exe", "shell", 
                "cmd", "media_session", "dispatch", "com.android.tts", "speak", response_text
            ], capture_output=True, text=True, timeout=8)
            
            print(f"🎤 TTS命令返回码: {tts_result.returncode}")
            if tts_result.stdout:
                print(f"🎤 TTS命令输出: {tts_result.stdout}")
            if tts_result.stderr:
                print(f"🎤 TTS命令错误: {tts_result.stderr}")
            
            if tts_result.returncode == 0:
                print("✅ 成功发送TTS命令")
            else:
                print(f"❌ TTS命令失败，尝试备用方案...")
                # 备用方案：简单的音频播放
                backup_result = subprocess.run([
                    "./platform-tools/adb.exe", "shell",
                    "settings", "put", "secure", "tts_default_synth", "com.google.android.tts"
                ], capture_output=True, text=True, timeout=5)
                print(f"🎤 备用方案返回码: {backup_result.returncode}")
                
        except Exception as e:
            print(f"❌ 执行TTS命令异常: {e}")
        
        # 4. 等待播放完成
        print("⏱️ 步骤4: 等待播放完成...")
        time.sleep(6)
        
        # 5. 挂断电话 (keyevent 6)
        print("📴 步骤5: 挂断电话...")
        try:
            hangup_result = subprocess.run(["./platform-tools/adb.exe", "shell", "input", "keyevent", "6"],
                                         capture_output=True, text=True, timeout=5)
            print(f"📴 挂断命令返回码: {hangup_result.returncode}")
            if hangup_result.stdout:
                print(f"📴 挂断命令输出: {hangup_result.stdout}")
            if hangup_result.stderr:
                print(f"📴 挂断命令错误: {hangup_result.stderr}")
                
            if hangup_result.returncode == 0:
                print("✅ 成功发送挂断命令")
            else:
                print(f"❌ 挂断命令失败，返回码: {hangup_result.returncode}")
        except Exception as e:
            print(f"❌ 执行挂断命令异常: {e}")
        
        print("🎉 智能代接流程完成！")
        
    except Exception as e:
        print(f"❌ 智能代接流程总体异常: {e}")
        import traceback
        print(f"❌ 异常详情: {traceback.format_exc()}")

def main():
    """主函数"""
    print("📞 真实来电实时检测系统")
    print("=" * 50)
    
    detector = RealTimeCallDetector()
    detector.add_callback(on_call_detected)
    
    print("🚀 启动实时监控...")
    detector.start_monitoring()
    
    try:
        print("\n📱 请用另一台手机拨打您的电话进行测试")
        print("系统将实时显示所有相关事件")
        print("按 Ctrl+C 停止监控")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 用户停止监控")
        detector.stop_monitoring()

if __name__ == "__main__":
    main()
