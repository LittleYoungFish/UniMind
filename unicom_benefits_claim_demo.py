#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户权益领取业务演示程序
User Benefits Claim Demo Application
"""

import streamlit as st
import sys
import os
import time
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agilemind.tool.unicom_android_tools import UnicomAndroidTools


class BenefitsClaimDemo:
    """权益领取演示类"""
    
    def __init__(self):
        if 'unicom_tools' not in st.session_state:
            st.session_state.unicom_tools = UnicomAndroidTools()
        if 'device_connected' not in st.session_state:
            st.session_state.device_connected = False
        if 'operation_logs' not in st.session_state:
            st.session_state.operation_logs = []
    
    def log_operation(self, message: str, status: str = "info"):
        """记录操作日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.operation_logs.append({
            "timestamp": timestamp,
            "message": message,
            "status": status
        })
    
    def user_interaction_callback(self, question: str, options: list) -> str:
        """处理用户交互"""
        # 在Streamlit中显示用户选择界面
        st.info(f"🤔 {question}")
        
        # 使用单选按钮让用户选择
        choice = st.radio("请选择:", options, key=f"choice_{hash(question)}")
        
        # 等待用户确认
        if st.button("确认选择", key=f"confirm_{hash(question)}"):
            self.log_operation(f"用户选择: {choice}", "success")
            return choice
        
        return options[0]  # 默认返回第一个选项
    
    def render_sidebar(self):
        """渲染侧边栏"""
        st.sidebar.title("🎁 权益领取控制台")
        
        # 设备连接部分
        st.sidebar.subheader("📱 设备连接")
        
        device_id = st.sidebar.text_input(
            "设备ID", 
            value=st.session_state.unicom_tools.config.get("android_connection", {}).get("device_id", ""),
            help="输入Android设备的序列号"
        )
        
        if st.sidebar.button("连接设备"):
            if device_id:
                with st.spinner("正在连接设备..."):
                    result = st.session_state.unicom_tools.unicom_android_connect(device_id)
                    if result["success"]:
                        st.session_state.device_connected = True
                        self.log_operation(f"成功连接设备: {device_id}", "success")
                        st.sidebar.success("设备连接成功!")
                        
                        # 显示已安装的APP
                        installed_apps = result.get("installed_unicom_apps", [])
                        if installed_apps:
                            st.sidebar.info(f"已安装APP: {', '.join(installed_apps)}")
                    else:
                        st.session_state.device_connected = False
                        self.log_operation(f"设备连接失败: {result['message']}", "error")
                        st.sidebar.error(f"连接失败: {result['message']}")
            else:
                st.sidebar.warning("请输入设备ID")
        
        # 连接状态指示
        if st.session_state.device_connected:
            st.sidebar.success("🟢 设备已连接")
        else:
            st.sidebar.error("🔴 设备未连接")
        
        # 快速操作
        st.sidebar.subheader("🚀 快速操作")
        
        if st.sidebar.button("获取APP状态", disabled=not st.session_state.device_connected):
            self.get_app_status()
        
        if st.sidebar.button("截取屏幕", disabled=not st.session_state.device_connected):
            self.capture_screen()
        
        if st.sidebar.button("启动联通APP", disabled=not st.session_state.device_connected):
            self.launch_unicom_app()
    
    def get_app_status(self):
        """获取APP状态"""
        with st.spinner("获取APP状态..."):
            result = st.session_state.unicom_tools.unicom_get_app_status()
            if result["success"]:
                self.log_operation("APP状态获取成功", "success")
                
                # 显示APP状态表格
                app_status = result["app_status"]
                status_data = []
                for app_name, status in app_status.items():
                    status_data.append({
                        "APP名称": app_name,
                        "安装状态": "✅ 已安装" if status["is_installed"] else "❌ 未安装",
                        "运行状态": "🟢 运行中" if status["is_running"] else "⚪ 未运行",
                        "包名": status["package_name"]
                    })
                
                st.dataframe(status_data)
            else:
                self.log_operation(f"APP状态获取失败: {result['message']}", "error")
                st.error(f"获取失败: {result['message']}")
    
    def capture_screen(self):
        """截取屏幕"""
        with st.spinner("截取屏幕..."):
            result = st.session_state.unicom_tools.unicom_get_screen_content("unicom_app")
            if result["success"]:
                self.log_operation("屏幕截取成功", "success")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📸 截图")
                    if os.path.exists(result["screenshot_path"]):
                        st.image(result["screenshot_path"], caption="当前屏幕", use_column_width=True)
                    else:
                        st.warning("截图文件未找到")
                
                with col2:
                    st.subheader("📄 OCR识别结果")
                    st.text_area("识别文本", result["ocr_text"], height=300)
                    st.info(f"页面类型: {result['page_type']}")
            else:
                self.log_operation(f"屏幕截取失败: {result['message']}", "error")
                st.error(f"截取失败: {result['message']}")
    
    def launch_unicom_app(self):
        """启动联通APP"""
        with st.spinner("启动联通APP..."):
            result = st.session_state.unicom_tools.unicom_launch_app("unicom_app")
            if result["success"]:
                self.log_operation("联通APP启动成功", "success")
                st.success("APP启动成功!")
                time.sleep(2)
                # 自动截取屏幕
                self.capture_screen()
            else:
                self.log_operation(f"APP启动失败: {result['message']}", "error")
                st.error(f"启动失败: {result['message']}")
    
    def render_main_interface(self):
        """渲染主界面"""
        st.title("🎁 用户权益领取业务演示")
        st.markdown("---")
        
        # 业务介绍
        with st.expander("📋 业务流程说明", expanded=True):
            st.markdown("""
            ### 用户权益领取业务流程
            
            1. **启动APP**: 自动打开中国联通手机营业厅APP
            2. **进入我的页面**: 点击底部"我的"按钮
            3. **领券中心**: 进入领券中心，自动点击所有"领取"按钮
            4. **进入服务页面**: 点击底部"服务"按钮
            5. **权益超市**: 询问用户是否需要消费，根据选择操作
            6. **PLUS会员**: 检查会员状态，管理会员权益
            
            ### 特点
            - 🤖 全自动化操作
            - 🎯 智能UI识别
            - 💬 用户交互支持
            - 📊 详细日志记录
            """)
        
        # 主要操作区域
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🎮 操作控制")
            
            # 权益领取按钮
            if st.button(
                "🎁 开始权益领取业务", 
                disabled=not st.session_state.device_connected,
                help="执行完整的权益领取业务流程"
            ):
                self.execute_benefits_claim()
            
            # 分步操作
            st.subheader("🔧 分步操作")
            
            step_col1, step_col2 = st.columns(2)
            
            with step_col1:
                if st.button("1️⃣ 进入我的页面", disabled=not st.session_state.device_connected):
                    self.navigate_to_my_page()
                
                if st.button("3️⃣ 领取优惠券", disabled=not st.session_state.device_connected):
                    self.claim_coupons()
            
            with step_col2:
                if st.button("2️⃣ 进入服务页面", disabled=not st.session_state.device_connected):
                    self.navigate_to_service()
                
                if st.button("4️⃣ 处理PLUS会员", disabled=not st.session_state.device_connected):
                    self.handle_plus_membership()
        
        with col2:
            st.subheader("📊 实时状态")
            
            # 设备状态
            if st.session_state.device_connected:
                st.success("🟢 设备已连接")
            else:
                st.error("🔴 设备未连接")
            
            # 操作统计
            total_ops = len(st.session_state.operation_logs)
            success_ops = len([log for log in st.session_state.operation_logs if log["status"] == "success"])
            error_ops = len([log for log in st.session_state.operation_logs if log["status"] == "error"])
            
            st.metric("总操作数", total_ops)
            st.metric("成功操作", success_ops, delta=None)
            st.metric("失败操作", error_ops, delta=None)
    
    def execute_benefits_claim(self):
        """执行权益领取业务"""
        st.subheader("🎁 执行权益领取业务")
        
        # 创建进度条
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 用户交互容器
        interaction_container = st.container()
        
        def interactive_callback(question: str, options: list) -> str:
            """交互回调函数"""
            with interaction_container:
                st.info(f"🤔 {question}")
                
                # 使用unique key避免重复
                key = f"choice_{hash(question)}_{time.time()}"
                choice = st.selectbox("请选择:", options, key=key)
                
                if st.button("确认选择", key=f"confirm_{key}"):
                    self.log_operation(f"用户选择: {choice}", "success")
                    return choice
                
                # 默认选择（用于自动演示）
                return options[0]
        
        try:
            status_text.text("🚀 开始执行权益领取业务...")
            progress_bar.progress(10)
            
            # 执行权益领取业务
            result = st.session_state.unicom_tools.unicom_user_benefits_claim(
                user_interaction_callback=interactive_callback
            )
            
            progress_bar.progress(100)
            
            if result["success"]:
                status_text.text("✅ 权益领取业务执行完成!")
                self.log_operation("权益领取业务执行成功", "success")
                
                # 显示执行结果
                with st.expander("📋 执行详情", expanded=True):
                    results = result.get("results", [])
                    for i, step_result in enumerate(results, 1):
                        step_name = step_result["step"]
                        step_success = step_result["result"]["success"]
                        step_message = step_result["result"].get("message", "")
                        
                        if step_success:
                            st.success(f"✅ 步骤 {i}: {step_name} - {step_message}")
                        else:
                            st.error(f"❌ 步骤 {i}: {step_name} - {step_message}")
                        
                        # 显示优惠券领取结果
                        if "claimed_coupons" in step_result["result"]:
                            coupons = step_result["result"]["claimed_coupons"]
                            st.info(f"🎫 领取了 {len(coupons)} 张优惠券")
                
                st.balloons()  # 成功庆祝动画
            else:
                status_text.text("❌ 权益领取业务执行失败")
                self.log_operation(f"权益领取业务失败: {result['message']}", "error")
                st.error(f"执行失败: {result['message']}")
                
        except Exception as e:
            status_text.text("❌ 执行异常")
            self.log_operation(f"执行异常: {str(e)}", "error")
            st.error(f"执行异常: {str(e)}")
    
    def navigate_to_my_page(self):
        """导航到我的页面"""
        with st.spinner("导航到我的页面..."):
            result = st.session_state.unicom_tools._navigate_to_my_page()
            if result["success"]:
                self.log_operation("成功进入我的页面", "success")
                st.success("✅ 成功进入我的页面")
            else:
                self.log_operation(f"进入我的页面失败: {result['message']}", "error")
                st.error(f"❌ {result['message']}")
    
    def navigate_to_service(self):
        """导航到服务页面"""
        with st.spinner("导航到服务页面..."):
            result = st.session_state.unicom_tools._navigate_to_service_page()
            if result["success"]:
                self.log_operation("成功进入服务页面", "success")
                st.success("✅ 成功进入服务页面")
            else:
                self.log_operation(f"进入服务页面失败: {result['message']}", "error")
                st.error(f"❌ {result['message']}")
    
    def claim_coupons(self):
        """领取优惠券"""
        with st.spinner("领取优惠券..."):
            result = st.session_state.unicom_tools._claim_coupons_in_center()
            if result["success"]:
                coupons = result.get("claimed_coupons", [])
                self.log_operation(f"成功领取 {len(coupons)} 张优惠券", "success")
                st.success(f"✅ 成功领取 {len(coupons)} 张优惠券")
            else:
                self.log_operation(f"领取优惠券失败: {result['message']}", "error")
                st.error(f"❌ {result['message']}")
    
    def handle_plus_membership(self):
        """处理PLUS会员"""
        with st.spinner("处理PLUS会员..."):
            result = st.session_state.unicom_tools._handle_plus_membership()
            if result["success"]:
                self.log_operation("PLUS会员处理成功", "success")
                st.success(f"✅ {result['message']}")
            else:
                self.log_operation(f"PLUS会员处理失败: {result['message']}", "error")
                st.error(f"❌ {result['message']}")
    
    def render_logs(self):
        """渲染操作日志"""
        st.subheader("📝 操作日志")
        
        if st.session_state.operation_logs:
            # 显示最近的日志
            recent_logs = st.session_state.operation_logs[-10:]  # 最近10条
            
            for log in reversed(recent_logs):
                timestamp = log["timestamp"]
                message = log["message"]
                status = log["status"]
                
                if status == "success":
                    st.success(f"[{timestamp}] ✅ {message}")
                elif status == "error":
                    st.error(f"[{timestamp}] ❌ {message}")
                else:
                    st.info(f"[{timestamp}] ℹ️ {message}")
            
            # 清除日志按钮
            if st.button("🗑️ 清除日志"):
                st.session_state.operation_logs = []
                st.experimental_rerun()
        else:
            st.info("暂无操作日志")
    
    def run(self):
        """运行演示应用"""
        st.set_page_config(
            page_title="用户权益领取演示",
            page_icon="🎁",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # 渲染界面
        self.render_sidebar()
        self.render_main_interface()
        
        st.markdown("---")
        self.render_logs()


def main():
    """主函数"""
    demo = BenefitsClaimDemo()
    demo.run()


if __name__ == "__main__":
    main()

