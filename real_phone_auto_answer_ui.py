#!/usr/bin/env python3
"""
真实智能代接系统用户界面
Real Phone Auto Answer User Interface

用户可以完全自定义各场景的回复语
"""

import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unimind.tool.real_phone_auto_answer import (
    real_phone_manager,
    real_phone_toggle_auto_answer,
    real_phone_set_scenario,
    real_phone_set_user_response,
    real_phone_get_user_responses,
    real_phone_get_status,
    real_phone_set_ring_delay
)

def main():
    """主界面"""
    st.set_page_config(
        page_title="真实智能代接系统",
        page_icon="📞",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("📞 真实智能代接系统")
    st.markdown("---")
    
    # 获取当前状态
    status = real_phone_get_status()
    
    # 侧边栏控制
    with st.sidebar:
        st.header("🎛️ 系统控制")
        
        # 开关控制
        current_enabled = status.get("enabled", False)
        new_enabled = st.toggle("智能代接开关", value=current_enabled)
        
        if new_enabled != current_enabled:
            result = real_phone_toggle_auto_answer(new_enabled)
            if result["success"]:
                st.success(result["message"])
                st.rerun()
            else:
                st.error(result.get("error", "操作失败"))
        
        # 响铃延迟设置
        st.subheader("⏰ 响铃设置")
        ring_delay = st.slider(
            "未开启代接时的响铃延迟（秒）",
            min_value=5,
            max_value=30,
            value=status.get("ring_delay_seconds", 10),
            step=1
        )
        
        if st.button("保存延迟设置"):
            result = real_phone_set_ring_delay(ring_delay)
            if result["success"]:
                st.success(result["message"])
            else:
                st.error(result.get("error", "设置失败"))
        
        # 状态显示
        st.subheader("📊 系统状态")
        st.write(f"**代接状态**: {'🟢 开启' if status.get('enabled', False) else '🔴 关闭'}")
        st.write(f"**当前场景**: {status.get('current_scenario', '未知')}")
        st.write(f"**监控状态**: {'🔴 监控中' if status.get('monitoring', False) else '⚪ 未监控'}")
        st.write(f"**总通话数**: {status.get('total_calls', 0)}")
        st.write(f"**24小时通话**: {status.get('recent_calls_24h', 0)}")
    
    # 主要内容区域
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("🎭 场景管理")
        
        # 场景选择
        available_scenarios = status.get("available_scenarios", [])
        current_scenario = status.get("current_scenario", "busy")
        
        if available_scenarios:
            scenario_index = available_scenarios.index(current_scenario) if current_scenario in available_scenarios else 0
            selected_scenario = st.selectbox(
                "选择当前场景",
                available_scenarios,
                index=scenario_index
            )
            
            if selected_scenario != current_scenario:
                result = real_phone_set_scenario(selected_scenario)
                if result["success"]:
                    st.success(f"场景已切换到: {selected_scenario}")
                    st.rerun()
                else:
                    st.error(result.get("error", "切换失败"))
        
        # 快捷场景按钮
        st.subheader("🚀 快捷切换")
        
        scenario_buttons = {
            "work": "💼 工作模式",
            "meeting": "👥 会议模式",
            "delivery": "🚚 外卖模式",
            "rest": "😴 休息模式",
            "driving": "🚗 驾驶模式",
            "study": "📚 学习模式",
            "unknown": "❓ 陌生电话",
            "busy": "⏰ 忙碌模式",
            "hospital": "🏥 医院模式"
        }
        
        cols = st.columns(3)
        for i, (scenario_key, scenario_name) in enumerate(scenario_buttons.items()):
            with cols[i % 3]:
                if st.button(scenario_name, key=f"btn_{scenario_key}"):
                    result = real_phone_set_scenario(scenario_key)
                    if result["success"]:
                        st.success(f"已切换到{scenario_name}")
                        st.rerun()
                    else:
                        st.error("切换失败")
    
    with col2:
        st.header("📝 自定义回复设置")
        
        # 获取当前用户回复
        user_responses = real_phone_get_user_responses()
        
        # 场景回复编辑
        st.subheader("✏️ 编辑场景回复")
        
        # 选择要编辑的场景
        edit_scenario = st.selectbox(
            "选择要编辑的场景",
            list(scenario_buttons.keys()),
            format_func=lambda x: scenario_buttons[x]
        )
        
        # 当前回复显示
        current_response = user_responses.get(edit_scenario, "")
        st.text_area(
            f"当前{scenario_buttons[edit_scenario]}回复",
            value=current_response,
            height=80,
            disabled=True,
            key="current_response_display"
        )
        
        # 新回复输入
        new_response = st.text_area(
            f"设置新的{scenario_buttons[edit_scenario]}回复",
            value=current_response,
            height=100,
            placeholder="请输入您希望在此场景下播放的回复语音...",
            help="这段话将会通过语音合成播放给来电者"
        )
        
        col_save, col_preview = st.columns(2)
        
        with col_save:
            if st.button("💾 保存回复", type="primary"):
                if new_response.strip():
                    result = real_phone_set_user_response(edit_scenario, new_response.strip())
                    if result["success"]:
                        st.success("回复已保存！")
                        st.rerun()
                    else:
                        st.error(result.get("error", "保存失败"))
                else:
                    st.warning("回复内容不能为空")
        
        with col_preview:
            if st.button("🔊 预览语音"):
                if new_response.strip():
                    st.info(f"语音预览: {new_response[:50]}...")
                    # 这里可以集成真实的TTS预览
                    st.write("📢 语音将播放: ", new_response)
                else:
                    st.warning("请先输入回复内容")
    
    # 全屏回复管理
    st.markdown("---")
    st.header("📋 所有场景回复一览")
    
    # 显示所有场景的回复
    cols = st.columns(3)
    for i, (scenario_key, scenario_name) in enumerate(scenario_buttons.items()):
        with cols[i % 3]:
            with st.container():
                st.subheader(scenario_name)
                response_text = user_responses.get(scenario_key, "未设置")
                st.text_area(
                    "回复内容",
                    value=response_text,
                    height=100,
                    disabled=True,
                    key=f"view_{scenario_key}"
                )
                
                # 字数统计
                char_count = len(response_text) if response_text != "未设置" else 0
                estimated_duration = char_count * 0.15  # 估算播放时长
                st.caption(f"字数: {char_count} | 预计播放: {estimated_duration:.1f}秒")
    
    # 批量操作
    st.markdown("---")
    st.header("🔧 批量操作")
    
    col_export, col_import, col_reset = st.columns(3)
    
    with col_export:
        if st.button("📤 导出设置"):
            st.json(user_responses)
            st.success("设置已显示，您可以复制保存")
    
    with col_import:
        import_text = st.text_area("📥 导入设置（JSON格式）", height=100)
        if st.button("导入") and import_text.strip():
            try:
                import json
                imported_responses = json.loads(import_text)
                for scenario, response in imported_responses.items():
                    real_phone_set_user_response(scenario, response)
                st.success("设置导入成功！")
                st.rerun()
            except Exception as e:
                st.error(f"导入失败: {e}")
    
    with col_reset:
        if st.button("🔄 重置为默认", type="secondary"):
            if st.button("确认重置", type="secondary"):
                # 重置为默认回复
                default_responses = {
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
                for scenario, response in default_responses.items():
                    real_phone_set_user_response(scenario, response)
                st.success("已重置为默认回复！")
                st.rerun()
    
    # 使用说明
    with st.expander("📚 使用说明"):
        st.markdown("""
        ### 🎯 系统功能
        - **真实电话接听**: 监控来电状态，自动接听并播放自定义回复
        - **完全自定义**: 所有场景的回复语都可以由您自己设置
        - **智能场景**: 支持9种生活场景，覆盖各种日常情况
        - **灵活控制**: 可以随时开启/关闭，调整响铃延迟
        
        ### 🛠️ 使用步骤
        1. **设置回复语**: 在右侧为各个场景设置您希望的回复内容
        2. **选择场景**: 根据当前情况选择合适的场景模式
        3. **开启代接**: 在侧边栏开启智能代接功能
        4. **等待来电**: 系统将自动监控并处理来电
        
        ### ⚠️ 注意事项
        - 确保Android设备已连接并开启USB调试
        - 需要电话和音频相关权限
        - 建议在回复语中保持礼貌和简洁
        - 紧急情况下可通过物理按键强制接听
        
        ### 🎨 回复语建议
        - **工作场景**: 专业、礼貌，说明当前状态
        - **会议场景**: 简洁、道歉，承诺尽快回复
        - **外卖场景**: 实用、指导性，提供具体指引
        - **陌生电话**: 安全、询问，要求说明来意
        - **其他场景**: 根据实际情况个性化设置
        """)

if __name__ == "__main__":
    main()
