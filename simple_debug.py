#!/usr/bin/env python3
"""
简单调试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agilemind.tool.unicom_android_tools import UnicomAndroidTools

def simple_test():
    print("🔍 简单调试测试")
    print("=" * 40)
    
    tools = UnicomAndroidTools()
    
    print("📱 测试启动APP...")
    launch_result = tools.unicom_launch_app("unicom_app")
    print(f"启动结果: {launch_result}")
    
    if launch_result["success"]:
        print("\n👤 测试导航到我的页面...")
        my_result = tools._navigate_to_my_page()
        print(f"我的页面结果: {my_result}")
        
        if my_result["success"]:
            print("\n🎫 测试领券中心...")
            coupon_result = tools._claim_coupons_in_center()
            print(f"领券结果: {coupon_result}")

if __name__ == "__main__":
    simple_test()
