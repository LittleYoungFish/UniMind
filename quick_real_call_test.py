#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实来电检测快速测试脚本
Quick Real Call Detection Test Script
"""

import subprocess
import time
import os
import json
from datetime import datetime
import threading

class QuickCallDetector:
    """快速来电检测器"""
    
    def __init__(self):
        self.adb_path = "./platform-tools/adb.exe"
        self.monitoring = False
        self.last_call_state = "IDLE"  # 统一使用字符串状态
        self.detected_calls = []
        self.last_checked_time = None  # 上次检查的最新事件时间
        self.processed_events = set()  # 已处理的事件集合
        
    def check_adb_connection(self):
        """检查ADB连接"""
        try:
            result = subprocess.run([self.adb_path, "devices"], 
                                  capture_output=True, text=True, timeout=5)
            
            devices = []
            for line in result.stdout.strip().split('\n')[1:]:
                if 'device' in line and 'offline' not in line:
                    device_id = line.split('\t')[0]
                    devices.append(device_id)
            
            if devices:
                print(f"✅ 检测到 {len(devices)} 个设备连接:")
                for device in devices:
                    print(f"   📱 {device}")
                return True
            else:
                print("❌ 未检测到设备连接")
                print("请确保:")
                print("1. 设备已通过USB连接")
                print("2. 已开启开发者选项和USB调试")
                print("3. 已允许计算机调试授权")
                return False
                
        except FileNotFoundError:
            print("❌ 未找到ADB工具")
            print("请确保platform-tools目录存在且包含adb.exe")
            return False
        except Exception as e:
            print(f"❌ 设备检查失败: {e}")
            return False
    
    def get_phone_state(self):
        """获取电话状态 - 改为检测新的状态变化事件"""
        try:
            result = subprocess.run([
                self.adb_path, "shell", "dumpsys", "telecom"
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode != 0:
                return None, "命令执行失败"
            
            output = result.stdout
            
            # 检查是否有新的状态变化事件
            new_events = self._get_new_state_events(output)
            
            if new_events:
                # 处理最新的事件
                latest_event = new_events[-1]
                return self._create_state_info_from_event(latest_event, output), None
            
            # 如果没有新事件，返回当前状态
            current_state = self._find_current_call_state(output)
            
            return {
                "call_state": current_state,
                "state_name": {"RINGING": "响铃中", "ACTIVE": "通话中", "ANSWERED": "已接听", "IDLE": "空闲"}.get(current_state, "未知"),
                "phone_number": self._extract_phone_number(output) or "无",
                "direction": self._extract_call_direction(output) or "NONE",
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }, None
            
        except subprocess.TimeoutExpired:
            return None, "命令执行超时"
        except Exception as e:
            return None, f"获取状态失败: {e}"
    
    def _parse_latest_call(self, output):
        """解析最新的通话信息"""
        try:
            lines = output.split('\n')
            
            # 先查找 mCurrentCalls 中的活动通话
            in_current_calls = False
            current_call = None
            
            for i, line in enumerate(lines):
                if 'mCurrentCalls:' in line:
                    in_current_calls = True
                    continue
                
                if in_current_calls:
                    # 如果遇到空行或其他section，停止解析
                    if line.strip() == '' or (line.startswith(' ') and 'Call TC@' in line):
                        # 找到当前活动通话
                        call_info = self._parse_call_details(lines[i:i+100])
                        if call_info and self._is_active_call(call_info):
                            return call_info
                    elif not line.startswith(' '):
                        in_current_calls = False
                        
            # 如果没有找到活动通话，查找最近的通话记录
            recent_calls = []
            for i, line in enumerate(lines):
                if 'Call TC@' in line and '[' in line and 'User=' in line:
                    call_info = self._parse_call_details(lines[i:i+100])
                    if call_info:
                        recent_calls.append((i, call_info))
            
            # 返回最新的通话记录（如果是活动状态）
            if recent_calls:
                # 按行号排序，取最后一个
                recent_calls.sort(key=lambda x: x[0], reverse=True)
                for _, call_info in recent_calls:
                    if self._is_active_call(call_info):
                        return call_info
                        
        except Exception as e:
            print(f"解析通话信息失败: {e}")
        
        return None
    
    def _parse_call_details(self, lines):
        """解析通话详情"""
        call_info = {
            "call_state": "UNKNOWN",
            "state_name": "未知",
            "phone_number": "未知",
            "direction": "UNKNOWN",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        
        for line in lines:
            line = line.strip()
            
            # 解析方向
            if 'direction:' in line:
                if 'INCOMING' in line:
                    call_info["direction"] = "INCOMING"
                elif 'OUTGOING' in line:
                    call_info["direction"] = "OUTGOING"
            
            # 解析电话号码
            if 'To address:' in line and 'tel:' in line:
                try:
                    phone_part = line.split('tel:')[1].split()[0]
                    call_info["phone_number"] = phone_part
                except:
                    pass
            
            # 解析通话状态 - 收集所有状态变化
            if '- SET_RINGING' in line:
                call_info["call_state"] = "RINGING"
                call_info["state_name"] = "响铃中"
                call_info["last_event_time"] = self._extract_time_from_line(line)
            elif '- SET_ACTIVE' in line:
                call_info["call_state"] = "ACTIVE" 
                call_info["state_name"] = "通话中"
                call_info["last_event_time"] = self._extract_time_from_line(line)
            elif '- SET_ANSWERED' in line:
                call_info["call_state"] = "ANSWERED"
                call_info["state_name"] = "已接听"
                call_info["last_event_time"] = self._extract_time_from_line(line)
            elif '- SET_DISCONNECTED' in line:
                call_info["call_state"] = "DISCONNECTED"
                call_info["state_name"] = "已挂断"
                call_info["last_event_time"] = self._extract_time_from_line(line)
                
                # 解析挂断原因
                if 'MISSED' in line:
                    call_info["state_name"] = "未接来电"
                elif 'REJECTED' in line:
                    call_info["state_name"] = "已拒绝"
                elif 'REMOTE' in line:
                    call_info["state_name"] = "对方挂断"
                elif 'LOCAL' in line:
                    call_info["state_name"] = "本地挂断"
        
        return call_info
    
    def _is_active_call(self, call_info):
        """判断是否是活动通话"""
        # 活动通话的状态：正在响铃、已接听或通话中（排除已挂断状态）
        active_states = ["RINGING", "ACTIVE", "ANSWERED"]
        return call_info["call_state"] in active_states
    
    def _find_current_call_state(self, output):
        """从输出中查找当前通话状态的更直接方法"""
        try:
            lines = output.split('\n')
            
            # 收集所有状态变化事件，并按时间排序
            state_events = []
            
            for line in lines:
                line = line.strip()
                
                # 提取时间戳和状态事件
                if ' - SET_' in line:
                    try:
                        # 提取时间戳 (格式: HH:MM:SS.mmm)
                        time_part = line.split(' - SET_')[0].strip()
                        if ':' in time_part:
                            # 解析状态类型
                            if 'SET_RINGING' in line and 'successful incoming call' in line:
                                state_events.append((time_part, "RINGING"))
                            elif 'SET_ANSWERED' in line and 'answered' in line:
                                state_events.append((time_part, "ANSWERED"))
                            elif 'SET_ACTIVE' in line and 'active set explicitly' in line:
                                state_events.append((time_part, "ACTIVE"))
                            elif 'SET_DISCONNECTED' in line:
                                state_events.append((time_part, "DISCONNECTED"))
                    except:
                        continue
            
            # 如果找到状态事件，返回最新的状态
            if state_events:
                # 按时间戳排序，取最后一个（最新的）
                state_events.sort(key=lambda x: x[0])
                latest_state = state_events[-1][1]
                
                # 如果最新状态是已挂断，返回空闲
                if latest_state == "DISCONNECTED":
                    return "IDLE"
                
                return latest_state
            
            return "IDLE"
            
        except Exception as e:
            print(f"查找通话状态失败: {e}")
            return "IDLE"
    
    def _extract_phone_number(self, output):
        """从输出中提取电话号码"""
        try:
            lines = output.split('\n')
            for line in lines:
                if 'To address:' in line and 'tel:' in line:
                    phone_part = line.split('tel:')[1].split()[0]
                    return phone_part
        except:
            pass
        return None
    
    def _extract_call_direction(self, output):
        """从输出中提取通话方向"""
        try:
            lines = output.split('\n')
            for line in lines:
                if 'direction:' in line:
                    if 'INCOMING' in line:
                        return "INCOMING"
                    elif 'OUTGOING' in line:
                        return "OUTGOING"
        except:
            pass
        return None
    
    def _extract_time_from_line(self, line):
        """从状态事件行中提取时间戳"""
        try:
            # 格式: "HH:MM:SS.mmm - SET_XXX"
            time_part = line.split(' - SET_')[0].strip()
            return time_part
        except:
            return None
    
    def _get_new_state_events(self, output):
        """获取新的状态变化事件"""
        try:
            lines = output.split('\n')
            all_events = []
            
            for line in lines:
                if ' - SET_' in line:
                    try:
                        time_part = line.split(' - SET_')[0].strip()
                        if ':' in time_part:
                            event_id = f"{time_part}:{line.strip()}"
                            
                            # 检查是否是新事件
                            if event_id not in self.processed_events:
                                event_info = {
                                    "time": time_part,
                                    "line": line.strip(),
                                    "id": event_id
                                }
                                
                                # 解析事件类型
                                if 'SET_RINGING' in line and 'successful incoming call' in line:
                                    event_info["state"] = "RINGING"
                                    event_info["description"] = "来电响铃"
                                elif 'SET_ANSWERED' in line and 'answered' in line:
                                    event_info["state"] = "ANSWERED"
                                    event_info["description"] = "用户接听"
                                elif 'SET_ACTIVE' in line and 'active set explicitly' in line:
                                    event_info["state"] = "ACTIVE"
                                    event_info["description"] = "通话激活"
                                elif 'SET_DISCONNECTED' in line:
                                    event_info["state"] = "DISCONNECTED"
                                    event_info["description"] = "通话结束"
                                else:
                                    continue
                                
                                all_events.append(event_info)
                                self.processed_events.add(event_id)
                    except:
                        continue
            
            # 按时间排序返回新事件
            all_events.sort(key=lambda x: x["time"])
            return all_events
            
        except Exception as e:
            print(f"获取新事件失败: {e}")
            return []
    
    def _create_state_info_from_event(self, event, output):
        """从事件创建状态信息"""
        state = event["state"]
        
        # 如果是挂断事件，返回空闲状态
        if state == "DISCONNECTED":
            state = "IDLE"
        
        phone_number = self._extract_phone_number(output) or "未知"
        direction = self._extract_call_direction(output) or "UNKNOWN"
        
        state_names = {
            "RINGING": "响铃中",
            "ACTIVE": "通话中", 
            "ANSWERED": "已接听",
            "IDLE": "空闲"
        }
        
        return {
            "call_state": state,
            "state_name": state_names.get(state, "未知"),
            "phone_number": phone_number,
            "direction": direction,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "event_time": event["time"],
            "event_description": event["description"]
        }
    
    def detect_call_change(self, current_call_info):
        """检测电话状态变化"""
        current_state = current_call_info["call_state"]
        
        if current_state != self.last_call_state:
            change_info = {
                "from_state": self.last_call_state,
                "to_state": current_state,
                "direction": current_call_info.get("direction", "UNKNOWN"),
                "phone_number": current_call_info.get("phone_number", "未知"),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.last_call_state = current_state
            return change_info
        
        return None
    
    def handle_incoming_call(self, call_info):
        """处理来电事件"""
        print("\n" + "="*50)
        print("🔔 检测到来电!")
        print(f"📞 号码: {call_info['phone_number']}")
        print(f"⏰ 时间: {call_info['timestamp']}")
        print("="*50)
        
        # 记录来电
        self.detected_calls.append({
            "phone_number": call_info['phone_number'],
            "timestamp": call_info['timestamp'],
            "action": "检测到来电"
        })
        
        # 这里可以添加自动接听逻辑
        print("💡 提示: 这里可以添加自动接听和语音回复逻辑")
        
    def handle_call_answered(self, call_info):
        """处理接听事件"""
        print(f"\n📞 电话已接听 - {call_info['timestamp']}")
        
        # 这里可以添加语音播放逻辑
        print("💡 提示: 这里可以播放智能语音回复")
        
    def handle_call_ended(self, call_info):
        """处理挂断事件"""
        print(f"\n📴 通话结束 - {call_info['timestamp']}")
    
    def start_monitoring(self):
        """开始监听电话状态"""
        if not self.check_adb_connection():
            return
        
        print("\n📞 开始监听电话状态...")
        print("💡 请用另一部手机拨打测试设备号码")
        print("🔄 监听中... (按 Ctrl+C 停止)")
        print("-" * 50)
        
        self.monitoring = True
        
        try:
            while self.monitoring:
                phone_state, error = self.get_phone_state()
                
                if error:
                    print(f"❌ 状态获取错误: {error}")
                    time.sleep(2)
                    continue
                
                # 检测状态变化
                change = self.detect_call_change(phone_state)
                
                if change:
                    print(f"\n🔄 状态变化: {change['from_state']} → {change['to_state']} ({change['timestamp']})")
                    
                    # 显示事件详情
                    if 'event_description' in phone_state:
                        print(f"📋 事件: {phone_state['event_description']} ({phone_state.get('event_time', 'unknown')})")
                    
                    if change.get('direction') == 'INCOMING':
                        print(f"📞 来电: {change['phone_number']}")
                    elif change.get('direction') == 'OUTGOING':
                        print(f"📱 去电: {change['phone_number']}")
                    
                    # 处理不同的状态变化
                    if change['to_state'] == "RINGING" and change.get('direction') == 'INCOMING':
                        self.handle_incoming_call(phone_state)
                    elif change['to_state'] in ["ACTIVE", "ANSWERED"]:
                        self.handle_call_answered(phone_state)
                    elif change['to_state'] in ["DISCONNECTED", "IDLE"]:
                        self.handle_call_ended(phone_state)
                
                # 显示当前状态
                status_info = f"{phone_state['state_name']}"
                if phone_state['phone_number'] != "无" and phone_state['phone_number'] != "未知":
                    status_info += f" - {phone_state['phone_number']}"
                print(f"\r⏰ {phone_state['timestamp']} | {status_info} | {phone_state['direction']}", end="", flush=True)
                
                time.sleep(0.5)  # 每0.5秒检查一次
                
        except KeyboardInterrupt:
            print("\n\n🛑 监听已停止")
        except Exception as e:
            print(f"\n❌ 监听异常: {e}")
        finally:
            self.monitoring = False
            self.print_summary()
    
    def print_summary(self):
        """打印检测总结"""
        print("\n" + "="*50)
        print("📊 检测总结")
        print("="*50)
        
        if self.detected_calls:
            print(f"📞 检测到 {len(self.detected_calls)} 次来电:")
            for i, call in enumerate(self.detected_calls, 1):
                print(f"   {i}. {call['timestamp']} - {call['phone_number']}")
        else:
            print("📞 未检测到来电")
        
        print("\n💡 后续可以实现的功能:")
        print("   ✅ 自动接听按钮点击")
        print("   ✅ 智能语音回复播放")
        print("   ✅ 场景模式自动切换")
        print("   ✅ 通话记录智能管理")
    
    def test_ui_detection(self):
        """测试UI检测功能"""
        print("\n🔍 测试UI检测功能...")
        
        try:
            # 截取屏幕
            result = subprocess.run([
                self.adb_path, "shell", "screencap", "/sdcard/test_screen.png"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # 下载截图
                result = subprocess.run([
                    self.adb_path, "pull", "/sdcard/test_screen.png", "./test_screen.png"
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    print("✅ 屏幕截图成功: test_screen.png")
                    print("💡 可以基于截图进行UI元素识别和自动点击")
                    return True
                else:
                    print("❌ 截图下载失败")
            else:
                print("❌ 屏幕截图失败")
                
        except Exception as e:
            print(f"❌ UI测试异常: {e}")
        
        return False

def main():
    """主函数"""
    print("📞 真实来电检测快速测试")
    print("=" * 50)
    
    detector = QuickCallDetector()
    
    print("\n🔧 测试选项:")
    print("1. 开始电话状态监听 (推荐)")
    print("2. 测试UI截图功能")
    print("3. 检查设备连接状态")
    print("4. 查看使用说明")
    
    try:
        choice = input("\n请选择测试选项 (1-4): ").strip()
        
        if choice == "1":
            detector.start_monitoring()
        elif choice == "2":
            detector.test_ui_detection()
        elif choice == "3":
            detector.check_adb_connection()
        elif choice == "4":
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
    print("3. 已允许计算机调试授权")
    print("4. platform-tools目录包含adb.exe")
    print("\n🔍 测试步骤:")
    print("1. 运行选项1开始监听")
    print("2. 用另一部手机拨打测试设备")
    print("3. 观察是否能检测到来电状态变化")
    print("\n💡 成功检测后可以继续实现:")
    print("- 自动点击接听按钮")
    print("- 播放智能语音回复")
    print("- 自动挂断通话")

if __name__ == "__main__":
    main()
