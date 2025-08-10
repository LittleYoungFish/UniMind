#!/usr/bin/env python3
"""调试通话检测逻辑"""

import subprocess
from datetime import datetime

class CallDebugger:
    def __init__(self):
        self.adb_path = "./platform-tools/adb.exe"
    
    def debug_telecom_output(self):
        """调试telecom输出"""
        print("🔍 调试 dumpsys telecom 输出...")
        
        try:
            result = subprocess.run([
                self.adb_path, "shell", "dumpsys", "telecom"
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode != 0:
                print("❌ 命令执行失败")
                return
            
            output = result.stdout
            
            # 1. 查看所有状态事件
            print("\n📊 所有状态事件:")
            print("=" * 50)
            self._show_all_state_events(output)
            
            # 2. 测试我的解析函数
            print("\n🧪 测试状态解析:")
            print("=" * 50)
            current_state = self._find_current_call_state(output)
            print(f"检测到的当前状态: {current_state}")
            
            # 3. 查看最新通话记录
            print("\n📱 最新通话记录:")
            print("=" * 50)
            latest_call = self._parse_latest_call(output)
            if latest_call:
                print(f"找到通话: {latest_call}")
            else:
                print("未找到活动通话")
                
        except Exception as e:
            print(f"❌ 调试失败: {e}")
    
    def _show_all_state_events(self, output):
        """显示所有状态事件"""
        lines = output.split('\n')
        state_events = []
        
        for line in lines:
            if ' - SET_' in line:
                try:
                    time_part = line.split(' - SET_')[0].strip()
                    if ':' in time_part:
                        if 'SET_RINGING' in line and 'successful incoming call' in line:
                            state_events.append((time_part, "RINGING", line.strip()))
                        elif 'SET_ANSWERED' in line and 'answered' in line:
                            state_events.append((time_part, "ANSWERED", line.strip()))
                        elif 'SET_ACTIVE' in line and 'active set explicitly' in line:
                            state_events.append((time_part, "ACTIVE", line.strip()))
                        elif 'SET_DISCONNECTED' in line:
                            state_events.append((time_part, "DISCONNECTED", line.strip()))
                except:
                    continue
        
        # 显示最近10个事件
        state_events.sort(key=lambda x: x[0])
        recent_events = state_events[-10:] if len(state_events) > 10 else state_events
        
        for i, (time, state, full_line) in enumerate(recent_events):
            print(f"{i+1:2}. {time} - {state}")
            print(f"    {full_line[:100]}...")
            print()
    
    def _find_current_call_state(self, output):
        """从输出中查找当前通话状态"""
        try:
            lines = output.split('\n')
            state_events = []
            
            for line in lines:
                line = line.strip()
                
                if ' - SET_' in line:
                    try:
                        time_part = line.split(' - SET_')[0].strip()
                        if ':' in time_part:
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
            
            print(f"找到 {len(state_events)} 个状态事件")
            
            if state_events:
                state_events.sort(key=lambda x: x[0])
                print("排序后的事件:")
                for time, state in state_events[-5:]:  # 显示最后5个
                    print(f"  {time} - {state}")
                
                latest_state = state_events[-1][1]
                print(f"最新状态: {latest_state}")
                
                if latest_state == "DISCONNECTED":
                    return "IDLE"
                
                return latest_state
            
            return "IDLE"
            
        except Exception as e:
            print(f"解析状态失败: {e}")
            return "IDLE"
    
    def _parse_latest_call(self, output):
        """解析最新通话"""
        try:
            lines = output.split('\n')
            
            # 查找最近的通话记录
            for i, line in enumerate(lines):
                if 'Call TC@' in line and '[' in line and 'User=' in line:
                    call_info = self._parse_call_details(lines[i:i+100])
                    if call_info:
                        print(f"找到通话记录: {call_info.get('phone_number', 'Unknown')} - {call_info.get('call_state', 'Unknown')}")
                        if self._is_active_call(call_info):
                            return call_info
                            
        except Exception as e:
            print(f"解析通话失败: {e}")
        
        return None
    
    def _parse_call_details(self, lines):
        """解析通话详情"""
        call_info = {
            "call_state": "UNKNOWN",
            "state_name": "未知",
            "phone_number": "未知", 
            "direction": "UNKNOWN"
        }
        
        latest_event_time = None
        latest_state = None
        
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
            
            # 解析通话状态 - 找最新的状态
            if ' - SET_' in line:
                try:
                    time_part = line.split(' - SET_')[0].strip()
                    if ':' in time_part:
                        if latest_event_time is None or time_part > latest_event_time:
                            if '- SET_RINGING' in line:
                                latest_event_time = time_part
                                latest_state = "RINGING"
                            elif '- SET_ACTIVE' in line:
                                latest_event_time = time_part
                                latest_state = "ACTIVE"
                            elif '- SET_ANSWERED' in line:
                                latest_event_time = time_part
                                latest_state = "ANSWERED"
                            elif '- SET_DISCONNECTED' in line:
                                latest_event_time = time_part
                                latest_state = "DISCONNECTED"
                except:
                    pass
        
        # 设置最新状态
        if latest_state:
            call_info["call_state"] = latest_state
            state_names = {
                "RINGING": "响铃中",
                "ACTIVE": "通话中", 
                "ANSWERED": "已接听",
                "DISCONNECTED": "已挂断"
            }
            call_info["state_name"] = state_names.get(latest_state, "未知")
        
        return call_info
    
    def _is_active_call(self, call_info):
        """判断是否是活动通话"""
        active_states = ["RINGING", "ACTIVE", "ANSWERED"]
        return call_info["call_state"] in active_states

def main():
    debugger = CallDebugger()
    debugger.debug_telecom_output()

if __name__ == "__main__":
    main()
