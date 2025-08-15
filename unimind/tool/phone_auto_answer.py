"""
电话智能代接功能模块
Phone Auto Answer Module

基础版本实现：
1. 自动接听电话
2. 场景模式管理
3. 语音回复播放
4. 来电记录管理
"""

import os
import json
import time
import logging
import subprocess
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

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

from .tool_decorator import tool


class ScenarioMode(Enum):
    """场景模式枚举"""
    WORK = "work"           # 工作模式
    REST = "rest"           # 休息模式
    DRIVING = "driving"     # 驾驶模式
    MEETING = "meeting"     # 会议模式
    STUDY = "study"         # 学习模式
    DELIVERY = "delivery"   # 外卖模式
    UNKNOWN = "unknown"     # 陌生电话模式
    BUSY = "busy"           # 忙碌模式
    HOSPITAL = "hospital"   # 医院模式
    CUSTOM = "custom"       # 自定义模式


@dataclass
class CallRecord:
    """来电记录数据类"""
    phone_number: str
    caller_name: Optional[str]
    call_time: datetime
    scenario_mode: ScenarioMode
    response_played: str
    duration_seconds: float
    auto_answered: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "phone_number": self.phone_number,
            "caller_name": self.caller_name,
            "call_time": self.call_time.isoformat(),
            "scenario_mode": self.scenario_mode.value,
            "response_played": self.response_played,
            "duration_seconds": self.duration_seconds,
            "auto_answered": self.auto_answered
        }


@dataclass
class ScenarioConfig:
    """场景配置数据类"""
    mode: ScenarioMode
    name: str
    description: str
    response_text: str
    voice_file: Optional[str] = None
    auto_trigger_conditions: Optional[Dict[str, Any]] = None
    special_handling: Optional[Dict[str, Any]] = None


