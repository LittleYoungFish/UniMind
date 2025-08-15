#!/usr/bin/env python3
"""
电话智能代接界面
Phone Auto Answer UI
"""

import streamlit as st
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unimind.tool.phone_auto_answer import (
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

# 页面配置
st.set_page_config(
    page_title="电话智能代接",
    page_icon="📞",
    layout="wide"
)

def init_session_state():
    """初始化会话状态"""
    if 'phone_status' not in st.session_state:
        st.session_state.phone_status = phone_get_status()
    if 'custom_responses' not in st.session_state:
        st.session_state.custom_responses = phone_get_custom_responses()

def render_header():
    """渲染页面头部"""
    st.title("📞 电话智能代接系统")
    st.markdown("### 自动接听、智能回复、场景管理")
    
    # 状态概览
    status = phone_get_status()
    col1, col2, col3, col4 = st.columns(4)
    
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

def render_scenario_management():
    """渲染场景管理"""
    st.header("🎭 场景模式管理")
    
    # 获取当前状态
    status = phone_get_status()
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
                st.success(f"✅ {result['message']}")
                st.rerun()
            else:
                st.error(f"❌ {result['error']}")
    
    # 显示当前场景信息
    if current_scenario in scenario_options:
        scenario_info = next((s for s in status["available_scenarios"] if s["mode"] == current_scenario), None)
        if scenario_info:
            st.info(f"**{scenario_info['name']}**: {scenario_info['description']}")

def render_custom_responses():
    """渲染自定义回复设置"""
    st.header("🎨 自定义回复语设置")
    
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
        status = phone_get_status()
        
        # 开关控制
        enabled = st.toggle("启用自动代接", value=status["enabled"])
        
        if st.button("应用设置", key="toggle_setting"):
            result = phone_toggle_auto_answer(enabled)
            if result["success"]:
                st.success(f"✅ {result['message']}")
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
        
        for test_name, scenario, phone, caller in test_scenarios:
            if st.button(test_name, key=f"quick_{scenario}"):
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
    
    # 获取通话记录
    records_result = phone_get_call_records(20)
    
    if records_result["success"] and records_result["records"]:
        records = records_result["records"]
        
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

def main():
    """主函数"""
    init_session_state()
    render_header()
    
    # 主要功能标签页
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
    
    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
    📞 电话智能代接系统 | 基于AgileMind多智能体架构 | 🤖 AI驱动的智能化通话管理
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
