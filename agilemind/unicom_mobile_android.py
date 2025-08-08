"""
中国联通Android手机多智能体助手工作流
China Unicom Android Mobile Multi-Agent Assistant Workflow
"""

import os
import yaml
import logging
from typing import Dict, Any, List
from datetime import datetime

from .execution.agent import Agent
from .tool.unicom_android_tools import UnicomAndroidTools
from .prompt.unicom_mobile import (
    DEMAND_ANALYZER,
    APP_IDENTIFIER, 
    UI_ANALYZER,
    UNICOM_OPERATOR,
    OPERATION_EXECUTOR,
    RESULT_VALIDATOR,
    MONITOR_FEEDBACK
)


class UnicomMobileAndroidAssistant:
    """中国联通Android手机多智能体助手"""
    
    def __init__(self, config_path: str = "config_unicom_android.yaml"):
        """初始化联通手机助手"""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.unicom_tools = UnicomAndroidTools()
        self.agents = self._initialize_agents()
        self.session_id = f"unicom_session_{int(datetime.now().timestamp())}"
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            else:
                # 返回默认配置
                return {
                    "workflow": {
                        "agents": {
                            "demand_analyzer": {"model": "gpt-4o-mini", "temperature": 0.3},
                            "app_identifier": {"model": "gpt-4o-mini", "temperature": 0.2},
                            "ui_analyzer": {"model": "gpt-4o-mini", "temperature": 0.1},
                            "unicom_operator": {"model": "gpt-4o-mini", "temperature": 0.2},
                            "operation_executor": {"model": "gpt-4o-mini", "temperature": 0.1},
                            "result_validator": {"model": "gpt-4o-mini", "temperature": 0.1},
                            "monitor_feedback": {"model": "gpt-4o-mini", "temperature": 0.3}
                        }
                    }
                }
        except Exception as e:
            logging.error(f"加载配置失败: {e}")
            return {}
    
    def _setup_logging(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger("UnicomMobileAssistant")
        logger.setLevel(logging.INFO)
        
        # 创建日志目录
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # 创建文件处理器
        log_file = os.path.join(log_dir, "unicom_mobile_assistant.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _initialize_agents(self) -> Dict[str, Agent]:
        """初始化智能体"""
        agents = {}
        agent_configs = self.config.get("workflow", {}).get("agents", {})
        
        # 需求分析智能体
        agents["demand_analyzer"] = Agent(
            name="需求分析智能体",
            prompt=DEMAND_ANALYZER,
            model=agent_configs.get("demand_analyzer", {}).get("model", "gpt-4o-mini"),
            temperature=agent_configs.get("demand_analyzer", {}).get("temperature", 0.3),
            tools=[
                self.unicom_tools.unicom_android_connect,
                self.unicom_tools.unicom_get_screen_content
            ]
        )
        
        # APP识别智能体
        agents["app_identifier"] = Agent(
            name="APP识别智能体", 
            prompt=APP_IDENTIFIER,
            model=agent_configs.get("app_identifier", {}).get("model", "gpt-4o-mini"),
            temperature=agent_configs.get("app_identifier", {}).get("temperature", 0.2),
            tools=[
                self.unicom_tools.unicom_launch_app,
                self.unicom_tools.unicom_get_app_status,
                self.unicom_tools.unicom_android_connect
            ]
        )
        
        # UI界面分析智能体
        agents["ui_analyzer"] = Agent(
            name="UI界面分析智能体",
            prompt=UI_ANALYZER, 
            model=agent_configs.get("ui_analyzer", {}).get("model", "gpt-4o-mini"),
            temperature=agent_configs.get("ui_analyzer", {}).get("temperature", 0.1),
            tools=[
                self.unicom_tools.unicom_get_screen_content,
                self.unicom_tools.unicom_find_element_by_text
            ]
        )
        
        # 联通操作智能体
        agents["unicom_operator"] = Agent(
            name="联通操作智能体",
            prompt=UNICOM_OPERATOR,
            model=agent_configs.get("unicom_operator", {}).get("model", "gpt-4o-mini"), 
            temperature=agent_configs.get("unicom_operator", {}).get("temperature", 0.2),
            tools=[
                self.unicom_tools.unicom_tap_element,
                self.unicom_tools.unicom_input_text,
                self.unicom_tools.unicom_perform_operation,
                self.unicom_tools.unicom_get_screen_content
            ]
        )
        
        # 操作执行智能体
        agents["operation_executor"] = Agent(
            name="操作执行智能体",
            prompt=OPERATION_EXECUTOR,
            model=agent_configs.get("operation_executor", {}).get("model", "gpt-4o-mini"),
            temperature=agent_configs.get("operation_executor", {}).get("temperature", 0.1),
            tools=[
                self.unicom_tools.unicom_tap_element,
                self.unicom_tools.unicom_input_text,
                self.unicom_tools.unicom_get_screen_content,
                self.unicom_tools.unicom_launch_app,
                self.unicom_tools.unicom_close_app
            ]
        )
        
        # 结果验证智能体
        agents["result_validator"] = Agent(
            name="结果验证智能体",
            prompt=RESULT_VALIDATOR,
            model=agent_configs.get("result_validator", {}).get("model", "gpt-4o-mini"),
            temperature=agent_configs.get("result_validator", {}).get("temperature", 0.1),
            tools=[
                self.unicom_tools.unicom_get_screen_content,
                self.unicom_tools.unicom_find_element_by_text
            ]
        )
        
        # 监控反馈智能体
        agents["monitor_feedback"] = Agent(
            name="监控反馈智能体",
            prompt=MONITOR_FEEDBACK,
            model=agent_configs.get("monitor_feedback", {}).get("model", "gpt-4o-mini"),
            temperature=agent_configs.get("monitor_feedback", {}).get("temperature", 0.3),
            tools=[
                self.unicom_tools.unicom_get_screen_content
            ]
        )
        
        return agents
    
    def analyze_user_demand(self, user_input: str, device_id: str) -> Dict[str, Any]:
        """分析用户需求"""
        self.logger.info(f"开始分析用户需求: {user_input}")
        
        try:
            # 构建分析提示
            analysis_prompt = f"""
            用户需求: {user_input}
            设备ID: {device_id}
            
            请分析这个用户需求，识别需要操作的中国联通业务类型，并提供详细的操作计划。
            """
            
            # 调用需求分析智能体
            result = self.agents["demand_analyzer"].run(analysis_prompt)
            
            self.logger.info(f"需求分析完成: {result}")
            return {
                "success": True,
                "analysis_result": result,
                "session_id": self.session_id
            }
            
        except Exception as e:
            self.logger.error(f"需求分析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": self.session_id
            }
    
    def identify_target_app(self, demand_analysis: Dict[str, Any], device_id: str) -> Dict[str, Any]:
        """识别目标APP并启动"""
        self.logger.info("开始识别和启动目标APP")
        
        try:
            # 构建APP识别提示
            app_prompt = f"""
            需求分析结果: {demand_analysis}
            设备ID: {device_id}
            
            根据需求分析结果，请：
            1. 连接到Android设备
            2. 识别需要使用的中国联通APP
            3. 检查APP是否已安装
            4. 启动目标APP
            5. 验证APP启动状态
            """
            
            # 调用APP识别智能体
            result = self.agents["app_identifier"].run(app_prompt)
            
            self.logger.info(f"APP识别和启动完成: {result}")
            return {
                "success": True,
                "app_result": result,
                "session_id": self.session_id
            }
            
        except Exception as e:
            self.logger.error(f"APP识别失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": self.session_id
            }
    
    def analyze_ui_elements(self, app_context: str) -> Dict[str, Any]:
        """分析UI界面元素"""
        self.logger.info("开始分析UI界面元素")
        
        try:
            # 构建UI分析提示
            ui_prompt = f"""
            APP上下文: {app_context}
            
            请分析当前中国联通APP的界面：
            1. 获取当前屏幕截图
            2. 进行OCR文本识别
            3. 识别可操作的界面元素
            4. 判断当前页面类型
            5. 提供操作路径建议
            """
            
            # 调用UI分析智能体
            result = self.agents["ui_analyzer"].run(ui_prompt)
            
            self.logger.info(f"UI分析完成: {result}")
            return {
                "success": True,
                "ui_analysis": result,
                "session_id": self.session_id
            }
            
        except Exception as e:
            self.logger.error(f"UI分析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": self.session_id
            }
    
    def execute_unicom_operations(self, demand_analysis: Dict[str, Any], ui_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """执行联通业务操作"""
        self.logger.info("开始执行联通业务操作")
        
        try:
            # 构建操作提示
            operation_prompt = f"""
            需求分析: {demand_analysis}
            UI分析: {ui_analysis}
            
            请根据需求分析和UI分析结果，执行具体的中国联通业务操作：
            1. 根据需求确定操作步骤
            2. 执行界面交互操作
            3. 处理操作过程中的异常
            4. 确保操作的安全性
            5. 记录操作过程和结果
            
            注意：遇到支付页面时请停止操作，仅演示到确认页面。
            """
            
            # 调用联通操作智能体
            result = self.agents["unicom_operator"].run(operation_prompt)
            
            self.logger.info(f"联通业务操作完成: {result}")
            return {
                "success": True,
                "operation_result": result,
                "session_id": self.session_id
            }
            
        except Exception as e:
            self.logger.error(f"联通业务操作失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": self.session_id
            }
    
    def execute_device_operations(self, operation_plan: Dict[str, Any]) -> Dict[str, Any]:
        """执行设备操作"""
        self.logger.info("开始执行设备操作")
        
        try:
            # 构建执行提示
            execution_prompt = f"""
            操作计划: {operation_plan}
            
            请执行具体的设备操作指令：
            1. 将操作计划转化为设备交互指令
            2. 执行点击、输入、滑动等操作
            3. 处理执行过程中的异常
            4. 验证每步操作的执行结果
            5. 提供详细的执行报告
            """
            
            # 调用操作执行智能体
            result = self.agents["operation_executor"].run(execution_prompt)
            
            self.logger.info(f"设备操作执行完成: {result}")
            return {
                "success": True,
                "execution_result": result,
                "session_id": self.session_id
            }
            
        except Exception as e:
            self.logger.error(f"设备操作执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": self.session_id
            }
    
    def validate_operation_results(self, operation_results: Dict[str, Any]) -> Dict[str, Any]:
        """验证操作结果"""
        self.logger.info("开始验证操作结果")
        
        try:
            # 构建验证提示
            validation_prompt = f"""
            操作结果: {operation_results}
            
            请验证操作结果的准确性和完整性：
            1. 检查操作是否达到预期目标
            2. 验证获取数据的准确性
            3. 识别操作过程中的异常
            4. 评估操作质量和用户体验
            5. 提供结果质量评估报告
            """
            
            # 调用结果验证智能体
            result = self.agents["result_validator"].run(validation_prompt)
            
            self.logger.info(f"结果验证完成: {result}")
            return {
                "success": True,
                "validation_result": result,
                "session_id": self.session_id
            }
            
        except Exception as e:
            self.logger.error(f"结果验证失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": self.session_id
            }
    
    def monitor_and_feedback(self, all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """监控和反馈"""
        self.logger.info("开始生成监控反馈报告")
        
        try:
            # 构建监控提示
            monitor_prompt = f"""
            所有执行结果: {all_results}
            会话ID: {self.session_id}
            
            请生成综合性的监控反馈报告：
            1. 分析整个操作流程的执行情况
            2. 收集各智能体的性能数据
            3. 评估系统性能和用户体验
            4. 生成用户友好的结果报告
            5. 提供系统优化建议
            """
            
            # 调用监控反馈智能体
            result = self.agents["monitor_feedback"].run(monitor_prompt)
            
            self.logger.info(f"监控反馈报告生成完成: {result}")
            return {
                "success": True,
                "feedback_report": result,
                "session_id": self.session_id
            }
            
        except Exception as e:
            self.logger.error(f"监控反馈生成失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": self.session_id
            }


def unicom_mobile_android_assistant(user_demand: str, device_id: str) -> Dict[str, Any]:
    """
    中国联通Android手机多智能体助手主函数
    
    Args:
        user_demand: 用户需求描述
        device_id: Android设备ID
        
    Returns:
        Dict[str, Any]: 执行结果
    """
    try:
        # 初始化助手
        assistant = UnicomMobileAndroidAssistant()
        
        # 记录开始时间
        start_time = datetime.now()
        
        # 执行工作流
        results = []
        
        # 1. 分析用户需求
        demand_result = assistant.analyze_user_demand(user_demand, device_id)
        results.append(("需求分析", demand_result))
        
        if not demand_result["success"]:
            return {
                "success": False,
                "error": "需求分析失败",
                "details": demand_result,
                "session_id": assistant.session_id
            }
        
        # 2. 识别和启动目标APP
        app_result = assistant.identify_target_app(demand_result["analysis_result"], device_id)
        results.append(("APP识别", app_result))
        
        if not app_result["success"]:
            return {
                "success": False,
                "error": "APP识别失败",
                "details": app_result,
                "session_id": assistant.session_id
            }
        
        # 3. 分析UI界面元素
        ui_result = assistant.analyze_ui_elements(app_result["app_result"])
        results.append(("UI分析", ui_result))
        
        if not ui_result["success"]:
            return {
                "success": False,
                "error": "UI分析失败", 
                "details": ui_result,
                "session_id": assistant.session_id
            }
        
        # 4. 执行联通业务操作
        operation_result = assistant.execute_unicom_operations(
            demand_result["analysis_result"],
            ui_result["ui_analysis"]
        )
        results.append(("业务操作", operation_result))
        
        # 5. 执行设备操作
        if operation_result["success"]:
            execution_result = assistant.execute_device_operations(operation_result["operation_result"])
            results.append(("设备操作", execution_result))
        else:
            execution_result = {"success": False, "error": "业务操作失败"}
            results.append(("设备操作", execution_result))
        
        # 6. 验证操作结果
        if execution_result["success"]:
            validation_result = assistant.validate_operation_results(execution_result["execution_result"])
            results.append(("结果验证", validation_result))
        else:
            validation_result = {"success": False, "error": "设备操作失败"}
            results.append(("结果验证", validation_result))
        
        # 7. 生成监控反馈报告
        feedback_result = assistant.monitor_and_feedback(results)
        results.append(("监控反馈", feedback_result))
        
        # 计算总执行时间
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        # 返回最终结果
        return {
            "success": True,
            "session_id": assistant.session_id,
            "user_demand": user_demand,
            "device_id": device_id,
            "execution_duration": total_duration,
            "results": results,
            "final_report": feedback_result.get("feedback_report", "报告生成失败"),
            "timestamp": end_time.isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"系统异常: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

