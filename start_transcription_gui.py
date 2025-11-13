#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动图形化转录工具
"""

import sys
import os
from pathlib import Path

# 确保当前目录在Python路径中
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 设置工作目录
os.chdir(current_dir)

def main():
    """主函数"""
    try:
        # 检查依赖
        try:
            from PySide6.QtWidgets import QApplication
        except ImportError:
            print("错误: 缺少PySide6依赖")
            print("请安装依赖: pip install PySide6")
            input("按回车键退出...")
            return
        
        # 检查核心文件
        core_client_path = current_dir / "core_client.py"
        if not core_client_path.exists():
            print(f"错误: 找不到核心转录文件 {core_client_path}")
            print("请确保在CapsWriter-Offline项目根目录下运行此程序")
            input("按回车键退出...")
            return
        
        # 导入并运行GUI
        from transcription_gui import main as gui_main
        gui_main()
        
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")

if __name__ == "__main__":
    main()