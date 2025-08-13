#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户权益领取业务测试脚本
User Benefits Claim Test Script
"""

import sys
import os
import time
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agilemind.tool.unicom_android_tools import UnicomAndroidTools


class UserBenefitsClaimTest:
    """用户权益领取业务测试"""
    
    def __init__(self):
        self.unicom_tools = UnicomAndroidTools()
        self.device_id = None
        
    def mock_user_interaction(self, question: str, options: list) -> str:
        """模拟用户交互"""
        print(f"\n📋 系统询问: {question}")
        print("📝 可选项:", ", ".join(options))
        
        # 模拟用户选择逻辑
        if "消费" in question:
            choice = "否"  # 模拟用户不想在权益超市消费
            print(f"🤖 模拟用户选择: {choice}")
            return choice
        elif "PLUS会员" in question and "办理" in question:
            choice = "否"  # 模拟用户不想办理PLUS会员
            print(f"🤖 模拟用户选择: {choice}")
            return choice
        elif "PLUS会员" in question:
            choice = "是"  # 模拟用户是PLUS会员
            print(f"🤖 模拟用户选择: {choice}")
            return choice
        elif "权益" in question:
            # 模拟选择第一个权益
            choice = options[0] if options else "流量包"
            print(f"🤖 模拟用户选择: {choice}")
            return choice
        else:
            choice = options[0] if options else "是"
            print(f"🤖 模拟用户选择: {choice}")
            return choice
    
    def check_device_connection(self) -> bool:
        """检查设备连接"""
        try:
            print("🔍 检查设备连接...")
            
            # 从配置中获取设备ID
            config = self.unicom_tools.config
            device_id = config.get("android_connection", {}).get("device_id", "")
            
            if not device_id:
                print("❌ 配置文件中未找到设备ID")
                return False
            
            # 连接设备
            connect_result = self.unicom_tools.unicom_android_connect(device_id)
            if not connect_result["success"]:
                print(f"❌ 设备连接失败: {connect_result['message']}")
                return False
            
            self.device_id = device_id
            print(f"✅ 成功连接到设备: {device_id}")
            
            # 显示已安装的联通APP
            installed_apps = connect_result.get("installed_unicom_apps", [])
            if installed_apps:
                print(f"📱 已安装的联通APP: {', '.join(installed_apps)}")
            else:
                print("⚠️ 未检测到已安装的联通APP")
            
            return True
            
        except Exception as e:
            print(f"❌ 设备连接检查失败: {e}")
            return False
    
    def test_app_status(self):
        """测试APP状态获取"""
        print("\n📊 获取APP状态...")
        
        status_result = self.unicom_tools.unicom_get_app_status()
        if status_result["success"]:
            print("✅ APP状态获取成功")
            app_status = status_result["app_status"]
            
            for app_name, status in app_status.items():
                status_str = "🟢 运行中" if status["is_running"] else "⚪ 未运行"
                install_str = "✅ 已安装" if status["is_installed"] else "❌ 未安装"
                print(f"   {app_name}: {install_str}, {status_str}")
        else:
            print(f"❌ APP状态获取失败: {status_result['message']}")
    
    def test_screen_capture(self):
        """测试屏幕截图功能"""
        print("\n📸 测试屏幕截图...")
        
        screen_result = self.unicom_tools.unicom_get_screen_content("unicom_app")
        if screen_result["success"]:
            print("✅ 屏幕截图成功")
            print(f"📄 OCR识别文本预览: {screen_result['ocr_text'][:100]}...")
            print(f"📁 截图路径: {screen_result['screenshot_path']}")
            print(f"📱 页面类型: {screen_result['page_type']}")
        else:
            print(f"❌ 屏幕截图失败: {screen_result['message']}")
    
    def test_benefits_claim_workflow(self):
        """测试完整的权益领取业务流程"""
        print("\n🎁 开始测试用户权益领取业务流程...")
        print("=" * 50)
        
        start_time = time.time()
        
        # 执行权益领取业务
        result = self.unicom_tools.unicom_user_benefits_claim(
            user_interaction_callback=self.mock_user_interaction
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 50)
        print("📊 测试结果统计")
        print("=" * 50)
        
        if result["success"]:
            print("✅ 权益领取业务流程测试成功")
            print(f"⏱️ 执行时间: {duration:.2f} 秒")
            
            # 显示详细步骤结果
            results = result.get("results", [])
            print(f"📋 执行步骤: {len(results)} 步")
            
            for i, step_result in enumerate(results, 1):
                step_name = step_result["step"]
                step_success = step_result["result"]["success"]
                step_status = "✅" if step_success else "❌"
                print(f"   {i}. {step_status} {step_name}")
                
                if not step_success:
                    print(f"      错误: {step_result['result'].get('message', '未知错误')}")
                elif "claimed_coupons" in step_result["result"]:
                    coupons = step_result["result"]["claimed_coupons"]
                    print(f"      领取券数: {len(coupons)}")
        else:
            print("❌ 权益领取业务流程测试失败")
            print(f"❌ 错误信息: {result['message']}")
            print(f"⏱️ 执行时间: {duration:.2f} 秒")
        
        return result["success"]
    
    def run_test(self):
        """运行完整测试"""
        print("🎁 用户权益领取业务测试")
        print("=" * 50)
        print(f"🕒 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 1. 检查设备连接
            if not self.check_device_connection():
                print("\n❌ 设备连接失败，测试终止")
                return False
            
            # 2. 测试APP状态
            self.test_app_status()
            
            # 3. 测试屏幕截图
            self.test_screen_capture()
            
            # 4. 测试权益领取业务流程
            success = self.test_benefits_claim_workflow()
            
            print("\n" + "=" * 50)
            if success:
                print("🎉 所有测试完成，权益领取功能正常工作")
                print("\n💡 后续可以实现的增强功能:")
                print("   ✅ 更精确的UI元素定位")
                print("   ✅ 智能重试机制")
                print("   ✅ 更多权益类型识别")
                print("   ✅ 用户偏好记忆")
            else:
                print("❌ 测试失败，需要检查和修复问题")
            
            return success
            
        except KeyboardInterrupt:
            print("\n🛑 测试被用户中断")
            return False
        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
            return False


def main():
    """主函数"""
    print("🎁 用户权益领取业务测试工具")
    print("=" * 50)
    
    tester = UserBenefitsClaimTest()
    
    print("\n🔧 测试选项:")
    print("1. 运行完整权益领取业务测试 (推荐)")
    print("2. 仅测试设备连接")
    print("3. 仅测试APP状态")
    print("4. 仅测试屏幕截图")
    print("5. 查看使用说明")
    
    try:
        choice = input("\n请选择测试选项 (1-5): ").strip()
        
        if choice == "1":
            tester.run_test()
        elif choice == "2":
            tester.check_device_connection()
        elif choice == "3":
            if tester.check_device_connection():
                tester.test_app_status()
        elif choice == "4":
            if tester.check_device_connection():
                tester.test_screen_capture()
        elif choice == "5":
            print_usage_guide()
        else:
            print("❌ 无效选择")
            
    except KeyboardInterrupt:
        print("\n👋 测试已取消")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")


def print_usage_guide():
    """打印使用说明"""
    print("\n📖 使用说明")
    print("=" * 50)
    print("1. 确保Android设备通过USB连接到电脑")
    print("2. 设备已开启开发者选项和USB调试")
    print("3. 已安装中国联通手机营业厅APP")
    print("4. 配置文件中设置正确的设备ID")
    print("\n🔍 测试流程:")
    print("1. 自动启动联通APP")
    print("2. 导航到'我的'页面")
    print("3. 进入领券中心并自动领取优惠券")
    print("4. 进入服务页面")
    print("5. 处理权益超市（询问用户是否消费）")
    print("6. 处理PLUS会员（检查会员状态和权益领取）")
    print("\n💡 测试特点:")
    print("- 支持模拟用户交互")
    print("- 完整的业务流程覆盖")
    print("- 详细的错误信息和步骤追踪")
    print("- 自动截图和OCR识别")


if __name__ == "__main__":
    main()

