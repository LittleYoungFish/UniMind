"""
通用型AI助手Web界面
Universal AI Assistant Web Interface

中国联通挑战杯比赛 - 基于多智能体架构的通用型AI助手Web界面
"""

import streamlit as st
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, Any
import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agilemind.universal_ai_assistant import universal_ai_assistant, run_universal_assistant
from agilemind.tool.unicom_android_tools import UnicomAndroidTools
from agilemind.tool.real_phone_auto_answer import (
    real_phone_manager,
    real_phone_get_status,
    real_phone_toggle_auto_answer,
    real_phone_set_scenario,
    real_phone_set_user_response
)
from agilemind.tool.phone_auto_answer import (
    phone_manager,
    ScenarioMode,
    phone_set_scenario_mode,
    phone_toggle_auto_answer,
    phone_get_status,
    phone_set_custom_response,
    phone_get_custom_responses,
    phone_set_ring_delay,
    phone_simulate_call,
    phone_get_call_records
)


def init_session_state():
    """初始化会话状态"""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'current_task' not in st.session_state:
        st.session_state.current_task = None
    if 'device_connected' not in st.session_state:
        st.session_state.device_connected = False


def check_dependencies():
    """检查依赖"""
    try:
        import agilemind
        return True
    except ImportError as e:
        st.error(f"❌ 依赖检查失败: {str(e)}")
        st.error("请确保已正确安装 unimind 包")
        return False


def render_header():
    """渲染页面头部"""
    st.set_page_config(
        page_title="UniMind--您的联通好帮手",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 主标题
    st.title("🤖 UniMind")
    st.markdown("### 基于多智能体架构的联通APP自动化操作系统")
    
    # 添加徽章
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        st.markdown("![多智能体](https://img.shields.io/badge/架构-多智能体-blue)")
    with col2:
        st.markdown("![APP自动化](https://img.shields.io/badge/功能-APP自动化-green)")
    with col3:
        st.markdown("![自然语言](https://img.shields.io/badge/交互-自然语言-orange)")
    with col4:
        st.markdown("![联通定制](https://img.shields.io/badge/定制-中国联通-red)")


def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.header("🔧 系统配置")
        
        # API配置
        st.subheader("🔑 API设置")
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="请输入您的OpenAI API密钥",
            key="api_key_input"
        )
        
        api_base_url = st.text_input(
            "API Base URL (可选)",
            value="https://api.openai.com/v1",
            help="自定义API端点",
            key="api_base_url_input"
        )
        
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            if api_base_url and api_base_url != "https://api.openai.com/v1":
                os.environ["OPENAI_BASE_URL"] = api_base_url
            st.success("✅ API配置完成")
        else:
            st.warning("⚠️ 请配置API Key")
        
        st.divider()
        
        # 设备配置
        st.subheader("📱 设备设置")
        device_id = st.text_input(
            "Android设备序列号",
            placeholder="通过'adb devices'获取",
            help="连接的Android设备序列号",
            key="device_id_input"
        )
        
        if device_id:
            st.success(f"✅ 设备: {device_id}")
            st.session_state.device_connected = True
        else:
            st.warning("⚠️ 请输入设备序列号")
            st.session_state.device_connected = False
        
        # 设备测试按钮
        if st.button("🔍 测试设备连接"):
            if device_id:
                with st.spinner("正在测试设备连接..."):
                    try:
                        from agilemind.tool.app_automation_tools import AppAutomationTools
                        tools = AppAutomationTools()
                        result = tools.get_installed_apps(device_id)
                        
                        if result["success"]:
                            st.success(f"✅ 设备连接正常，找到 {len(result.get('apps', []))} 个应用")
                            st.session_state.device_connected = True
                        else:
                            st.error(f"❌ 设备连接失败: {result.get('message', '未知错误')}")
                            st.session_state.device_connected = False
                    except Exception as e:
                        st.error(f"❌ 测试异常: {str(e)}")
                        st.session_state.device_connected = False
            else:
                st.error("❌ 请先输入设备序列号")
        
        st.divider()
        
        # 功能选择
        st.subheader("🎯 功能类别")
        
        task_categories = {
            "🏢 联通电信服务": [
                "查询话费余额",
                "查询流量使用",
                "权益领取",
                "智能代接设置",
                "办理套餐业务",
                "账单查询"
            ],
            "💬 消息通讯": [
                "回复微信消息",
                "发送QQ消息",
                "管理群聊",
                "分享内容到朋友圈"
            ],
            "🛒 购物商务": [
                "搜索商品",
                "比较价格",
                "下单购买",
                "查询订单"
            ],
            "🗺️ 出行导航": [
                "规划路线",
                "叫车服务",
                "查询公交",
                "预订酒店"
            ],
            "🎵 娱乐服务": [
                "播放音乐",
                "观看视频",
                "游戏操作",
                "内容推荐"
            ]
        }
        
        selected_category = st.selectbox(
            "选择服务类别",
            list(task_categories.keys()),
            key="category_select"
        )
        
        if selected_category:
            st.write("**常用操作:**")
            for operation in task_categories[selected_category]:
                if st.button(operation, key=f"op_{operation}"):
                    # 特殊处理智能代接设置
                    if operation == "智能代接设置":
                        # 开启智能代接服务
                        try:
                            result = phone_toggle_auto_answer(True)
                            if result["success"]:
                                st.success("✅ 智能代接已开启")
                                # 设置标识让用户关注智能代接标签页
                                st.info("💡 请点击顶部的'📞 智能代接'标签页进行详细设置")
                                # 清除状态缓存，强制刷新
                                if "phone_status_cache" in st.session_state:
                                    del st.session_state.phone_status_cache
                                st.session_state.phone_status_refresh = st.session_state.get("phone_status_refresh", 0) + 1
                                # 强制刷新状态并重新运行
                                st.rerun()
                            else:
                                st.error(f"❌ 开启失败: {result.get('error', '未知错误')}")
                        except Exception as e:
                            st.error(f"❌ 开启智能代接失败: {str(e)}")
                    else:
                        st.session_state.quick_command = operation
        
        st.divider()
        
        # 系统状态
        st.subheader("📊 系统状态")
        
        status_col1, status_col2 = st.columns(2)
        with status_col1:
            api_status = "🟢" if api_key else "🔴"
            st.write(f"{api_status} API")
        with status_col2:
            device_status = "🟢" if st.session_state.device_connected else "🔴"
            st.write(f"{device_status} 设备")
        
        # 系统信息
        with st.expander("ℹ️ 系统信息"):
            st.write("**版本**: v1.0.0")
            st.write("**架构**: 多智能体协作")
            st.write("**支持**: 中国联通APP")
            st.write("**交互**: 自然语言")
            
        return api_key, device_id


