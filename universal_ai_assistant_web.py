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
        st.error("请确保已正确安装 agilemind 包")
        return False


def render_header():
    """渲染页面头部"""
    st.set_page_config(
        page_title="通用型AI助手",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 主标题
    st.title("🤖 通用型AI助手")
    st.markdown("### 基于多智能体架构的APP自动化操作系统")
    
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
                "办理套餐业务",
                "权益领取",
                "设置智能代接",
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
        - "领取我的联通积分权益"
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
            st.info("👋 欢迎使用通用型AI助手！请输入您的指令开始对话。")
    
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


def render_footer():
    """渲染页脚"""
    st.markdown("---")
    
    footer_cols = st.columns([1, 2, 1])
    
    with footer_cols[1]:
        st.markdown(
            """
            <div style='text-align: center; color: #666;'>
                <p>🤖 <b>通用型AI助手</b> | 基于多智能体架构 | 中国联通挑战杯参赛作品</p>
                <p>🔧 技术栈: OpenAI GPT + Android ADB + Streamlit</p>
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
    main_tabs = st.tabs(["💬 智能对话", "💡 使用示例", "📊 执行结果"])
    
    with main_tabs[0]:
        render_chat_interface(api_key, device_id)
    
    with main_tabs[1]:
        render_task_examples()
    
    with main_tabs[2]:
        render_task_results()
    
    # 渲染页脚
    render_footer()


if __name__ == "__main__":
    main()