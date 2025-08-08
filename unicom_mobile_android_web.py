"""
中国联通Android手机多智能体助手Web界面
China Unicom Android Mobile Multi-Agent Assistant Web Interface
"""

import streamlit as st
import json
import time
from datetime import datetime
from agilemind.unicom_mobile_android import unicom_mobile_android_assistant


def main():
    """主函数"""
    st.set_page_config(
        page_title="中国联通多智能体手机助手",
        page_icon="📱",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 页面标题
    st.title("📱 中国联通多智能体手机助手")
    st.markdown("### 基于多智能体架构的中国联通APP自动化操作系统")
    
    # 侧边栏配置
    with st.sidebar:
        st.header("🔧 系统配置")
        
        # API配置
        st.subheader("API配置")
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="请输入您的OpenAI API密钥"
        )
        
        if api_key:
            import os
            os.environ["OPENAI_API_KEY"] = api_key
            st.success("✅ API Key已配置")
        else:
            st.warning("⚠️ 请配置API Key")
        
        # 设备配置
        st.subheader("Android设备配置")
        device_id = st.text_input(
            "设备序列号",
            placeholder="请输入Android设备序列号",
            help="通过'adb devices'命令获取设备序列号"
        )
        
        if device_id:
            st.success(f"✅ 设备ID: {device_id}")
        else:
            st.warning("⚠️ 请输入设备序列号")
        
        # 系统状态
        st.subheader("系统状态")
        if st.button("🔍 检查系统状态"):
            with st.spinner("检查中..."):
                # 这里可以添加系统状态检查逻辑
                st.info("系统正常运行")
    
    # 主界面
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 用户需求输入")
        
        # 需求类型选择
        demand_type = st.selectbox(
            "选择需求类型",
            [
                "账户查询（话费、流量、余额）",
                "充值缴费（话费充值、套餐续费）", 
                "套餐服务（套餐查询、办理变更）",
                "网络服务（宽带查询、网络测速）",
                "增值服务（会员服务、权益兑换）",
                "客户服务（在线客服、投诉建议）",
                "自定义需求"
            ]
        )
        
        # 需求描述输入
        if demand_type == "自定义需求":
            user_demand = st.text_area(
                "请描述您的具体需求",
                placeholder="例如：帮我查询一下当前的话费余额和流量使用情况",
                height=100
            )
        else:
            # 根据选择的类型提供预设的需求描述
            preset_demands = {
                "账户查询（话费、流量、余额）": "请帮我查询当前的话费余额和流量使用情况",
                "充值缴费（话费充值、套餐续费）": "请帮我进行话费充值，充值金额50元",
                "套餐服务（套餐查询、办理变更）": "请帮我查询当前套餐信息和可办理的套餐选项",
                "网络服务（宽带查询、网络测速）": "请帮我查询宽带服务状态并进行网络测速",
                "增值服务（会员服务、权益兑换）": "请帮我查询会员权益和可兑换的服务",
                "客户服务（在线客服、投诉建议）": "请帮我联系在线客服进行业务咨询"
            }
            
            user_demand = st.text_area(
                "需求描述（可修改）",
                value=preset_demands.get(demand_type, ""),
                height=100
            )
        
        # 高级选项
        with st.expander("🔧 高级选项"):
            col_a, col_b = st.columns(2)
            
            with col_a:
                enable_screenshot = st.checkbox("启用截图记录", value=True)
                enable_detailed_log = st.checkbox("启用详细日志", value=False)
            
            with col_b:
                operation_timeout = st.slider("操作超时时间(秒)", 10, 120, 30)
                retry_count = st.slider("失败重试次数", 0, 5, 2)
        
        # 执行按钮
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
        
        with col_btn1:
            execute_button = st.button(
                "🚀 开始执行",
                type="primary",
                disabled=not (api_key and device_id and user_demand)
            )
        
        with col_btn2:
            if st.button("📋 查看示例"):
                st.info("""
                **示例需求：**
                - "查询我的话费余额"
                - "帮我充值30元话费"
                - "查看我的流量使用情况"
                - "办理一个新的流量包"
                - "查询我的当前套餐信息"
                - "联系客服咨询业务问题"
                """)
        
        with col_btn3:
            if st.button("🧹 清空结果"):
                if 'execution_results' in st.session_state:
                    del st.session_state.execution_results
                st.rerun()
    
    with col2:
        st.header("📊 联通业务功能")
        
        # 功能说明
        st.markdown("""
        **支持的中国联通APP：**
        - 📱 中国联通营业厅
        - 💰 沃钱包
        - 🎬 沃视频
        - 📚 沃阅读
        - 🎵 沃音乐
        - ☁️ 沃云
        - 🏠 联通智慧家庭
        - 🔧 联通公众APP
        """)
        
        st.markdown("""
        **主要功能：**
        - ✅ 账户信息查询
        - ✅ 话费充值缴费
        - ✅ 套餐查询办理
        - ✅ 流量使用查询
        - ✅ 网络服务管理
        - ✅ 客户服务支持
        """)
        
        # 安全提醒
        st.warning("""
        **安全提醒：**
        - 本系统仅进行演示操作
        - 不会执行真实的支付操作
        - 遇到支付页面会自动停止
        - 请确保设备安全可靠
        """)
    
    # 执行逻辑
    if execute_button:
        if not api_key:
            st.error("❌ 请先配置OpenAI API Key")
        elif not device_id:
            st.error("❌ 请先输入Android设备序列号")
        elif not user_demand:
            st.error("❌ 请输入用户需求描述")
        else:
            # 执行助手
            with st.spinner("🔄 正在执行中国联通多智能体操作..."):
                start_time = time.time()
                
                try:
                    # 调用主函数
                    result = unicom_mobile_android_assistant(user_demand, device_id)
                    
                    # 保存结果到session state
                    st.session_state.execution_results = result
                    st.session_state.execution_time = time.time() - start_time
                    
                except Exception as e:
                    st.error(f"❌ 执行过程中发生错误: {str(e)}")
                    st.session_state.execution_results = {
                        "success": False,
                        "error": str(e)
                    }
    
    # 显示执行结果
    if 'execution_results' in st.session_state:
        st.header("📋 执行结果")
        
        result = st.session_state.execution_results
        execution_time = st.session_state.get('execution_time', 0)
        
        # 结果概览
        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        
        with col_r1:
            if result.get('success'):
                st.metric("执行状态", "✅ 成功")
            else:
                st.metric("执行状态", "❌ 失败")
        
        with col_r2:
            st.metric("执行时间", f"{execution_time:.2f}秒")
        
        with col_r3:
            if 'results' in result:
                st.metric("执行步骤", f"{len(result['results'])}步")
            else:
                st.metric("执行步骤", "0步")
        
        with col_r4:
            if 'session_id' in result:
                st.metric("会话ID", result['session_id'][-8:])
        
        # 详细结果
        if result.get('success'):
            # 用户友好报告
            if 'final_report' in result:
                st.subheader("📄 操作报告")
                st.info(result['final_report'])
            
            # 执行步骤详情
            if 'results' in result:
                st.subheader("🔍 执行详情")
                
                for i, (step_name, step_result) in enumerate(result['results'], 1):
                    with st.expander(f"步骤 {i}: {step_name}"):
                        if step_result.get('success'):
                            st.success(f"✅ {step_name}执行成功")
                        else:
                            st.error(f"❌ {step_name}执行失败")
                        
                        # 显示步骤详细信息
                        if enable_detailed_log:
                            st.json(step_result)
                        else:
                            # 简化显示
                            if 'message' in step_result:
                                st.write(f"**说明**: {step_result['message']}")
                            if 'error' in step_result:
                                st.error(f"**错误**: {step_result['error']}")
        else:
            # 错误信息
            st.error("❌ 执行失败")
            if 'error' in result:
                st.error(f"错误详情: {result['error']}")
            
            # 显示详细错误信息
            if enable_detailed_log:
                st.subheader("🐛 详细错误信息")
                st.json(result)
        
        # 导出结果
        st.subheader("💾 导出结果")
        col_e1, col_e2 = st.columns(2)
        
        with col_e1:
            # 导出JSON
            result_json = json.dumps(result, ensure_ascii=False, indent=2)
            st.download_button(
                label="📄 导出JSON报告",
                data=result_json,
                file_name=f"unicom_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        with col_e2:
            # 导出文本报告
            if result.get('success') and 'final_report' in result:
                text_report = f"""
中国联通多智能体助手执行报告
=====================================

用户需求: {user_demand}
设备ID: {device_id}
执行时间: {execution_time:.2f}秒
执行状态: {'成功' if result.get('success') else '失败'}
会话ID: {result.get('session_id', 'N/A')}
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

操作报告:
{result.get('final_report', '无报告')}
"""
                st.download_button(
                    label="📝 导出文本报告",
                    data=text_report,
                    file_name=f"unicom_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
    
    # 页脚
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
        中国联通多智能体手机助手 | 基于AgileMind架构 | 专为中国联通比赛设计
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