def render_task_examples():
    """渲染任务示例"""
    st.subheader("💡 使用示例")
    
    examples_tabs = st.tabs(["📱 联通服务", "💬 社交应用", "🛒 购物应用", "🗺️ 出行应用"])
    
    with examples_tabs[0]:
        st.markdown("""
        **中国联通APP操作示例：**
        
        📞 **电信服务**
        - "帮我查询话费余额"
        - "查看我的流量使用情况" 
        - "办理一个30元流量包"
        - "设置电话智能代接"
        
        🎁 **权益服务**
        - "领取我的联通权益"
        - "查看可用的优惠券"
        - "兑换话费抵用券"
        
        📋 **账单服务**
        - "查询本月账单详情"
        - "查看历史消费记录"
        - "设置账单提醒"
        """)
    
    with examples_tabs[1]:
        st.markdown("""
        **社交应用操作示例：**
        
        💬 **消息处理**
        - "回复微信上张三的消息说'好的'"
        - "在工作群里发送'会议已结束'"
        - "给妈妈发微信说到家了"
        
        📱 **内容分享**
        - "把这张图片分享到朋友圈"
        - "转发这个链接到微信群"
        - "在QQ空间发布状态"
        """)
    
    with examples_tabs[2]:
        st.markdown("""
        **购物应用操作示例：**
        
        🔍 **商品搜索**
        - "在淘宝上搜索iPhone 15"
        - "在京东找性价比高的笔记本"
        - "比较不同平台的价格"
        
        🛒 **购买操作**
        - "把这个商品加入购物车"
        - "查询我的订单状态"
        - "申请退换货"
        """)
    
    with examples_tabs[3]:
        st.markdown("""
        **出行应用操作示例：**
        
        🗺️ **导航规划**
        - "规划到北京站的最优路线"
        - "查找附近的加油站"
        - "避开拥堵路段"
        
        🚗 **出行服务**
        - "叫一辆到机场的滴滴"
        - "查询地铁换乘方案"
        - "预订明天的高铁票"
        """)


def render_chat_interface(api_key: str, device_id: str):
    """渲染聊天界面"""
    st.subheader("💬 AI助手对话")
    
    # 显示聊天历史
    chat_container = st.container()
    
    with chat_container:
        if st.session_state.chat_history:
            for i, (role, message, timestamp) in enumerate(st.session_state.chat_history):
                if role == "user":
                    with st.chat_message("user", avatar="👤"):
                        st.write(message)
                        st.caption(f"🕒 {timestamp}")
                else:
                    with st.chat_message("assistant", avatar="🤖"):
                        st.write(message)
                        st.caption(f"🕒 {timestamp}")
        else:
            st.info("👋 欢迎使用UniMind！请输入您的指令开始对话。")
    
    # 用户输入
    with st.container():
        col_input, col_send = st.columns([4, 1])
        
        with col_input:
            user_input = st.text_input(
                "请输入您的指令",
                placeholder="例如: 帮我查询联通话费余额",
                key="user_input",
                label_visibility="collapsed"
            )
        
        with col_send:
            send_button = st.button(
                "发送 🚀",
                type="primary",
                disabled=not (api_key and user_input.strip())
            )
    
    # 快捷指令
    if hasattr(st.session_state, 'quick_command'):
        user_input = st.session_state.quick_command
        send_button = True
        del st.session_state.quick_command
    
    # 处理用户输入
    if send_button and user_input.strip():
        if not api_key:
            st.error("❌ 请先配置OpenAI API Key")
            return
        
        # 添加用户消息到历史
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.chat_history.append(("user", user_input, timestamp))
        
        # 执行AI助手
        with st.spinner("🤖 AI助手正在思考和执行..."):
            try:
                # 显示执行进度
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 模拟进度更新
                for i in range(20, 100, 20):
                    progress_bar.progress(i)
                    if i == 20:
                        status_text.text("🧠 分析用户意图...")
                    elif i == 40:
                        status_text.text("📱 选择目标应用...")
                    elif i == 60:
                        status_text.text("🔍 分析界面元素...")
                    elif i == 80:
                        status_text.text("⚡ 执行操作指令...")
                    time.sleep(1)
                
                # 检查是否是权益领取请求，如果是则直接调用权益领取功能
                if _is_benefits_claim_request(user_input):
                    result = handle_benefits_claim_request(user_input, device_id)
                # 检查是否是智能代接请求，如果是则直接调用智能代接功能
                elif _is_phone_auto_answer_request(user_input):
                    result = handle_phone_auto_answer_request(user_input, device_id)
                else:
                    # 调用AI助手
                    result = universal_ai_assistant(user_input, device_id)
                
                progress_bar.progress(100)
                status_text.text("✅ 执行完成!")
                time.sleep(1)
                
                # 清除进度显示
                progress_bar.empty()
                status_text.empty()
                
                # 处理结果
                if result.get("success"):
                    response = result.get("user_response", "操作已完成")
                    
                    # 添加详细信息
                    if result.get("target_app"):
                        response += f"\n\n📱 使用应用: {result['target_app']}"
                    if result.get("execution_steps"):
                        response += f"\n🔢 执行步骤: {result['execution_steps']} 步"
                else:
                    response = f"❌ 执行失败: {result.get('error', '未知错误')}"
                
                # 添加助手回复到历史
                response_timestamp = datetime.now().strftime("%H:%M:%S")
                st.session_state.chat_history.append(("assistant", response, response_timestamp))
                
                # 保存当前任务
                st.session_state.current_task = result
                
                # 重新运行以更新界面
                st.rerun()
                
            except Exception as e:
                error_message = f"❌ 系统异常: {str(e)}"
                error_timestamp = datetime.now().strftime("%H:%M:%S")
                st.session_state.chat_history.append(("assistant", error_message, error_timestamp))
                st.rerun()


