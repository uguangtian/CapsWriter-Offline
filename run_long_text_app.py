#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
长文本处理应用启动脚本
集成到CapsWriter离线工具套件中
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from long_text_gui import main

if __name__ == "__main__":
    main()