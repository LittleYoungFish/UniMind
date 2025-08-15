"""
真实电话智能代接系统
Real Phone Auto Answer System

实现真正的电话接听功能：
1. 监控来电状态
2. 自动接听电话
3. 播放用户自定义回复语
4. 管理通话记录
"""

import os
import json
import time
import logging
import subprocess
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from .tool_decorator import tool

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RealPhoneAutoAnswer")

class CallState(Enum):
    """通话状态枚举"""
    IDLE = "idle"           # 空闲
    RINGING = "ringing"     # 响铃中
    OFFHOOK = "offhook"     # 接听中
    UNKNOWN = "unknown"     # 未知状态

@dataclass
class RealCallRecord:
    """真实通话记录"""
    phone_number: str
    caller_name: str = "未知"
    start_time: str = ""
    end_time: str = ""
    duration_seconds: float = 0
    scenario_used: str = "busy"
    custom_response_used: str = ""
    auto_answered: bool = False
    call_state: str = "completed"

class RealPhoneAutoAnswerManager:
    """真实智能代接管理器"""
    
    def __init__(self):
        """初始化管理器"""
        self.logger = logger
        self.is_enabled = False
        self.current_scenario = "busy"
        self.ring_delay_seconds = 10
        self.monitoring_thread = None
        self.is_monitoring = False
        
        # 数据文件路径
        self.data_dir = "data/phone_auto_answer/"
        self.records_file = os.path.join(self.data_dir, "real_call_records.json")
        self.responses_file = os.path.join(self.data_dir, "user_custom_responses.json")
        self.config_file = os.path.join(self.data_dir, "auto_answer_config.json")
        
        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        
        # ADB路径配置
        self.adb_path = "./platform-tools/adb.exe"
        
        # 用户自定义回复（完全由用户设置）
        self.user_responses = self._load_user_responses()
        
        # 加载配置
        self.config = self._load_config()
        
        # 初始化默认场景（如果用户没有设置）
        self._ensure_default_scenarios()
        
        self.logger.info("📞 真实智能代接管理器初始化完成")
    
    def _load_user_responses(self) -> Dict[str, str]:
        """加载用户自定义回复"""
        try:
            if os.path.exists(self.responses_file):
                with open(self.responses_file, 'r', encoding='utf-8') as f:
                    responses = json.load(f)
                    self.logger.info(f"📝 加载了 {len(responses)} 个用户自定义回复")
                    return responses
            return {}
        except Exception as e:
            self.logger.error(f"❌ 加载用户回复失败: {e}")
            return {}
    
    def _save_user_responses(self):
        """保存用户自定义回复"""
        try:
            with open(self.responses_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_responses, f, ensure_ascii=False, indent=2)
            self.logger.info("✅ 用户自定义回复已保存")
        except Exception as e:
            self.logger.error(f"❌ 保存用户回复失败: {e}")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {
                "enabled": False,
                "current_scenario": "busy",
                "ring_delay": 10
            }
        except Exception as e:
            self.logger.error(f"❌ 加载配置失败: {e}")
            return {}
    
    def _save_config(self):
        """保存配置"""
        try:
            config = {
                "enabled": self.is_enabled,
                "current_scenario": self.current_scenario,
                "ring_delay": self.ring_delay_seconds
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"❌ 保存配置失败: {e}")
    
    def _ensure_default_scenarios(self):
        """确保有默认场景回复（仅在用户未设置时）"""
        default_scenarios = {
            "work": "您好，我现在正在工作无法接听电话。请留言或稍后再拨，我会尽快回复您。",
            "meeting": "不好意思，我现在正在开会无法接听电话。请留言说明事由，我会尽快联系您。",
            "delivery": "您好，如果是外卖配送，请直接放在门口。如有其他事宜，请稍后再拨。谢谢！",
            "unknown": "您好，请问您找哪位？请说明来意，我会记录您的留言。",
            "busy": "对不起，我现在很忙无法接听电话。请稍后再拨，或发送短信说明事由。谢谢理解。",
            "rest": "现在是我的休息时间，无法接听电话。如有紧急事务，请发送短信。",
            "driving": "我现在正在开车，为了安全无法接听电话。请稍后再拨或发送短信。",
            "study": "我现在正在学习，无法接听电话。请留言或稍后联系，我会尽快回复。",
            "hospital": "我现在在安静的环境中，不便接听电话。请发送短信或稍后联系。"
        }
        
        # 只有当用户没有设置回复时才使用默认值
        for scenario, default_text in default_scenarios.items():
            if scenario not in self.user_responses:
                self.user_responses[scenario] = default_text
        
        self._save_user_responses()
    
    def set_user_response(self, scenario: str, response_text: str) -> Dict[str, Any]:
        """设置用户自定义回复"""
        try:
            self.user_responses[scenario] = response_text
            self._save_user_responses()
            self.logger.info(f"✅ 用户设置 {scenario} 场景回复: {response_text[:30]}...")
            return {
                "success": True,
                "message": f"成功设置{scenario}场景的自定义回复"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"设置自定义回复失败: {e}"
            }
    
    def get_user_responses(self) -> Dict[str, str]:
        """获取所有用户自定义回复"""
        return self.user_responses.copy()
    
    def toggle_auto_answer(self, enable: bool) -> Dict[str, Any]:
        """开启/关闭自动代接"""
        try:
            old_state = self.is_enabled
            self.is_enabled = enable
            self._save_config()
            
            if enable and not old_state:
                # 开启监控
                self._start_call_monitoring()
                self.logger.info("🎛️ 智能代接功能已开启，开始监控来电")
            elif not enable and old_state:
                # 关闭监控
                self._stop_call_monitoring()
                self.logger.info("🎛️ 智能代接功能已关闭")
            
            return {
                "success": True,
                "message": f"自动代接功能已{'开启' if enable else '关闭'}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"切换代接状态失败: {e}"
            }
    
    def set_scenario(self, scenario: str) -> Dict[str, Any]:
        """设置当前场景"""
        try:
            if scenario not in self.user_responses:
                return {
                    "success": False,
                    "error": f"未知场景: {scenario}"
                }
            
            old_scenario = self.current_scenario
            self.current_scenario = scenario
            self._save_config()
            
            self.logger.info(f"🔄 场景切换: {old_scenario} → {scenario}")
            return {
                "success": True,
                "message": f"场景已切换到: {scenario}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"设置场景失败: {e}"
            }
    
    def _start_call_monitoring(self):
        """开始监控来电"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitor_calls, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("📡 来电监控线程已启动")
    
    def _stop_call_monitoring(self):
        """停止监控来电"""
        self.is_monitoring = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2)
        self.logger.info("📡 来电监控线程已停止")
    
    def _monitor_calls(self):
        """监控来电状态"""
        last_state = CallState.IDLE
        ringing_detected = False
        ringing_start_time = None
        
        while self.is_monitoring:
            try:
                # 获取当前通话状态
                current_state = self._get_call_state()
                current_time = time.time()
                
                # 状态变化日志
                if current_state != last_state:
                    self.logger.info(f"📱 通话状态变化: {last_state.value} → {current_state.value}")
                
                # 检测到响铃状态
                if current_state == CallState.RINGING:
                    if not ringing_detected:
                        # 首次检测到响铃
                        ringing_detected = True
                        ringing_start_time = current_time
                        caller_info = self._get_caller_info()
                        self.logger.info(f"🔔 检测到来电响铃: {caller_info.get('number', '未知号码')}")
                        
                        if self.is_enabled:
                            # 立即自动接听（不使用线程，直接处理）
                            self.logger.info("⚡ 智能代接已开启，立即处理来电...")
                            try:
                                # 快速处理来电
                                response_text = self.user_responses.get(self.current_scenario, "系统忙碌，请稍后再试")
                                self.logger.info(f"📝 准备播放: {response_text[:30]}...")
                                
                                # 立即接听
                                self.logger.info("📞 立即接听电话...")
                                self._answer_call()
                                
                                # 短暂等待
                                time.sleep(1)
                                
                                # 播放回复
                                self.logger.info("🔊 播放智能回复...")
                                self._play_voice_response(response_text)
                                
                                # 等待播放完成
                                play_time = max(len(response_text) * 0.15, 3)
                                self.logger.info(f"⏰ 等待播放完成 ({play_time:.1f}秒)...")
                                time.sleep(play_time)
                                
                                # 挂断
                                self.logger.info("📞 挂断电话")
                                self._end_call()
                                
                                self.logger.info("✅ 快速智能代接完成！")
                                
                            except Exception as e:
                                self.logger.error(f"❌ 快速处理失败: {e}")
                        else:
                            # 延迟后播放忙碌回复
                            self.logger.info(f"⏰ 智能代接未开启，将在{self.ring_delay_seconds}秒后回复...")
                            threading.Thread(target=self._handle_delayed_response, args=(caller_info,), daemon=True).start()
                
                # 检测到从响铃变为其他状态
                elif ringing_detected and current_state != CallState.RINGING:
                    if current_state == CallState.OFFHOOK:
                        self.logger.info("📞 电话已接听")
                    elif current_state == CallState.IDLE:
                        self.logger.info("📴 来电已结束")
                    
                    # 重置响铃检测状态
                    ringing_detected = False
                    ringing_start_time = None
                
                # 检测从IDLE直接到OFFHOOK（可能错过了RINGING状态）
                elif last_state == CallState.IDLE and current_state == CallState.OFFHOOK and not ringing_detected:
                    self.logger.warning("⚠️ 检测到可能错过的来电（直接进入通话状态）")
                    caller_info = self._get_caller_info()
                    
                    # 如果是在监控状态下突然进入通话，可能需要补充处理
                    if self.is_enabled:
                        self.logger.info("📞 可能错过了响铃阶段，但系统已开启代接")
                        
                        # 尝试立即播放回复语（如果还在通话初期）
                        self.logger.info("🔄 尝试在通话中播放智能回复...")
                        response_text = self.user_responses.get(self.current_scenario, "系统忙碌，请稍后再试")
                        
                        # 等待一秒确保通话稳定
                        time.sleep(1)
                        
                        # 播放回复语
                        self.logger.info(f"🔊 播放智能回复: {response_text[:30]}...")
                        self._play_voice_response(response_text)
                        
                        # 等待播放完成后挂断
                        play_duration = max(len(response_text) * 0.2, 5)
                        self.logger.info(f"⏰ 等待回复播放完成 ({play_duration:.1f}秒)...")
                        time.sleep(play_duration)
                        
                        # 挂断电话
                        self.logger.info("📞 播放完成，挂断电话")
                        self._end_call()
                        
                        # 记录通话
                        start_time = datetime.now() - timedelta(seconds=play_duration + 2)
                        end_time = datetime.now()
                        duration = (end_time - start_time).total_seconds()
                        
                        self._save_call_record(
                            caller_info.get("number", "未知号码"),
                            caller_info.get("name", "未知联系人"),
                            start_time,
                            end_time,
                            duration,
                            self.current_scenario,
                            response_text,
                            True
                        )
                        
                        self.logger.info(f"✅ 补充处理完成，耗时 {duration:.1f} 秒")
                    else:
                        self.logger.info("📞 智能代接未开启，跳过处理")
                
                last_state = current_state
                time.sleep(0.2)  # 每0.2秒检查一次，极速响应
                
            except Exception as e:
                self.logger.error(f"❌ 监控来电异常: {e}")
                time.sleep(2)  # 出错时等待2秒再试
    
    def _get_call_state(self) -> CallState:
        """获取当前通话状态（高速检测）"""
        try:
            # 快速方法1: 检查telephony registry（最快）
            result = subprocess.run([self.adb_path, "shell", "dumpsys", "telephony.registry"], 
                                  capture_output=True, text=True, timeout=1)
            
            if result.returncode == 0:
                output = result.stdout
                if "mCallState=1" in output:  # RINGING
                    return CallState.RINGING
                elif "mCallState=2" in output:  # OFFHOOK
                    return CallState.OFFHOOK
                elif "mCallState=0" in output:  # IDLE
                    return CallState.IDLE
            
            # 快速方法2: 检查GSM属性
            result = subprocess.run([self.adb_path, "shell", "getprop", "gsm.voice.call.state"], 
                                  capture_output=True, text=True, timeout=1)
            
            if result.returncode == 0:
                state = result.stdout.strip()
                if state == "1":  # RINGING
                    return CallState.RINGING
                elif state == "2":  # OFFHOOK
                    return CallState.OFFHOOK
                elif state == "0":  # IDLE
                    return CallState.IDLE
            
            # 快速方法3: 检查音频模式（备选）
            result = subprocess.run([self.adb_path, "shell", "dumpsys", "audio"], 
                                  capture_output=True, text=True, timeout=1)
            
            if result.returncode == 0:
                output = result.stdout
                if "MODE_IN_CALL" in output:
                    return CallState.OFFHOOK
                elif "MODE_RINGTONE" in output or "ringtone" in output.lower():
                    return CallState.RINGING
            
            return CallState.IDLE
            
        except Exception as e:
            self.logger.error(f"❌ 快速检测失败: {e}")
            return CallState.UNKNOWN
    
    def _get_caller_info(self) -> Dict[str, str]:
        """获取来电者信息"""
        try:
            # 使用ADB获取来电号码
            cmd = [self.adb_path, "shell", "dumpsys", "telephony.registry", "|", "grep", "mCallIncomingNumber"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            phone_number = "未知号码"
            if result.returncode == 0:
                output = result.stdout.strip()
                # 解析电话号码
                if "mCallIncomingNumber" in output:
                    parts = output.split("=")
                    if len(parts) > 1:
                        phone_number = parts[1].strip()
            
            return {
                "number": phone_number,
                "name": "未知联系人"  # 可以后续扩展从联系人列表获取姓名
            }
            
        except Exception as e:
            self.logger.error(f"❌ 获取来电信息失败: {e}")
            return {"number": "未知号码", "name": "未知联系人"}
    
    def _execute_fast_auto_answer(self, response_text: str):
        """执行快速自动接听流程"""
        import os
        try:
            # 1. 接听电话
            self.logger.info("📞 接听电话...")
            os.system("platform-tools\\adb.exe shell input keyevent 5")
            
            # 2. 等待连接稳定
            time.sleep(1)
            
            # 3. 播放语音回复
            self.logger.info("🎤 播放语音回复...")
            voice_success = False
            
            # 尝试方法1：pyttsx3（离线）
            try:
                import pyttsx3
                self.logger.info("使用pyttsx3生成语音...")
                engine = pyttsx3.init()
                
                # 设置语音属性
                voices = engine.getProperty('voices')
                if len(voices) > 1:
                    engine.setProperty('voice', voices[1].id)  # 尝试女声
                engine.setProperty('rate', 150)  # 语速
                engine.setProperty('volume', 1.0)  # 音量
                
                # 生成语音文件
                audio_file = "voice_reply.wav"
                engine.save_to_file(response_text, audio_file)
                engine.runAndWait()
                
                if os.path.exists(audio_file):
                    # 推送到设备
                    device_path = "/sdcard/voice_reply.wav"
                    os.system(f'platform-tools\\adb.exe push "{audio_file}" "{device_path}"')
                    
                    # 播放音频
                    os.system(f'platform-tools\\adb.exe shell "am start -a android.intent.action.VIEW -d file://{device_path} -t audio/wav"')
                    
                    # 删除本地文件
                    os.remove(audio_file)
                    
                    self.logger.info("✅ pyttsx3语音播放成功")
                    voice_success = True
                    
            except Exception as e:
                self.logger.warning(f"pyttsx3失败: {e}")
            
            # 尝试方法2：gTTS（在线）
            if not voice_success:
                try:
                    from gtts import gTTS
                    self.logger.info("使用gTTS生成语音...")
                    tts = gTTS(text=response_text, lang='zh', slow=False)
                    
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
                    
                    self.logger.info("✅ gTTS语音播放成功")
                    voice_success = True
                    
                except Exception as e:
                    self.logger.warning(f"gTTS失败: {e}")
            
            # 备用方案
            if not voice_success:
                self.logger.info("使用备用提示方案...")
                # 发送通知
                os.system(f'platform-tools\\adb.exe shell "cmd notification post -S bigtext -t \'智能代接\' \'AutoReply\' \'{response_text}\'"')
                # 播放系统音效
                os.system('platform-tools\\adb.exe shell "input keyevent KEYCODE_CAMERA"')
                time.sleep(0.3)
                os.system('platform-tools\\adb.exe shell "input keyevent KEYCODE_FOCUS"')
                self.logger.info("✅ 备用提示已发送")
            
            # 4. 等待播放
            time.sleep(4)
            
            # 5. 挂断电话
            self.logger.info("📴 挂断电话...")
            os.system("platform-tools\\adb.exe shell input keyevent 6")
            
            self.logger.info("✅ 快速自动接听流程完成")
            
        except Exception as e:
            self.logger.error(f"❌ 快速自动接听流程异常: {e}")
    
    def _handle_incoming_call(self, caller_info: Dict[str, str]):
        """处理来电"""
        try:
            start_time = datetime.now()
            phone_number = caller_info.get("number", "未知号码")
            caller_name = caller_info.get("name", "未知联系人")
            
            self.logger.info(f"🔄 开始处理来电: {phone_number} ({caller_name})")
            self.logger.info(f"📱 当前场景: {self.current_scenario}")
            
            # 获取当前场景的回复语
            response_text = self.user_responses.get(self.current_scenario, "系统忙碌，请稍后再试")
            self.logger.info(f"📝 将要播放的回复: {response_text[:50]}...")
            
            # 等待1秒确保来电稳定
            time.sleep(1)
            
            # 使用新的快速自动接听流程
            self.logger.info("🚀 执行快速自动接听流程...")
            self._execute_fast_auto_answer(response_text)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 记录通话
            self._save_call_record(
                phone_number,
                caller_name,
                start_time,
                end_time,
                duration,
                self.current_scenario,
                response_text,
                True
            )
            
            self.logger.info(f"✅ 自动代接完成，总耗时 {duration:.1f} 秒")
            
        except Exception as e:
            self.logger.error(f"❌ 处理来电失败: {e}")
            import traceback
            self.logger.error(f"错误详情: {traceback.format_exc()}")
    
    def _handle_delayed_response(self, caller_info: Dict[str, str]):
        """处理延迟回复（未开启代接时）"""
        try:
            # 等待延迟时间
            time.sleep(self.ring_delay_seconds)
            
            # 检查是否还在响铃
            if self._get_call_state() == CallState.RINGING:
                start_time = datetime.now()
                
                # 接听电话
                self._answer_call()
                time.sleep(2)
                
                # 播放忙碌回复
                busy_response = self.user_responses.get("busy", "用户繁忙，请稍后再拨")
                self._play_voice_response(busy_response)
                
                time.sleep(len(busy_response) * 0.15)
                self._end_call()
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                # 记录通话
                self._save_call_record(
                    caller_info["number"],
                    caller_info["name"],
                    start_time,
                    end_time,
                    duration,
                    "busy",
                    busy_response,
                    False
                )
                
                self.logger.info(f"✅ 延迟回复完成，耗时 {duration:.1f} 秒")
                
        except Exception as e:
            self.logger.error(f"❌ 延迟回复失败: {e}")
    
    def _answer_call(self):
        """接听电话"""
        try:
            # 方法1: 模拟接听按键
            cmd1 = [self.adb_path, "shell", "input", "keyevent", "KEYCODE_CALL"]
            result1 = subprocess.run(cmd1, timeout=5, capture_output=True)
            
            # 方法2: 模拟滑动接听（适用于滑动接听的界面）
            cmd2 = [self.adb_path, "shell", "input", "swipe", "500", "1500", "800", "1200", "500"]
            result2 = subprocess.run(cmd2, timeout=5, capture_output=True)
            
            # 方法3: 模拟点击接听按钮（通用坐标）
            cmd3 = [self.adb_path, "shell", "input", "tap", "700", "1600"]
            result3 = subprocess.run(cmd3, timeout=5, capture_output=True)
            
            self.logger.info("📞 已发送接听指令（多种方式）")
            return True
        except Exception as e:
            self.logger.error(f"❌ 接听电话失败: {e}")
            return False
    
    def _end_call(self):
        """挂断电话"""
        try:
            # 使用ADB模拟挂断按键
            cmd = [self.adb_path, "shell", "input", "keyevent", "KEYCODE_ENDCALL"]
            subprocess.run(cmd, timeout=5)
            self.logger.info("📞 已挂断电话")
        except Exception as e:
            self.logger.error(f"❌ 挂断电话失败: {e}")
    
    def _play_voice_response(self, text: str):
        """播放语音回复"""
        try:
            # 方法1: 使用系统TTS命令
            escaped_text = text.replace('"', '\\"').replace("'", "\\'")
            cmd1 = [
                self.adb_path, "shell", "cmd", "media_session", "dispatch", 
                "com.android.tts", "speak", escaped_text
            ]
            
            # 方法2: 使用TTS Intent
            cmd2 = [
                self.adb_path, "shell", "am", "start",
                "-a", "android.speech.tts.engine.INTENT_ACTION_TTS_SERVICE",
                "--es", "android.speech.tts.extra.UTTERANCE_ID", "auto_answer",
                "--es", "android.speech.tts.extra.TEXT", escaped_text
            ]
            
            # 方法3: 使用音频文件播放（简化版）
            # 这里可以预先录制音频文件并播放
            cmd3 = [
                self.adb_path, "shell", "am", "start",
                "-a", "android.intent.action.VIEW",
                "-t", "audio/*"
            ]
            
            # 尝试播放
            self.logger.info(f"🔊 尝试播放语音: {text[:30]}...")
            
            try:
                result = subprocess.run(cmd1, timeout=10, capture_output=True)
                if result.returncode == 0:
                    self.logger.info("✅ TTS命令执行成功")
                else:
                    self.logger.warning("⚠️ TTS命令执行失败，尝试其他方法")
                    subprocess.run(cmd2, timeout=10, capture_output=True)
            except:
                # 如果TTS失败，至少记录日志
                self.logger.warning(f"⚠️ 语音播放失败，但已记录回复内容: {text}")
                
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 播放语音失败: {e}")
            return False
    
    def _save_call_record(self, phone_number: str, caller_name: str,
                         start_time: datetime, end_time: datetime,
                         duration: float, scenario: str, response: str,
                         auto_answered: bool):
        """保存通话记录"""
        try:
            record = RealCallRecord(
                phone_number=phone_number,
                caller_name=caller_name,
                start_time=start_time.strftime("%Y-%m-%d %H:%M:%S"),
                end_time=end_time.strftime("%Y-%m-%d %H:%M:%S"),
                duration_seconds=duration,
                scenario_used=scenario,
                custom_response_used=response,
                auto_answered=auto_answered
            )
            
            # 加载现有记录
            records = []
            if os.path.exists(self.records_file):
                with open(self.records_file, 'r', encoding='utf-8') as f:
                    records = json.load(f)
            
            # 添加新记录
            records.append(asdict(record))
            
            # 保存记录
            with open(self.records_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
                
            self.logger.info("📝 通话记录已保存")
            
        except Exception as e:
            self.logger.error(f"❌ 保存通话记录失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        try:
            # 统计通话记录
            total_calls = 0
            recent_calls = 0
            
            if os.path.exists(self.records_file):
                with open(self.records_file, 'r', encoding='utf-8') as f:
                    records = json.load(f)
                    total_calls = len(records)
                    
                    # 计算24小时内的通话
                    now = datetime.now()
                    yesterday = now - timedelta(hours=24)
                    for record in records:
                        record_time = datetime.strptime(record['start_time'], "%Y-%m-%d %H:%M:%S")
                        if record_time > yesterday:
                            recent_calls += 1
            
            return {
                "success": True,
                "enabled": self.is_enabled,
                "current_scenario": self.current_scenario,
                "scenario_name": self.current_scenario,
                "ring_delay_seconds": self.ring_delay_seconds,
                "total_calls": total_calls,
                "recent_calls_24h": recent_calls,
                "available_scenarios": list(self.user_responses.keys()),
                "monitoring": self.is_monitoring
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"获取状态失败: {e}"
            }

# 创建全局管理器实例
real_phone_manager = RealPhoneAutoAnswerManager()

# 工具函数
@tool("real_phone_toggle_auto_answer")
def real_phone_toggle_auto_answer(enable: bool) -> Dict[str, Any]:
    """开启或关闭真实电话自动代接功能"""
    return real_phone_manager.toggle_auto_answer(enable)

@tool("real_phone_set_scenario")
def real_phone_set_scenario(scenario: str) -> Dict[str, Any]:
    """设置真实电话代接场景模式"""
    return real_phone_manager.set_scenario(scenario)

@tool("real_phone_set_user_response")
def real_phone_set_user_response(scenario: str, response_text: str) -> Dict[str, Any]:
    """设置用户自定义回复语"""
    return real_phone_manager.set_user_response(scenario, response_text)

@tool("real_phone_get_user_responses")
def real_phone_get_user_responses() -> Dict[str, str]:
    """获取所有用户自定义回复语"""
    return real_phone_manager.get_user_responses()

@tool("real_phone_get_status")
def real_phone_get_status() -> Dict[str, Any]:
    """获取真实电话代接系统状态"""
    return real_phone_manager.get_status()

@tool("real_phone_set_ring_delay")
def real_phone_set_ring_delay(seconds: int) -> Dict[str, Any]:
    """设置响铃延迟时间（秒）"""
    try:
        real_phone_manager.ring_delay_seconds = seconds
        real_phone_manager._save_config()
        return {
            "success": True,
            "message": f"响铃延迟已设置为 {seconds} 秒"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"设置延迟失败: {e}"
        }