def render_task_results():
    """渲染任务结果"""
    if st.session_state.current_task:
        result = st.session_state.current_task
        
        # 检查是否为话费查询结果
        if _is_balance_query_result(result):
            render_balance_query_result(result)
        # 检查是否为流量查询结果
        elif _is_data_usage_query_result(result):
            render_data_usage_query_result(result)
        # 检查是否为权益领取结果
        elif _is_benefits_claim_result(result):
            render_benefits_claim_result(result)
        # 检查是否为智能代接结果
        elif _is_phone_auto_answer_result(result):
            render_phone_auto_answer_result(result)
        else:
            render_general_task_result(result)

def _is_balance_query_result(result):
    """检查是否是话费查询结果"""
    user_input = result.get("user_input", "").lower()
    return any(keyword in user_input for keyword in ['话费', '余额', '查询话费', '话费余额'])

def _is_data_usage_query_result(result):
    """检查是否是流量查询结果"""
    user_input = result.get("user_input", "").lower()
    return any(keyword in user_input for keyword in ['流量', '剩余流量', '通用流量', '剩余通用流量', '查询流量', '数据流量', '流量使用'])

def _is_benefits_claim_result(result):
    """检查是否是权益领取结果"""
    user_input = result.get("user_input", "").lower()
    return any(keyword in user_input for keyword in ['权益', '领取', '优惠券', '领券', '权益领取', '积分权益', '联通积分', '会员权益'])

def _is_phone_auto_answer_result(result):
    """检查是否是智能代接结果"""
    user_input = result.get("user_input", "").lower()
    task_category = result.get("task_category", "").lower()
    return task_category == "智能代接" or any(keyword in user_input for keyword in ['智能代接', '电话代接', '自动接听', '代接设置', '电话回复', '来电管理'])

def _is_benefits_claim_request(user_input):
    """检查是否是权益领取请求"""
    user_input_lower = user_input.lower()
    return any(keyword in user_input_lower for keyword in ['权益领取', '领取权益', '优惠券', '领券', '积分权益', '联通积分', '会员权益', '权益'])

def _is_phone_auto_answer_request(user_input):
    """检查是否是智能代接请求"""
    user_input_lower = user_input.lower()
    keywords = [
        '智能代接', '电话代接', '自动接听', '代接设置', '电话回复', '来电管理', '智能接听',
        '会议模式', '外卖模式', '工作模式', '陌生电话', '忙碌模式', '场景模式', '自定义回复',
        '开启代接', '关闭代接', '代接状态', '电话设置', '来电设置'
    ]
    return any(keyword in user_input_lower for keyword in keywords)

