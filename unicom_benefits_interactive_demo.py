#!/usr/bin/env python3
"""
联通用户权益领取交互式演示界面
支持前端用户交互，提供完整的业务流程体验
"""

import streamlit as st
import sys
import os
import json
from typing import Dict, Any

# 添加项目路径
sys.path.append('.')
from agilemind.tool.unicom_android_tools import UnicomAndroidTools

# 页面配置
st.set_page_config(
    page_title="联通用户权益领取系统",
    page_icon="📱",
    layout="wide"
)

st.title("📱 联通用户权益领取交互式系统")
st.markdown("---")

# 初始化session state
if 'unicom_tools' not in st.session_state:
    st.session_state.unicom_tools = None
if 'device_connected' not in st.session_state:
    st.session_state.device_connected = False
if 'current_step' not in st.session_state:
    st.session_state.current_step = "device_setup"
if 'user_responses' not in st.session_state:
    st.session_state.user_responses = {}
if 'process_result' not in st.session_state:
    st.session_state.process_result = None

# 侧边栏 - 设备连接
with st.sidebar:
    st.header("🔧 设备设置")
    
    device_id = st.text_input("设备ID", value="", help="输入Android设备ID，留空使用默认设备")
    
    if st.button("连接设备", type="primary"):
        try:
            st.session_state.unicom_tools = UnicomAndroidTools()
            result = st.session_state.unicom_tools.unicom_android_connect(device_id=device_id or None)
            
            if result["success"]:
                st.session_state.device_connected = True
                st.success("✅ 设备连接成功！")
            else:
                st.error(f"❌ 设备连接失败: {result.get('message', '未知错误')}")
        except Exception as e:
            st.error(f"❌ 连接异常: {str(e)}")
    
    if st.session_state.device_connected:
        st.success("📱 设备已连接")
        
        if st.button("断开连接"):
            st.session_state.device_connected = False
            st.session_state.unicom_tools = None
            st.session_state.current_step = "device_setup"
            st.session_state.user_responses = {}
            st.rerun()

# 主界面
if not st.session_state.device_connected:
    st.info("👈 请先在侧边栏连接Android设备")
    st.markdown("""
    ### 📋 使用说明
    1. **连接设备**: 在侧边栏输入设备ID并点击连接
    2. **启动流程**: 设备连接后开始权益领取流程
    3. **交互选择**: 根据流程提示做出选择
    4. **完成业务**: 按步骤完成整个权益领取业务
    
    ### 🎯 业务流程
    - 📱 打开联通APP
    - 🎫 领取优惠券
    - 🛍️ 权益超市选择
    - 👑 PLUS会员处理
    - ✅ 完成业务
    """)
else:
    # 业务流程界面
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🎯 用户权益领取业务流程")
        
        # 流程进度显示
        progress_steps = {
            "device_setup": "设备连接",
            "starting_process": "启动流程", 
            "user_interaction": "用户交互",
            "processing": "执行中",
            "completed": "已完成"
        }
        
        current_step_index = list(progress_steps.keys()).index(st.session_state.current_step)
        progress = (current_step_index + 1) / len(progress_steps)
        
        st.progress(progress)
        st.caption(f"当前步骤: {progress_steps[st.session_state.current_step]}")
        
        # 开始业务流程
        if st.session_state.current_step == "device_setup":
            st.session_state.current_step = "starting_process"
        
        if st.session_state.current_step == "starting_process":
            st.info("🚀 准备开始权益领取流程...")
            
            if st.button("开始权益领取", type="primary"):
                st.session_state.current_step = "processing"
                st.rerun()
        
        elif st.session_state.current_step == "processing":
            st.info("⏳ 正在执行权益领取流程，请稍候...")
            
            # 执行交互式权益领取
            try:
                result = st.session_state.unicom_tools.unicom_user_benefits_claim_interactive(
                    user_responses=st.session_state.user_responses
                )
                st.session_state.process_result = result
                
                if result.get("success") and result.get("result", {}).get("interactions"):
                    st.session_state.current_step = "user_interaction"
                else:
                    st.session_state.current_step = "completed"
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ 执行失败: {str(e)}")
                st.session_state.current_step = "starting_process"
        
        elif st.session_state.current_step == "user_interaction":
            st.success("🤝 需要您的选择来继续业务流程")
            
            if st.session_state.process_result:
                interactions = st.session_state.process_result.get("result", {}).get("interactions", [])
                
                for interaction in interactions:
                    st.markdown(f"### ❓ {interaction['question']}")
                    
                    # 用户选择
                    user_choice = st.radio(
                        "请选择：",
                        interaction["options"],
                        key=f"choice_{interaction['key']}"
                    )
                    
                    if st.button(f"确认选择: {user_choice}", key=f"confirm_{interaction['key']}"):
                        st.session_state.user_responses[interaction["key"]] = user_choice
                        st.session_state.current_step = "processing"
                        st.success(f"✅ 已选择: {user_choice}")
                        st.rerun()
        
        elif st.session_state.current_step == "completed":
            st.success("🎉 权益领取业务流程已完成！")
            
            if st.session_state.process_result:
                result = st.session_state.process_result
                st.markdown(f"**结果**: {result.get('message', '处理完成')}")
                
                # 显示执行步骤
                if result.get("result", {}).get("steps"):
                    st.markdown("### 📋 执行步骤")
                    for i, step in enumerate(result["result"]["steps"], 1):
                        step_name = step.get("step", "未知步骤")
                        step_result = step.get("result", {})
                        choice = step.get("choice", "")
                        
                        if choice:
                            st.markdown(f"{i}. **{step_name}**: {choice}")
                        else:
                            st.markdown(f"{i}. **{step_name}**: {step_result.get('message', '完成')}")
            
            if st.button("重新开始", type="secondary"):
                st.session_state.current_step = "starting_process"
                st.session_state.user_responses = {}
                st.session_state.process_result = None
                st.rerun()
    
    with col2:
        st.header("📊 流程状态")
        
        # 显示用户响应历史
        if st.session_state.user_responses:
            st.markdown("### 🔄 用户选择历史")
            for key, value in st.session_state.user_responses.items():
                choice_labels = {
                    "consumption_choice": "权益超市消费",
                    "is_plus_member": "是否PLUS会员", 
                    "apply_membership": "申请会员",
                    "benefit_choice": "选择权益"
                }
                label = choice_labels.get(key, key)
                st.markdown(f"- **{label}**: {value}")
        
        # 显示流程详情
        if st.session_state.process_result:
            st.markdown("### 📄 详细信息")
            with st.expander("查看完整结果", expanded=False):
                st.json(st.session_state.process_result)
        
        # 帮助信息
        st.markdown("### 💡 温馨提示")
        st.info("""
        **权益超市**: 可以购买优惠的会员服务
        
        **PLUS会员**: 联通高级会员，享受更多权益
        
        **权益选择**: 可领取的会员服务和优惠券
        
        如遇问题，请检查手机连接状态
        """)

# 页脚
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
📱 联通用户权益领取系统 | 基于AgileMind多智能体架构 | 🤖 AI驱动的智能化业务流程
</div>
""", unsafe_allow_html=True)