class PhoneAutoAnswerManager:
    """电话自动代接管理器"""
    
    def __init__(self, adb_path: str = "adb"):
        """初始化代接管理器"""
        self.adb_path = adb_path
        self.logger = self._setup_logging()
        self.current_scenario = ScenarioMode.BUSY  # 默认为忙碌模式
        self.is_enabled = False
        self.call_records: List[CallRecord] = []
        self.ring_delay_seconds = 10  # 响铃延迟时间（秒）
        self.custom_responses = {}  # 自定义回复语
        
        # 真实来电监控相关
        self.monitoring_thread = None
        self.is_monitoring = False
        self.last_call_time = 0
        
        # 创建必要的目录
        self.data_dir = "data/phone_auto_answer"
        self.voice_dir = "data/voice_responses"
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.voice_dir, exist_ok=True)
        
        # 加载配置
        self.scenarios = self._load_scenario_configs()
        self._load_call_records()
        self._load_custom_responses()
        
        self.logger.info("📞 电话自动代接管理器初始化完成")
    
    def _setup_logging(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger("PhoneAutoAnswer")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # 创建日志目录
            os.makedirs("logs", exist_ok=True)
            
            # 文件处理器
            file_handler = logging.FileHandler("logs/phone_auto_answer.log", encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # 格式化
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
            
        return logger
    
    def _load_scenario_configs(self) -> Dict[ScenarioMode, ScenarioConfig]:
        """加载场景配置"""
        scenarios = {}
        
        # 工作模式
        scenarios[ScenarioMode.WORK] = ScenarioConfig(
            mode=ScenarioMode.WORK,
            name="工作模式",
            description="工作时间自动回复",
            response_text="您好，我正在工作中，无法接听电话。如有紧急事务请发送短信，我会尽快回复。谢谢理解。",
            auto_trigger_conditions={
                "time_range": [(9, 0), (18, 0)],  # 9:00-18:00
                "weekdays_only": True
            }
        )
        
        # 休息模式
        scenarios[ScenarioMode.REST] = ScenarioConfig(
            mode=ScenarioMode.REST,
            name="休息模式",
            description="休息时间自动回复",
            response_text="现在是休息时间，请勿打扰。如有紧急情况请发送短信说明，明天我会及时回复。晚安。",
            auto_trigger_conditions={
                "time_range": [(22, 0), (7, 0)]  # 22:00-7:00
            }
        )
        
        # 驾驶模式
        scenarios[ScenarioMode.DRIVING] = ScenarioConfig(
            mode=ScenarioMode.DRIVING,
            name="驾驶模式", 
            description="驾驶时安全回复",
            response_text="我正在驾驶中，为了安全无法接听电话。请发送语音或文字信息，到达后立即回复。安全驾驶，人人有责。"
        )
        
        # 会议模式
        scenarios[ScenarioMode.MEETING] = ScenarioConfig(
            mode=ScenarioMode.MEETING,
            name="会议模式",
            description="会议中自动回复",
            response_text="我正在开会，暂时无法接听。会议结束后会及时回复您。紧急事务请发送文字说明。"
        )
        
        # 学习模式
        scenarios[ScenarioMode.STUDY] = ScenarioConfig(
            mode=ScenarioMode.STUDY,
            name="学习模式",
            description="学习时专注回复",
            response_text="我正在学习中，需要专注。请发送信息说明来意，稍后会回复您。感谢理解。"
        )
        
        # 外卖模式
        scenarios[ScenarioMode.DELIVERY] = ScenarioConfig(
            mode=ScenarioMode.DELIVERY,
            name="外卖模式",
            description="外卖配送场景回复",
            response_text="您好，请把外卖放在外卖柜里，谢谢。如果没有外卖柜，请放在门口，我稍后取。"
        )
        
        # 陌生电话模式
        scenarios[ScenarioMode.UNKNOWN] = ScenarioConfig(
            mode=ScenarioMode.UNKNOWN,
            name="陌生电话模式",
            description="接听陌生电话并记录",
            response_text="您好，我暂时无法接听电话。请您说明来意，我会记录您的留言并尽快回复。"
        )
        
        # 忙碌模式（默认模式）
        scenarios[ScenarioMode.BUSY] = ScenarioConfig(
            mode=ScenarioMode.BUSY,
            name="忙碌模式",
            description="默认忙碌回复",
            response_text="对不起，我现在很忙无法接听电话。请稍后再拨，或发送短信说明事由。谢谢理解。"
        )
        
        # 医院模式
        scenarios[ScenarioMode.HOSPITAL] = ScenarioConfig(
            mode=ScenarioMode.HOSPITAL,
            name="医院模式",
            description="医院等安静场所回复",
            response_text="我现在在医院等安静场所，不方便接听电话。有急事请发短信，我会尽快回复。"
        )
        
        self.logger.info(f"✅ 加载了 {len(scenarios)} 个场景配置")
        return scenarios
    
    def _load_call_records(self):
        """加载通话记录"""
        records_file = os.path.join(self.data_dir, "call_records.json")
        try:
            if os.path.exists(records_file):
                with open(records_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for record_data in data:
                        record = CallRecord(
                            phone_number=record_data["phone_number"],
                            caller_name=record_data.get("caller_name"),
                            call_time=datetime.fromisoformat(record_data["call_time"]),
                            scenario_mode=ScenarioMode(record_data["scenario_mode"]),
                            response_played=record_data["response_played"],
                            duration_seconds=record_data["duration_seconds"],
                            auto_answered=record_data["auto_answered"]
                        )
                        self.call_records.append(record)
                self.logger.info(f"📋 加载了 {len(self.call_records)} 条通话记录")
        except Exception as e:
            self.logger.warning(f"⚠️ 加载通话记录失败: {e}")
            self.call_records = []
    
    def _save_call_records(self):
        """保存通话记录"""
        records_file = os.path.join(self.data_dir, "call_records.json")
        try:
            data = [record.to_dict() for record in self.call_records]
            with open(records_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"❌ 保存通话记录失败: {e}")
    
    def _load_custom_responses(self):
        """加载自定义回复语"""
        custom_file = os.path.join(self.data_dir, "custom_responses.json")
        try:
            if os.path.exists(custom_file):
                with open(custom_file, 'r', encoding='utf-8') as f:
                    self.custom_responses = json.load(f)
                    self.logger.info(f"📝 加载了 {len(self.custom_responses)} 个自定义回复")
            else:
                self.custom_responses = {}
        except Exception as e:
            self.logger.warning(f"⚠️ 加载自定义回复失败: {e}")
            self.custom_responses = {}
    
    def _save_custom_responses(self):
        """保存自定义回复语"""
        custom_file = os.path.join(self.data_dir, "custom_responses.json")
        try:
            with open(custom_file, 'w', encoding='utf-8') as f:
                json.dump(self.custom_responses, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"❌ 保存自定义回复失败: {e}")
    
    def set_custom_response(self, scenario: str, response_text: str) -> Dict[str, Any]:
        """设置自定义回复语"""
        try:
            # 验证场景模式
            scenario_mode = ScenarioMode(scenario.lower())
            
            # 保存自定义回复
            self.custom_responses[scenario_mode.value] = response_text
            self._save_custom_responses()
            
            self.logger.info(f"✅ 设置 {scenario_mode.value} 模式自定义回复")
            
            return {
                "success": True,
                "scenario": scenario_mode.value,
                "response_text": response_text,
                "message": f"成功设置{self.scenarios[scenario_mode].name}的自定义回复"
            }
            
        except ValueError:
            return {
                "success": False,
                "error": f"无效的场景模式: {scenario}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"设置自定义回复失败: {str(e)}"
            }
    
    def get_custom_responses(self) -> Dict[str, str]:
        """获取所有自定义回复语"""
        return self.custom_responses.copy()
    
    def set_ring_delay(self, seconds: int) -> Dict[str, Any]:
        """设置响铃延迟时间"""
        try:
            if seconds < 0 or seconds > 60:
                return {
                    "success": False,
                    "error": "响铃延迟时间必须在0-60秒之间"
                }
            
            old_delay = self.ring_delay_seconds
            self.ring_delay_seconds = seconds
            
            self.logger.info(f"⏰ 响铃延迟时间已设置为 {seconds} 秒")
            
            return {
                "success": True,
                "old_delay": old_delay,
                "new_delay": seconds,
                "message": f"响铃延迟时间已设置为 {seconds} 秒"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"设置响铃延迟失败: {str(e)}"
            }
    
    def check_device_connection(self) -> bool:
        """检查设备连接状态"""
        try:
            result = subprocess.run([self.adb_path, "devices"], 
                                  capture_output=True, text=True, timeout=5)
            connected_devices = []
            for line in result.stdout.strip().split('\n')[1:]:
                if 'device' in line and 'offline' not in line:
                    device_id = line.split('\t')[0]
                    connected_devices.append(device_id)
            
            if connected_devices:
                self.logger.info(f"📱 检测到 {len(connected_devices)} 个设备连接")
                return True
            else:
                self.logger.warning("⚠️ 未检测到设备连接")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 设备连接检查失败: {e}")
            return False
    
    def get_current_scenario(self) -> ScenarioMode:
        """获取当前场景模式"""
        if not self.is_enabled:
            return self.current_scenario
        
        # 检查是否需要自动切换场景
        current_time = datetime.now()
        current_hour = current_time.hour
        is_weekday = current_time.weekday() < 5  # 0-4 是工作日
        
        # 检查休息模式
        rest_config = self.scenarios[ScenarioMode.REST]
        if rest_config.auto_trigger_conditions:
            time_range = rest_config.auto_trigger_conditions["time_range"]
            start_hour, end_hour = time_range[0][0], time_range[1][0]
            if current_hour >= start_hour or current_hour < end_hour:
                return ScenarioMode.REST
        
        # 检查工作模式
        work_config = self.scenarios[ScenarioMode.WORK]
        if work_config.auto_trigger_conditions and is_weekday:
            time_range = work_config.auto_trigger_conditions["time_range"]
            start_hour, end_hour = time_range[0][0], time_range[1][0]
            if start_hour <= current_hour < end_hour:
                return ScenarioMode.WORK
        
        return self.current_scenario
    
    def simulate_auto_answer_call(self, phone_number: str, caller_name: str = None) -> Dict[str, Any]:
        """模拟自动代接电话（增强版本）"""
        start_time = datetime.now()
        current_scenario = self.get_current_scenario()
        scenario_config = self.scenarios[current_scenario]
        
        self.logger.info(f"📞 收到来电: {phone_number} ({caller_name or '未知'}) - 场景: {scenario_config.name}")
        
        try:
            # 响铃延迟（如果未开启自动代接，则使用默认延迟）
            if not self.is_enabled:
                self.logger.info(f"⏰ 自动代接未开启，响铃 {self.ring_delay_seconds} 秒后回复")
                time.sleep(self.ring_delay_seconds)
                # 使用忙碌模式的默认回复
                response_text = self.scenarios[ScenarioMode.BUSY].response_text
                current_scenario = ScenarioMode.BUSY
            else:
                # 模拟接听电话的延迟
                time.sleep(2)
                
                # 获取回复文本（优先使用自定义回复）
                if current_scenario.value in self.custom_responses:
                    response_text = self.custom_responses[current_scenario.value]
                    self.logger.info(f"🎨 使用自定义回复")
                else:
                    response_text = scenario_config.response_text
                    self.logger.info(f"📋 使用默认回复")
            
            self.logger.info(f"🔊 播放回复: {response_text[:50]}...")
            
            # 模拟语音播放时长（根据文字长度估算）
            estimated_duration = len(response_text) * 0.15  # 约每个字0.15秒
            time.sleep(min(estimated_duration, 10))  # 最长不超过10秒
            
            # 如果是陌生电话模式，记录通话内容
            if current_scenario == ScenarioMode.UNKNOWN:
                self.logger.info(f"📝 陌生电话，开始记录通话内容...")
                time.sleep(5)  # 模拟记录时间
            
            # 模拟挂断
            time.sleep(1)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 记录通话
            call_record = CallRecord(
                phone_number=phone_number,
                caller_name=caller_name,
                call_time=start_time,
                scenario_mode=current_scenario,
                response_played=response_text,
                duration_seconds=duration,
                auto_answered=self.is_enabled
            )
            
            self.call_records.append(call_record)
            self._save_call_records()
            
            status = "自动代接" if self.is_enabled else "延迟回复"
            self.logger.info(f"✅ {status}完成，耗时 {duration:.1f} 秒")
            
            return {
                "success": True,
                "phone_number": phone_number,
                "caller_name": caller_name,
                "scenario_mode": current_scenario.value,
                "scenario_name": scenario_config.name,
                "response_text": response_text,
                "duration_seconds": duration,
                "call_time": start_time.isoformat(),
                "message": f"已使用{scenario_config.name}自动代接来电"
            }
            
        except Exception as e:
            error_msg = f"自动代接失败: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            
            return {
                "success": False,
                "phone_number": phone_number,
                "error": error_msg,
                "call_time": start_time.isoformat()
            }
    
    def set_scenario_mode(self, mode: ScenarioMode) -> Dict[str, Any]:
        """设置场景模式"""
        try:
            if mode not in self.scenarios:
                return {
                    "success": False,
                    "error": f"不支持的场景模式: {mode.value}"
                }
            
            old_mode = self.current_scenario
            self.current_scenario = mode
            scenario_config = self.scenarios[mode]
            
            self.logger.info(f"🔄 场景模式切换: {old_mode.value} → {mode.value}")
            
            return {
                "success": True,
                "old_mode": old_mode.value,
                "new_mode": mode.value,
                "scenario_name": scenario_config.name,
                "description": scenario_config.description,
                "response_preview": scenario_config.response_text[:100] + "..." if len(scenario_config.response_text) > 100 else scenario_config.response_text
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"设置场景模式失败: {str(e)}"
            }
    
    def toggle_auto_answer(self, enabled: bool = None) -> Dict[str, Any]:
        """开启/关闭自动代接"""
        try:
            if enabled is None:
                enabled = not self.is_enabled
            
            old_status = self.is_enabled
            self.is_enabled = enabled
            
            # 管理真实监控
            if enabled and not old_status:
                # 开启时启动真实监控
                self.start_real_monitoring()
            elif not enabled and old_status:
                # 关闭时停止真实监控
                self.stop_real_monitoring()
            
            status_text = "开启" if enabled else "关闭"
            self.logger.info(f"🎛️ 自动代接功能已{status_text}")
            
            return {
                "success": True,
                "enabled": enabled,
                "old_status": old_status,
                "current_scenario": self.current_scenario.value,
                "scenario_name": self.scenarios[self.current_scenario].name,
                "message": f"自动代接功能已{status_text}",
                "real_monitoring": self.is_monitoring
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"切换自动代接状态失败: {str(e)}"
            }
    
    def get_recent_call_records(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的通话记录"""
        try:
            # 按时间倒序排序
            sorted_records = sorted(self.call_records, key=lambda x: x.call_time, reverse=True)
            recent_records = sorted_records[:limit]
            
            return [record.to_dict() for record in recent_records]
            
        except Exception as e:
            self.logger.error(f"❌ 获取通话记录失败: {e}")
            return []
    
    def get_status_info(self) -> Dict[str, Any]:
        """获取当前状态信息"""
        current_scenario = self.get_current_scenario()
        scenario_config = self.scenarios[current_scenario]
        
        return {
            "enabled": self.is_enabled,
            "current_scenario": current_scenario.value,
            "scenario_name": scenario_config.name,
            "scenario_description": scenario_config.description,
            "total_calls": len(self.call_records),
            "recent_calls_24h": len([r for r in self.call_records 
                                   if r.call_time > datetime.now() - timedelta(hours=24)]),
            "device_connected": self.check_device_connection(),
            "real_monitoring": self.is_monitoring,
            "monitoring_active": self.is_monitoring and self.is_enabled,
            "available_scenarios": [
                {
                    "mode": mode.value,
                    "name": config.name,
                    "description": config.description
                }
                for mode, config in self.scenarios.items()
            ]
        }
    
    def get_telephony_state(self) -> str:
        """获取telephony状态"""
        try:
            result = subprocess.run([
                self.adb_path, "shell", "dumpsys", "telephony.registry"
            ], capture_output=True, text=True, timeout=1)
            
            if result.returncode == 0:
                return result.stdout
        except Exception as e:
            self.logger.debug(f"获取telephony状态失败: {e}")
        return ""

    def is_incoming_call(self, telephony_output: str) -> bool:
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

    def execute_real_auto_answer(self) -> bool:
        """执行真实自动接听流程"""
        self.logger.info("🚨 执行真实自动接听流程...")
        
        try:
            # 1. 接听电话
            self.logger.info("📞 接听电话...")
            subprocess.run([self.adb_path, "shell", "input", "keyevent", "5"], timeout=5)
            
            # 2. 等待连接稳定
            time.sleep(1)
            
            # 3. 获取当前场景的回复文本
            current_config = self.scenarios.get(self.current_scenario)
            if self.current_scenario.value in self.custom_responses:
                text = self.custom_responses[self.current_scenario.value]
            elif current_config:
                text = current_config.response_text
            else:
                text = "您好，我现在不方便接听电话，有重要事情请稍后联系，谢谢！"
            
            # 4. 播放语音回复
            self.logger.info("🎤 播放语音回复...")
            voice_success = self._play_voice_response(text)
            
            # 5. 等待播放完成
            time.sleep(4)
            
            # 6. 挂断电话
            self.logger.info("📴 挂断电话...")
            subprocess.run([self.adb_path, "shell", "input", "keyevent", "6"], timeout=5)
            
            # 7. 记录通话记录
            self._add_real_call_record("未知号码", "未知", text)
            
            self.logger.info("✅ 真实自动接听完成！")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 执行真实自动接听异常: {e}")
            return False

    def _play_voice_response(self, text: str) -> bool:
        """播放语音回复"""
        voice_success = False
        
        # 尝试方法1：gTTS（在线）
        if GTTS_AVAILABLE and not voice_success:
            try:
                self.logger.info("🎤 使用gTTS生成语音...")
                tts = gTTS(text=text, lang='zh', slow=False)
                
                audio_file = "voice_reply.mp3"
                tts.save(audio_file)
                
                # 推送到设备
                device_path = "/sdcard/voice_reply.mp3"
                subprocess.run([self.adb_path, "push", audio_file, device_path], timeout=10)
                
                # 播放音频文件
                subprocess.run([
                    self.adb_path, "shell", 
                    f"am start -a android.intent.action.VIEW -d file://{device_path} -t audio/mpeg"
                ], timeout=5)
                
                # 删除本地文件
                if os.path.exists(audio_file):
                    os.remove(audio_file)
                
                self.logger.info("✅ gTTS语音播放成功")
                voice_success = True
                
            except Exception as e:
                self.logger.warning(f"❌ gTTS失败: {e}")
        
        # 尝试方法2：pyttsx3（离线）
        if PYTTSX3_AVAILABLE and not voice_success:
            try:
                self.logger.info("🎤 使用pyttsx3生成语音...")
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
                    subprocess.run([self.adb_path, "push", audio_file, device_path], timeout=10)
                    
                    # 播放音频
                    subprocess.run([
                        self.adb_path, "shell",
                        f"am start -a android.intent.action.VIEW -d file://{device_path} -t audio/wav"
                    ], timeout=5)
                    
                    # 删除本地文件
                    os.remove(audio_file)
                    
                    self.logger.info("✅ pyttsx3语音播放成功")
                    voice_success = True
                    
            except Exception as e:
                self.logger.warning(f"❌ pyttsx3失败: {e}")
        
        # 备用方案
        if not voice_success:
            try:
                self.logger.info("🎤 使用备用提示方案...")
                # 发送通知
                subprocess.run([
                    self.adb_path, "shell", 
                    f"cmd notification post -S bigtext -t '智能代接' 'AutoReply' '{text[:50]}...'"
                ], timeout=5)
                # 播放系统音效
                subprocess.run([self.adb_path, "shell", "input", "keyevent", "KEYCODE_CAMERA"], timeout=5)
                time.sleep(0.3)
                subprocess.run([self.adb_path, "shell", "input", "keyevent", "KEYCODE_FOCUS"], timeout=5)
                self.logger.info("✅ 备用提示已发送")
                voice_success = True
            except Exception as e:
                self.logger.error(f"❌ 备用方案也失败: {e}")
        
        return voice_success

    def _add_real_call_record(self, phone_number: str, caller_name: str, response_text: str):
        """添加真实通话记录"""
        try:
            record = CallRecord(
                phone_number=phone_number,
                caller_name=caller_name,
                call_time=datetime.now(),
                scenario_mode=self.current_scenario,
                response_played=response_text,
                duration_seconds=4.0,  # 估算时长
                auto_answered=True
            )
            
            self.call_records.append(record)
            # 只保留最近50条记录
            if len(self.call_records) > 50:
                self.call_records = self.call_records[-50:]
            
            self._save_call_records()
            self.logger.info(f"📝 已记录真实通话: {phone_number}")
            
        except Exception as e:
            self.logger.error(f"❌ 保存真实通话记录失败: {e}")

    def start_real_monitoring(self):
        """启动真实来电监控"""
        if self.is_monitoring:
            self.logger.warning("⚠️ 真实监控已在运行")
            return
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._real_monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("🚀 真实来电监控已启动")

    def stop_real_monitoring(self):
        """停止真实来电监控"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2)
        self.logger.info("🛑 真实来电监控已停止")

    def _real_monitoring_loop(self):
        """真实来电监控循环"""
        self.logger.info("📱 开始真实来电监控循环...")
        
        while self.is_monitoring and self.is_enabled:
            try:
                # 获取telephony状态
                telephony_output = self.get_telephony_state()
                
                # 检查是否有来电
                if self.is_incoming_call(telephony_output):
                    current_time = time.time()
                    
                    # 防重复执行（5秒内只执行一次）
                    if current_time - self.last_call_time > 5:
                        self.logger.info("🔔 检测到真实来电！")
                        self.execute_real_auto_answer()
                        self.last_call_time = current_time
                
                time.sleep(0.5)  # 0.5秒检查一次
                
            except Exception as e:
                self.logger.error(f"❌ 真实监控循环异常: {e}")
                time.sleep(1)
        
        self.logger.info("📱 真实来电监控循环结束")


# 创建全局实例 - 使用正确的ADB路径
adb_path = "platform-tools/adb.exe" if os.path.exists("platform-tools/adb.exe") else "adb"
phone_manager = PhoneAutoAnswerManager(adb_path=adb_path)


@tool(
    "phone_auto_answer_call",
    description="模拟自动代接电话功能，播放智能回复",
    group="phone_automation"
)
def phone_auto_answer_call(phone_number: str, caller_name: str = None) -> Dict[str, Any]:
    """
    自动代接电话功能
    
    Args:
        phone_number: 来电号码
        caller_name: 来电者姓名（可选）
        
    Returns:
        包含代接结果的字典
    """
    return phone_manager.simulate_auto_answer_call(phone_number, caller_name)


@tool(
    "phone_set_scenario_mode", 
    description="设置电话代接的场景模式（工作/休息/驾驶/会议/学习）",
    group="phone_automation"
)
def phone_set_scenario_mode(mode: str) -> Dict[str, Any]:
    """
    设置场景模式
    
    Args:
        mode: 场景模式 (work/rest/driving/meeting/study/custom)
        
    Returns:
        包含设置结果的字典
    """
    try:
        scenario_mode = ScenarioMode(mode.lower())
        return phone_manager.set_scenario_mode(scenario_mode)
    except ValueError:
        return {
            "success": False,
            "error": f"无效的场景模式: {mode}. 支持: work, rest, driving, meeting, study, custom"
        }


@tool(
    "phone_toggle_auto_answer",
    description="开启或关闭电话自动代接功能",
    group="phone_automation"
)
def phone_toggle_auto_answer(enabled: bool = None) -> Dict[str, Any]:
    """
    开启/关闭自动代接
    
    Args:
        enabled: True开启，False关闭，None切换状态
        
    Returns:
        包含切换结果的字典
    """
    return phone_manager.toggle_auto_answer(enabled)


@tool(
    "phone_get_status",
    description="获取电话自动代接功能的当前状态",
    group="phone_automation"
)
def phone_get_status() -> Dict[str, Any]:
    """
    获取当前状态信息
    
    Returns:
        包含状态信息的字典
    """
    return phone_manager.get_status_info()


@tool(
    "phone_set_custom_response",
    description="设置指定场景的自定义回复语",
    group="phone_automation"
)
def phone_set_custom_response(scenario: str, response_text: str) -> Dict[str, Any]:
    """
    设置自定义回复语
    
    Args:
        scenario: 场景模式 (work/rest/driving/meeting/study/delivery/unknown/busy/hospital)
        response_text: 自定义回复文本
        
    Returns:
        包含设置结果的字典
    """
    return phone_manager.set_custom_response(scenario, response_text)


@tool(
    "phone_get_custom_responses",
    description="获取所有自定义回复语设置",
    group="phone_automation"
)
def phone_get_custom_responses() -> Dict[str, str]:
    """
    获取自定义回复语
    
    Returns:
        自定义回复语字典
    """
    return phone_manager.get_custom_responses()


@tool(
    "phone_set_ring_delay",
    description="设置响铃延迟时间（秒）",
    group="phone_automation"
)
def phone_set_ring_delay(seconds: int) -> Dict[str, Any]:
    """
    设置响铃延迟时间
    
    Args:
        seconds: 延迟时间（0-60秒）
        
    Returns:
        包含设置结果的字典
    """
    return phone_manager.set_ring_delay(seconds)


@tool(
    "phone_simulate_call",
    description="模拟来电以测试智能代接功能",
    group="phone_automation"
)
def phone_simulate_call(phone_number: str, caller_name: str = None, scenario: str = None) -> Dict[str, Any]:
    """
    模拟来电测试
    
    Args:
        phone_number: 来电号码
        caller_name: 来电者姓名（可选）
        scenario: 强制使用的场景模式（可选）
        
    Returns:
        包含代接结果的字典
    """
    # 如果指定了场景，临时切换
    original_scenario = None
    if scenario:
        try:
            original_scenario = phone_manager.current_scenario
            phone_manager.current_scenario = ScenarioMode(scenario.lower())
        except ValueError:
            return {
                "success": False,
                "error": f"无效的场景模式: {scenario}"
            }
    
    # 执行模拟代接
    result = phone_manager.simulate_auto_answer_call(phone_number, caller_name)
    
    # 恢复原场景
    if original_scenario:
        phone_manager.current_scenario = original_scenario
    
    return result


@tool(
    "phone_get_call_records",
    description="获取最近的电话代接记录",
    group="phone_automation"
)
def phone_get_call_records(limit: int = 10) -> Dict[str, Any]:
    """
    获取通话记录
    
    Args:
        limit: 返回记录数量限制
        
    Returns:
        包含通话记录的字典
    """
    records = phone_manager.get_recent_call_records(limit)
    return {
        "success": True,
        "total_records": len(phone_manager.call_records),
        "recent_records": records,
        "limit": limit
    }