def handle_benefits_claim_request(user_input, device_id):
    """处理权益领取请求"""
    try:
        # 创建联通工具实例
        tools = UnicomAndroidTools()
        
        # 连接设备
        if device_id:
            connect_result = tools.unicom_android_connect(device_id=device_id)
            if not connect_result["success"]:
                return {
                    "success": False,
                    "error": f"设备连接失败: {connect_result.get('message', '未知错误')}",
                    "user_input": user_input,
                    "target_app": "中国联通",
                    "task_category": "权益领取"
                }
        
        # 执行权益领取
        result = tools.unicom_user_benefits_claim_interactive()
        
        # 格式化返回结果
        return {
            "success": result.get("success", False),
            "result": result.get("result", {}),
            "user_response": result.get("message", "权益领取操作完成"),
            "user_input": user_input,
            "target_app": "中国联通",
            "task_category": "权益领取",
            "execution_steps": len(result.get("result", {}).get("steps", [])),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
                    return {
                "success": False,
                "error": f"权益领取执行失败: {str(e)}",
                "user_input": user_input,
                "target_app": "中国联通",
                "task_category": "权益领取"
            }

def handle_phone_auto_answer_request(user_input, device_id):
    """处理智能代接请求"""
    try:
        # 获取当前智能代接状态
        status = phone_get_status()
        
        # 根据用户输入判断具体操作
        user_input_lower = user_input.lower()
        
        if "开启" in user_input_lower or "启用" in user_input_lower:
            # 开启智能代接
            from agilemind.tool.phone_auto_answer import phone_toggle_auto_answer
            result = phone_toggle_auto_answer(True)
            action = "开启智能代接"
            
        elif "关闭" in user_input_lower or "停用" in user_input_lower:
            # 关闭智能代接
            from agilemind.tool.phone_auto_answer import phone_toggle_auto_answer
            result = phone_toggle_auto_answer(False)
            action = "关闭智能代接"
            
        elif "工作模式" in user_input_lower:
            # 切换到工作模式
            from agilemind.tool.phone_auto_answer import phone_set_scenario_mode
            result = phone_set_scenario_mode("work")
            action = "设置工作模式"
            
        elif "会议模式" in user_input_lower:
            # 切换到会议模式
            from agilemind.tool.phone_auto_answer import phone_set_scenario_mode
            result = phone_set_scenario_mode("meeting")
            action = "设置会议模式"
            
        elif "外卖模式" in user_input_lower:
            # 切换到外卖模式
            from agilemind.tool.phone_auto_answer import phone_set_scenario_mode
            result = phone_set_scenario_mode("delivery")
            action = "设置外卖模式"
            
        else:
            # 默认显示状态信息
            result = {"success": True, "status": status}
            action = "查询智能代接状态"
        
        # 格式化返回结果
        return {
            "success": result.get("success", False),
            "result": {
                "action": action,
                "phone_status": phone_get_status(),
                "operation_result": result
            },
            "user_response": f"{action}操作完成",
            "user_input": user_input,
            "target_app": "电话系统",
            "task_category": "智能代接",
            "execution_steps": 1,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"智能代接操作失败: {str(e)}",
            "user_input": user_input,
            "target_app": "电话系统",
            "task_category": "智能代接"
        }

def render_balance_query_result(result):
    """渲染话费查询专用结果界面"""
    st.subheader("💰 话费查询结果")
    
    # 检查是否有话费相关的结果
    balance_info = None
    if "result" in result and isinstance(result["result"], dict):
        if "balance" in result["result"]:
            balance_info = result["result"]
        # 检查结果字符串中是否包含金额信息
        elif "您的话费余额为" in str(result.get("result", "")):
            result_str = str(result["result"])
            import re
            # 提取金额
            amount_match = re.search(r'(\d+\.?\d*)\s*元', result_str)
            if amount_match:
                balance_info = {
                    "balance": amount_match.group(0),
                    "raw_amount": float(amount_match.group(1)),
                    "query_time": result.get("timestamp", "未知"),
                    "message": "话费查询成功"
                }
    
    if balance_info:
        # 显示话费余额 - 突出显示
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(
                f"""
                <div style='
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 2rem;
                    border-radius: 1rem;
                    text-align: center;
                    color: white;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                '>
                    <h1 style='margin: 0; font-size: 3rem; font-weight: bold;'>
                        {balance_info.get('balance', '未知')}
                    </h1>
                    <p style='margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;'>
                        当前话费余额
                    </p>
                    <small style='opacity: 0.7;'>
                        查询时间: {balance_info.get('query_time', '未知')}
                    </small>
                </div>
                """,
                unsafe_allow_html=True
            )
        st.markdown("---")
        
        # 详细信息
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 查询详情")
            st.info(f"**余额:** {balance_info.get('balance', 'N/A')}")
            st.info(f"**数值:** {balance_info.get('raw_amount', 'N/A')} 元")
            if "confidence_score" in balance_info:
                st.info(f"**置信度得分:** {balance_info.get('confidence_score', 'N/A')}")
        
        with col2:
            st.markdown("#### ✅ 执行状态")
            st.success("✅ 查询成功")
            st.success("✅ 自动化操作完成")
            st.success("✅ 智能识别成功")
    
    else:
        # 查询失败的情况
        st.error("❌ 话费查询失败")
        if "result" in result:
            st.write(f"**结果信息:** {result['result']}")
    
    # 通用操作按钮和详细信息
    render_common_result_section(result)

def render_data_usage_query_result(result):
    """渲染流量查询专用结果界面"""
    st.subheader("📊 流量查询结果")
    
    # 检查是否有流量相关的结果
    data_info = None
    if "result" in result and isinstance(result["result"], dict):
        if "data_usage" in result["result"]:
            data_info = result["result"]
        # 检查结果字符串中是否包含流量信息
        elif "您的剩余流量为" in str(result.get("result", "")):
            result_str = str(result["result"])
            import re
            # 提取流量信息
            data_match = re.search(r'(\d+\.?\d*)\s*(GB|MB|TB)', result_str, re.IGNORECASE)
            if data_match:
                data_info = {
                    "data_usage": data_match.group(0),
                    "raw_amount": float(data_match.group(1)),
                    "unit": data_match.group(2).upper(),
                    "message": "流量查询成功"
                }
    
    if data_info:
        # 显示剩余流量 - 突出显示
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # 根据流量大小选择不同的颜色
            raw_amount = data_info.get('raw_amount', 0)
            unit = data_info.get('unit', '').upper()
            
            # 转换为GB进行颜色判断
            gb_amount = raw_amount
            if unit == 'MB':
                gb_amount = raw_amount / 1024
            elif unit == 'TB':
                gb_amount = raw_amount * 1024
            
            # 根据剩余流量选择颜色
            if gb_amount >= 10:  # 10GB以上 - 绿色
                gradient_colors = "#00c851, #007e33"
                status_text = "充足"
            elif gb_amount >= 1:  # 1-10GB - 橙色
                gradient_colors = "#ffbb33, #ff8800"
                status_text = "适中"
            else:  # 1GB以下 - 红色
                gradient_colors = "#ff4444, #cc0000"
                status_text = "偏少"
            
            st.markdown(
                f"""
                <div style='
                    background: linear-gradient(135deg, {gradient_colors});
                    padding: 2rem;
                    border-radius: 1rem;
                    text-align: center;
                    color: white;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                '>
                    <h1 style='margin: 0; font-size: 3rem; font-weight: bold;'>
                        {data_info.get('data_usage', '未知')}
                    </h1>
                    <p style='margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;'>
                        剩余流量 ({status_text})
                    </p>
                    <small style='opacity: 0.7;'>
                        查询时间: {data_info.get('query_time', '未知')}
                    </small>
                </div>
                """,
                unsafe_allow_html=True
            )
        st.markdown("---")
        
        # 详细信息
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 流量详情")
            st.info(f"**剩余流量:** {data_info.get('data_usage', 'N/A')}")
            st.info(f"**数值:** {data_info.get('raw_amount', 'N/A')} {data_info.get('unit', '')}")
            if "confidence_score" in data_info:
                st.info(f"**置信度得分:** {data_info.get('confidence_score', 'N/A')}")
            
            # 流量使用建议
            if gb_amount < 1:
                st.warning("⚠️ 流量不足，建议及时充值")
            elif gb_amount < 5:
                st.info("💡 流量适中，注意合理使用")
            else:
                st.success("✅ 流量充足，可放心使用")
        
        with col2:
            st.markdown("#### ✅ 执行状态")
            st.success("✅ 查询成功")
            st.success("✅ 自动化操作完成")
            st.success("✅ 智能识别成功")
            if data_info.get('duration_seconds'):
                st.info(f"⏱️ 执行时间: {data_info.get('duration_seconds', 0):.1f} 秒")
    
    else:
        # 查询失败的情况
        st.error("❌ 流量查询失败")
        if "result" in result:
            st.write(f"**结果信息:** {result['result']}")
    
    # 通用操作按钮和详细信息
    render_common_result_section(result)

def render_benefits_claim_result(result):
    """渲染权益领取专用结果界面"""
    st.subheader("🎁 权益领取结果")
    
    # 检查是否有权益领取相关的结果
    benefits_info = None
    if "result" in result and isinstance(result["result"], dict):
        if "steps" in result["result"]:
            benefits_info = result["result"]
        # 检查结果字符串中是否包含权益信息
        elif "权益领取" in str(result.get("result", "")) or "优惠券" in str(result.get("result", "")):
            result_str = str(result["result"])
            benefits_info = {
                "message": result_str,
                "success": result.get("success", False)
            }
    
    if benefits_info and benefits_info.get("steps"):
        # 显示权益领取结果 - 突出显示
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # 统计成功的步骤
            successful_steps = sum(1 for step in benefits_info["steps"] if step.get("result", {}).get("success", False))
            total_steps = len(benefits_info["steps"])
            
            # 检查是否有优惠券信息
            claimed_coupons = 0
            for step in benefits_info["steps"]:
                if step.get("step") == "claim_coupons" and step.get("result", {}).get("success"):
                    claimed_coupons = len(step["result"].get("claimed_coupons", []))
            
            st.markdown(
                f"""
                <div style='
                    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
                    padding: 2rem;
                    border-radius: 1rem;
                    text-align: center;
                    color: white;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                '>
                    <h1 style='margin: 0; font-size: 3rem; font-weight: bold;'>
                        🎁 {claimed_coupons}
                    </h1>
                    <p style='margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;'>
                        成功领取优惠券
                    </p>
                    <small style='opacity: 0.7;'>
                        执行步骤: {successful_steps}/{total_steps} 完成
                    </small>
                </div>
                """,
                unsafe_allow_html=True
            )
        st.markdown("---")
        
        # 详细步骤信息
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 执行步骤")
            for i, step in enumerate(benefits_info["steps"], 1):
                step_name = step.get("step", "未知步骤")
                step_result = step.get("result", {})
                step_success = step_result.get("success", False)
                step_message = step_result.get("message", "")
                choice = step.get("choice", "")
                
                status_icon = "✅" if step_success else "❌"
                display_message = choice if choice else step_message
                
                if step_name == "claim_coupons" and step_success:
                    claimed_coupons_list = step_result.get("claimed_coupons", [])
                    if claimed_coupons_list:
                        display_message += f" ({len(claimed_coupons_list)} 张)"
                
                st.info(f"{status_icon} **{step_name}**: {display_message}")
        
        with col2:
            st.markdown("#### ✅ 执行状态")
            st.success("✅ 权益领取完成")
            st.success("✅ 自动化操作完成")
            if claimed_coupons > 0:
                st.success(f"✅ 成功领取 {claimed_coupons - 1} 张优惠券")
            
            # 权益领取建议
            if claimed_coupons >= 3:
                st.info("💡 优惠券领取充足，记得及时使用")
            elif claimed_coupons > 0:
                st.info("💡 已领取部分优惠券，可稍后再次尝试")
            else:
                st.warning("⚠️ 暂无可领取的优惠券")
    
    else:
        # 权益领取失败的情况
        st.error("❌ 权益领取失败")
        if "result" in result:
            st.write(f"**结果信息:** {result['result']}")
    
    # 通用操作按钮和详细信息
    render_common_result_section(result)

def render_phone_auto_answer_result(result):
    """渲染智能代接专用结果界面"""
    st.subheader("📞 智能代接结果")
    
    # 检查是否有智能代接相关的结果
    phone_info = None
    if "result" in result and isinstance(result["result"], dict):
        phone_info = result["result"]
    
    if phone_info:
        # 获取操作信息
        action = phone_info.get("action", "未知操作")
        phone_status = phone_info.get("phone_status", {})
        operation_result = phone_info.get("operation_result", {})
        
        # 显示智能代接结果 - 突出显示
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # 根据操作类型选择颜色
            if "开启" in action:
                gradient_colors = "#00c851, #007e33"
                icon = "🟢"
            elif "关闭" in action:
                gradient_colors = "#ff4444, #cc0000"
                icon = "🔴"
            elif "模式" in action:
                gradient_colors = "#007bff, #0056b3"
                icon = "🎭"
            else:
                gradient_colors = "#6c757d, #495057"
                icon = "📞"
            
            st.markdown(
                f"""
                <div style='
                    background: linear-gradient(135deg, {gradient_colors});
                    padding: 2rem;
                    border-radius: 1rem;
                    text-align: center;
                    color: white;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                '>
                    <h1 style='margin: 0; font-size: 3rem; font-weight: bold;'>
                        {icon}
                    </h1>
                    <p style='margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;'>
                        {action}
                    </p>
                    <small style='opacity: 0.7;'>
                        当前场景: {phone_status.get('scenario_name', '未知')}
                    </small>
                </div>
                """,
                unsafe_allow_html=True
            )
        st.markdown("---")
        
        # 详细状态信息
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 当前状态")
            
            # 代接状态
            enabled_status = "🟢 已开启" if phone_status.get("enabled") else "🔴 已关闭"
            st.info(f"**代接状态**: {enabled_status}")
            
            # 当前场景
            st.info(f"**当前场景**: {phone_status.get('scenario_name', '未知')}")
            
            # 今日通话
            st.info(f"**今日通话**: {phone_status.get('recent_calls_24h', 0)} 次")
            
            # 设备连接
            device_status = "🟢 已连接" if phone_status.get("device_connected") else "🔴 未连接"
            st.info(f"**设备状态**: {device_status}")
        
        with col2:
            st.markdown("#### ⚙️ 操作结果")
            
            if operation_result.get("success"):
                st.success("✅ 操作成功")
                if operation_result.get("message"):
                    st.success(f"✅ {operation_result['message']}")
            else:
                st.error("❌ 操作失败")
                if operation_result.get("error"):
                    st.error(f"❌ {operation_result['error']}")
            
            # 快捷操作
            st.markdown("#### 🎯 快捷操作")
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("📞 代接界面", key="phone_ui_btn"):
                    st.info("💡 请运行: streamlit run phone_auto_answer_ui.py")
            
            with col_b:
                if st.button("🧪 模拟测试", key="phone_test_btn"):
                    # 模拟来电测试
                    from agilemind.tool.phone_auto_answer import phone_simulate_call
                    test_result = phone_simulate_call("138-TEST-8888", "测试来电")
                    if test_result["success"]:
                        st.success("✅ 测试完成")
                    else:
                        st.error("❌ 测试失败")
        
        # 可用场景列表
        if phone_status.get("available_scenarios"):
            st.markdown("#### 🎭 可用场景")
            scenarios = phone_status["available_scenarios"]
            
            # 分列显示场景
            cols = st.columns(3)
            for i, scenario in enumerate(scenarios):
                with cols[i % 3]:
                    icon_map = {
                        "work": "🏢", "rest": "😴", "driving": "🚗",
                        "meeting": "📝", "study": "📚", "delivery": "🍕",
                        "unknown": "❓", "busy": "⏰", "hospital": "🏥"
                    }
                    icon = icon_map.get(scenario["mode"], "📞")
                    st.write(f"{icon} **{scenario['name']}**")
                    st.caption(scenario["description"])
    
    else:
        # 智能代接操作失败的情况
        st.error("❌ 智能代接操作失败")
        if "result" in result:
            st.write(f"**结果信息**: {result['result']}")
    
    # 通用操作按钮和详细信息
    render_common_result_section(result)

def render_general_task_result(result):
    """渲染通用任务结果界面"""
    st.subheader("📊 执行结果详情")
    
    # 结果概览
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status = "✅ 成功" if result.get("success") else "❌ 失败"
        st.metric("执行状态", status)
    
    with col2:
        st.metric("目标应用", result.get("target_app", "N/A"))
    
    with col3:
        st.metric("执行步骤", f"{result.get('execution_steps', 0)} 步")
    
    with col4:
        category = result.get("task_category", "N/A")
        if hasattr(category, 'value'):
            category = category.value
        st.metric("任务分类", category)
    
    render_common_result_section(result)

def render_common_result_section(result):
    """渲染通用的结果详情部分"""
    # 详细信息
    with st.expander("🔍 查看详细信息"):
        result_tabs = st.tabs(["📋 基本信息", "⚙️ 执行过程", "📄 原始数据"])
        
        with result_tabs[0]:
            st.json({
                "用户指令": result.get("user_input", ""),
                "会话ID": result.get("session_id", ""),
                "执行时间": result.get("timestamp", ""),
                "任务分类": str(result.get("task_category", "")),
                "目标应用": result.get("target_app", ""),
                "执行状态": result.get("success", False)
            })
        
        with result_tabs[1]:
            if "result" in result:
                st.write("**验证结果:**")
                st.text(str(result["result"]))
            else:
                st.info("暂无详细执行过程信息")
        
        with result_tabs[2]:
            st.json(result)
        
        # 操作按钮
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            if st.button("📥 导出结果"):
                result_json = json.dumps(result, ensure_ascii=False, indent=2)
                st.download_button(
                    label="下载JSON文件",
                    data=result_json,
                    file_name=f"ai_assistant_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col_b:
            if st.button("🧹 清除结果"):
                st.session_state.current_task = None
                st.rerun()
        
        with col_c:
            if st.button("🔄 重新执行"):
                if result.get("user_input"):
                    st.session_state.quick_command = result["user_input"]
                    st.rerun()


def render_phone_auto_answer_tab():
    """渲染智能代接管理标签页 - 完全按照原有逻辑"""
    st.title("📞 电话智能代接系统")
    st.markdown("### 自动接听、智能回复、场景管理")
    
    # 状态概览 - 使用缓存机制减少频繁检测
    if "phone_status_cache" not in st.session_state:
        st.session_state.phone_status_cache = phone_get_status()
    
    # 如果有刷新标志，重新获取状态
    if st.session_state.get("phone_status_refresh", 0) > 0:
        st.session_state.phone_status_cache = phone_get_status()
        st.session_state.phone_status_refresh = 0
    
    status = st.session_state.phone_status_cache
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        status_icon = "🟢" if status["enabled"] else "🔴"
        st.metric("代接状态", f"{status_icon} {'开启' if status['enabled'] else '关闭'}")
    
    with col2:
        st.metric("当前场景", status["scenario_name"])
    
    with col3:
        st.metric("今日通话", status["recent_calls_24h"])
    
    with col4:
        device_icon = "🟢" if status["device_connected"] else "🔴"
        st.metric("设备连接", f"{device_icon} {'已连接' if status['device_connected'] else '未连接'}")
    
    with col5:
        monitoring_icon = "🚀" if status.get("monitoring_active", False) else "⏸️"
        monitoring_text = "监控中" if status.get("monitoring_active", False) else "未监控"
        st.metric("真实监控", f"{monitoring_icon} {monitoring_text}")
    
    # 主要功能标签页 - 完全按照原有的main函数逻辑
    tabs = st.tabs(["🎭 场景管理", "🎨 自定义回复", "⚙️ 系统设置", "🧪 模拟测试", "📋 通话记录"])
    
    with tabs[0]:
        render_scenario_management()
    
    with tabs[1]:
        render_custom_responses()
    
    with tabs[2]:
        render_system_settings()
    
    with tabs[3]:
        render_simulation_test()
    
    with tabs[4]:
        render_call_records()


def render_scenario_management():
    """渲染场景管理"""
    st.header("🎭 场景管理")
    
    # 获取当前状态
    status = st.session_state.get("phone_status_cache", phone_get_status())
    current_scenario = status["current_scenario"]
    
    # 场景选择
    col1, col2 = st.columns([2, 1])
    
    with col1:
        scenario_options = {
            "work": "🏢 工作模式",
            "rest": "😴 休息模式", 
            "driving": "🚗 驾驶模式",
            "meeting": "📝 会议模式",
            "study": "📚 学习模式",
            "delivery": "🍕 外卖模式",
            "unknown": "❓ 陌生电话模式",
            "busy": "⏰ 忙碌模式",
            "hospital": "🏥 医院模式"
        }
        
        selected_scenario = st.selectbox(
            "选择场景模式",
            options=list(scenario_options.keys()),
            format_func=lambda x: scenario_options[x],
            index=list(scenario_options.keys()).index(current_scenario) if current_scenario in scenario_options else 0
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # 垂直对齐
        if st.button("应用场景", type="primary"):
            result = phone_set_scenario_mode(selected_scenario)
            if result["success"]:
                st.success(f"✅ 场景已切换")
                # 清除状态缓存，强制刷新
                if "phone_status_cache" in st.session_state:
                    del st.session_state.phone_status_cache
                st.session_state.phone_status_refresh = st.session_state.get("phone_status_refresh", 0) + 1
                st.rerun()
            else:
                st.error(f"❌ {result['error']}")
    
    # 显示当前场景信息
    if current_scenario in scenario_options:
        scenario_info = next((s for s in status["available_scenarios"] if s["mode"] == current_scenario), None)
        if scenario_info:
            st.info(f"**{scenario_info['name']}**: {scenario_info['description']}")
    
    # 快速场景切换按钮
    st.subheader("🚀 快捷场景切换")
    cols = st.columns(3)
    for i, (scenario_key, scenario_name) in enumerate(scenario_options.items()):
        with cols[i % 3]:
            if st.button(scenario_name, key=f"quick_{scenario_key}"):
                result = phone_set_scenario_mode(scenario_key)
                if result["success"]:
                    st.success(f"✅ 已切换到{scenario_name}")
                    # 清除状态缓存，强制刷新
                    if "phone_status_cache" in st.session_state:
                        del st.session_state.phone_status_cache
                    st.session_state.phone_status_refresh = st.session_state.get("phone_status_refresh", 0) + 1
                    st.rerun()
                else:
                    st.error(f"❌ 切换失败: {result['error']}")


def render_custom_responses():
    """渲染自定义回复设置"""
    st.header("🎨 自定义回复设置")
    
    # 获取当前自定义回复
    custom_responses = phone_get_custom_responses()
    
    # 场景选择和回复设置
    scenario_options = {
        "work": "🏢 工作模式",
        "rest": "😴 休息模式", 
        "driving": "🚗 驾驶模式",
        "meeting": "📝 会议模式",
        "study": "📚 学习模式",
        "delivery": "🍕 外卖模式",
        "unknown": "❓ 陌生电话模式",
        "busy": "⏰ 忙碌模式",
        "hospital": "🏥 医院模式"
    }
    
    selected_scenario_for_custom = st.selectbox(
        "选择要设置自定义回复的场景",
        options=list(scenario_options.keys()),
        format_func=lambda x: scenario_options[x],
        key="custom_scenario"
    )
    
    # 当前回复内容
    current_response = custom_responses.get(selected_scenario_for_custom, "")
    
    # 回复文本输入
    col1, col2 = st.columns([3, 1])
    
    with col1:
        custom_text = st.text_area(
            "自定义回复内容",
            value=current_response,
            height=100,
            placeholder="输入自定义回复语...",
            key=f"response_{selected_scenario_for_custom}"
        )
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)  # 垂直对齐
        if st.button("保存回复", type="primary", key="save_response"):
            if custom_text.strip():
                result = phone_set_custom_response(selected_scenario_for_custom, custom_text.strip())
                if result["success"]:
                    st.success(f"✅ {result['message']}")
                    st.rerun()
                else:
                    st.error(f"❌ {result['error']}")
            else:
                st.warning("⚠️ 回复内容不能为空")
        
        if current_response and st.button("删除回复", key="delete_response"):
            result = phone_set_custom_response(selected_scenario_for_custom, "")
            if result["success"]:
                st.success("✅ 已删除自定义回复")
                st.rerun()
    
    # 显示所有自定义回复
    if custom_responses:
        st.subheader("📋 当前自定义回复")
        for scenario, response in custom_responses.items():
            if response:  # 只显示非空的回复
                scenario_name = scenario_options.get(scenario, scenario)
                with st.expander(f"{scenario_name}"):
                    st.write(response)


def render_system_settings():
    """渲染系统设置"""
    st.header("⚙️ 系统设置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📞 代接功能控制")
        
        # 获取当前状态
        status = st.session_state.get("phone_status_cache", phone_get_status())
        
        # 开关控制
        enabled = st.toggle("启用自动代接", value=status["enabled"])
        
        if st.button("应用设置", key="toggle_setting"):
            result = phone_toggle_auto_answer(enabled)
            if result["success"]:
                st.success(f"✅ {result['message']}")
                # 清除状态缓存，强制刷新
                if "phone_status_cache" in st.session_state:
                    del st.session_state.phone_status_cache
                st.session_state.phone_status_refresh = st.session_state.get("phone_status_refresh", 0) + 1
                st.rerun()
            else:
                st.error(f"❌ {result['error']}")
    
    with col2:
        st.subheader("⏰ 响铃延迟设置")
        
        # 响铃延迟设置
        ring_delay = st.slider(
            "响铃延迟时间（秒）",
            min_value=0,
            max_value=60,
            value=phone_manager.ring_delay_seconds,
            help="未开启自动代接时的响铃时间"
        )
        
        if st.button("设置延迟", key="set_delay"):
            result = phone_set_ring_delay(ring_delay)
            if result["success"]:
                st.success(f"✅ {result['message']}")
            else:
                st.error(f"❌ {result['error']}")


def render_simulation_test():
    """渲染模拟测试"""
    st.header("🧪 模拟测试")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📞 模拟来电")
        
        # 来电信息输入
        phone_number = st.text_input("来电号码", value="138****8888", key="sim_phone")
        caller_name = st.text_input("来电者姓名", value="", placeholder="可选", key="sim_name")
        
        # 场景选择
        scenario_options = {
            "": "使用当前场景",
            "work": "🏢 工作模式",
            "rest": "😴 休息模式", 
            "driving": "🚗 驾驶模式",
            "meeting": "📝 会议模式",
            "study": "📚 学习模式",
            "delivery": "🍕 外卖模式",
            "unknown": "❓ 陌生电话模式",
            "busy": "⏰ 忙碌模式",
            "hospital": "🏥 医院模式"
        }
        
        force_scenario = st.selectbox(
            "强制使用场景（可选）",
            options=list(scenario_options.keys()),
            format_func=lambda x: scenario_options[x],
            key="sim_scenario"
        )
        
        if st.button("开始模拟", type="primary"):
            with st.spinner("📞 模拟来电中..."):
                result = phone_simulate_call(
                    phone_number, 
                    caller_name or None, 
                    force_scenario or None
                )
                
                if result["success"]:
                    st.success("✅ 模拟完成")
                    
                    # 显示结果详情
                    st.json({
                        "来电号码": result["phone_number"],
                        "来电者": result.get("caller_name", "未知"),
                        "使用场景": result["scenario_name"],
                        "回复内容": result["response_text"],
                        "通话时长": f"{result['duration_seconds']:.1f} 秒",
                        "代接状态": "自动代接" if result["auto_answered"] else "延迟回复"
                    })
                else:
                    st.error(f"❌ 模拟失败: {result['error']}")
    
    with col2:
        st.subheader("📊 快速测试")
        
        # 快速测试按钮
        test_scenarios = [
            ("外卖测试", "delivery", "400-123-4567", "外卖小哥"),
            ("会议测试", "meeting", "138-0000-1234", "同事"),
            ("陌生电话测试", "unknown", "150-9999-8888", None),
            ("休息时间测试", "rest", "186-7777-6666", "朋友")
        ]
        
        for i, (test_name, scenario, phone, caller) in enumerate(test_scenarios):
            if st.button(test_name, key=f"quick_{scenario}_{i}"):
                with st.spinner(f"📞 {test_name}中..."):
                    result = phone_simulate_call(phone, caller, scenario)
                    if result["success"]:
                        st.success(f"✅ {test_name}完成")
                        st.write(f"**回复**: {result['response_text'][:50]}...")
                    else:
                        st.error(f"❌ {test_name}失败")


def render_call_records():
    """渲染通话记录"""
    st.header("📋 通话记录")
    
    # 获取通话记录 - 按照原始逻辑直接使用manager方法
    records = phone_manager.get_recent_call_records(20)
    
    if records:
        
        # 统计信息
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("总通话数", len(records))
        
        with col2:
            auto_answered = sum(1 for r in records if r["auto_answered"])
            st.metric("自动代接", auto_answered)
        
        with col3:
            avg_duration = sum(r["duration_seconds"] for r in records) / len(records)
            st.metric("平均时长", f"{avg_duration:.1f}秒")
        
        # 记录列表
        st.subheader("最近通话记录")
        
        for record in records[:10]:  # 显示最近10条
            call_time = datetime.fromisoformat(record["call_time"])
            
            with st.expander(f"📞 {record['phone_number']} - {call_time.strftime('%m-%d %H:%M')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**来电者**: {record.get('caller_name', '未知')}")
                    st.write(f"**场景模式**: {record['scenario_mode']}")
                    st.write(f"**通话时长**: {record['duration_seconds']:.1f} 秒")
                
                with col2:
                    st.write(f"**代接状态**: {'自动代接' if record['auto_answered'] else '延迟回复'}")
                    st.write(f"**回复内容**: {record['response_played'][:100]}...")
    else:
        st.info("📝 暂无通话记录")


def render_footer():
    """渲染页脚"""
    st.markdown("---")
    
    footer_cols = st.columns([1, 2, 1])
    
    with footer_cols[1]:
        st.markdown(
            """
            <div style='text-align: center; color: #666;'>
                <p>🤖 <b>通用型AI助手</b> | 多智能体架构 | 第十九届挑战杯揭榜挂帅</p>
            </div>
            """,
            unsafe_allow_html=True
        )


def main():
    """主函数"""
    # 检查依赖
    if not check_dependencies():
        return
    
    # 初始化会话状态
    init_session_state()
    
    # 渲染页面组件
    render_header()
    
    # 渲染侧边栏并获取配置
    api_key, device_id = render_sidebar()
    
    # 主界面布局
    main_tabs = st.tabs(["💬 智能对话", "📞 智能代接", "💡 使用示例", "📊 执行结果"])
    
    with main_tabs[0]:
        render_chat_interface(api_key, device_id)
    
    with main_tabs[1]:
        render_phone_auto_answer_tab()
    
    with main_tabs[2]:
        render_task_examples()
    
    with main_tabs[3]:
        render_task_results()
    
    # 渲染页脚
    render_footer()


if __name__ == "__main__":
    main()