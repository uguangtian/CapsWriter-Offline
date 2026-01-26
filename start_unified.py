#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CapsWriter-Offline 统一启动器

这个脚本提供了一键启动服务端和客户端的功能，同时保持与原有启动方式的兼容性。

使用方法:
1. 统一启动模式: python start_unified.py
2. 仅启动服务端: python start_unified.py --server-only
3. 仅启动客户端: python start_unified.py --client-only
4. 后台模式: python start_unified.py --background
"""

import argparse
import os
import subprocess
import sys
import time
import threading
from pathlib import Path

from util.check_process import check_process
from util.config import ServerConfig, ClientConfig


class UnifiedLauncher:
    def __init__(self):
        self.server_process = None
        self.client_process = None
        self.background_mode = False
        
    def check_dependencies(self):
        """检查必要的依赖文件是否存在"""
        required_files = [
            "core_server.py",
            "start_server_gui.py", 
            "start_client_gui.py"
        ]
        
        missing_files = []
        for file in required_files:
            if not Path(file).exists():
                missing_files.append(file)
                
        if missing_files:
            print(f"错误：缺少必要文件: {', '.join(missing_files)}")
            return False
            
        return True
        
    def start_server(self, gui_mode=True):
        """启动服务端"""
        print("正在启动服务端...")
        
        # 检查是否已有服务端在运行
        if ServerConfig.only_run_once and check_process("pythonw_CapsWriter_Server.exe"):
            print("检测到服务端已在运行，跳过启动")
            return True
            
        try:
            # 在 macOS/Linux 上默认使用核心版本，在 Windows 上可以选择 GUI 版本
            if gui_mode and not self.background_mode and sys.platform == "win32":
                # 启动GUI版本的服务端（仅Windows）
                self.server_process = subprocess.Popen(
                    ["python", "start_server_gui.py"]
                )
            else:
                # 启动核心服务端（无GUI）
                if sys.platform == "win32":
                    self.server_process = subprocess.Popen(
                        ["python", "core_server.py"],
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                else:
                    self.server_process = subprocess.Popen(["python3", "core_server.py"])
                    
            print("服务端启动成功")
            return True
            
        except Exception as e:
            print(f"服务端启动失败: {e}")
            return False
            
    def start_client(self, gui_mode=True):
        """启动客户端"""
        print("正在启动客户端...")
        
        # 检查是否已有客户端在运行
        if check_process("start_client_gui.exe") or check_process("start_client_gui_admin.exe"):
            print("检测到客户端已在运行，跳过启动")
            return True
            
        try:
            # 在 macOS/Linux 上默认使用核心版本，在 Windows 上可以选择 GUI 版本
            if gui_mode and sys.platform == "win32":
                # 启动GUI版本的客户端（仅Windows）
                self.client_process = subprocess.Popen(
                    ["python", "start_client_gui.py"],
                    creationflags=subprocess.CREATE_NO_WINDOW if self.background_mode else 0
                )
            else:
                # 启动核心客户端（无GUI）
                if sys.platform == "win32":
                    self.client_process = subprocess.Popen(
                        ["python", "core_client.py"],
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                else:
                    self.client_process = subprocess.Popen(["python3", "core_client.py"])
                    
            print("客户端启动成功")
            return True
            
        except Exception as e:
            print(f"客户端启动失败: {e}")
            return False
            
    def wait_for_server_ready(self, timeout=30):
        """等待服务端就绪"""
        print("等待服务端就绪...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # 这里可以添加检查服务端是否就绪的逻辑
            # 比如检查端口是否开放，或者检查特定的进程状态
            time.sleep(1)
            if self.server_process and self.server_process.poll() is not None:
                print("服务端进程异常退出")
                return False
                
        print("服务端就绪")
        return True
        
    def cleanup(self):
        """清理进程"""
        print("正在清理进程...")
        
        if self.client_process:
            try:
                self.client_process.terminate()
                self.client_process.wait(timeout=5)
            except:
                if self.client_process.poll() is None:
                    self.client_process.kill()
                    
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except:
                if self.server_process.poll() is None:
                    self.server_process.kill()
                    
        print("清理完成")
        
    def run_unified(self, server_only=False, client_only=False, background=False):
        """统一启动模式"""
        self.background_mode = background
        
        if not self.check_dependencies():
            return False
            
        try:
            if not client_only:
                # 启动服务端
                if not self.start_server(gui_mode=not background):
                    return False
                    
                # 等待服务端就绪
                if not server_only:
                    self.wait_for_server_ready()
                    
            if not server_only:
                # 启动客户端
                if not self.start_client(gui_mode=not background):
                    if not client_only:
                        self.cleanup()
                    return False
                    
            if not background:
                print("\n=== CapsWriter-Offline 统一启动器 ===")
                print("服务端和客户端已启动")
                print("按 Ctrl+C 退出")
                print("==============================\n")
                
                try:
                    # 等待进程结束或用户中断
                    while True:
                        if self.server_process and self.server_process.poll() is not None:
                            print("服务端进程已退出")
                            break
                        if self.client_process and self.client_process.poll() is not None:
                            print("客户端进程已退出")
                            break
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n收到中断信号，正在退出...")
                    
            return True
            
        except Exception as e:
            print(f"启动过程中发生错误: {e}")
            return False
        finally:
            if not background:
                self.cleanup()


def main():
    parser = argparse.ArgumentParser(
        description="CapsWriter-Offline 统一启动器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python start_unified.py                    # 统一启动服务端和客户端
  python start_unified.py --server-only      # 仅启动服务端
  python start_unified.py --client-only      # 仅启动客户端
  python start_unified.py --background       # 后台模式启动
  python start_unified.py --help             # 显示帮助信息
        """
    )
    
    parser.add_argument(
        "--server-only", 
        action="store_true", 
        help="仅启动服务端"
    )
    parser.add_argument(
        "--client-only", 
        action="store_true", 
        help="仅启动客户端"
    )
    parser.add_argument(
        "--background", 
        action="store_true", 
        help="后台模式启动（无GUI界面）"
    )
    parser.add_argument(
        "--version", 
        action="version", 
        version="CapsWriter-Offline 统一启动器 v1.0"
    )
    
    args = parser.parse_args()
    
    # 检查参数冲突
    if args.server_only and args.client_only:
        print("错误：--server-only 和 --client-only 不能同时使用")
        sys.exit(1)
        
    launcher = UnifiedLauncher()
    
    try:
        success = launcher.run_unified(
            server_only=args.server_only,
            client_only=args.client_only,
            background=args.background
        )
        
        if success:
            print("启动完成")
            sys.exit(0)
        else:
            print("启动失败")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n用户中断")
        launcher.cleanup()
        if getattr(sys, 'frozen', False):
            input("按回车键退出...")
        sys.exit(0)
    except Exception as e:
        print(f"未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        launcher.cleanup()
        if getattr(sys, 'frozen', False):
            input("按回车键退出...")
        sys.exit(1)


if __name__ == "__main__":
    main()