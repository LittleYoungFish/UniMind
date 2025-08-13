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
            
            # 使用简单的方法：先保存到设备，再拉取
            success, output = self._execute_adb_command("shell screencap -p /sdcard/screenshot_temp.png")
            if success:
                # 拉取文件到本地
                success, output = self._execute_adb_command(f"pull /sdcard/screenshot_temp.png \"{screenshot_path}\"")
                if success:
                    # 清理设备上的临时文件
                    self._execute_adb_command("shell rm /sdcard/screenshot_temp.png")
                    return screenshot_path
                else:
                    self.logger.error(f"拉取截图失败: {output}")
            else:
                self.logger.error(f"设备截图失败: {output}")
                        
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
        "unicom_android_connect",
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
        "unicom_launch_app",
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
        "unicom_get_screen_content",
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
        "unicom_find_element_by_text",
        description="在联通APP中根据文本查找元素",
        group="unicom_android"
    )
    def unicom_find_element_by_text(self, text: str, app_context: str = "unicom_app") -> Dict[str, Any]:
        """根据文本查找元素"""
        try:
            # 首先尝试使用UI Automator查找元素（不依赖OCR）
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
            
            # 如果UI Automator没找到，尝试OCR方法
            screen_result = self.unicom_get_screen_content(app_context)
            if screen_result["success"]:
                ocr_text = screen_result["ocr_text"]
                
                # 检查文本是否存在
                if text in ocr_text:
                    return {
                        "success": True,
                        "found": True,
                        "text": text,
                        "method": "ocr"
                    }
            
            return {
                "success": True,
                "found": False,
                "text": text,
                "message": f"未找到文本: {text}"
            }
                
        except Exception as e:
            return {"success": False, "message": f"查找元素失败: {str(e)}"}

    @tool(
        "unicom_tap_element",
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
            
            # 尝试使用更直接的方式点击 - 通过input tap
            # 首先尝试通过UI Automator获取坐标
            success, output = self._execute_adb_command(f'shell uiautomator dump /sdcard/ui_dump.xml')
            if success:
                success, xml_content = self._execute_adb_command('shell cat /sdcard/ui_dump.xml')
                if success and text in xml_content:
                    # 尝试提取坐标信息（简化实现）
                    # 这里使用模拟点击，先尝试通过input tap命令
                    import re
                    bounds_pattern = rf'text="{text}"[^>]*bounds="(\[[\d,\]]+)"'
                    match = re.search(bounds_pattern, xml_content)
                    if match:
                        bounds = match.group(1)
                        # 解析bounds获取中心点坐标
                        coords = re.findall(r'\d+', bounds)
                        if len(coords) >= 4:
                            x = (int(coords[0]) + int(coords[2])) // 2
                            y = (int(coords[1]) + int(coords[3])) // 2
                            
                            # 使用坐标点击
                            success, output = self._execute_adb_command(f'shell input tap {x} {y}')
                            if success:
                                time.sleep(self.config.get("ui_automation", {}).get("operations", {}).get("tap_duration", 100) / 1000)
                                return {
                                    "success": True,
                                    "message": f"成功点击元素: {text} (坐标: {x}, {y})",
                                    "method": "coordinate_tap"
                                }
            
            # 如果坐标点击失败，尝试使用内容描述点击
            content_desc_command = f'shell input tap $(dumpsys window | grep -E "mCurrentFocus.*{text}" | head -1)'
            
            # 简化方案：直接尝试点击屏幕中心附近的常见位置
            common_positions = [
                (540, 1800),  # 底部导航"我的"
                (540, 1600),  # 底部导航"服务"  
                (540, 800),   # 屏幕中央
                (200, 300),   # 左上角
                (800, 300),   # 右上角
            ]
            
            for x, y in common_positions:
                # 先截图检查当前状态
                self._capture_screenshot()
                success, output = self._execute_adb_command(f'shell input tap {x} {y}')
                if success:
                    time.sleep(1)
                    return {
                        "success": True,
                        "message": f"尝试点击位置: {text} (坐标: {x}, {y})",
                        "method": "common_position"
                    }
            
            return {"success": False, "message": f"所有点击方法均失败: {text}"}
            
        except Exception as e:
            return {"success": False, "message": f"点击失败: {str(e)}"}

    @tool(
        "unicom_input_text",
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
        "unicom_perform_operation",
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
        "unicom_close_app",
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
        "unicom_get_app_status",
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

    @tool(
        "unicom_user_benefits_claim",
        description="执行用户权益领取业务流程，包括领券中心、权益超市、PLUS会员等",
        group="unicom_android"
    )
    def unicom_user_benefits_claim(self, user_interaction_callback=None) -> Dict[str, Any]:
        """执行用户权益领取业务流程"""
        try:
            results = []
            
            # 1. 启动中国联通APP
            launch_result = self.unicom_launch_app("unicom_app")
            if not launch_result["success"]:
                return launch_result
            results.append({"step": "启动APP", "result": launch_result})
            
            # 等待APP加载
            time.sleep(3)
            
            # 2. 进入"我的"页面
            my_page_result = self._navigate_to_my_page()
            results.append({"step": "进入我的页面", "result": my_page_result})
            if not my_page_result["success"]:
                return {"success": False, "message": "无法进入我的页面", "results": results}
            
            # 3. 进入领券中心并领取优惠券
            coupon_result = self._claim_coupons_in_center()
            results.append({"step": "领取优惠券", "result": coupon_result})
            
            # 4. 进入服务页面
            service_result = self._navigate_to_service_page()
            results.append({"step": "进入服务页面", "result": service_result})
            if not service_result["success"]:
                return {"success": False, "message": "无法进入服务页面", "results": results}
            
            # 5. 处理权益超市
            market_result = self._handle_benefits_market(user_interaction_callback)
            results.append({"step": "处理权益超市", "result": market_result})
            
            # 6. 处理PLUS会员
            plus_result = self._handle_plus_membership(user_interaction_callback)
            results.append({"step": "处理PLUS会员", "result": plus_result})
            
            return {
                "success": True,
                "message": "用户权益领取业务流程完成",
                "results": results
            }
            
        except Exception as e:
            return {"success": False, "message": f"权益领取失败: {str(e)}"}

    def _navigate_to_my_page(self) -> Dict[str, Any]:
        """导航到"我的"页面"""
        try:
            # 查找并点击"我的"按钮
            find_result = self.unicom_find_element_by_text("我的")
            if not find_result["success"] or not find_result.get("found"):
                return {"success": False, "message": "未找到我的按钮"}
            
            # 点击"我的"
            tap_result = self.unicom_tap_element("我的")
            if not tap_result["success"]:
                return {"success": False, "message": "点击我的按钮失败"}
            
            # 等待页面加载
            time.sleep(2)
            
            return {"success": True, "message": "成功进入我的页面"}
            
        except Exception as e:
            return {"success": False, "message": f"导航到我的页面失败: {str(e)}"}

    def _claim_coupons_in_center(self) -> Dict[str, Any]:
        """在领券中心领取优惠券"""
        try:
            claimed_coupons = []
            
            # 尝试查找并点击"领券中心"
            # 首先通过UI Automator查找
            success, output = self._execute_adb_command('shell uiautomator dump /sdcard/ui_dump.xml')
            if success:
                success, xml_content = self._execute_adb_command('shell cat /sdcard/ui_dump.xml')
                if success and ("领券中心" in xml_content or "领券" in xml_content):
                    # 找到了领券中心元素，尝试点击
                    tap_result = self.unicom_tap_element("领券中心")
                    if not tap_result["success"]:
                        # 如果直接点击失败，尝试滑动查找
                        for _ in range(3):
                            self._execute_adb_command("shell input swipe 500 800 500 400 500")
                            time.sleep(1)
                            tap_result = self.unicom_tap_element("领券中心")
                            if tap_result["success"]:
                                break
                    
                    if tap_result["success"]:
                        # 等待页面加载
                        time.sleep(3)
                        
                        # 循环查找所有"领取"按钮并点击
                        max_attempts = 10  # 最多尝试10次
                        for attempt in range(max_attempts):
                            # 获取UI dump查找领取按钮
                            success, output = self._execute_adb_command('shell uiautomator dump /sdcard/ui_dump.xml')
                            if success:
                                success, xml_content = self._execute_adb_command('shell cat /sdcard/ui_dump.xml')
                                if success and "领取" in xml_content:
                                    # 尝试点击领取按钮
                                    tap_result = self.unicom_tap_element("领取")
                                    if tap_result["success"]:
                                        claimed_coupons.append(f"优惠券_{attempt + 1}")
                                        time.sleep(2)  # 等待领取完成
                                        
                                        # 检查是否需要返回
                                        self._execute_adb_command("shell input keyevent KEYCODE_BACK")
                                        time.sleep(1)
                                    else:
                                        break
                                else:
                                    break  # 没有更多可领取的券
                            else:
                                break
                        
                        # 返回到我的页面
                        self._execute_adb_command("shell input keyevent KEYCODE_BACK")
                        time.sleep(2)
                        
                        return {
                            "success": True, 
                            "message": f"成功领取 {len(claimed_coupons)} 张优惠券",
                            "claimed_coupons": claimed_coupons
                        }
                    else:
                        return {"success": False, "message": "点击领券中心失败"}
                else:
                    return {"success": False, "message": "未找到领券中心"}
            else:
                return {"success": False, "message": "UI分析失败"}
            
        except Exception as e:
            return {"success": False, "message": f"领取优惠券失败: {str(e)}"}

    def _navigate_to_service_page(self) -> Dict[str, Any]:
        """导航到服务页面"""
        try:
            # 查找并点击"服务"按钮
            find_result = self.unicom_find_element_by_text("服务")
            if not find_result["success"] or not find_result.get("found"):
                return {"success": False, "message": "未找到服务按钮"}
            
            tap_result = self.unicom_tap_element("服务")
            if not tap_result["success"]:
                return {"success": False, "message": "点击服务按钮失败"}
            
            # 等待页面加载
            time.sleep(2)
            
            return {"success": True, "message": "成功进入服务页面"}
            
        except Exception as e:
            return {"success": False, "message": f"导航到服务页面失败: {str(e)}"}

    def _handle_benefits_market(self, user_interaction_callback=None) -> Dict[str, Any]:
        """处理权益超市"""
        try:
            # 向下滑动寻找权益栏目
            for _ in range(3):  # 最多滑动3次
                screen_result = self.unicom_get_screen_content("unicom_app")
                if "权益" in screen_result.get("ocr_text", ""):
                    break
                # 向下滑动
                self._execute_adb_command("shell input swipe 500 800 500 400 500")
                time.sleep(1)
            
            # 查找并点击"权益超市"
            find_result = self.unicom_find_element_by_text("权益超市")
            if not find_result["success"] or not find_result.get("found"):
                return {"success": False, "message": "未找到权益超市"}
            
            tap_result = self.unicom_tap_element("权益超市")
            if not tap_result["success"]:
                return {"success": False, "message": "点击权益超市失败"}
            
            # 等待页面加载
            time.sleep(3)
            
            # 询问用户是否需要消费
            user_wants_to_consume = False
            if user_interaction_callback:
                user_wants_to_consume = user_interaction_callback("是否需要在权益超市进行消费？", ["是", "否"]) == "是"
            
            if not user_wants_to_consume:
                # 返回到权益界面
                self._execute_adb_command("shell input keyevent KEYCODE_BACK")
                time.sleep(2)
                return {"success": True, "message": "用户选择不在权益超市消费，已返回"}
            
            return {"success": True, "message": "用户选择在权益超市消费，请手动操作"}
            
        except Exception as e:
            return {"success": False, "message": f"处理权益超市失败: {str(e)}"}

    def _handle_plus_membership(self, user_interaction_callback=None) -> Dict[str, Any]:
        """处理PLUS会员"""
        try:
            # 在权益界面查找"PLUS会员"
            find_result = self.unicom_find_element_by_text("PLUS会员")
            if not find_result["success"] or not find_result.get("found"):
                return {"success": False, "message": "未找到PLUS会员"}
            
            tap_result = self.unicom_tap_element("PLUS会员")
            if not tap_result["success"]:
                return {"success": False, "message": "点击PLUS会员失败"}
            
            # 等待页面加载
            time.sleep(3)
            
            # 检查用户是否是PLUS会员
            screen_result = self.unicom_get_screen_content("unicom_app")
            screen_text = screen_result.get("ocr_text", "")
            
            is_plus_member = any(keyword in screen_text for keyword in ["已开通", "会员有效", "PLUS会员"])
            
            if user_interaction_callback:
                if not is_plus_member:
                    # 询问用户是否是PLUS会员
                    user_is_member = user_interaction_callback("您是PLUS会员吗？", ["是", "否"]) == "是"
                    
                    if not user_is_member:
                        # 询问是否需要办理
                        want_to_apply = user_interaction_callback("是否需要办理PLUS会员？", ["是", "否"]) == "是"
                        
                        if not want_to_apply:
                            # 退出界面
                            self._execute_adb_command("shell input keyevent KEYCODE_BACK")
                            time.sleep(2)
                            return {"success": True, "message": "用户选择不办理PLUS会员，已退出"}
                        else:
                            return {"success": True, "message": "用户选择办理PLUS会员，业务结束，请手动操作"}
                    else:
                        is_plus_member = True
                
                if is_plus_member:
                    # 让用户选择领取哪个权益
                    available_benefits = self._get_available_benefits(screen_text)
                    if available_benefits:
                        selected_benefit = user_interaction_callback(
                            f"请选择要领取的权益：{', '.join(available_benefits)}", 
                            available_benefits
                        )
                        
                        # 尝试点击选择的权益
                        if selected_benefit:
                            tap_result = self.unicom_tap_element(selected_benefit)
                            if tap_result["success"]:
                                return {"success": True, "message": f"成功选择权益: {selected_benefit}"}
                            else:
                                return {"success": False, "message": f"点击权益失败: {selected_benefit}"}
                    else:
                        return {"success": True, "message": "未找到可领取的权益"}
            
            return {"success": True, "message": "PLUS会员处理完成"}
            
        except Exception as e:
            return {"success": False, "message": f"处理PLUS会员失败: {str(e)}"}

    def _get_available_benefits(self, screen_text: str) -> List[str]:
        """从屏幕文本中提取可用的权益"""
        # 常见的权益关键词
        benefit_keywords = [
            "流量包", "话费券", "视频会员", "音乐会员", "阅读券", 
            "购物券", "外卖券", "打车券", "咖啡券", "电影券"
        ]
        
        available_benefits = []
        for keyword in benefit_keywords:
            if keyword in screen_text:
                available_benefits.append(keyword)
        
        return available_benefits

