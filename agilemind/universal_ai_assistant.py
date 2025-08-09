"""
通用型AI助手 - 基于多智能体架构的APP自动化操作系统
Universal AI Assistant - Multi-Agent Architecture for APP Automation

符合中国联通挑战杯比赛要求的通用型AI助手实现
"""

import os
import yaml
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from .execution.agent import Agent
from .context.context import Context
from .tool.app_automation_tools import AppAutomationTools
from .prompt.universal_assistant_prompts import (
    INTENT_ANALYZER,
    APP_SELECTOR,
    UI_NAVIGATOR,
    ACTION_EXECUTOR, 
    RESULT_VALIDATOR,
    CONVERSATION_MANAGER,
    MULTIMODAL_PROCESSOR
)


class TaskCategory(Enum):
    """任务分类枚举"""
    UNICOM_TELECOM = "联通电信服务"  # 联通APP操作
    MESSAGE_COMMUNICATION = "消息通讯"  # 消息回复、社交媒体
    SHOPPING_COMMERCE = "购物商务"  # 商品订购、电商操作  
    TRAVEL_NAVIGATION = "出行导航"  # 出行规划、导航服务
    ENTERTAINMENT = "娱乐服务"  # 视频、音乐、游戏等
    LIFE_SERVICES = "生活服务"  # 其他日常生活服务
    

