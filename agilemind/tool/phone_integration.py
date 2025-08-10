"""
电话代接功能与APP自动化工具集成模块
Phone Auto Answer Integration with App Automation Tools
"""

import logging
from datetime import datetime
from typing import Dict, Any

from .tool_decorator import tool
from .phone_auto_answer import phone_manager, ScenarioMode


class PhoneIntegrationTools:
    """电话代接功能集成工具类"""
    
    def __init__(self):
        self.logger = logging.getLogger("PhoneIntegration")
        
    @tool(
        "phone_answer_demo",
        description="演示电话自动代接功能，模拟接听指定号码的来电",
        group="phone_automation"
    )
    def phone_answer_demo(self, phone_number: str, caller_name: str = None) -> Dict[str, Any]:
        """
        演示电话自动代接功能
        
        Args:
            phone_number: 演示的来电号码
            caller_name: 来电者姓名
            
        Returns:
            包含代接演示结果的字典
        """
        start_time = datetime.now()
        self.logger.info("📞 开始演示电话自动代接功能...")
        
        try:
            # 使用全局的电话管理器
            result = phone_manager.simulate_auto_answer_call(phone_number, caller_name)
            
            if result.get('success'):
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                return {
                    "success": True,
                    "demo_type": "phone_auto_answer",
                    "phone_number": phone_number,
                    "caller_name": caller_name or "未知来电",
                    "scenario_mode": result.get('scenario_mode'),
                    "scenario_name": result.get('scenario_name'),
                    "response_text": result.get('response_text'),
                    "call_duration": result.get('duration_seconds', 0),
                    "demo_duration": duration,
                    "call_time": result.get('call_time'),
                    "message": f"成功演示{result.get('scenario_name')}代接来电 {phone_number}"
                }
            else:
                return {
                    "success": False,
                    "demo_type": "phone_auto_answer",
                    "phone_number": phone_number,
                    "error": result.get('error', '未知错误'),
                    "message": f"代接演示失败: {result.get('error')}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "demo_type": "phone_auto_answer", 
                "phone_number": phone_number,
                "error": str(e),
                "message": f"代接演示异常: {str(e)}"
            }

    @tool(
        "phone_scenario_control",
        description="控制电话代接的场景模式和开关状态",
        group="phone_automation"
    )
    def phone_scenario_control(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        控制电话代接功能
        
        Args:
            action: 操作类型 (set_mode/toggle/status/records)
            **kwargs: 其他参数
            
        Returns:
            包含操作结果的字典
        """
        self.logger.info(f"🎛️ 电话代接控制操作: {action}")
        
        try:
            if action == "set_mode":
                # 设置场景模式
                mode = kwargs.get('mode', 'work')
                try:
                    scenario_mode = ScenarioMode(mode.lower())
                    result = phone_manager.set_scenario_mode(scenario_mode)
                    return {
                        "success": result.get('success', False),
                        "action": "set_mode",
                        "mode": mode,
                        "result": result,
                        "message": f"场景模式设置为: {result.get('scenario_name', mode)}"
                    }
                except ValueError:
                    return {
                        "success": False,
                        "action": "set_mode",
                        "error": f"无效的场景模式: {mode}",
                        "available_modes": ["work", "rest", "driving", "meeting", "study"]
                    }
            
            elif action == "toggle":
                # 开启/关闭自动代接
                enabled = kwargs.get('enabled')
                result = phone_manager.toggle_auto_answer(enabled)
                return {
                    "success": result.get('success', False),
                    "action": "toggle",
                    "enabled": result.get('enabled', False),
                    "result": result,
                    "message": result.get('message', '切换完成')
                }
            
            elif action == "status":
                # 获取状态信息
                status_info = phone_manager.get_status_info()
                return {
                    "success": True,
                    "action": "status",
                    "status": status_info,
                    "message": f"当前模式: {status_info.get('scenario_name')}"
                }
            
            elif action == "records":
                # 获取通话记录
                limit = kwargs.get('limit', 10)
                records = phone_manager.get_recent_call_records(limit)
                return {
                    "success": True,
                    "action": "records", 
                    "records": records,
                    "total_records": len(phone_manager.call_records),
                    "message": f"获取了最近 {len(records)} 条记录"
                }
            
            else:
                return {
                    "success": False,
                    "action": action,
                    "error": f"不支持的操作: {action}",
                    "available_actions": ["set_mode", "toggle", "status", "records"]
                }
                
        except Exception as e:
            return {
                "success": False,
                "action": action,
                "error": str(e),
                "message": f"操作失败: {str(e)}"
            }
    
    @tool(
        "phone_smart_assistant",
        description="电话智能助手综合功能，支持自然语言控制",
        group="phone_automation"
    )
    def phone_smart_assistant(self, user_request: str) -> Dict[str, Any]:
        """
        电话智能助手综合功能
        
        Args:
            user_request: 用户自然语言请求
            
        Returns:
            包含处理结果的字典
        """
        self.logger.info(f"🤖 电话智能助手收到请求: {user_request}")
        
        request_lower = user_request.lower()
        
        try:
            # 场景模式切换请求
            if any(keyword in request_lower for keyword in ['切换', '设置', '改为', '调整']):
                if '工作' in request_lower:
                    return self.phone_scenario_control('set_mode', mode='work')
                elif '休息' in request_lower:
                    return self.phone_scenario_control('set_mode', mode='rest')
                elif '驾驶' in request_lower:
                    return self.phone_scenario_control('set_mode', mode='driving')
                elif '会议' in request_lower:
                    return self.phone_scenario_control('set_mode', mode='meeting')
                elif '学习' in request_lower:
                    return self.phone_scenario_control('set_mode', mode='study')
            
            # 开启/关闭请求
            elif any(keyword in request_lower for keyword in ['开启', '启动', '打开']):
                return self.phone_scenario_control('toggle', enabled=True)
            elif any(keyword in request_lower for keyword in ['关闭', '停止', '关掉']):
                return self.phone_scenario_control('toggle', enabled=False)
            
            # 状态查询请求
            elif any(keyword in request_lower for keyword in ['状态', '当前', '模式']):
                return self.phone_scenario_control('status')
            
            # 记录查询请求
            elif any(keyword in request_lower for keyword in ['记录', '历史', '通话']):
                return self.phone_scenario_control('records', limit=10)
            
            # 演示请求
            elif any(keyword in request_lower for keyword in ['演示', '测试', '试试']):
                # 提取电话号码（如果有）
                import re
                phone_match = re.search(r'1[3-9]\d{9}', user_request)
                phone_number = phone_match.group() if phone_match else "138****8888"
                return self.phone_answer_demo(phone_number, "演示来电")
            
            else:
                return {
                    "success": False,
                    "user_request": user_request,
                    "error": "未识别的请求",
                    "suggestions": [
                        "切换到工作模式",
                        "开启电话代接",
                        "查看当前状态", 
                        "查看通话记录",
                        "演示电话代接"
                    ]
                }
                
        except Exception as e:
            return {
                "success": False,
                "user_request": user_request,
                "error": str(e),
                "message": f"处理请求时发生异常: {str(e)}"
            }


# 创建全局实例
phone_integration = PhoneIntegrationTools()
