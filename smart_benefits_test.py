#!/usr/bin/env python3
"""
智能权益领取流程 - 基于真实UI分析的精确操作
"""

import subprocess
import time
import os
import re
import xml.etree.ElementTree as ET

def execute_adb_command(command):
    """执行ADB命令"""
    try:
        result = subprocess.run(['./platform-tools/adb.exe'] + command.split(), 
                              capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout
    except Exception as e:
        print(f"❌ ADB命令执行失败: {str(e)}")
        return False, str(e)

def get_ui_dump():
    """获取UI布局信息"""
    print("🔍 获取UI布局信息...")
    success, _ = execute_adb_command("shell uiautomator dump /sdcard/ui_current.xml")
    if success:
        success, content = execute_adb_command("shell cat /sdcard/ui_current.xml")
        if success:
            return content
    return None

def find_element_by_text(ui_content, text):
    """从UI内容中查找包含指定文本的元素坐标"""
    print(f"🔍 查找元素: '{text}'")
    
    if not ui_content:
        return None
    
    # 使用正则表达式查找包含指定文本的元素及其bounds
    pattern = rf'text="{text}"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
    match = re.search(pattern, ui_content)
    
    if match:
        x1, y1, x2, y2 = map(int, match.groups())
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        print(f"✅ 找到 '{text}' 在坐标: ({center_x}, {center_y})")
        return (center_x, center_y)
    
    # 如果没找到精确匹配，尝试模糊匹配
    pattern = rf'text="[^"]*{text}[^"]*"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
    match = re.search(pattern, ui_content)
    
    if match:
        x1, y1, x2, y2 = map(int, match.groups())
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        print(f"✅ 模糊匹配找到 '{text}' 在坐标: ({center_x}, {center_y})")
        return (center_x, center_y)
    
    print(f"❌ 未找到元素: '{text}'")
    return None

def find_clickable_elements_with_text(ui_content, keywords):
    """查找包含关键词的可点击元素"""
    print(f"🔍 查找包含关键词的可点击元素: {keywords}")
    
    elements = []
    for keyword in keywords:
        # 方法1: 查找包含关键词且可点击的元素
        pattern1 = rf'clickable="true"[^>]*text="{keyword}"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
        matches1 = re.findall(pattern1, ui_content)
        
        for match in matches1:
            x1, y1, x2, y2 = map(int, match)
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            elements.append((center_x, center_y, keyword))
            print(f"   找到精确匹配: '{keyword}' 在 ({center_x}, {center_y})")
        
        # 方法2: 如果没找到精确匹配，尝试模糊匹配
        if not matches1:
            pattern2 = rf'text="{keyword}"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
            matches2 = re.findall(pattern2, ui_content)
            
            for match in matches2:
                x1, y1, x2, y2 = map(int, match)
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                elements.append((center_x, center_y, keyword))
                print(f"   找到文本匹配: '{keyword}' 在 ({center_x}, {center_y})")
    
    print(f"   共找到 {len(elements)} 个匹配元素")
    return elements

def click_coordinate(x, y, description=""):
    """点击指定坐标"""
    print(f"👆 点击坐标 ({x}, {y}) - {description}")
    success, output = execute_adb_command(f"shell input tap {x} {y}")
    if success:
        print(f"✅ 成功点击 {description}")
    else:
        print(f"❌ 点击失败 {description}: {output}")
    return success

def take_screenshot(filename):
    """截取屏幕截图"""
    print(f"📸 截取屏幕截图: {filename}")
    success, _ = execute_adb_command("shell screencap -p /sdcard/temp_screen.png")
    if success:
        success, _ = execute_adb_command(f"pull /sdcard/temp_screen.png ./screenshots/{filename}")
        execute_adb_command("shell rm /sdcard/temp_screen.png")
        return success
    return False

def main():
    print("🚀 开始智能权益领取流程")
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
    
    # 步骤2: 分析UI并点击"我的"按钮
    print("\n👤 步骤2: 智能查找并点击我的按钮")
    ui_content = get_ui_dump()
    
    my_pos = find_element_by_text(ui_content, "我的")
    if not my_pos:
        # 如果找不到文本，使用之前分析的精确坐标
        print("📍 使用预分析的坐标")
        my_pos = (972, 2167)
    
    success = click_coordinate(my_pos[0], my_pos[1], "我的按钮")
    if not success:
        print("❌ 点击我的按钮失败")
        return
    
    time.sleep(3)  # 等待页面加载
    take_screenshot("02_my_page.png")
    
    # 步骤3: 智能查找并点击"领券中心"
    print("\n🎫 步骤3: 智能查找并点击领券中心")
    ui_content = get_ui_dump()
    
    coupon_pos = find_element_by_text(ui_content, "领券中心")
    if coupon_pos:
        success = click_coordinate(coupon_pos[0], coupon_pos[1], "领券中心")
        if success:
            time.sleep(3)
            take_screenshot("03_coupon_center.png")
            
            # 步骤4: 智能循环领取优惠券
            print("\n🎁 步骤4: 智能循环领取优惠券")
            
            max_attempts = 10  # 最多尝试领取10个优惠券
            claimed_count = 0
            
            for attempt in range(max_attempts):
                print(f"\n   尝试领取第 {attempt + 1} 个优惠券...")
                ui_content = get_ui_dump()
                
                # 查找当前页面的"立即领取"按钮
                claim_buttons = find_clickable_elements_with_text(ui_content, ["立即领取", "领取"])
                
                if not claim_buttons:
                    print("   ✅ 没有更多优惠券可领取")
                    break
                
                # 点击第一个找到的"立即领取"按钮
                x, y, keyword = claim_buttons[0]
                success = click_coordinate(x, y, f"第{attempt+1}个_{keyword}")
                
                if success:
                    claimed_count += 1
                    time.sleep(2)  # 等待领取完成
                    
                    # 检查是否跳转到了新页面（如果跳转了，需要返回）
                    ##current_ui = get_ui_dump()
                    ##if "领券中心" not in current_ui and "优惠券" not in current_ui:
                    time.sleep(2)
                    print("   🔙 检测到页面跳转，返回领券中心")
                    execute_adb_command("shell input keyevent KEYCODE_BACK")
                    time.sleep(2)
                    
                    take_screenshot(f"04_claimed_{attempt+1}.png")
                else:
                    print(f"   ❌ 点击第{attempt+1}个领取按钮失败")
                    break
            
            print(f"\n🎉 优惠券领取完成，共领取了 {claimed_count} 个优惠券")
            
            # 返回到我的页面
            print("🔙 返回到我的页面")
            execute_adb_command("shell input keyevent KEYCODE_BACK")
            time.sleep(2)  # 等待返回
            take_screenshot("04_back_to_my.png")
    else:
        print("⚠️ 未找到领券中心，跳过优惠券领取")
    
    # 步骤5: 智能查找并点击"服务"按钮
    print("\n🛠️ 步骤5: 智能查找并点击服务按钮")
    ui_content = get_ui_dump()
    
    service_pos = find_element_by_text(ui_content, "服务")
    if not service_pos:
        # 使用预分析的坐标
        service_pos = (324, 2167)
    
    success = click_coordinate(service_pos[0], service_pos[1], "服务按钮")
    if not success:
        print("❌ 点击服务按钮失败")
        return
    
    time.sleep(3)  # 等待页面加载
    take_screenshot("05_service_page.png")
    
    # 步骤6: 向下滑动并智能查找PLUS会员
    print("\n⭐ 步骤6: 滑动并智能查找PLUS会员")
    
    plus_found = False
    for scroll_attempt in range(8):
        ui_content = get_ui_dump()
        plus_pos = find_element_by_text(ui_content, "PLUS会员")
        
        if plus_pos:
            print(f"✅ 找到PLUS会员，准备点击")
            success = click_coordinate(plus_pos[0], plus_pos[1], "PLUS会员")
            if success:
                time.sleep(3)
                take_screenshot("06_plus_member.png")
                plus_found = True
                break
        
        if scroll_attempt < 7:  # 不是最后一次尝试
            print(f"   滑动查找 {scroll_attempt + 1}/8")
            execute_adb_command("shell input swipe 500 1000 500 100 500")
            time.sleep(1)
    
    if not plus_found:
        print("❌ 未找到PLUS会员")
    
    print("\n🎉 智能权益领取流程完成!")
    print("请检查screenshots目录下的截图文件查看执行过程")

if __name__ == "__main__":
    main()