class UniversalAIAssistant:
    """
    通用型AI助手
    
    核心功能：
    1. 理解用户自然语言指令
    2. 自动识别目标APP和操作
    3. 多智能体协作完成复杂任务
    4. 支持多模态交互（文本、语音、图像）
    5. 自动化工具调用
    """
    
    def __init__(self, config_path: str = "config_unicom_android.yaml"):
        """初始化通用AI助手"""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.tools = AppAutomationTools()
        self.agents = self._initialize_agents()
        self.session_id = f"assistant_session_{int(datetime.now().timestamp())}"
        
        # 支持的APP类别和包名映射
        self.supported_apps = self._load_app_configurations()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            else:
                # 返回默认配置
                return self._get_default_config()
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "assistant": {
                "name": "通用型AI助手",
                "version": "1.0.0",
                "description": "基于多智能体架构的APP自动化操作系统"
            },
            "agents": {
                "intent_analyzer": {"model": "gpt-4o-mini", "temperature": 0.3},
                "app_selector": {"model": "gpt-4o-mini", "temperature": 0.2},
                "ui_navigator": {"model": "gpt-4o-mini", "temperature": 0.1},
                "action_executor": {"model": "gpt-4o-mini", "temperature": 0.1},
                "result_validator": {"model": "gpt-4o-mini", "temperature": 0.1},
                "conversation_manager": {"model": "gpt-4o-mini", "temperature": 0.4},
                "multimodal_processor": {"model": "gpt-4o-mini", "temperature": 0.2}
            }
        }
    
    def _setup_logging(self) -> logging.Logger:
        """设置日志系统"""
        logger = logging.getLogger("UniversalAIAssistant")
        logger.setLevel(logging.INFO)
        
        # 创建日志目录
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # 文件处理器
        log_file = os.path.join(log_dir, "universal_ai_assistant.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 格式化
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _load_app_configurations(self) -> Dict[str, Dict[str, Any]]:
        """加载支持的APP配置"""
        return {
            # 中国联通系列APP
            "unicom_apps": {
                "unicom_main": {
                    "name": "中国联通手机营业厅",
                    "package": "com.sinovatech.unicom.ui",
                    "category": TaskCategory.UNICOM_TELECOM,
                    "features": ["话费查询", "流量查询", "套餐办理", "缴费充值", "权益领取", "智能代接"]
                },
                "unicom_payment": {
                    "name": "沃钱包",
                    "package": "com.unicompay.wallet", 
                    "category": TaskCategory.UNICOM_TELECOM,
                    "features": ["支付", "转账", "理财", "生活缴费"]
                },
                "unicom_video": {
                    "name": "沃视频",
                    "package": "com.unicom.video",
                    "category": TaskCategory.ENTERTAINMENT,
                    "features": ["视频播放", "直播", "点播"]
                }
            },
            
            # 通讯社交APP
            "communication_apps": {
                "wechat": {
                    "name": "微信",
                    "package": "com.tencent.mm",
                    "category": TaskCategory.MESSAGE_COMMUNICATION,
                    "features": ["消息回复", "朋友圈分享", "群聊管理"]
                },
                "qq": {
                    "name": "QQ",
                    "package": "com.tencent.mobileqq", 
                    "category": TaskCategory.MESSAGE_COMMUNICATION,
                    "features": ["消息回复", "空间分享", "群管理"]
                }
            },
            
            # 购物电商APP
            "shopping_apps": {
                "taobao": {
                    "name": "淘宝",
                    "package": "com.taobao.taobao",
                    "category": TaskCategory.SHOPPING_COMMERCE,
                    "features": ["商品搜索", "下单购买", "订单查询"]
                },
                "jd": {
                    "name": "京东",
                    "package": "com.jingdong.app.mall",
                    "category": TaskCategory.SHOPPING_COMMERCE, 
                    "features": ["商品搜索", "下单购买", "物流查询"]
                }
            },
            
            # 出行导航APP
            "travel_apps": {
                "amap": {
                    "name": "高德地图",
                    "package": "com.autonavi.minimap",
                    "category": TaskCategory.TRAVEL_NAVIGATION,
                    "features": ["路线规划", "导航", "周边搜索"]
                },
                "didi": {
                    "name": "滴滴出行",
                    "package": "com.sidu.didi",
                    "category": TaskCategory.TRAVEL_NAVIGATION,
                    "features": ["叫车", "行程规划", "支付"]
                }
            }
        }
    
    def _initialize_agents(self) -> Dict[str, Agent]:
        """初始化多智能体系统"""
        agents = {}
        agent_configs = self.config.get("agents", {})
        
        # 意图理解智能体
        agents["intent_analyzer"] = Agent(
            name="意图理解智能体",
            description="理解用户自然语言指令，识别用户真实意图和需求",
            instructions=INTENT_ANALYZER,
            tools=[],
            model=agent_configs.get("intent_analyzer", {}).get("model", "gpt-4o-mini"),
            generation_params={
                "temperature": agent_configs.get("intent_analyzer", {}).get("temperature", 0.3)
            }
        )
        
        # APP选择智能体
        agents["app_selector"] = Agent(
            name="APP选择智能体", 
            description="根据用户意图选择最适合的APP应用",
            instructions=APP_SELECTOR,
            tools=[],  # 使用系统默认的工具集合
            model=agent_configs.get("app_selector", {}).get("model", "gpt-4o-mini"),
            generation_params={
                "temperature": agent_configs.get("app_selector", {}).get("temperature", 0.2)
            }
        )
        
        # UI导航智能体
        agents["ui_navigator"] = Agent(
            name="UI导航智能体",
            description="分析APP界面，导航到目标功能页面",
            instructions=UI_NAVIGATOR,
            tools=[],  # 使用系统默认的工具集合
            model=agent_configs.get("ui_navigator", {}).get("model", "gpt-4o-mini"),
            generation_params={
                "temperature": agent_configs.get("ui_navigator", {}).get("temperature", 0.1)
            }
        )
        
        # 动作执行智能体
        agents["action_executor"] = Agent(
            name="动作执行智能体",
            description="执行具体的APP操作动作",
            instructions=ACTION_EXECUTOR,
            tools=[],  # 使用系统默认的工具集合
            model=agent_configs.get("action_executor", {}).get("model", "gpt-4o-mini"),
            generation_params={
                "temperature": agent_configs.get("action_executor", {}).get("temperature", 0.1)
            }
        )
        
        # 结果验证智能体
        agents["result_validator"] = Agent(
            name="结果验证智能体",
            description="验证操作结果是否达到用户预期",
            instructions=RESULT_VALIDATOR,
            tools=[],  # 使用系统默认的工具集合
            model=agent_configs.get("result_validator", {}).get("model", "gpt-4o-mini"),
            generation_params={
                "temperature": agent_configs.get("result_validator", {}).get("temperature", 0.1)
            }
        )
        
        # 对话管理智能体
        agents["conversation_manager"] = Agent(
            name="对话管理智能体",
            description="管理与用户的对话，提供友好的交互体验",
            instructions=CONVERSATION_MANAGER,
            tools=[],
            model=agent_configs.get("conversation_manager", {}).get("model", "gpt-4o-mini"),
            generation_params={
                "temperature": agent_configs.get("conversation_manager", {}).get("temperature", 0.4)
            }
        )
        
        # 多模态处理智能体
        agents["multimodal_processor"] = Agent(
            name="多模态处理智能体",
            description="处理语音、图像等多模态输入",
            instructions=MULTIMODAL_PROCESSOR,
            tools=[],  # 使用系统默认的工具集合
            model=agent_configs.get("multimodal_processor", {}).get("model", "gpt-4o-mini"),
            generation_params={
                "temperature": agent_configs.get("multimodal_processor", {}).get("temperature", 0.2)
            }
        )
        
        return agents
    
    async def process_user_request(self, user_input: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        处理用户请求的主流程
        
        Args:
            user_input: 用户的自然语言指令
            context: 上下文信息（设备信息、历史对话等）
            
        Returns:
            处理结果字典
        """
        try:
            self.logger.info(f"开始处理用户请求: {user_input}")
            
            # 创建任务上下文
            task_context = Context(user_input, None)
            if context:
                task_context.metadata = context
            
            # 阶段1: 意图理解
            intent_result = await self._analyze_user_intent(user_input, task_context)
            if not intent_result["success"]:
                return intent_result
            
            # 阶段2: APP选择 
            app_result = await self._select_target_app(intent_result["intent"], task_context)
            if not app_result["success"]:
                return app_result
            
            # 阶段3: UI导航
            navigation_result = await self._navigate_to_target(app_result["app_info"], intent_result["intent"], task_context)
            if not navigation_result["success"]:
                return navigation_result
            
            # 阶段4: 动作执行
            execution_result = await self._execute_actions(navigation_result["navigation_plan"], task_context)
            if not execution_result["success"]:
                return execution_result
            
            # 阶段5: 结果验证
            validation_result = await self._validate_results(execution_result["actions"], intent_result["intent"], task_context)
            
            # 阶段6: 生成用户友好的反馈
            response = await self._generate_user_response(validation_result, task_context)
            
            return {
                "success": True,
                "session_id": self.session_id,
                "user_input": user_input,
                "task_category": intent_result["intent"].get("category"),
                "target_app": app_result["app_info"].get("name"),
                "execution_steps": len(execution_result["actions"]),
                "result": validation_result,
                "user_response": response,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"处理用户请求失败: {str(e)}")
            return {
                "success": False,
                "error": f"系统异常: {str(e)}",
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _analyze_user_intent(self, user_input: str, context: Context) -> Dict[str, Any]:
        """分析用户意图"""
        try:
            prompt = f"""
            用户输入: {user_input}
            
            请分析用户的真实意图，识别：
            1. 任务类型和分类
            2. 目标应用类别
            3. 具体操作需求
            4. 重要参数信息
            5. 用户期望结果
            """
            
            result = self.agents["intent_analyzer"].process(context, prompt)
            
            return {
                "success": True,
                "intent": {
                    "original_text": user_input,
                    "analysis": result,
                    "category": self._extract_task_category(result)
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"意图分析失败: {str(e)}"}
    
    async def _select_target_app(self, intent: Dict[str, Any], context: Context) -> Dict[str, Any]:
        """选择目标APP"""
        try:
            # 基于意图选择最合适的APP
            category = intent.get("category", TaskCategory.UNICOM_TELECOM)
            
            prompt = f"""
            用户意图分析: {intent}
            支持的APP列表: {self.supported_apps}
            
            请选择最适合完成用户任务的APP，并制定启动计划。
            """
            
            result = self.agents["app_selector"].process(context, prompt)
            
            return {
                "success": True,
                "app_info": {
                    "selected_app": result,
                    "category": category
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"APP选择失败: {str(e)}"}
    
    async def _navigate_to_target(self, app_info: Dict, intent: Dict, context: Context) -> Dict[str, Any]:
        """导航到目标功能"""
        try:
            prompt = f"""
            目标APP: {app_info}
            用户意图: {intent}
            
            请分析当前APP界面，规划导航路径，到达用户目标功能页面。
            """
            
            result = self.agents["ui_navigator"].process(context, prompt)
            
            return {
                "success": True,
                "navigation_plan": result
            }
            
        except Exception as e:
            return {"success": False, "error": f"UI导航失败: {str(e)}"}
    
    async def _execute_actions(self, navigation_plan: Any, context: Context) -> Dict[str, Any]:
        """执行具体动作"""
        try:
            prompt = f"""
            导航计划: {navigation_plan}
            
            请按照计划执行具体的操作动作，完成用户任务。
            """
            
            result = self.agents["action_executor"].process(context, prompt)
            
            return {
                "success": True,
                "actions": result
            }
            
        except Exception as e:
            return {"success": False, "error": f"动作执行失败: {str(e)}"}
    
    async def _validate_results(self, actions: Any, intent: Dict, context: Context) -> Dict[str, Any]:
        """验证操作结果"""
        try:
            prompt = f"""
            执行的动作: {actions}
            用户原始意图: {intent}
            
            请验证操作结果是否达到用户预期，并提供质量评估。
            """
            
            result = self.agents["result_validator"].process(context, prompt)
            
            return {
                "success": True,
                "validation": result
            }
            
        except Exception as e:
            return {"success": False, "error": f"结果验证失败: {str(e)}"}
    
    async def _generate_user_response(self, validation_result: Dict, context: Context) -> str:
        """生成用户友好的响应"""
        try:
            prompt = f"""
            操作验证结果: {validation_result}
            
            请生成友好的用户反馈，告知用户操作结果和状态。
            """
            
            result = self.agents["conversation_manager"].process(context, prompt)
            return str(result.get("output", "操作已完成"))
            
        except Exception as e:
            return f"操作完成，但响应生成出现问题: {str(e)}"
    
    def _extract_task_category(self, analysis_result: Any) -> TaskCategory:
        """从分析结果中提取任务分类"""
        # 简单的关键词匹配，实际可以更复杂
        result_text = str(analysis_result).lower()
        
        if any(keyword in result_text for keyword in ["联通", "话费", "流量", "套餐"]):
            return TaskCategory.UNICOM_TELECOM
        elif any(keyword in result_text for keyword in ["消息", "微信", "qq", "聊天"]):
            return TaskCategory.MESSAGE_COMMUNICATION  
        elif any(keyword in result_text for keyword in ["购物", "淘宝", "京东", "下单"]):
            return TaskCategory.SHOPPING_COMMERCE
        elif any(keyword in result_text for keyword in ["导航", "出行", "地图", "打车"]):
            return TaskCategory.TRAVEL_NAVIGATION
        elif any(keyword in result_text for keyword in ["视频", "音乐", "游戏", "娱乐"]):
            return TaskCategory.ENTERTAINMENT
        else:
            return TaskCategory.LIFE_SERVICES


# 主函数接口
async def run_universal_assistant(user_input: str, device_id: str = None, **kwargs) -> Dict[str, Any]:
    """
    通用AI助手主接口
    
    Args:
        user_input: 用户的自然语言指令
        device_id: 设备ID（可选）
        **kwargs: 其他参数
        
    Returns:
        执行结果字典
    """
    assistant = UniversalAIAssistant()
    
    context = {
        "device_id": device_id,
        "timestamp": datetime.now().isoformat(),
        **kwargs
    }
    
    result = await assistant.process_user_request(user_input, context)
    return result


# 同步版本（兼容现有调用）
def universal_ai_assistant(user_input: str, device_id: str = None, **kwargs) -> Dict[str, Any]:
    """
    通用AI助手同步接口（兼容性）
    现已集成真实的手机操作功能
    """
    from datetime import datetime
    from .tool.app_automation_tools import AppAutomationTools
    
    # 检查是否是话费查询相关请求
    user_input_lower = user_input.lower()
    is_balance_query = any(keyword in user_input_lower for keyword in [
        '话费', '余额', '查询话费', '话费余额', '剩余话费', '查询余额'
    ])
    
    if is_balance_query:
        # 直接调用我们集成的话费查询功能
        try:
            tools = AppAutomationTools()
            balance_result = tools.query_unicom_balance()
            
            if balance_result.get('success'):
                return {
                    "success": True,
                    "user_input": user_input,
                    "target_app": "中国联通",
                    "execution_steps": 5,  # 设备连接、APP启动、按钮查找、点击操作、余额提取
                    "user_response": f"话费查询成功！您的话费余额为 {balance_result['balance']}",
                    "result": {
                        "balance": balance_result['balance'], 
                        "raw_amount": balance_result.get('raw_amount', 0),
                        "confidence_score": balance_result.get('confidence_score', 0),
                        "query_time": balance_result.get('query_time'),
                        "duration_seconds": balance_result.get('duration_seconds', 0),
                        "context": balance_result.get('context', '')
                    },
                    "operation_details": {
                        "device_connected": True,
                        "app_launched": True, 
                        "balance_extracted": True,
                        "real_operation": True  # 标记这是真实操作
                    },
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "user_input": user_input,
                    "target_app": "中国联通",
                    "user_response": f"话费查询失败: {balance_result.get('message', '未知错误')}",
                    "error": balance_result.get('message', '未知错误'),
                    "operation_details": {
                        "real_operation": True,
                        "failure_reason": balance_result.get('message')
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "success": False,
                "user_input": user_input,
                "target_app": "中国联通",
                "user_response": f"话费查询过程中发生异常: {str(e)}",
                "error": str(e),
                "operation_details": {
                    "real_operation": True,
                    "exception": str(e)
                },
                "timestamp": datetime.now().isoformat()
            }
    
    # 对于非话费查询的请求，使用原有的多智能体模拟系统
    import asyncio
    try:
        return asyncio.run(run_universal_assistant(user_input, device_id, **kwargs))
    except RuntimeError:
        # 如果在已有事件循环中，创建新循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(run_universal_assistant(user_input, device_id, **kwargs))
        finally:
            loop.close()

