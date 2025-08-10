"""
APP自动化操作工具集
App Automation Tools

为通用型AI助手提供完整的APP自动化操作能力
"""

import os
import json
import time
import subprocess
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from .tool_decorator import tool
from .phone_auto_answer import phone_manager, ScenarioMode

# 尝试导入可选依赖
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    logging.warning("OpenCV未安装，图像处理功能不可用")

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    logging.warning("Numpy未安装，数值计算功能不可用")

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    logging.warning("PIL未安装，图像处理功能不可用")

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False
    logging.warning("Tesseract未安装，OCR功能不可用")

try:
    import speech_recognition as sr
    import pyttsx3
    HAS_SPEECH = True
except ImportError:
    HAS_SPEECH = False
    logging.warning("语音处理库未安装，语音功能不可用")


class AppAutomationTools:
    """APP自动化操作工具类"""
    
    def __init__(self):
        """初始化工具类"""
        global HAS_SPEECH
        self.logger = logging.getLogger(__name__)
        self.device_id = None
        self.screenshot_dir = "screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        # 初始化ADB路径
        try:
            self.adb_path = self._find_adb_path()
            self.logger.info(f"ADB路径已找到: {self.adb_path}")
        except FileNotFoundError as e:
            self.logger.error(f"ADB初始化失败: {str(e)}")
            raise
        
        # 初始化语音引擎（如果可用）
        if HAS_SPEECH:
            try:
                self.tts_engine = pyttsx3.init()
                self.speech_recognizer = sr.Recognizer()
            except:
                self.tts_engine = None
                self.speech_recognizer = None
                HAS_SPEECH = False
    
    def _find_adb_path(self) -> str:
        """查找ADB工具路径"""
        import os
        
        # 首先检查环境变量中的自定义路径
        custom_adb = os.environ.get('ADB_PATH')
        if custom_adb and os.path.exists(custom_adb):
            try:
                result = subprocess.run(
                    [custom_adb, "version"], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                if result.returncode == 0:
                    return custom_adb
            except:
                pass
        
        adb_paths = [
            "adb",  # 系统PATH中的adb
            "adb.exe",  # Windows系统PATH中
            # Windows常用路径
            r"C:\Users\%USERNAME%\AppData\Local\Android\Sdk\platform-tools\adb.exe",
            r"C:\Program Files\Android\Android Studio\Sdk\platform-tools\adb.exe", 
            r"C:\Program Files (x86)\Android\android-sdk\platform-tools\adb.exe",
            r"C:\Android\Sdk\platform-tools\adb.exe",
            r"C:\tools\android-platform-tools\adb.exe",  # Scoop安装路径
            r"C:\ProgramData\chocolatey\lib\adb\tools\adb.exe",  # Chocolatey安装路径
            # 用户目录
            os.path.expanduser("~/AppData/Local/Android/Sdk/platform-tools/adb.exe"),
            os.path.expanduser("~/scoop/apps/adb/current/adb.exe"),  # Scoop用户安装
            # macOS路径
            os.path.expanduser("~/Library/Android/sdk/platform-tools/adb"),
            "/usr/local/bin/adb",
            # Linux路径
            "/usr/bin/adb",
            "/opt/android-sdk/platform-tools/adb",
            # 当前目录下的相对路径
            "./platform-tools/adb.exe",
            "./adb.exe"
        ]
        
        for path in adb_paths:
            try:
                expanded_path = os.path.expandvars(path)
                if os.path.exists(expanded_path):
                    result = subprocess.run(
                        [expanded_path, "version"], 
                        capture_output=True, 
                        text=True, 
                        timeout=5
                    )
                    if result.returncode == 0:
                        self.logger.info(f"找到ADB工具: {expanded_path}")
                        return expanded_path
            except Exception as e:
                self.logger.debug(f"尝试路径 {path} 失败: {e}")
                continue
        
        # 如果都找不到，提供详细的错误信息和解决方案
        error_msg = """
未找到ADB工具！请选择以下解决方案之一：

1. 下载Android Platform Tools:
   - 访问: https://developer.android.com/studio/releases/platform-tools
   - 下载并解压到任意目录
   - 设置环境变量 ADB_PATH 指向 adb.exe 文件
   
2. 通过包管理器安装:
   - Scoop: scoop install adb
   - Chocolatey: choco install adb
   
3. 手动设置环境变量:
   - 设置 ADB_PATH 环境变量指向您的 adb.exe 文件路径
   
4. 将adb.exe放到项目目录下

当前搜索的路径包括: {}
""".format('\n  '.join([f"- {path}" for path in adb_paths[:10]]))
        
        raise FileNotFoundError(error_msg)

    @tool
    def get_installed_apps(self, device_id: str = None) -> Dict[str, Any]:
        """
        获取设备上已安装的应用列表
        
        Args:
            device_id: 设备ID，如果为None则使用默认设备
            
        Returns:
            包含已安装应用信息的字典
        """
        try:
            adb_cmd = self.adb_path
            device_args = ["-s", device_id] if device_id else []
            
            result = subprocess.run(
                [adb_cmd] + device_args + ["shell", "pm", "list", "packages", "-3"],
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "message": f"获取应用列表失败: {result.stderr}",
                    "apps": []
                }
            
            # 解析包名列表
            packages = []
            for line in result.stdout.strip().split('\n'):
                if line.startswith('package:'):
                    package_name = line.replace('package:', '')
                    packages.append(package_name)
            
            return {
                "success": True,
                "message": f"成功获取 {len(packages)} 个已安装应用",
                "apps": packages,
                "device_id": device_id or "default"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"获取应用列表异常: {str(e)}",
                "apps": []
            }
    
    @tool
    def check_app_status(self, package_name: str, device_id: str = None) -> Dict[str, Any]:
        """
        检查指定应用的状态
        
        Args:
            package_name: 应用包名
            device_id: 设备ID
            
        Returns:
            应用状态信息
        """
        try:
            adb_cmd = self.adb_path
            device_args = ["-s", device_id] if device_id else []
            
            # 检查应用是否安装
            check_result = subprocess.run(
                [adb_cmd] + device_args + ["shell", "pm", "list", "packages", package_name],
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if package_name not in check_result.stdout:
                return {
                    "success": False,
                    "message": f"应用 {package_name} 未安装",
                    "status": "not_installed"
                }
            
            # 检查应用是否正在运行
            running_result = subprocess.run(
                [adb_cmd] + device_args + ["shell", "ps", "|", "grep", package_name],
                shell=True,
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            is_running = package_name in running_result.stdout
            
            return {
                "success": True,
                "message": f"应用状态检查完成",
                "status": "running" if is_running else "stopped",
                "package_name": package_name,
                "is_installed": True,
                "is_running": is_running
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"检查应用状态异常: {str(e)}",
                "status": "unknown"
            }
    
    @tool
    def launch_app(self, package_name: str, activity: str = None, device_id: str = None) -> Dict[str, Any]:
        """
        启动指定应用
        
        Args:
            package_name: 应用包名
            activity: 指定的Activity，可选
            device_id: 设备ID
            
        Returns:
            启动结果
        """
        try:
            device_param = f"-s {device_id}" if device_id else ""
            
            # 使用找到的ADB路径
            adb_path = self.adb_path
            if activity:
                # 启动指定Activity
                cmd = f'"{adb_path}" {device_param} shell am start -n {package_name}/{activity}'
            else:
                # 启动主Activity
                cmd = f'"{adb_path}" {device_param} shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1'
            
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=15
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "message": f"启动应用失败: {result.stderr}",
                    "package_name": package_name
                }
            
            # 等待应用启动
            time.sleep(3)
            
            # 验证应用是否成功启动
            status = self.check_app_status(package_name, device_id)
            
            return {
                "success": True,
                "message": f"应用 {package_name} 启动成功",
                "package_name": package_name,
                "launch_time": time.time(),
                "status": status
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"启动应用异常: {str(e)}",
                "package_name": package_name
            }
    
    @tool
    def get_screen_content(self, device_id: str = None, include_ocr: bool = True) -> Dict[str, Any]:
        """
        获取当前屏幕内容
        
        Args:
            device_id: 设备ID
            include_ocr: 是否包含OCR文字识别
            
        Returns:
            屏幕内容信息
        """
        try:
            timestamp = int(time.time())
            screenshot_path = os.path.join(self.screenshot_dir, f"screen_{timestamp}.png")
            
            # 使用列表参数执行截屏命令
            adb_path = self.adb_path
            cmd_args = [adb_path]
            
            if device_id:
                cmd_args.extend(["-s", device_id])
            
            cmd_args.extend(["exec-out", "screencap", "-p"])
            
            # 执行截屏命令并将输出写入文件
            try:
                with open(screenshot_path, 'wb') as f:
                    result = subprocess.run(cmd_args, stdout=f, timeout=15, stderr=subprocess.PIPE)
                
                if result.returncode != 0:
                    return {
                        "success": False,
                        "message": f"截屏失败: {result.stderr.decode()}",
                        "content": {}
                    }
                
                # 检查文件是否成功创建
                if not os.path.exists(screenshot_path) or os.path.getsize(screenshot_path) == 0:
                    return {
                        "success": False,
                        "message": "截屏文件创建失败或为空",
                        "content": {}
                    }
                
            except Exception as e:
                return {
                    "success": False,
                    "message": f"截屏命令执行失败: {str(e)}",
                    "content": {}
                }
            
            screen_info = {
                "screenshot_path": screenshot_path,
                "timestamp": timestamp,
                "device_id": device_id or "default",
                "file_size": os.path.getsize(screenshot_path)
            }
            
            # 如果需要OCR识别且依赖可用
            if include_ocr and HAS_TESSERACT and HAS_PIL:
                try:
                    image = Image.open(screenshot_path)
                    # 使用pytesseract进行OCR
                    ocr_text = pytesseract.image_to_string(image, lang='chi_sim+eng')
                    screen_info["ocr_text"] = ocr_text
                    screen_info["has_ocr"] = True
                except Exception as e:
                    screen_info["ocr_error"] = str(e)
                    screen_info["has_ocr"] = False
            else:
                screen_info["has_ocr"] = False
                screen_info["ocr_note"] = "OCR功能不可用，缺少必要依赖"
            
            return {
                "success": True,
                "message": "屏幕内容获取成功",
                "content": screen_info
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"获取屏幕内容异常: {str(e)}",
                "content": {}
            }
    
    def _ensure_screen_awake(self, device_id: str = None) -> bool:
        """确保屏幕已唤醒并解锁"""
        try:
            adb_path = self.adb_path
            cmd_args = [adb_path]
            
            if device_id:
                cmd_args.extend(["-s", device_id])
            
            # 1. 唤醒屏幕
            wake_cmd = cmd_args + ["shell", "input", "keyevent", "KEYCODE_WAKEUP"]
            subprocess.run(wake_cmd, timeout=5, capture_output=True)
            
            # 2. 滑动解锁（简单滑动，适用于无密码锁屏）
            unlock_cmd = cmd_args + ["shell", "input", "swipe", "500", "1500", "500", "500", "500"]
            subprocess.run(unlock_cmd, timeout=5, capture_output=True)
            
            # 3. 按Home键确保回到桌面
            home_cmd = cmd_args + ["shell", "input", "keyevent", "KEYCODE_HOME"]
            subprocess.run(home_cmd, timeout=5, capture_output=True)
            
            time.sleep(1)  # 等待界面稳定
            return True
            
        except Exception as e:
            self.logger.warning(f"屏幕唤醒失败: {e}")
            return False

    @tool
    def find_elements(self, text: str = None, description: str = None, device_id: str = None) -> Dict[str, Any]:
        """
        在屏幕上查找UI元素
        
        Args:
            text: 要查找的文本内容
            description: 元素描述
            device_id: 设备ID
            
        Returns:
            查找结果
        """
        def _get_ui_elements(retry_count: int = 0) -> Dict[str, Any]:
            """内部函数：获取UI元素，支持重试"""
            try:
                # 使用列表参数执行ADB命令
                adb_path = self.adb_path
                
                # 构建命令参数
                dump_cmd = [adb_path]
                if device_id:
                    dump_cmd.extend(["-s", device_id])
                dump_cmd.extend(["shell", "uiautomator", "dump", "/sdcard/ui_dump.xml"])
                
                # 执行UI dump命令
                result = subprocess.run(dump_cmd, timeout=15, capture_output=True, text=True)
                if result.returncode != 0:
                    return {
                        "success": False,
                        "message": f"UI dump失败: {result.stderr}",
                        "elements": []
                    }
                
                # 拉取UI结构文件
                pull_cmd = [adb_path]
                if device_id:
                    pull_cmd.extend(["-s", device_id])
                pull_cmd.extend(["pull", "/sdcard/ui_dump.xml", "."])
                
                result = subprocess.run(pull_cmd, timeout=10, capture_output=True, text=True)
                if result.returncode != 0:
                    return {
                        "success": False,
                        "message": f"UI文件拉取失败: {result.stderr}",
                        "elements": []
                    }
                
                # 解析UI结构（检查多个可能的文件名）
                found_elements = []
                ui_file = None
                
                # 检查可能的文件名（处理扩展名截断问题）
                for filename in ["ui_dump.xml", "ui_dump.xm"]:
                    if os.path.exists(filename):
                        ui_file = filename
                        break
                
                if ui_file:
                    try:
                        with open(ui_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                            # 解析所有有用的UI元素
                            import re
                            import xml.etree.ElementTree as ET
                            
                            try:
                                root = ET.fromstring(content)
                                all_nodes = root.findall('.//node')
                                
                                for node in all_nodes:
                                    node_text = node.get('text', '').strip()
                                    content_desc = node.get('content-desc', '').strip()
                                    bounds = node.get('bounds', '')
                                    clickable = node.get('clickable', 'false')
                                    
                                    # 只处理有效的UI元素
                                    if bounds and bounds != '[0,0][0,0]':
                                        # 解析坐标
                                        coord_match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
                                        if coord_match:
                                            x1, y1, x2, y2 = map(int, coord_match.groups())
                                            
                                            # 有文本、描述或可点击的元素
                                            if node_text or content_desc or clickable == 'true':
                                                display_text = node_text or content_desc or f"可点击元素[{x1},{y1}]"
                                                found_elements.append({
                                                    "text": display_text,
                                                    "bounds": bounds,
                                                    "center_x": int((x1 + x2) / 2),
                                                    "center_y": int((y1 + y2) / 2),
                                                    "clickable": clickable == 'true',
                                                    "raw_text": node_text,
                                                    "content_desc": content_desc
                                                })
                                
                            except ET.ParseError:
                                # 如果XML解析失败，使用正则表达式
                                node_pattern = r'<node[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"[^>]*/?>'
                                matches = re.findall(node_pattern, content)
                                for match in matches:
                                    x1, y1, x2, y2 = map(int, match)
                                    if (x1, y1, x2, y2) != (0, 0, 0, 0):
                                        found_elements.append({
                                            "text": f"UI元素[{x1},{y1}]",
                                            "bounds": f"[{x1},{y1}][{x2},{y2}]",
                                            "center_x": int((x1 + x2) / 2),
                                            "center_y": int((y1 + y2) / 2),
                                            "clickable": True
                                        })
                            
                            # 如果指定了搜索文本，进行筛选
                            if text:
                                filtered_elements = []
                                for elem in found_elements:
                                    if (text.lower() in elem["text"].lower() or 
                                        text.lower() in elem.get("raw_text", "").lower() or
                                        text.lower() in elem.get("content_desc", "").lower()):
                                        filtered_elements.append(elem)
                                found_elements = filtered_elements
                            
                    except Exception as e:
                        self.logger.error(f"解析UI文件失败: {e}")
                        
                    # 清理临时文件
                    try:
                        os.remove(ui_file)
                    except:
                        pass
                        
                    # 如果没找到元素且是第一次尝试，可能需要唤醒屏幕
                    if len(found_elements) <= 1 and retry_count == 0:
                        self.logger.info("UI元素较少，可能屏幕锁定，尝试唤醒屏幕...")
                        if self._ensure_screen_awake(device_id):
                            time.sleep(2)  # 等待界面稳定
                            return _get_ui_elements(retry_count + 1)  # 重试
                else:
                    self.logger.warning("未找到UI dump文件")
                
                return {
                    "success": True,
                    "message": f"元素查找完成，找到 {len(found_elements)} 个匹配项",
                    "elements": found_elements,
                    "search_criteria": {
                        "text": text,
                        "description": description
                    }
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "message": f"UI元素获取失败: {str(e)}",
                    "elements": []
                }
        
        # 执行UI元素获取
        try:
            return _get_ui_elements()
        except Exception as e:
            return {
                "success": False,
                "message": f"查找元素异常: {str(e)}",
                "elements": []
            }
    
    @tool
    def tap_element(self, x: int, y: int, device_id: str = None) -> Dict[str, Any]:
        """
        点击屏幕指定位置
        
        Args:
            x: X坐标
            y: Y坐标
            device_id: 设备ID
            
        Returns:
            点击结果
        """
        try:
            # 使用找到的ADB路径和列表参数（避免shell问题）
            adb_path = self.adb_path
            cmd_args = [adb_path]
            
            if device_id:
                cmd_args.extend(["-s", device_id])
            
            cmd_args.extend(["shell", "input", "tap", str(x), str(y)])
            
            self.logger.info(f"执行点击命令: {' '.join(cmd_args)}")
            result = subprocess.run(cmd_args, timeout=10, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"ADB命令失败: {result.stderr}")
                return {
                    "success": False,
                    "message": f"点击操作失败: {result.stderr}",
                    "coordinates": (x, y)
                }
            
            # 等待操作响应
            time.sleep(0.5)
            
            self.logger.info(f"成功执行点击操作 ({x}, {y})")
            return {
                "success": True,
                "message": f"成功点击坐标 ({x}, {y})",
                "coordinates": (x, y),
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"点击操作异常: {str(e)}")
            return {
                "success": False,
                "message": f"点击操作异常: {str(e)}",
                "coordinates": (x, y)
            }
    
    @tool
    def input_text(self, text: str, device_id: str = None) -> Dict[str, Any]:
        """
        输入文本
        
        Args:
            text: 要输入的文本
            device_id: 设备ID
            
        Returns:
            输入结果
        """
        try:
            device_param = f"-s {device_id}" if device_id else ""
            
            # 转义特殊字符
            escaped_text = text.replace(' ', '%s').replace('&', '\\&')
            adb_path = self.adb_path
            cmd = f'"{adb_path}" {device_param} shell input text "{escaped_text}"'
            
            result = subprocess.run(cmd, shell=True, timeout=10)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "message": "文本输入失败",
                    "text": text
                }
            
            return {
                "success": True,
                "message": f"成功输入文本: {text}",
                "text": text,
                "length": len(text),
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"文本输入异常: {str(e)}",
                "text": text
            }
    
    @tool
    def swipe_gesture(self, start_x: int, start_y: int, end_x: int, end_y: int, 
                     duration: int = 500, device_id: str = None) -> Dict[str, Any]:
        """
        执行滑动手势
        
        Args:
            start_x: 起始X坐标
            start_y: 起始Y坐标  
            end_x: 结束X坐标
            end_y: 结束Y坐标
            duration: 滑动持续时间（毫秒）
            device_id: 设备ID
            
        Returns:
            滑动结果
        """
        try:
            device_param = f"-s {device_id}" if device_id else ""
            adb_path = self.adb_path
            cmd = f'"{adb_path}" {device_param} shell input swipe {start_x} {start_y} {end_x} {end_y} {duration}'
            
            result = subprocess.run(cmd, shell=True, timeout=10)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "message": "滑动操作失败",
                    "gesture": {
                        "start": (start_x, start_y),
                        "end": (end_x, end_y),
                        "duration": duration
                    }
                }
            
            # 等待滑动完成
            time.sleep(duration / 1000 + 0.5)
            
            return {
                "success": True,
                "message": f"成功执行滑动操作",
                "gesture": {
                    "start": (start_x, start_y),
                    "end": (end_x, end_y),
                    "duration": duration
                },
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"滑动操作异常: {str(e)}",
                "gesture": {
                    "start": (start_x, start_y),
                    "end": (end_x, end_y)
                }
            }
    
    @tool
    def press_key(self, key_code: str, device_id: str = None) -> Dict[str, Any]:
        """
        按下物理按键
        
        Args:
            key_code: 按键代码 (如 KEYCODE_BACK, KEYCODE_HOME, KEYCODE_MENU)
            device_id: 设备ID
            
        Returns:
            按键结果
        """
        try:
            device_param = f"-s {device_id}" if device_id else ""
            
            # 常用按键映射
            key_mapping = {
                "back": "4",
                "home": "3", 
                "menu": "82",
                "search": "84",
                "volume_up": "24",
                "volume_down": "25",
                "power": "26"
            }
            
            key_value = key_mapping.get(key_code.lower(), key_code)
            adb_path = self.adb_path
            cmd = f'"{adb_path}" {device_param} shell input keyevent {key_value}'
            
            result = subprocess.run(cmd, shell=True, timeout=5)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "message": f"按键操作失败",
                    "key_code": key_code
                }
            
            return {
                "success": True,
                "message": f"成功按下按键: {key_code}",
                "key_code": key_code,
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"按键操作异常: {str(e)}",
                "key_code": key_code
            }
    
    @tool
    def long_press(self, x: int, y: int, duration: int = 2000, device_id: str = None) -> Dict[str, Any]:
        """
        长按操作
        
        Args:
            x: X坐标
            y: Y坐标
            duration: 长按持续时间（毫秒）
            device_id: 设备ID
            
        Returns:
            长按结果
        """
        try:
            device_param = f"-s {device_id}" if device_id else ""
            adb_path = self.adb_path
            cmd = f'"{adb_path}" {device_param} shell input swipe {x} {y} {x} {y} {duration}'
            
            result = subprocess.run(cmd, shell=True, timeout=15)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "message": "长按操作失败",
                    "coordinates": (x, y),
                    "duration": duration
                }
            
            return {
                "success": True,
                "message": f"成功执行长按操作",
                "coordinates": (x, y),
                "duration": duration,
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"长按操作异常: {str(e)}",
                "coordinates": (x, y)
            }
    
    @tool
    def capture_screenshot(self, filename: str = None, device_id: str = None) -> Dict[str, Any]:
        """
        截取屏幕截图
        
        Args:
            filename: 文件名，如果为None则自动生成
            device_id: 设备ID
            
        Returns:
            截图结果
        """
        try:
            if filename is None:
                timestamp = int(time.time())
                filename = f"screenshot_{timestamp}.png"
            
            screenshot_path = os.path.join(self.screenshot_dir, filename)
            device_param = f"-s {device_id}" if device_id else ""
            
            adb_path = self.adb_path
            cmd = f'"{adb_path}" {device_param} exec-out screencap -p > {screenshot_path}'
            result = subprocess.run(cmd, shell=True, timeout=10)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "message": "截图失败",
                    "filename": filename
                }
            
            # 验证截图文件
            if not os.path.exists(screenshot_path) or os.path.getsize(screenshot_path) == 0:
                return {
                    "success": False,
                    "message": "截图文件无效",
                    "filename": filename
                }
            
            return {
                "success": True,
                "message": "截图成功",
                "filename": filename,
                "path": screenshot_path,
                "size": os.path.getsize(screenshot_path),
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"截图异常: {str(e)}",
                "filename": filename
            }
    
    @tool
    def verify_operation_result(self, expected_result: str, verification_method: str = "screen") -> Dict[str, Any]:
        """
        验证操作结果
        
        Args:
            expected_result: 期望的结果描述
            verification_method: 验证方法 (screen, ocr, element)
            
        Returns:
            验证结果
        """
        try:
            if verification_method == "screen":
                # 通过截图验证
                screen_result = self.capture_screenshot()
                if screen_result["success"]:
                    return {
                        "success": True,
                        "message": "已截图验证，请人工确认结果",
                        "verification_method": verification_method,
                        "screenshot": screen_result["path"],
                        "expected": expected_result
                    }
            
            elif verification_method == "ocr" and HAS_TESSERACT and HAS_PIL:
                # 通过OCR验证
                screen_result = self.get_screen_content(include_ocr=True)
                if screen_result["success"] and "ocr_text" in screen_result["content"]:
                    ocr_text = screen_result["content"]["ocr_text"]
                    is_found = expected_result.lower() in ocr_text.lower()
                    
                    return {
                        "success": True,
                        "message": f"OCR验证{'成功' if is_found else '失败'}",
                        "verification_method": verification_method,
                        "expected": expected_result,
                        "found": is_found,
                        "ocr_text": ocr_text[:200] + "..." if len(ocr_text) > 200 else ocr_text
                    }
            
            return {
                "success": False,
                "message": f"验证方法 {verification_method} 不可用或执行失败",
                "verification_method": verification_method
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"验证操作异常: {str(e)}",
                "verification_method": verification_method
            }
    
    @tool  
    def speech_to_text(self, audio_file: str = None, duration: int = 5) -> Dict[str, Any]:
        """
        语音转文本
        
        Args:
            audio_file: 音频文件路径，如果为None则录制音频
            duration: 录制时长（秒）
            
        Returns:
            语音识别结果
        """
        if not HAS_SPEECH or not self.speech_recognizer:
            return {
                "success": False,
                "message": "语音识别功能不可用，请安装相关依赖",
                "text": ""
            }
        
        try:
            import speech_recognition as sr
            
            if audio_file is None:
                # 录制音频（需要麦克风）
                with sr.Microphone() as source:
                    self.logger.info(f"开始录制音频，时长{duration}秒...")
                    audio = self.speech_recognizer.listen(source, timeout=duration)
            else:
                # 从文件读取音频
                with sr.AudioFile(audio_file) as source:
                    audio = self.speech_recognizer.record(source)
            
            # 语音识别
            text = self.speech_recognizer.recognize_google(audio, language="zh-CN")
            
            return {
                "success": True,
                "message": "语音识别成功",
                "text": text,
                "confidence": 1.0  # Google API不提供置信度
            }
            
        except sr.UnknownValueError:
            return {
                "success": False,
                "message": "无法识别语音内容",
                "text": ""
            }
        except sr.RequestError as e:
            return {
                "success": False, 
                "message": f"语音识别服务错误: {str(e)}",
                "text": ""
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"语音识别异常: {str(e)}",
                "text": ""
            }
    
    @tool
    def text_to_speech(self, text: str, save_file: str = None) -> Dict[str, Any]:
        """
        文本转语音
        
        Args:
            text: 要转换的文本
            save_file: 保存的音频文件路径，如果为None则直接播放
            
        Returns:
            语音合成结果
        """
        if not HAS_SPEECH or not self.tts_engine:
            return {
                "success": False,
                "message": "语音合成功能不可用，请安装相关依赖",
                "text": text
            }
        
        try:
            if save_file:
                # 保存为文件
                self.tts_engine.save_to_file(text, save_file)
                self.tts_engine.runAndWait()
                
                return {
                    "success": True,
                    "message": "语音合成并保存成功",
                    "text": text,
                    "output_file": save_file
                }
            else:
                # 直接播放
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
                
                return {
                    "success": True,
                    "message": "语音播放成功",
                    "text": text
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"语音合成异常: {str(e)}",
                "text": text
            }
    
    @tool
    def image_analysis(self, image_path: str, analysis_type: str = "general") -> Dict[str, Any]:
        """
        图像分析
        
        Args:
            image_path: 图像文件路径
            analysis_type: 分析类型 (general, ocr, object_detection)
            
        Returns:
            图像分析结果
        """
        try:
            if not os.path.exists(image_path):
                return {
                    "success": False,
                    "message": f"图像文件不存在: {image_path}",
                    "analysis": {}
                }
            
            results = {
                "image_path": image_path,
                "analysis_type": analysis_type,
                "file_size": os.path.getsize(image_path)
            }
            
            if analysis_type == "ocr" and HAS_TESSERACT and HAS_PIL:
                # OCR文字识别
                try:
                    from PIL import Image
                    image = Image.open(image_path)
                    ocr_text = pytesseract.image_to_string(image, lang='chi_sim+eng')
                    results["ocr_text"] = ocr_text
                    results["has_text"] = len(ocr_text.strip()) > 0
                except Exception as e:
                    results["ocr_error"] = str(e)
            
            elif analysis_type == "general" and HAS_PIL:
                # 通用图像信息
                try:
                    from PIL import Image
                    image = Image.open(image_path)
                    results["image_info"] = {
                        "size": image.size,
                        "mode": image.mode,
                        "format": image.format
                    }
                except Exception as e:
                    results["image_error"] = str(e)
            else:
                results["note"] = "图像分析功能受限，缺少必要依赖"
            
            return {
                "success": True,
                "message": "图像分析完成",
                "analysis": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"图像分析异常: {str(e)}",
                "analysis": {}
            }

    def smart_extract_balance(self, elements: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        智能提取剩余话费金额
        通过语义分析和相邻元素关系找到真正的余额信息
        
        Args:
            elements: UI元素列表
            
        Returns:
            提取到的余额信息或None
        """
        import re
        
        balance_candidates = []
        
        # 遍历所有元素，查找金额
        for i, elem in enumerate(elements):
            text = elem.get('text', '').strip()
            if not text:
                continue
                
            # 方法1：查找包含完整金额的文本（如"66.60元"）
            money_pattern = r'(\d+(?:\.\d{1,2})?)\s*[元￥¥]'
            money_matches = re.findall(money_pattern, text)
            
            # 方法2：查找纯数字金额（如"66.60"），然后检查相邻元素
            pure_number_pattern = r'^(\d+(?:\.\d{1,2})?)$'
            pure_number_match = re.match(pure_number_pattern, text)
            
            # 处理完整金额文本
            if money_matches:
                for amount in money_matches:
                    candidate = self._create_balance_candidate(amount, text, i, elements, "完整金额文本")
                    balance_candidates.append(candidate)
            
            # 处理纯数字金额（重点改进部分）
            elif pure_number_match:
                amount = pure_number_match.group(1)
                candidate = self._create_balance_candidate(amount, text, i, elements, "纯数字金额")
                
                # 检查相邻元素是否有货币符号
                currency_bonus = 0
                nearby_currency = []
                for j in range(max(0, i-2), min(len(elements), i+3)):  # 检查前后2个元素
                    if j != i and j < len(elements):
                        neighbor_text = elements[j].get('text', '').strip()
                        if neighbor_text in ['¥', '￥', '元']:
                            currency_bonus = 80  # 高分奖励
                            nearby_currency.append(f"相邻货币符号: {neighbor_text}")
                            
                candidate['context_score'] += currency_bonus
                candidate['context'].extend(nearby_currency)
                
                # 特别检查：紧密相邻的"剩余话费"标题（重点加分）
                title_proximity_bonus = 0
                for j in range(max(0, i-3), i):  # 检查前3个元素
                    if j < len(elements):
                        neighbor_text = elements[j].get('text', '').strip().lower()
                        if '剩余话费' in neighbor_text:
                            distance = i - j
                            if distance == 1:  # 紧挨着
                                title_proximity_bonus = 200
                                candidate['context'].append(f"紧挨着剩余话费标题(距离{distance})")
                            elif distance == 2:  # 中间隔一个元素（可能是货币符号）
                                title_proximity_bonus = 180
                                candidate['context'].append(f"非常接近剩余话费标题(距离{distance})")
                            elif distance == 3:
                                title_proximity_bonus = 120
                                candidate['context'].append(f"接近剩余话费标题(距离{distance})")
                            break
                
                candidate['context_score'] += title_proximity_bonus
                
                # 检查是否在页面顶部位置（通过元素索引判断）
                if i <= 15:  # 前15个元素认为是顶部
                    candidate['context_score'] += 40
                    candidate['context'].append("位于页面顶部区域")
                
                balance_candidates.append(candidate)
        
        # 按语义得分排序
        balance_candidates.sort(key=lambda x: x['context_score'], reverse=True)
        
        # 输出分析结果
        self.logger.info(f"🧠 智能分析找到 {len(balance_candidates)} 个金额候选")
        for i, candidate in enumerate(balance_candidates[:5]):  # 显示前5个
            self.logger.info(f"  {i+1}. {candidate['amount']} (得分: {candidate['context_score']})")
            self.logger.info(f"     原文: {candidate['element_text']}")
            self.logger.info(f"     元素位置: 第{candidate['element_index']+1}个")
            self.logger.info(f"     上下文: {'; '.join(candidate['context'])}")
        
        # 返回得分最高的候选
        if balance_candidates and balance_candidates[0]['context_score'] > 0:
            best_candidate = balance_candidates[0]
            return {
                'amount': best_candidate['amount'],
                'raw_amount': best_candidate['raw_amount'],
                'context': best_candidate['element_text'],
                'score': best_candidate['context_score']
            }
        
        return None

    def _create_balance_candidate(self, amount: str, text: str, element_index: int, elements: List[Dict[str, Any]], source_type: str) -> Dict[str, Any]:
        """创建金额候选"""
        candidate = {
            'amount': f"{amount}元",
            'raw_amount': float(amount),
            'element_text': text,
            'element_index': element_index,
            'context_score': 0,
            'context': [f"来源: {source_type}"]
        }
        
        # 分析当前元素的语义上下文
        text_lower = text.lower()
        
        # 高优先级关键词（明确表示余额）
        high_priority_keywords = ['剩余', '余额', '可用', '账户余额', '话费余额', '当前余额']
        for keyword in high_priority_keywords:
            if keyword in text_lower:
                candidate['context_score'] += 60
                candidate['context'].append(f"包含关键词: {keyword}")
        
        # 中优先级关键词
        medium_priority_keywords = ['话费', '余量', '当前']
        for keyword in medium_priority_keywords:
            if keyword in text_lower:
                candidate['context_score'] += 30
                candidate['context'].append(f"包含关键词: {keyword}")
        
        # 负面关键词（表示不是余额）
        negative_keywords = ['充值', '缴费', '交费', '套餐', '售价', '优惠', '立即', '领取', '券', '福利', '不可使用', '暂不可使用']
        for keyword in negative_keywords:
            if keyword in text_lower:
                candidate['context_score'] -= 50
                candidate['context'].append(f"负面关键词: {keyword}")
        
        # 检查邻近元素的语义上下文（重点增强）
        context_range = 3  # 检查前后3个元素
        for j in range(max(0, element_index-context_range), min(len(elements), element_index+context_range+1)):
            if j == element_index:
                continue
            if j < len(elements):
                neighbor = elements[j]
                neighbor_text = neighbor.get('text', '').strip().lower()
                
                # 高优先级邻近元素
                if any(keyword in neighbor_text for keyword in high_priority_keywords):
                    distance_bonus = max(30 - abs(j - element_index) * 10, 10)  # 距离越近分数越高
                    candidate['context_score'] += distance_bonus
                    candidate['context'].append(f"邻近关键元素(距离{abs(j-element_index)}): {neighbor_text}")
                
                # 中优先级邻近元素
                elif any(keyword in neighbor_text for keyword in medium_priority_keywords):
                    distance_bonus = max(20 - abs(j - element_index) * 5, 5)
                    candidate['context_score'] += distance_bonus
                    candidate['context'].append(f"邻近相关元素(距离{abs(j-element_index)}): {neighbor_text}")
                
                # 负面邻近元素
                elif any(keyword in neighbor_text for keyword in negative_keywords):
                    candidate['context_score'] -= 30
                    candidate['context'].append(f"邻近负面元素: {neighbor_text}")
        
        # 金额合理性检查
        if 0.01 <= candidate['raw_amount'] <= 9999:  # 合理的话费余额范围
            candidate['context_score'] += 15
            candidate['context'].append("金额在合理范围内")
        else:
            candidate['context_score'] -= 30
            candidate['context'].append("金额可能不合理")
        
        return candidate

    def _check_if_in_app(self, elements: List[Dict[str, Any]], app_name: str = "联通") -> bool:
        """检查是否还在目标APP内"""
        for elem in elements:
            text = elem.get('text', '').lower()
            if app_name.lower() in text or any(keyword in text for keyword in ['话费', '剩余', '流量', '语音']):
                return True
        return False

    @tool(
        "query_unicom_balance",
        description="查询中国联通话费余额，集成了智能识别功能",
        group="unicom_android"
    )
    def query_unicom_balance(self) -> Dict[str, Any]:
        """
        查询联通话费余额的完整流程
        集成了修复后的设备连接、APP启动和智能余额识别功能
        
        Returns:
            包含余额信息的字典
        """
        from datetime import datetime
        
        start_time = datetime.now()
        self.logger.info("🎯 开始联通话费余额查询...")
        
        try:
            # 1. 检查设备连接
            self.logger.info("📱 1. 检查设备连接...")
            try:
                result = subprocess.run([self.adb_path, "devices"], capture_output=True, text=True, timeout=5)
                if "device" in result.stdout and len(result.stdout.split('\n')) > 1:
                    self.logger.info("✅ 设备连接正常")
                else:
                    return {
                        "success": False,
                        "message": "设备未连接",
                        "query_time": str(datetime.now())
                    }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"设备检查失败: {e}",
                    "query_time": str(datetime.now())
                }
            
            # 2. 直接启动联通APP
            self.logger.info("🚀 2. 直接启动联通APP...")
            try:
                # 获取设备ID
                device_result = subprocess.run([self.adb_path, "devices"], capture_output=True, text=True, timeout=5)
                device_lines = device_result.stdout.strip().split('\n')[1:]  # 跳过第一行标题
                device_id = None
                for line in device_lines:
                    if 'device' in line:
                        device_id = line.split('\t')[0]
                        break
                
                if device_id:
                    self.logger.info(f"📱 检测到设备: {device_id}")
                    # 使用monkey命令启动联通APP
                    launch_cmd = [self.adb_path, "-s", device_id, "shell", "monkey", "-p", "com.sinovatech.unicom.ui", "-c", "android.intent.category.LAUNCHER", "1"]
                    launch_result = subprocess.run(launch_cmd, capture_output=True, text=True, timeout=10)
                    
                    if launch_result.returncode == 0:
                        self.logger.info("✅ 联通APP启动成功")
                        time.sleep(5)  # 等待APP完全启动
                    else:
                        self.logger.info("🔄 尝试备用启动方案...")
                        backup_cmd = [self.adb_path, "-s", device_id, "shell", "am", "start", "-n", "com.sinovatech.unicom.ui/.MainActivity"]
                        backup_result = subprocess.run(backup_cmd, capture_output=True, text=True, timeout=10)
                        if backup_result.returncode == 0:
                            self.logger.info("✅ 备用方案启动成功")
                            time.sleep(5)
                        else:
                            return {
                                "success": False,
                                "message": f"APP启动失败: {backup_result.stderr}",
                                "query_time": str(datetime.now())
                            }
                else:
                    return {
                        "success": False,
                        "message": "未检测到设备",
                        "query_time": str(datetime.now())
                    }
                        
            except Exception as e:
                return {
                    "success": False,
                    "message": f"启动APP时出错: {e}",
                    "query_time": str(datetime.now())
                }
            
            # 3. 检查是否成功进入APP
            self.logger.info("📋 3. 检查APP是否已启动...")
            new_elements = self.find_elements()
            if new_elements.get('success'):
                new_elem_list = new_elements.get('elements', [])
                self.logger.info(f"✅ 新界面有 {len(new_elem_list)} 个元素")
                
                # 检查是否在APP内
                if self._check_if_in_app(new_elem_list):
                    self.logger.info("✅ 确认已进入联通APP")
                    
                    # 查找话费查询相关按钮
                    self.logger.info("🔍 4. 查找话费查询按钮...")
                    balance_buttons = []
                    
                    for elem in new_elem_list:
                        text = elem.get('text', '').strip()
                        text_lower = text.lower()
                        
                        # 精确匹配话费相关按钮
                        if any(keyword in text_lower for keyword in ['剩余话费', '话费余额', '余额', '账户余额']):
                            if '流量' not in text_lower and '语音' not in text_lower:  # 排除流量和语音
                                balance_buttons.append(elem)
                                self.logger.info(f"  🎯 找到话费按钮: {text} - 位置{elem['bounds']}")
                    
                    if balance_buttons:
                        self.logger.info(f"🎯 找到 {len(balance_buttons)} 个话费按钮")
                        # 选择最合适的按钮
                        best_button = balance_buttons[0]
                        self.logger.info(f"🔥 准备点击: {best_button['text']}")
                        
                        # 获取点击前的截图
                        self.logger.info("📸 点击前截图...")
                        self.capture_screenshot()
                        
                        # 精确点击，避免滑动
                        self.logger.info(f"🎯 精确点击位置: ({best_button['center_x']}, {best_button['center_y']})")
                        tap_result2 = self.tap_element(best_button['center_x'], best_button['center_y'])
                        
                        if tap_result2.get('success'):
                            self.logger.info("✅ 话费按钮点击成功")
                            
                            # 等待界面响应
                            self.logger.info("⏳ 等待界面加载...")
                            time.sleep(4)
                            
                            # 获取点击后的截图
                            self.logger.info("📸 点击后截图...")
                            self.capture_screenshot()
                            
                            # 检查是否还在APP内
                            self.logger.info("🔍 5. 检查点击后的界面状态...")
                            final_elements = self.find_elements()
                            if final_elements.get('success'):
                                final_elem_list = final_elements.get('elements', [])
                                self.logger.info(f"✅ 当前界面有 {len(final_elem_list)} 个元素")
                                
                                # 检查是否还在APP内
                                if self._check_if_in_app(final_elem_list):
                                    self.logger.info("✅ 确认还在APP内，开始查找话费信息...")
                                    
                                    # 智能识别剩余话费
                                    balance_result = self.smart_extract_balance(final_elem_list)
                                    if balance_result:
                                        end_time = datetime.now()
                                        duration = (end_time - start_time).total_seconds()
                                        
                                        result = {
                                            "success": True,
                                            "balance": balance_result['amount'],
                                            "raw_amount": balance_result['raw_amount'],
                                            "context": balance_result['context'],
                                            "confidence_score": balance_result['score'],
                                            "query_time": str(end_time),
                                            "duration_seconds": duration,
                                            "message": f"成功查询话费余额: {balance_result['amount']}"
                                        }
                                        self.logger.info(f"🎉 成功查询话费余额: {balance_result['amount']}")
                                        return result
                                    else:
                                        return {
                                            "success": False,
                                            "message": "未能智能识别剩余话费",
                                            "available_elements": [elem.get('text', '') for elem in final_elem_list[:10] if elem.get('text', '').strip()],
                                            "query_time": str(datetime.now())
                                        }
                                else:
                                    return {
                                        "success": False,
                                        "message": "应用已退出，点击操作可能触发了意外行为",
                                        "query_time": str(datetime.now())
                                    }
                            else:
                                return {
                                    "success": False,
                                    "message": "获取点击后界面失败",
                                    "query_time": str(datetime.now())
                                }
                        else:
                            return {
                                "success": False,
                                "message": "话费按钮点击失败",
                                "query_time": str(datetime.now())
                            }
                    else:
                        return {
                            "success": False,
                            "message": "未找到话费查询按钮",
                            "available_texts": [elem.get('text', '') for elem in new_elem_list[:10] if elem.get('text', '').strip()],
                            "query_time": str(datetime.now())
                        }
                else:
                    return {
                        "success": False,
                        "message": "未成功进入APP，可能启动失败",
                        "query_time": str(datetime.now())
                    }
            else:
                return {
                    "success": False,
                    "message": "获取APP启动后界面失败",
                    "query_time": str(datetime.now())
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"查询过程中发生异常: {str(e)}",
                "query_time": str(datetime.now())
            }

    def smart_extract_data_usage(self, elements: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        智能提取剩余流量数据
        通过语义分析和相邻元素关系找到真正的流量信息
        
        Args:
            elements: UI元素列表
            
        Returns:
            提取到的流量信息或None
        """
        import re
        
        data_candidates = []
        
        # 遍历所有元素，查找流量数据
        for i, elem in enumerate(elements):
            text = elem.get('text', '').strip()
            if not text:
                continue
                
            # 方法1：查找包含完整流量的文本（如"2.5GB"、"500MB"）
            data_pattern = r'(\d+(?:\.\d+)?)\s*(GB|MB|TB|g|m|t)'
            data_matches = re.findall(data_pattern, text, re.IGNORECASE)
            
            # 方法2：查找纯数字流量（如"2.5"），然后检查相邻元素
            pure_number_pattern = r'^(\d+(?:\.\d+)?)$'
            pure_number_match = re.match(pure_number_pattern, text)
            
            # 处理完整流量文本
            if data_matches:
                for amount, unit in data_matches:
                    candidate = self._create_data_candidate(amount, unit.upper(), text, i, elements, "完整流量文本")
                    data_candidates.append(candidate)
            
            # 处理纯数字流量（重点改进部分）
            elif pure_number_match:
                amount = pure_number_match.group(1)
                
                # 检查相邻元素是否有流量单位
                unit_found = None
                unit_bonus = 0
                nearby_units = []
                for j in range(max(0, i-2), min(len(elements), i+3)):  # 检查前后2个元素
                    if j != i and j < len(elements):
                        neighbor_text = elements[j].get('text', '').strip().upper()
                        if neighbor_text in ['GB', 'MB', 'TB', 'G', 'M', 'T']:
                            unit_found = neighbor_text if neighbor_text in ['GB', 'MB', 'TB'] else neighbor_text + 'B'
                            unit_bonus = 80  # 高分奖励
                            nearby_units.append(f"相邻流量单位: {neighbor_text}")
                            break
                
                # 如果找到单位，创建候选
                if unit_found:
                    candidate = self._create_data_candidate(amount, unit_found, text, i, elements, "纯数字流量")
                    candidate['context_score'] += unit_bonus
                    candidate['context'].extend(nearby_units)
                    
                    # 特别检查：紧密相邻的"剩余流量"、"剩余通用流量"标题（重点加分）
                    title_proximity_bonus = 0
                    for j in range(max(0, i-3), i):  # 检查前3个元素
                        if j < len(elements):
                            neighbor_text = elements[j].get('text', '').strip().lower()
                            if any(keyword in neighbor_text for keyword in ['剩余通用流量', '剩余流量', '通用流量', '剩余数据', '可用流量']):
                                distance = i - j
                                if distance == 1:  # 紧挨着
                                    title_proximity_bonus = 200
                                    candidate['context'].append(f"紧挨着流量标题(距离{distance})")
                                elif distance == 2:  # 中间隔一个元素（可能是单位）
                                    title_proximity_bonus = 180
                                    candidate['context'].append(f"非常接近流量标题(距离{distance})")
                                elif distance == 3:
                                    title_proximity_bonus = 120
                                    candidate['context'].append(f"接近流量标题(距离{distance})")
                                break
                    
                    candidate['context_score'] += title_proximity_bonus
                    
                    # 检查是否在页面顶部位置（通过元素索引判断）
                    if i <= 15:  # 前15个元素认为是顶部
                        candidate['context_score'] += 40
                        candidate['context'].append("位于页面顶部区域")
                    
                    data_candidates.append(candidate)
        
        # 按语义得分排序
        data_candidates.sort(key=lambda x: x['context_score'], reverse=True)
        
        # 输出分析结果
        self.logger.info(f"🧠 智能分析找到 {len(data_candidates)} 个流量候选")
        for i, candidate in enumerate(data_candidates[:5]):  # 显示前5个
            self.logger.info(f"  {i+1}. {candidate['amount']} (得分: {candidate['context_score']})")
            self.logger.info(f"     原文: {candidate['element_text']}")
            self.logger.info(f"     元素位置: 第{candidate['element_index']+1}个")
            self.logger.info(f"     上下文: {'; '.join(candidate['context'])}")
        
        # 返回得分最高的候选
        if data_candidates and data_candidates[0]['context_score'] > 0:
            best_candidate = data_candidates[0]
            return {
                'amount': best_candidate['amount'],
                'raw_amount': best_candidate['raw_amount'],
                'unit': best_candidate['unit'],
                'context': best_candidate['element_text'],
                'score': best_candidate['context_score']
            }
        
        return None

    def _create_data_candidate(self, amount: str, unit: str, text: str, element_index: int, elements: List[Dict[str, Any]], source_type: str) -> Dict[str, Any]:
        """创建流量候选"""
        candidate = {
            'amount': f"{amount}{unit}",
            'raw_amount': float(amount),
            'unit': unit,
            'element_text': text,
            'element_index': element_index,
            'context_score': 0,
            'context': [f"来源: {source_type}"]
        }
        
        # 分析当前元素的语义上下文
        text_lower = text.lower()
        
        # 高优先级关键词（明确表示剩余流量）
        high_priority_keywords = ['剩余通用流量', '剩余流量', '通用流量', '可用流量', '剩余数据', '可用数据', '剩余上网流量']
        for keyword in high_priority_keywords:
            if keyword in text_lower:
                candidate['context_score'] += 70  # 比话费稍高，因为流量词汇更具体
                candidate['context'].append(f"包含关键词: {keyword}")
        
        # 中优先级关键词
        medium_priority_keywords = ['流量', '数据', '上网', '网络', '通用']
        for keyword in medium_priority_keywords:
            if keyword in text_lower:
                candidate['context_score'] += 35
                candidate['context'].append(f"包含关键词: {keyword}")
        
        # 负面关键词（表示不是剩余流量）
        negative_keywords = ['充值', '购买', '套餐', '售价', '优惠', '立即', '领取', '券', '福利', '已用', '已使用', '消耗']
        for keyword in negative_keywords:
            if keyword in text_lower:
                candidate['context_score'] -= 50
                candidate['context'].append(f"负面关键词: {keyword}")
        
        # 检查邻近元素的语义上下文
        context_range = 3  # 检查前后3个元素
        for j in range(max(0, element_index-context_range), min(len(elements), element_index+context_range+1)):
            if j == element_index:
                continue
            if j < len(elements):
                neighbor = elements[j]
                neighbor_text = neighbor.get('text', '').strip().lower()
                
                # 高优先级邻近元素
                if any(keyword in neighbor_text for keyword in high_priority_keywords):
                    distance_bonus = max(35 - abs(j - element_index) * 10, 10)  # 距离越近分数越高
                    candidate['context_score'] += distance_bonus
                    candidate['context'].append(f"邻近关键元素(距离{abs(j-element_index)}): {neighbor_text}")
                
                # 中优先级邻近元素
                elif any(keyword in neighbor_text for keyword in medium_priority_keywords):
                    distance_bonus = max(25 - abs(j - element_index) * 5, 5)
                    candidate['context_score'] += distance_bonus
                    candidate['context'].append(f"邻近相关元素(距离{abs(j-element_index)}): {neighbor_text}")
                
                # 负面邻近元素
                elif any(keyword in neighbor_text for keyword in negative_keywords):
                    candidate['context_score'] -= 30
                    candidate['context'].append(f"邻近负面元素: {neighbor_text}")
        
        # 流量合理性检查
        # GB范围：0.01-1000GB，MB范围：1-999999MB
        if unit.upper() == 'GB':
            if 0.01 <= candidate['raw_amount'] <= 1000:
                candidate['context_score'] += 20
                candidate['context'].append("GB数值在合理范围内")
            else:
                candidate['context_score'] -= 25
                candidate['context'].append("GB数值可能不合理")
        elif unit.upper() == 'MB':
            if 1 <= candidate['raw_amount'] <= 999999:
                candidate['context_score'] += 15
                candidate['context'].append("MB数值在合理范围内")
            else:
                candidate['context_score'] -= 25
                candidate['context'].append("MB数值可能不合理")
        
        return candidate

    @tool(
        "query_unicom_data_usage",
        description="查询中国联通剩余流量，集成了智能识别功能",
        group="unicom_android"
    )
    def query_unicom_data_usage(self) -> Dict[str, Any]:
        """
        查询联通剩余流量的完整流程
        集成了修复后的设备连接、APP启动和智能流量识别功能
        
        Returns:
            包含流量信息的字典
        """
        from datetime import datetime
        
        start_time = datetime.now()
        self.logger.info("🎯 开始联通剩余流量查询...")
        
        try:
            # 1. 检查设备连接
            self.logger.info("📱 1. 检查设备连接...")
            try:
                result = subprocess.run([self.adb_path, "devices"], capture_output=True, text=True, timeout=5)
                if "device" in result.stdout and len(result.stdout.split('\n')) > 1:
                    self.logger.info("✅ 设备连接正常")
                else:
                    return {
                        "success": False,
                        "message": "设备未连接",
                        "query_time": str(datetime.now())
                    }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"设备检查失败: {e}",
                    "query_time": str(datetime.now())
                }
            
            # 2. 直接启动联通APP
            self.logger.info("🚀 2. 直接启动联通APP...")
            try:
                # 获取设备ID
                device_result = subprocess.run([self.adb_path, "devices"], capture_output=True, text=True, timeout=5)
                device_lines = device_result.stdout.strip().split('\n')[1:]  # 跳过第一行标题
                device_id = None
                for line in device_lines:
                    if 'device' in line:
                        device_id = line.split('\t')[0]
                        break
                
                if device_id:
                    self.logger.info(f"📱 检测到设备: {device_id}")
                    # 使用monkey命令启动联通APP
                    launch_cmd = [self.adb_path, "-s", device_id, "shell", "monkey", "-p", "com.sinovatech.unicom.ui", "-c", "android.intent.category.LAUNCHER", "1"]
                    launch_result = subprocess.run(launch_cmd, capture_output=True, text=True, timeout=10)
                    
                    if launch_result.returncode == 0:
                        self.logger.info("✅ 联通APP启动成功")
                        time.sleep(5)  # 等待APP完全启动
                    else:
                        self.logger.info("🔄 尝试备用启动方案...")
                        backup_cmd = [self.adb_path, "-s", device_id, "shell", "am", "start", "-n", "com.sinovatech.unicom.ui/.MainActivity"]
                        backup_result = subprocess.run(backup_cmd, capture_output=True, text=True, timeout=10)
                        if backup_result.returncode == 0:
                            self.logger.info("✅ 备用方案启动成功")
                            time.sleep(5)
                        else:
                            return {
                                "success": False,
                                "message": f"APP启动失败: {backup_result.stderr}",
                                "query_time": str(datetime.now())
                            }
                else:
                    return {
                        "success": False,
                        "message": "未检测到设备",
                        "query_time": str(datetime.now())
                    }
                        
            except Exception as e:
                return {
                    "success": False,
                    "message": f"启动APP时出错: {e}",
                    "query_time": str(datetime.now())
                }
            
            # 3. 检查是否成功进入APP
            self.logger.info("📋 3. 检查APP是否已启动...")
            new_elements = self.find_elements()
            if new_elements.get('success'):
                new_elem_list = new_elements.get('elements', [])
                self.logger.info(f"✅ 新界面有 {len(new_elem_list)} 个元素")
                
                # 检查是否在APP内
                if self._check_if_in_app(new_elem_list):
                    self.logger.info("✅ 确认已进入联通APP")
                    
                    # 查找流量查询相关按钮
                    self.logger.info("🔍 4. 查找流量查询按钮...")
                    data_buttons = []
                    
                    for elem in new_elem_list:
                        text = elem.get('text', '').strip()
                        text_lower = text.lower()
                        
                        # 精确匹配流量相关按钮
                        if any(keyword in text_lower for keyword in ['剩余通用流量', '剩余流量', '通用流量', '流量使用', '数据流量']):
                            if '话费' not in text_lower and '语音' not in text_lower:  # 排除话费和语音
                                data_buttons.append(elem)
                                self.logger.info(f"  🎯 找到流量按钮: {text} - 位置{elem['bounds']}")
                    
                    if data_buttons:
                        self.logger.info(f"🎯 找到 {len(data_buttons)} 个流量按钮")
                        # 选择最合适的按钮
                        best_button = data_buttons[0]
                        self.logger.info(f"🔥 准备点击: {best_button['text']}")
                        
                        # 获取点击前的截图
                        self.logger.info("📸 点击前截图...")
                        self.capture_screenshot()
                        
                        # 精确点击，避免滑动
                        self.logger.info(f"🎯 精确点击位置: ({best_button['center_x']}, {best_button['center_y']})")
                        tap_result2 = self.tap_element(best_button['center_x'], best_button['center_y'])
                        
                        if tap_result2.get('success'):
                            self.logger.info("✅ 流量按钮点击成功")
                            
                            # 等待界面响应
                            self.logger.info("⏳ 等待界面加载...")
                            time.sleep(4)
                            
                            # 获取点击后的截图
                            self.logger.info("📸 点击后截图...")
                            self.capture_screenshot()
                            
                            # 检查是否还在APP内
                            self.logger.info("🔍 5. 检查点击后的界面状态...")
                            final_elements = self.find_elements()
                            if final_elements.get('success'):
                                final_elem_list = final_elements.get('elements', [])
                                self.logger.info(f"✅ 当前界面有 {len(final_elem_list)} 个元素")
                                
                                # 检查是否还在APP内
                                if self._check_if_in_app(final_elem_list):
                                    self.logger.info("✅ 确认还在APP内，开始查找流量信息...")
                                    
                                    # 智能识别剩余流量
                                    data_result = self.smart_extract_data_usage(final_elem_list)
                                    if data_result:
                                        end_time = datetime.now()
                                        duration = (end_time - start_time).total_seconds()
                                        
                                        result = {
                                            "success": True,
                                            "data_usage": data_result['amount'],
                                            "raw_amount": data_result['raw_amount'],
                                            "unit": data_result['unit'],
                                            "context": data_result['context'],
                                            "confidence_score": data_result['score'],
                                            "query_time": str(end_time),
                                            "duration_seconds": duration,
                                            "message": f"成功查询剩余流量: {data_result['amount']}"
                                        }
                                        self.logger.info(f"🎉 成功查询剩余流量: {data_result['amount']}")
                                        return result
                                    else:
                                        return {
                                            "success": False,
                                            "message": "未能智能识别剩余流量",
                                            "available_elements": [elem.get('text', '') for elem in final_elem_list[:10] if elem.get('text', '').strip()],
                                            "query_time": str(datetime.now())
                                        }
                                else:
                                    return {
                                        "success": False,
                                        "message": "应用已退出，点击操作可能触发了意外行为",
                                        "query_time": str(datetime.now())
                                    }
                            else:
                                return {
                                    "success": False,
                                    "message": "获取点击后界面失败",
                                    "query_time": str(datetime.now())
                                }
                        else:
                            return {
                                "success": False,
                                "message": "流量按钮点击失败",
                                "query_time": str(datetime.now())
                            }
                    else:
                        return {
                            "success": False,
                            "message": "未找到流量查询按钮",
                            "available_texts": [elem.get('text', '') for elem in new_elem_list[:10] if elem.get('text', '').strip()],
                            "query_time": str(datetime.now())
                        }
                else:
                    return {
                        "success": False,
                        "message": "APP启动后未能进入主界面",
                        "query_time": str(datetime.now())
                    }
            else:
                return {
                    "success": False,
                    "message": "获取APP界面失败", 
                    "query_time": str(datetime.now())
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"查询过程中发生异常: {str(e)}",
                "query_time": str(datetime.now())
            }
