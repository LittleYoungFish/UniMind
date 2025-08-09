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
