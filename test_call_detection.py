#!/usr/bin/env python3
"""
测试来电检测功能
Test Call Detection
"""

import subprocess
import time
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_adb_connection():
    """测试ADB连接"""
    print("🔍 测试ADB连接...")
    try:
        adb_path = "./platform-tools/adb.exe"
        result = subprocess.run([adb_path, "devices"], capture_output=True, text=True, timeout=5)
        print(f"ADB设备列表:\n{result.stdout}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ ADB连接测试失败: {e}")
        return False

def test_telephony_registry():
    """测试telephony registry状态"""
    print("\n📞 测试telephony registry...")
    try:
        adb_path = "./platform-tools/adb.exe"
        result = subprocess.run([adb_path, "shell", "dumpsys", "telephony.registry"], 
                              capture_output=True, text=True, timeout=3)
        
        if result.returncode == 0:
            output = result.stdout
            print("📋 Telephony Registry 输出片段:")
            
            # 查找关键状态信息
            lines = output.split('\n')
            for line in lines:
                if any(keyword in line for keyword in ['mCallState', 'CallState', 'call state', 'Call state']):
                    print(f"  📱 {line.strip()}")
            
            # 检查通话状态
            if "mCallState=1" in output:
                print("🔔 检测到响铃状态 (RINGING)")
                return "RINGING"
            elif "mCallState=2" in output:
                print("📞 检测到通话状态 (OFFHOOK)")
                return "OFFHOOK"
            elif "mCallState=0" in output:
                print("📱 设备空闲状态 (IDLE)")
                return "IDLE"
            else:
                print("❓ 未找到明确的通话状态")
                return "UNKNOWN"
        else:
            print(f"❌ 获取telephony registry失败: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Telephony registry测试失败: {e}")
        return None

def test_gsm_properties():
    """测试GSM属性"""
    print("\n📡 测试GSM属性...")
    try:
        adb_path = "./platform-tools/adb.exe"
        result = subprocess.run([adb_path, "shell", "getprop", "gsm.voice.call.state"], 
                              capture_output=True, text=True, timeout=3)
        
        if result.returncode == 0:
            state = result.stdout.strip()
            print(f"📡 GSM通话状态: {state}")
            
            if state == "1":
                print("🔔 GSM显示响铃状态")
                return "RINGING"
            elif state == "2":
                print("📞 GSM显示通话状态")
                return "OFFHOOK"
            elif state == "0":
                print("📱 GSM显示空闲状态")
                return "IDLE"
            else:
                print(f"❓ GSM状态未知: {state}")
                return "UNKNOWN"
        else:
            print(f"❌ 获取GSM属性失败: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ GSM属性测试失败: {e}")
        return None

def test_real_phone_detection():
    """测试真实电话检测功能"""
    print("\n🧪 测试真实电话检测功能...")
    try:
        from agilemind.tool.real_phone_auto_answer import RealPhoneAutoAnswerManager
        
        manager = RealPhoneAutoAnswerManager()
        
        # 测试状态获取
        status = manager.get_status()
        print("📊 当前管理器状态:")
        print(f"  开启状态: {status.get('enabled', False)}")
        print(f"  当前场景: {status.get('current_scenario', 'unknown')}")
        print(f"  监控状态: {status.get('monitoring', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 真实电话检测测试失败: {e}")
        return False

def continuous_monitoring():
    """持续监控来电状态"""
    print("\n🔄 开始持续监控来电状态...")
    print("请现在拨打电话到您的设备，我将监控状态变化")
    print("按 Ctrl+C 停止监控")
    
    last_telephony_state = None
    last_gsm_state = None
    
    try:
        while True:
            # 检查telephony registry
            telephony_state = test_telephony_registry()
            
            # 检查GSM属性
            gsm_state = test_gsm_properties()
            
            # 状态变化检测
            if telephony_state != last_telephony_state:
                print(f"\n🔄 Telephony状态变化: {last_telephony_state} → {telephony_state}")
                last_telephony_state = telephony_state
            
            if gsm_state != last_gsm_state:
                print(f"🔄 GSM状态变化: {last_gsm_state} → {gsm_state}")
                last_gsm_state = gsm_state
            
            # 如果检测到响铃
            if telephony_state == "RINGING" or gsm_state == "RINGING":
                print("🚨 🚨 🚨 检测到来电响铃！ 🚨 🚨 🚨")
                print("这表明来电检测功能正常工作")
                break
            
            time.sleep(0.5)  # 0.5秒检查一次
            
    except KeyboardInterrupt:
        print("\n⏹️ 监控已停止")

def main():
    """主测试函数"""
    print("📞 来电检测功能测试")
    print("=" * 50)
    
    # 测试ADB连接
    if not test_adb_connection():
        print("❌ ADB连接失败，请检查设备连接")
        return
    
    # 测试telephony registry
    telephony_state = test_telephony_registry()
    
    # 测试GSM属性
    gsm_state = test_gsm_properties()
    
    # 测试真实电话检测功能
    real_phone_ok = test_real_phone_detection()
    
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print(f"  ADB连接: ✅")
    print(f"  Telephony Registry: {'✅' if telephony_state else '❌'} ({telephony_state})")
    print(f"  GSM属性: {'✅' if gsm_state else '❌'} ({gsm_state})")
    print(f"  真实电话检测: {'✅' if real_phone_ok else '❌'}")
    
    if telephony_state and gsm_state and real_phone_ok:
        print("\n✅ 所有检测功能正常，准备进行实时监控")
        input("\n按回车键开始实时监控来电状态...")
        continuous_monitoring()
    else:
        print("\n❌ 部分功能检测失败，请检查配置")

if __name__ == "__main__":
    main()

