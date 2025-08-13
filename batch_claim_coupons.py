#!/usr/bin/env python3
"""
批量领取优惠券脚本
自动点击所有"立即领取"按钮并处理返回操作
"""

import subprocess
import time

# 所有"立即领取"按钮的坐标位置（从之前的UI dump中提取）
CLAIM_BUTTONS = [
    (165, 991),   # 合约直降券
    (414, 991),   # 国家大剧院
    (666, 991),   # 浪漫爱情号
    (915, 991),   # 万元还款金
    (930, 1471),  # 至高1000
    (930, 1768),  # 开通好礼
    (930, 2067),  # 权益超市
    (930, 2244),  # 更多"立即领取"按钮...
]

def execute_adb_command(command):
    """执行ADB命令"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def tap_button(x, y):
    """点击指定坐标"""
    success, stdout, stderr = execute_adb_command(f"./platform-tools/adb.exe shell input tap {x} {y}")
    return success

def press_back():
    """按返回键"""
    success, stdout, stderr = execute_adb_command("./platform-tools/adb.exe shell input keyevent 4")
    return success

def main():
    print("🎯 开始批量领取优惠券...")
    
    claimed_count = 0
    for i, (x, y) in enumerate(CLAIM_BUTTONS, 1):
        print(f"📱 点击第 {i} 个立即领取按钮 ({x}, {y})")
        
        # 点击领取按钮
        if tap_button(x, y):
            print(f"✅ 成功点击第 {i} 个按钮")
            claimed_count += 1
            
            # 等待页面响应
            time.sleep(2)
            
            # 如果跳转到新页面，按返回键
            print("🔙 按返回键回到领券中心")
            if press_back():
                print("✅ 成功返回领券中心")
            else:
                print("❌ 返回失败")
            
            # 等待页面加载
            time.sleep(1.5)
        else:
            print(f"❌ 点击第 {i} 个按钮失败")
    
    print(f"\n🎉 批量领取完成！共成功领取 {claimed_count} 个优惠券")
    
    # 完成后导航到服务页面
    print("\n📱 导航到服务页面...")
    
    # 点击底部"服务"按钮 (324, 2212)
    if tap_button(324, 2212):
        print("✅ 成功切换到服务页面")
        time.sleep(3)  # 等待服务页面加载
        return True
    else:
        print("❌ 切换到服务页面失败")
        return False

if __name__ == "__main__":
    main()
