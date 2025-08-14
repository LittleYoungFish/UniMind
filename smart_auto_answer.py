#!/usr/bin/env python3
"""
智能代接系统 - 使用gTTS语音回复
"""

import subprocess
import time
import os
# 尝试导入语音库
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

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

def execute_auto_answer():
    """执行自动接听流程"""
    print("🚨 执行自动接听流程...")
    
    try:
        # 1. 接听电话
        print("📞 接听电话...")
        os.system("platform-tools\\adb.exe shell input keyevent 5")
        
        # 2. 等待连接稳定
        time.sleep(1)
        
        # 3. 播放语音回复
        print("🎤 播放语音回复...")
        
        text = "您好，我现在不方便接听电话，有重要事情请稍后联系，谢谢！"
        voice_success = False
        
        # 尝试方法1：pyttsx3（离线）
        if PYTTSX3_AVAILABLE and not voice_success:
            try:
                print("🎤 使用pyttsx3生成语音...")
                engine = pyttsx3.init()
                
                # 设置语音属性
                voices = engine.getProperty('voices')
                if len(voices) > 1:
                    engine.setProperty('voice', voices[1].id)  # 尝试女声
                engine.setProperty('rate', 150)  # 语速
                engine.setProperty('volume', 1.0)  # 音量
                
                # 生成语音文件
                audio_file = "voice_reply.wav"
                engine.save_to_file(text, audio_file)
                engine.runAndWait()
                
                if os.path.exists(audio_file):
                    # 推送到设备
                    device_path = "/sdcard/voice_reply.wav"
                    os.system(f'platform-tools\\adb.exe push "{audio_file}" "{device_path}"')
                    
                    # 播放音频
                    os.system(f'platform-tools\\adb.exe shell "am start -a android.intent.action.VIEW -d file://{device_path} -t audio/wav"')
                    
                    # 删除本地文件
                    os.remove(audio_file)
                    
                    print("✅ pyttsx3语音播放成功")
                    voice_success = True
                    
            except Exception as e:
                print(f"❌ pyttsx3失败: {e}")
        
        # 尝试方法2：gTTS（在线）
        if GTTS_AVAILABLE and not voice_success:
            try:
                print("🎤 使用gTTS生成语音...")
                tts = gTTS(text=text, lang='zh', slow=False)
                
                audio_file = "voice_reply.mp3"
                tts.save(audio_file)
                
                # 推送到设备
                device_path = "/sdcard/voice_reply.mp3"
                os.system(f'platform-tools\\adb.exe push "{audio_file}" "{device_path}"')
                
                # 播放音频文件
                os.system(f'platform-tools\\adb.exe shell "am start -a android.intent.action.VIEW -d file://{device_path} -t audio/mpeg"')
                
                # 删除本地文件
                if os.path.exists(audio_file):
                    os.remove(audio_file)
                
                print("✅ gTTS语音播放成功")
                voice_success = True
                
            except Exception as e:
                print(f"❌ gTTS失败: {e}")
        
        # 备用方案
        if not voice_success:
            print("🎤 使用备用提示方案...")
            # 发送通知
            os.system('platform-tools\\adb.exe shell "cmd notification post -S bigtext -t \'智能代接\' \'AutoReply\' \'现在不方便接听，请稍后联系\'"')
            # 播放系统音效
            os.system('platform-tools\\adb.exe shell "input keyevent KEYCODE_CAMERA"')
            time.sleep(0.3)
            os.system('platform-tools\\adb.exe shell "input keyevent KEYCODE_FOCUS"')
            print("✅ 备用提示已发送")
        
        # 4. 等待播放
        time.sleep(4)
        
        # 5. 挂断电话
        print("📴 挂断电话...")
        os.system("platform-tools\\adb.exe shell input keyevent 6")
        
        print("✅ 自动接听完成！")
        print("🔚 智能代接流程结束，程序退出")
        return True  # 返回True表示需要退出程序
        
    except Exception as e:
        print(f"❌ 执行异常: {e}")
        return False

def main():
    print("🚀 智能代接系统 (gTTS版本)")
    print("📱 使用dumpsys telephony.registry检测来电...")
    print("🎤 使用gTTS生成语音回复")
    print("按 Ctrl+C 停止监控")
    print("-" * 40)
    
    last_call_time = 0
    
    while True:
        try:
            # 获取telephony状态
            telephony_output = get_telephony_state()
            
            # 检查是否有来电
            if is_incoming_call(telephony_output):
                current_time = time.time()
                
                # 防重复执行（5秒内只执行一次）
                if current_time - last_call_time > 5:
                    print("🔔 检测到来电！")
                    should_exit = execute_auto_answer()
                    if should_exit:
                        print("👋 程序正常退出")
                        break
                    last_call_time = current_time
            
            time.sleep(0.5)  # 0.5秒检查一次
            
        except KeyboardInterrupt:
            print("\n🛑 停止监控")
            break
        except Exception as e:
            print(f"❌ 监控异常: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
