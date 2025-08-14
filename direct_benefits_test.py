#!/usr/bin/env python3
"""
直接测试用户权益领取流程 - 简单明确的操作序列
"""

import subprocess
import time
import os

def execute_adb_command(command):
    """执行ADB命令"""
    try:
        result = subprocess.run(['./platform-tools/adb.exe'] + command.split(), 
                              capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout
    except Exception as e:
        print(f"❌ ADB命令执行失败: {str(e)}")
        return False, str(e)

def take_screenshot(filename):
    """截取屏幕截图"""
    print(f"📸 截取屏幕截图: {filename}")
    success, _ = execute_adb_command("shell screencap -p /sdcard/temp_screen.png")
    if success:
        success, _ = execute_adb_command(f"pull /sdcard/temp_screen.png ./screenshots/{filename}")
        execute_adb_command("shell rm /sdcard/temp_screen.png")
        return success
    return False

def click_coordinate(x, y, description=""):
    """点击指定坐标"""
    print(f"👆 点击坐标 ({x}, {y}) - {description}")
    success, output = execute_adb_command(f"shell input tap {x} {y}")
    if success:
        print(f"✅ 成功点击 {description}")
    else:
        print(f"❌ 点击失败 {description}: {output}")
    return success

def main():
    print("🚀 开始用户权益领取流程测试")
    print("=" * 60)
    
    # 确保截图目录存在
    os.makedirs("screenshots", exist_ok=True)
    
    # 步骤1: 启动联通APP
    print("\n📱 步骤1: 启动联通APP")
    success, _ = execute_adb_command("shell monkey -p com.sinovatech.unicom.ui -c android.intent.category.LAUNCHER 1")
    if not success:
        print("❌ 启动APP失败")
        return
    
    time.sleep(5)  # 等待APP启动
    take_screenshot("01_app_launched.png")
    
    # 步骤2: 点击"我的"按钮
    print("\n👤 步骤2: 点击我的按钮")
    success = click_coordinate(972, 2167, "我的按钮")
    if not success:
        print("❌ 点击我的按钮失败")
        return
    
    time.sleep(3)  # 等待页面加载
    take_screenshot("02_my_page.png")
    
    # 步骤3: 点击"领券中心"
    print("\n🎫 步骤3: 点击领券中心")
    # 先尝试获取UI布局找到领券中心
    execute_adb_command("shell uiautomator dump /sdcard/ui_my_page.xml")
    execute_adb_command("pull /sdcard/ui_my_page.xml ./")
    
    # 尝试点击领券中心（可能的位置）
    coupon_positions = [
        (540, 600, "领券中心位置1"),
        (540, 700, "领券中心位置2"),
        (540, 800, "领券中心位置3"),
    ]
    
    coupon_clicked = False
    for x, y, desc in coupon_positions:
        if click_coordinate(x, y, desc):
            time.sleep(2)
            take_screenshot("03_coupon_center.png")
            coupon_clicked = True
            break
    
    if not coupon_clicked:
        print("⚠️ 未能找到领券中心，继续下一步")
    else:
        # 步骤4: 在领券中心领取优惠券
        print("\n🎁 步骤4: 领取优惠券")
        # 尝试点击"领取"按钮
        claim_positions = [
            (930, 1471, "立即领取按钮1"),
            (930, 1768, "立即领取按钮2"),
            (930, 2067, "立即领取按钮3"),
        ]
        
        for x, y, desc in claim_positions:
            click_coordinate(x, y, desc)
            time.sleep(1)
            # 检查是否需要返回
            execute_adb_command("shell input keyevent KEYCODE_BACK")
            time.sleep(1)
        
        # 返回到我的页面
        print("🔙 返回到我的页面")
        execute_adb_command("shell input keyevent KEYCODE_BACK")
        time.sleep(2)
        take_screenshot("04_back_to_my.png")
    
    # 步骤5: 点击"服务"按钮
    print("\n🛠️ 步骤5: 点击服务按钮")
    success = click_coordinate(324, 2167, "服务按钮")
    if not success:
        print("❌ 点击服务按钮失败")
        return
    
    time.sleep(3)  # 等待页面加载
    take_screenshot("05_service_page.png")
    
    # 步骤6: 向下滑动找到权益栏
    print("\n📜 步骤6: 向下滑动找到权益栏")
    for i in range(3):
        print(f"   滑动 {i+1}/3")
        execute_adb_command("shell input swipe 500 800 500 400 500")
        time.sleep(1)
    
    take_screenshot("06_scrolled_service.png")
    
    # 步骤7: 点击PLUS会员
    print("\n⭐ 步骤7: 查找并点击PLUS会员")
    # 获取当前UI布局
    execute_adb_command("shell uiautomator dump /sdcard/ui_service.xml")
    execute_adb_command("pull /sdcard/ui_service.xml ./")
    
    # 尝试点击PLUS会员的可能位置
    plus_positions = [
        (540, 1000, "PLUS会员位置1"),
        (540, 1200, "PLUS会员位置2"),
        (540, 1400, "PLUS会员位置3"),
    ]
    
    for x, y, desc in plus_positions:
        if click_coordinate(x, y, desc):
            time.sleep(3)
            take_screenshot("07_plus_member.png")
            break
    
    print("\n🎉 权益领取流程测试完成!")
    print("请检查screenshots目录下的截图文件查看执行过程")

if __name__ == "__main__":
    main()

