"""
通用型AI助手主入口
Universal AI Assistant Main Entry

中国联通挑战杯比赛 - 基于多智能体架构的通用型AI助手
"""

import sys
import time
import signal
import argparse
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from .universal_ai_assistant import universal_ai_assistant, run_universal_assistant

console = Console()
interrupt_counter = 0


def signal_handler(sig, frame):
    """处理中断信号"""
    global interrupt_counter
    interrupt_counter += 1

    if interrupt_counter >= 3:
        console.print(Panel(
            Align.center("程序已强制退出"),
            border_style="red",
            title="[bold red]退出[/bold red]"
        ))
        time.sleep(1)
        console.clear()
        sys.exit(1)
    else:
        console.print(f"⚠️ 再按 {3 - interrupt_counter} 次 Ctrl+C 强制退出")
        return


def parse_args() -> argparse.Namespace:
    """
    解析命令行参数
    
    Returns:
        解析后的命令行参数
    """
    parser = argparse.ArgumentParser(
        description="通用型AI助手 - 基于多智能体架构的APP自动化操作系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s "帮我查询联通话费余额" --device emulator-5554
  %(prog)s "在微信上回复'好的'" --device phone_001
  %(prog)s "帮我在淘宝上搜索手机" --async
  %(prog)s --interactive  # 交互式模式
        """
    )
    
    # 主要参数
    parser.add_argument(
        "command",
        nargs="?",
        help="用户的自然语言指令"
    )
    
    # 设备配置
    parser.add_argument(
        "--device",
        "--device-id",
        dest="device_id",
        help="Android设备ID (通过 adb devices 查看)"
    )
    
    # 执行模式
    parser.add_argument(
        "--async",
        dest="use_async",
        action="store_true",
        help="使用异步模式执行"
    )
    
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="启动交互式模式"
    )
    
    # 输出配置
    parser.add_argument(
        "--output",
        choices=["simple", "detailed", "json"],
        default="simple",
        help="输出格式 (默认: simple)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    
    # 功能选项
    parser.add_argument(
        "--list-apps",
        action="store_true",
        help="列出设备上的已安装应用"
    )
    
    parser.add_argument(
        "--check-device",
        action="store_true", 
        help="检查设备连接状态"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="通用型AI助手 v1.0.0 - 中国联通挑战杯版本"
    )
    
    return parser.parse_args()


def print_welcome():
    """打印欢迎信息"""
    welcome_text = """
🤖 通用型AI助手

基于多智能体架构的APP自动化操作系统
支持自然语言指令，智能操作各种移动应用

✨ 主要功能:
  📱 中国联通APP自动化操作 (话费查询、权益领取等)
  💬 社交应用消息处理 (微信、QQ等)
  🛒 购物应用自动操作 (淘宝、京东等)
  🗺️ 出行应用路线规划 (高德、滴滴等)
  🎵 娱乐应用智能控制 (音乐、视频等)

🔧 技术特点:
  🧠 多模态大模型理解
  🤝 多智能体协作
  🔧 自动化工具调用
  🔒 安全操作控制
"""
    
    console.print(Panel(
        welcome_text,
        border_style="bright_blue",
        title="[bold bright_blue]欢迎使用[/bold bright_blue]",
        padding=(1, 2)
    ))


def print_result(result: dict, output_format: str = "simple"):
    """
    打印执行结果
    
    Args:
        result: 执行结果字典
        output_format: 输出格式
    """
    if output_format == "json":
        import json
        console.print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    # 简单格式输出
    console.print("\n" + "="*60)
    console.print("🤖 [bold]AI助手执行结果[/bold]")
    console.print("="*60)
    
    if result.get("success"):
        console.print("✅ [green]执行状态: 成功[/green]")
        
        # 基本信息
        console.print(f"💬 用户指令: {result.get('user_input', 'N/A')}")
        console.print(f"📱 目标应用: {result.get('target_app', 'N/A')}")
        console.print(f"📂 任务分类: {result.get('task_category', 'N/A')}")
        console.print(f"🔢 执行步骤: {result.get('execution_steps', 0)} 步")
        
        # 用户反馈
        if result.get("user_response"):
            console.print(f"\n📄 [bold]操作结果:[/bold]")
            console.print(f"   {result['user_response']}")
        
        # 详细模式
        if output_format == "detailed":
            console.print(f"\n🔍 [bold]详细信息:[/bold]")
            console.print(f"   会话ID: {result.get('session_id', 'N/A')}")
            console.print(f"   执行时间: {result.get('timestamp', 'N/A')}")
            
            if "result" in result:
                console.print(f"   验证结果: {result['result']}")
    else:
        console.print("❌ [red]执行状态: 失败[/red]")
        console.print(f"❌ 错误信息: {result.get('error', 'Unknown error')}")
        
        if result.get('session_id'):
            console.print(f"🔍 会话ID: {result['session_id']}")
    
    console.print("="*60)


async def interactive_mode():
    """交互式模式"""
    print_welcome()
    console.print("\n💡 [yellow]提示: 输入 'quit' 或 'exit' 退出程序[/yellow]\n")
    
    while True:
        try:
            # 获取用户输入
            user_input = console.input("[bold cyan]📱 请输入您的指令: [/bold cyan]")
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                console.print(Panel(
                    Align.center("感谢使用通用型AI助手！"),
                    border_style="green",
                    title="[bold green]再见[/bold green]"
                ))
                break
            
            if not user_input.strip():
                continue
            
            # 执行指令
            console.print("🔄 [yellow]正在处理您的指令...[/yellow]")
            
            result = await run_universal_assistant(user_input)
            print_result(result, "simple")
            
            console.print("\n" + "-"*40 + "\n")
            
        except KeyboardInterrupt:
            console.print("\n⚠️ [yellow]操作被中断[/yellow]")
            continue
        except Exception as e:
            console.print(f"\n❌ [red]处理异常: {str(e)}[/red]")


def check_device_connection(device_id: str = None):
    """检查设备连接"""
    try:
        from .tool.app_automation_tools import AppAutomationTools
        tools = AppAutomationTools()
        
        console.print("🔍 [yellow]正在检查设备连接...[/yellow]")
        
        # 获取已安装应用列表来测试连接
        result = tools.get_installed_apps(device_id)
        
        console.print("\n" + "="*50)
        console.print("📱 [bold]设备连接检查[/bold]")
        console.print("="*50)
        
        if result["success"]:
            console.print("✅ [green]设备连接: 正常[/green]")
            console.print(f"📱 设备ID: {result.get('device_id', 'default')}")
            console.print(f"📦 已安装应用: {len(result.get('apps', []))} 个")
            
            if result.get('apps'):
                console.print("\n📋 [bold]部分已安装应用:[/bold]")
                for i, app in enumerate(result['apps'][:10]):
                    console.print(f"   {i+1}. {app}")
                
                if len(result['apps']) > 10:
                    console.print(f"   ... 还有 {len(result['apps']) - 10} 个应用")
        else:
            console.print("❌ [red]设备连接: 失败[/red]")
            console.print(f"❌ 错误信息: {result.get('message', 'Unknown error')}")
        
        console.print("="*50)
        
    except Exception as e:
        console.print(f"❌ [red]设备检查异常: {str(e)}[/red]")


def list_installed_apps(device_id: str = None):
    """列出已安装应用"""
    try:
        from .tool.app_automation_tools import AppAutomationTools
        tools = AppAutomationTools()
        
        console.print("📱 [yellow]正在获取已安装应用列表...[/yellow]")
        result = tools.get_installed_apps(device_id)
        
        if result["success"]:
            apps = result.get('apps', [])
            
            console.print(f"\n📦 [bold]已安装应用列表 (共 {len(apps)} 个):[/bold]")
            console.print("="*60)
            
            for i, app in enumerate(apps, 1):
                console.print(f"{i:3d}. {app}")
            
            console.print("="*60)
        else:
            console.print(f"❌ [red]获取应用列表失败: {result.get('message', 'Unknown error')}[/red]")
            
    except Exception as e:
        console.print(f"❌ [red]获取应用列表异常: {str(e)}[/red]")


async def main():
    """主函数"""
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    
    args = parse_args()
    
    # 特殊命令处理
    if args.check_device:
        check_device_connection(args.device_id)
        return
    
    if args.list_apps:
        list_installed_apps(args.device_id)
        return
    
    # 交互式模式
    if args.interactive:
        await interactive_mode()
        return
    
    # 命令行模式
    if not args.command:
        print_welcome()
        console.print("[yellow]💡 提示: 请提供指令或使用 --interactive 进入交互模式[/yellow]")
        console.print("[yellow]💡 使用 --help 查看帮助信息[/yellow]")
        return
    
    try:
        console.print(f"🚀 [bold]正在执行指令:[/bold] {args.command}")
        
        if args.use_async:
            result = await run_universal_assistant(args.command, args.device_id)
        else:
            result = universal_ai_assistant(args.command, args.device_id)
        
        print_result(result, args.output)
        
    except KeyboardInterrupt:
        console.print("\n⚠️ [yellow]操作被用户中断[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n❌ [red]执行异常: {str(e)}[/red]")
        if args.verbose:
            import traceback
            console.print("[red]" + traceback.format_exc() + "[/red]")
        sys.exit(1)


def entry():
    """CLI入口点"""
    asyncio.run(main())


if __name__ == "__main__":
    entry()