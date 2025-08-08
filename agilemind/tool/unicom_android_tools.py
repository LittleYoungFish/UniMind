"""
中国联通Android设备操作工具
China Unicom Android Device Operation Tools
"""

import os
import json
import time
import subprocess
import logging
import cv2
import numpy as np
import yaml
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from .tool_decorator import tool


class UnicomAndroidTools:
    """中国联通Android设备操作工具"""
    
    def __init__(self):
        self.config = self._load_unicom_config()
        self.device_id = None
        self.scrcpy_process = None
        self.logger = logging.getLogger(__name__)
        self.unicom_apps = self.config.get("unicom_app_packages", {})
        
    def _load_unicom_config(self) -> Dict[str, Any]:
        """加载中国联通配置"""
        try:
            config_path = "config_unicom_android.yaml"
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            else:
                # 默认配置
                return {
                    "android_connection": {
                        "device_id": "",
                        "adb_path": "adb",
                        "scrcpy_path": "scrcpy"
                    },
                    "unicom_app_packages": {
                        "unicom_app": "com.sinovatech.unicom.ui",
                        "unicom_payment": "com.unicompay.wallet",
                        "unicom_video": "com.unicom.video",
                        "unicom_public": "com.unicom.public"
                    }
                }
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            return {}

    def _execute_adb_command(self, command: str) -> Tuple[bool, str]:
        """执行ADB命令"""
        try:
            if self.device_id:
                full_command = f"{self.config['android_connection']['adb_path']} -s {self.device_id} {command}"
            else:
                full_command = f"{self.config['android_connection']['adb_path']} {command}"
            
            result = subprocess.run(
                full_command.split(),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, result.stderr.strip()
                
        except subprocess.TimeoutExpired:
            return False, "命令执行超时"
        except Exception as e:
            return False, str(e)

    def _capture_screenshot(self) -> Optional[str]:
        """截取屏幕截图"""
        try:
            screenshot_dir = self.config.get("android_connection", {}).get("screenshot_path", "./screenshots/")
            os.makedirs(screenshot_dir, exist_ok=True)
            
            timestamp = int(time.time())
            screenshot_path = os.path.join(screenshot_dir, f"screenshot_{timestamp}.png")
            
            success, output = self._execute_adb_command(f"exec-out screencap -p > {screenshot_path}")
            if success:
                return screenshot_path
            else:
                # 尝试另一种方法
                success, output = self._execute_adb_command("shell screencap -p /sdcard/screenshot.png")
                if success:
                    success, output = self._execute_adb_command(f"pull /sdcard/screenshot.png {screenshot_path}")
                    if success:
                        return screenshot_path
                        
            return None
        except Exception as e:
            self.logger.error(f"截图失败: {e}")
            return None

    def _perform_ocr(self, image_path: str) -> str:
        """对图像进行OCR识别"""
        try:
            import pytesseract
            from PIL import Image
            
            # 加载图像
            image = Image.open(image_path)
            
            # 进行OCR识别
            ocr_config = self.config.get("ui_automation", {}).get("ocr", {})
            languages = "+".join(ocr_config.get("languages", ["chi_sim", "eng"]))
            config = ocr_config.get("config", "--psm 6")
            
            text = pytesseract.image_to_string(
                image, 
                lang=languages, 
                config=config
            )
            
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"OCR识别失败: {e}")
            return ""

    def _find_unicom_app_elements(self, screenshot_path: str, app_type: str) -> List[Dict[str, Any]]:
        """查找联通APP特定元素"""
        elements = []
        
        try:
            # 根据APP类型查找特定元素
            if app_type == "unicom_app":
                # 联通营业厅常见元素
                common_texts = ["话费", "流量", "充值", "套餐", "账单", "客服", "我的"]
            elif app_type == "unicom_payment":
                # 联通支付常见元素
                common_texts = ["余额", "充值", "转账", "支付", "钱包", "银行卡"]
            elif app_type == "unicom_video":
                # 联通视频常见元素
                common_texts = ["播放", "收藏", "历史", "搜索", "分类", "我的"]
            else:
                common_texts = ["确定", "取消", "返回", "下一步", "提交"]
            
            # 进行OCR识别
            ocr_text = self._perform_ocr(screenshot_path)
            
            # 查找匹配的文本
            for text in common_texts:
                if text in ocr_text:
                    elements.append({
                        "type": "text",
                        "content": text,
                        "found": True
                    })
            
            return elements
            
        except Exception as e:
            self.logger.error(f"查找联通APP元素失败: {e}")
            return []

    @tool(
        name="unicom_android_connect",
        description="连接到Android设备，专门用于中国联通APP操作",
        group="unicom_android"
    )
    def unicom_android_connect(self, device_id: str) -> Dict[str, Any]:
        """连接到Android设备"""
        try:
            self.device_id = device_id
            
            # 检查设备连接
            success, output = self._execute_adb_command("devices")
            if not success:
                return {"success": False, "message": f"ADB连接失败: {output}"}
            
            if device_id not in output:
                return {"success": False, "message": f"设备 {device_id} 未连接"}
            
            # 检查联通APP是否已安装
            installed_apps = []
            for app_name, package_name in self.unicom_apps.items():
                success, output = self._execute_adb_command(f"shell pm list packages {package_name}")
                if success and package_name in output:
                    installed_apps.append(app_name)
            
            return {
                "success": True,
                "message": f"成功连接到设备 {device_id}",
                "device_id": device_id,
                "installed_unicom_apps": installed_apps
            }
            
        except Exception as e:
            return {"success": False, "message": f"连接失败: {str(e)}"}

    @tool(
        name="unicom_launch_app",
        description="启动指定的中国联通APP",
        group="unicom_android"
    )
    def unicom_launch_app(self, app_name: str) -> Dict[str, Any]:
        """启动联通APP"""
        try:
            if app_name not in self.unicom_apps:
                return {"success": False, "message": f"未知的联通APP: {app_name}"}
            
            package_name = self.unicom_apps[app_name]
            
            # 启动APP
            success, output = self._execute_adb_command(f"shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1")
            
            if success:
                time.sleep(self.config.get("ui_automation", {}).get("wait_times", {}).get("app_launch", 5))
                return {
                    "success": True,
                    "message": f"成功启动 {app_name}",
                    "package_name": package_name
                }
            else:
                return {"success": False, "message": f"启动失败: {output}"}
                
        except Exception as e:
            return {"success": False, "message": f"启动失败: {str(e)}"}

    @tool(
        name="unicom_get_screen_content",
        description="获取当前屏幕内容，专门识别中国联通APP界面元素",
        group="unicom_android"
    )
    def unicom_get_screen_content(self, app_context: str = "unicom_app") -> Dict[str, Any]:
        """获取屏幕内容，专门针对联通APP"""
        try:
            # 截取屏幕
            screenshot_path = self._capture_screenshot()
            if not screenshot_path:
                return {"success": False, "message": "截图失败"}
            
            # 进行OCR识别
            ocr_text = self._perform_ocr(screenshot_path)
            
            # 查找联通APP特定元素
            elements = self._find_unicom_app_elements(screenshot_path, app_context)
            
            # 分析当前页面类型
            page_type = self._analyze_unicom_page_type(ocr_text)
            
            return {
                "success": True,
                "screenshot_path": screenshot_path,
                "ocr_text": ocr_text,
                "unicom_elements": elements,
                "page_type": page_type,
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {"success": False, "message": f"获取屏幕内容失败: {str(e)}"}

    def _analyze_unicom_page_type(self, ocr_text: str) -> str:
        """分析联通APP页面类型"""
        page_indicators = {
            "主页": ["首页", "话费", "流量", "套餐", "我的"],
            "话费查询": ["话费余额", "当前余额", "可用余额"],
            "流量查询": ["流量使用", "剩余流量", "流量包"],
            "充值缴费": ["充值", "缴费", "支付", "金额"],
            "套餐办理": ["套餐", "办理", "月租", "包含"],
            "客服页面": ["客服", "咨询", "帮助", "联系"],
            "账单详情": ["账单", "消费", "详情", "明细"],
            "登录页面": ["登录", "手机号", "密码", "验证码"]
        }
        
        for page_type, keywords in page_indicators.items():
            if any(keyword in ocr_text for keyword in keywords):
                return page_type
        
        return "未知页面"

    @tool(
        name="unicom_find_element_by_text",
        description="在联通APP中根据文本查找元素",
        group="unicom_android"
    )
    def unicom_find_element_by_text(self, text: str, app_context: str = "unicom_app") -> Dict[str, Any]:
        """根据文本查找元素"""
        try:
            # 获取当前屏幕内容
            screen_result = self.unicom_get_screen_content(app_context)
            if not screen_result["success"]:
                return screen_result
            
            ocr_text = screen_result["ocr_text"]
            
            # 检查文本是否存在
            if text in ocr_text:
                # 使用UI Automator查找具体位置
                success, output = self._execute_adb_command(f'shell uiautomator dump /sdcard/ui_dump.xml')
                if success:
                    success, xml_content = self._execute_adb_command('shell cat /sdcard/ui_dump.xml')
                    if success and text in xml_content:
                        return {
                            "success": True,
                            "found": True,
                            "text": text,
                            "method": "uiautomator"
                        }
                
                return {
                    "success": True,
                    "found": True,
                    "text": text,
                    "method": "ocr"
                }
            else:
                return {
                    "success": True,
                    "found": False,
                    "text": text,
                    "message": f"未找到文本: {text}"
                }
                
        except Exception as e:
            return {"success": False, "message": f"查找元素失败: {str(e)}"}

    @tool(
        name="unicom_tap_element",
        description="点击联通APP中的指定元素",
        group="unicom_android"
    )
    def unicom_tap_element(self, text: str, app_context: str = "unicom_app") -> Dict[str, Any]:
        """点击指定元素"""
        try:
            # 先查找元素
            find_result = self.unicom_find_element_by_text(text, app_context)
            if not find_result["success"] or not find_result.get("found"):
                return {"success": False, "message": f"未找到元素: {text}"}
            
            # 尝试使用UI Automator点击
            success, output = self._execute_adb_command(f'shell uiautomator2 click "{text}"')
            if success:
                time.sleep(self.config.get("ui_automation", {}).get("operations", {}).get("tap_duration", 100) / 1000)
                return {
                    "success": True,
                    "message": f"成功点击元素: {text}",
                    "method": "uiautomator"
                }
            
            # 如果UI Automator失败，尝试通过坐标点击
            # 这里需要更复杂的图像处理来定位元素坐标
            return {"success": False, "message": f"点击元素失败: {text}"}
            
        except Exception as e:
            return {"success": False, "message": f"点击失败: {str(e)}"}

    @tool(
        name="unicom_input_text",
        description="在联通APP中输入文本",
        group="unicom_android"
    )
    def unicom_input_text(self, text: str) -> Dict[str, Any]:
        """输入文本"""
        try:
            # 清除输入法缓存
            self._execute_adb_command("shell input keyevent KEYCODE_CTRL_A")
            self._execute_adb_command("shell input keyevent KEYCODE_DEL")
            
            # 输入文本
            success, output = self._execute_adb_command(f'shell input text "{text}"')
            
            if success:
                time.sleep(self.config.get("ui_automation", {}).get("operations", {}).get("input_delay", 100) / 1000)
                return {
                    "success": True,
                    "message": f"成功输入文本: {text}"
                }
            else:
                return {"success": False, "message": f"输入失败: {output}"}
                
        except Exception as e:
            return {"success": False, "message": f"输入失败: {str(e)}"}

    @tool(
        name="unicom_perform_operation",
        description="执行联通业务操作，如查询话费、充值、办理套餐等",
        group="unicom_android"
    )
    def unicom_perform_operation(self, operation_type: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行联通业务操作"""
        try:
            if parameters is None:
                parameters = {}
                
            operations = self.config.get("unicom_operations", {})
            
            # 查找匹配的操作
            operation_found = None
            for category, ops in operations.items():
                if isinstance(ops, list):
                    for op in ops:
                        if op.get("name") == operation_type or operation_type in op.get("keywords", []):
                            operation_found = op
                            break
                if operation_found:
                    break
            
            if not operation_found:
                return {"success": False, "message": f"未知的操作类型: {operation_type}"}
            
            # 启动对应的APP
            app_name = operation_found.get("app", "unicom_app")
            launch_result = self.unicom_launch_app(app_name)
            if not launch_result["success"]:
                return launch_result
            
            # 等待APP加载
            time.sleep(3)
            
            # 获取当前屏幕内容
            screen_result = self.unicom_get_screen_content(app_name)
            if not screen_result["success"]:
                return screen_result
            
            # 根据操作类型执行具体步骤
            steps_result = self._execute_operation_steps(operation_type, operation_found, parameters)
            
            return {
                "success": True,
                "operation": operation_type,
                "app": app_name,
                "steps_result": steps_result,
                "message": f"操作 {operation_type} 执行完成"
            }
            
        except Exception as e:
            return {"success": False, "message": f"执行操作失败: {str(e)}"}

    def _execute_operation_steps(self, operation_type: str, operation_config: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行具体的操作步骤"""
        try:
            steps = []
            
            # 根据操作类型定义步骤
            if "查询话费" in operation_type:
                steps = [
                    {"action": "find_and_tap", "target": "话费"},
                    {"action": "wait", "duration": 2},
                    {"action": "get_screen_content", "context": "话费查询"}
                ]
            elif "充值" in operation_type:
                amount = parameters.get("amount", "")
                steps = [
                    {"action": "find_and_tap", "target": "充值"},
                    {"action": "wait", "duration": 2},
                    {"action": "input_text", "text": amount} if amount else {"action": "skip"},
                    {"action": "find_and_tap", "target": "确定"}
                ]
            elif "查询流量" in operation_type:
                steps = [
                    {"action": "find_and_tap", "target": "流量"},
                    {"action": "wait", "duration": 2},
                    {"action": "get_screen_content", "context": "流量查询"}
                ]
            else:
                steps = [
                    {"action": "get_screen_content", "context": "通用操作"}
                ]
            
            # 执行步骤
            results = []
            for step in steps:
                if step["action"] == "find_and_tap":
                    result = self.unicom_tap_element(step["target"])
                elif step["action"] == "input_text":
                    result = self.unicom_input_text(step["text"])
                elif step["action"] == "wait":
                    time.sleep(step["duration"])
                    result = {"success": True, "action": "wait"}
                elif step["action"] == "get_screen_content":
                    result = self.unicom_get_screen_content(step.get("context", "unicom_app"))
                elif step["action"] == "skip":
                    result = {"success": True, "action": "skip"}
                else:
                    result = {"success": False, "message": f"未知步骤: {step['action']}"}
                
                results.append(result)
                
                # 如果某个步骤失败，停止执行
                if not result.get("success", False):
                    break
            
            return {
                "success": True,
                "steps_executed": len(results),
                "results": results
            }
            
        except Exception as e:
            return {"success": False, "message": f"执行步骤失败: {str(e)}"}

    @tool(
        name="unicom_close_app",
        description="关闭指定的中国联通APP",
        group="unicom_android"
    )
    def unicom_close_app(self, app_name: str) -> Dict[str, Any]:
        """关闭联通APP"""
        try:
            if app_name not in self.unicom_apps:
                return {"success": False, "message": f"未知的联通APP: {app_name}"}
            
            package_name = self.unicom_apps[app_name]
            
            # 强制停止APP
            success, output = self._execute_adb_command(f"shell am force-stop {package_name}")
            
            if success:
                return {
                    "success": True,
                    "message": f"成功关闭 {app_name}",
                    "package_name": package_name
                }
            else:
                return {"success": False, "message": f"关闭失败: {output}"}
                
        except Exception as e:
            return {"success": False, "message": f"关闭失败: {str(e)}"}

    @tool(
        name="unicom_get_app_status",
        description="获取中国联通APP的运行状态",
        group="unicom_android"
    )
    def unicom_get_app_status(self) -> Dict[str, Any]:
        """获取联通APP运行状态"""
        try:
            app_status = {}
            
            for app_name, package_name in self.unicom_apps.items():
                # 检查APP是否正在运行
                success, output = self._execute_adb_command(f"shell pidof {package_name}")
                is_running = success and output.strip() != ""
                
                # 检查APP是否已安装
                success, output = self._execute_adb_command(f"shell pm list packages {package_name}")
                is_installed = success and package_name in output
                
                app_status[app_name] = {
                    "package_name": package_name,
                    "is_installed": is_installed,
                    "is_running": is_running,
                    "pid": output.strip() if is_running else None
                }
            
            return {
                "success": True,
                "device_id": self.device_id,
                "app_status": app_status,
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {"success": False, "message": f"获取状态失败: {str(e)}"}

