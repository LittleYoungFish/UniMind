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
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from .tool_decorator import tool


class ScenarioMode(Enum):
    """场景模式枚举"""
    WORK = "work"           # 工作模式
    REST = "rest"           # 休息模式
    DRIVING = "driving"     # 驾驶模式
    MEETING = "meeting"     # 会议模式
    STUDY = "study"         # 学习模式
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
        self.current_scenario = ScenarioMode.WORK
        self.is_enabled = False
        self.call_records: List[CallRecord] = []
        
        # 创建必要的目录
        self.data_dir = "data/phone_auto_answer"
        self.voice_dir = "data/voice_responses"
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.voice_dir, exist_ok=True)
        
        # 加载配置
        self.scenarios = self._load_scenario_configs()
        self._load_call_records()
        
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
        """模拟自动代接电话（基础版本）"""
        start_time = datetime.now()
        current_scenario = self.get_current_scenario()
        scenario_config = self.scenarios[current_scenario]
        
        self.logger.info(f"📞 收到来电: {phone_number} ({caller_name or '未知'}) - 场景: {scenario_config.name}")
        
        try:
            # 模拟接听电话的延迟
            time.sleep(2)
            
            # 播放自动回复
            response_text = scenario_config.response_text
            self.logger.info(f"🔊 播放回复: {response_text[:50]}...")
            
            # 模拟语音播放时长（根据文字长度估算）
            estimated_duration = len(response_text) * 0.15  # 约每个字0.15秒
            time.sleep(min(estimated_duration, 10))  # 最长不超过10秒
            
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
                auto_answered=True
            )
            
            self.call_records.append(call_record)
            self._save_call_records()
            
            self.logger.info(f"✅ 自动代接完成，耗时 {duration:.1f} 秒")
            
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
            
            status_text = "开启" if enabled else "关闭"
            self.logger.info(f"🎛️ 自动代接功能已{status_text}")
            
            return {
                "success": True,
                "enabled": enabled,
                "old_status": old_status,
                "current_scenario": self.current_scenario.value,
                "scenario_name": self.scenarios[self.current_scenario].name,
                "message": f"自动代接功能已{status_text}"
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
            "available_scenarios": [
                {
                    "mode": mode.value,
                    "name": config.name,
                    "description": config.description
                }
                for mode, config in self.scenarios.items()
            ]
        }


# 创建全局实例
phone_manager = PhoneAutoAnswerManager()


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
