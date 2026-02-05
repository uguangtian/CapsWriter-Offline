#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CapsWriter-Offline Mac应用打包工具

此脚本将CapsWriter-Offline打包成一个独立的Mac应用程序(.app)
使用PyInstaller进行打包，生成的应用可以双击运行
"""

import os
import sys
import shutil
import subprocess
import json
from pathlib import Path

class MacAppBuilder:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.app_name = "CapsWriter-Offline"
        self.app_version = "1.0.0"
        
    def check_dependencies(self):
        """检查必要的依赖"""
        print("检查依赖...")
        
        # 检查PyInstaller
        try:
            import PyInstaller
            print(f"✓ PyInstaller已安装: {PyInstaller.__version__}")
        except ImportError:
            print("✗ PyInstaller未安装，正在安装...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
            print("✓ PyInstaller安装完成")
            
        # 检查其他必要依赖
        required_packages = [
            "PySide6",
            "websockets",
            "numpy",
            "sounddevice",
            "requests",
            "Pillow"
        ]
        
        for package in required_packages:
            try:
                if package == "PySide6":
                    import PySide6
                elif package == "sounddevice":
                    import sounddevice
                elif package == "Pillow":
                    import PIL
                else:
                    __import__(package.lower().replace("-", "_"))
                print(f"✓ {package}已安装")
            except ImportError:
                print(f"✗ {package}未安装，请先安装: pip install {package}")
                return False
                
        return True
    
    def create_spec_file(self):
        """创建PyInstaller spec文件"""
        print("创建spec文件...")
        
        spec_content = f'''
# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []
tmp_ret = collect_all('rich')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

block_cipher = None

# 主应用分析
a = Analysis(
    ['start_unified.py'],
    pathex=['{self.project_root}'],
    binaries=binaries,
    datas=datas + [
        ('assets', 'assets'),
        ('util', 'util'),
        ('agent', 'agent'),
        ('config_example.toml', '.'),
        ('config.toml', '.'),
        ('hot-*.txt', '.'),
        ('keywords.txt', '.'),
        ('README_UNIFIED_LAUNCHER.md', '.'),
        ('readme.md', '.'),
        ('requirements*.txt', '.'),
    ],
    hiddenimports=hiddenimports + [
        'PySide6.QtCore',
        'PySide6.QtWidgets', 
        'PySide6.QtGui',
        'PySide6.QtSvg',
        'websockets',
        'sounddevice',
        'numpy',
        'requests',
        'json',
        'asyncio',
        'threading',
        'multiprocessing',
        'signal',
        'pathlib',
        'argparse',
        'subprocess',
        'sys',
        'os',
        'time',
        'datetime',
        'logging',
        'traceback',
        'queue',
        'collections',
        'functools',
        'itertools',
        'contextlib',
        'weakref',
        'copy',
        'pickle',
        'base64',
        'hashlib',
        'hmac',
        'uuid',
        'random',
        'math',
        'statistics',
        're',
        'string',
        'textwrap',
        'unicodedata',
        'locale',
        'gettext',
        'calendar',
        'email',
        'mimetypes',
        'urllib',
        'http',
        'ftplib',
        'poplib',
        'imaplib',
        'smtplib',
        'socketserver',
        'xmlrpc',
        'xml',
        'html',
        'csv',
        'configparser',
        'fileinput',
        'glob',
        'fnmatch',
        'linecache',
        'tempfile',
        'gzip',
        'bz2',
        'lzma',
        'zipfile',
        'tarfile',
        'mlx',
        'mlx.core',
        'mlx.nn',
        'mlx_lm',
        'mlx_lm.models',
        'mlx_lm.utils',
        'mlx_lm.sample_utils',
        'mlx_lm.tokenizer_utils',
        'rich',
        'rich.console',
        'rich.live',
        'rich.panel',
        'rich.markdown',
        'rich.text',
        'rich.progress',
        'rich.table',
        'rich.logging',
        'rich.style',
        'rich.theme',
        'rich.syntax',
        'rich.align',
        'rich.box',
        'rich.padding',
        'rich._unicode_data',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{self.app_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 设置为终端应用
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/appicon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{self.app_name}',
)

app = BUNDLE(
    coll,
    name='{self.app_name}.app',
    icon=None,  # 暂时移除图标以避免格式问题
    bundle_identifier='com.capswriter.offline',
    version='{self.app_version}',
    info_plist={{
        'CFBundleName': '{self.app_name}',
        'CFBundleDisplayName': 'CapsWriter离线版',
        'CFBundleVersion': '{self.app_version}',
        'CFBundleShortVersionString': '{self.app_version}',
        'CFBundleIdentifier': 'com.capswriter.offline',
        'CFBundleExecutable': '{self.app_name}',
        # 'CFBundleIconFile': 'appicon.ico',  # 暂时注释掉图标文件
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': 'CWOF',
        'LSMinimumSystemVersion': '10.13.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'LSUIElement': False,  # 设置为普通应用，在 Dock 中显示
        'NSMicrophoneUsageDescription': 'CapsWriter需要访问麦克风进行语音识别',
        'NSAppleEventsUsageDescription': 'CapsWriter需要发送Apple Events来控制其他应用程序',
        'NSSystemAdministrationUsageDescription': 'CapsWriter需要系统管理权限来监控键盘输入',
    }},
)
'''
        
        spec_file = self.project_root / f"{self.app_name}.spec"
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
            
        print(f"✓ spec文件已创建: {spec_file}")
        return spec_file
    
    def clean_build_dirs(self):
        """清理构建目录"""
        print("清理构建目录...")
        
        for dir_path in [self.build_dir, self.dist_dir]:
            if dir_path.exists():
                try:
                    shutil.rmtree(dir_path)
                    print(f"✓ 已清理: {dir_path}")
                except OSError as e:
                    # 如果删除失败，尝试强制删除
                    import subprocess
                    try:
                        subprocess.run(["rm", "-rf", str(dir_path)], check=True)
                        print(f"✓ 已强制清理: {dir_path}")
                    except subprocess.CalledProcessError:
                        print(f"⚠ 无法清理目录: {dir_path}，继续构建...")
    
    def build_app(self, spec_file):
        """使用PyInstaller构建应用"""
        print("开始构建应用...")
        
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm", 
            str(spec_file)
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        
        try:
            # 不捕获输出，以便在控制台实时显示
            result = subprocess.run(cmd, cwd=self.project_root, check=True, 
                                  capture_output=False, text=True)
            print("✓ 构建成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ 构建失败: {e}")
            print(f"错误输出: {e.stderr}")
            return False
    
    def post_process(self):
        """后处理：复制额外文件和设置权限"""
        print("执行后处理...")
        
        app_path = self.dist_dir / f"{self.app_name}.app"
        if not app_path.exists():
            print(f"✗ 应用包不存在: {app_path}")
            return False
            
        # 复制配置文件到应用包内
        contents_path = app_path / "Contents" / "MacOS"
        
        # 复制配置示例文件
        config_files = [
            "config_example.toml",
            "chat_ui_config.json"
        ]
        
        for config_file in config_files:
            src = self.project_root / config_file
            if src.exists():
                dst = contents_path / config_file
                shutil.copy2(src, dst)
                print(f"✓ 已复制配置文件: {config_file}")
        
        # 设置执行权限
        executable_path = contents_path / self.app_name
        if executable_path.exists():
            os.chmod(executable_path, 0o755)
            print("✓ 已设置执行权限")
        
        print(f"✓ 应用包已创建: {app_path}")
        
        # 提示用户关于模型文件的信息
        print("\n" + "="*50)
        print("注意：模型文件(models目录)未包含在应用包中（因为体积过大）。")
        print("请手动将 models 目录复制到应用包内的 MacOS 目录下：")
        print(f"cp -r models {app_path}/Contents/MacOS/")
        print("="*50 + "\n")
        
        return True
    
    def create_dmg(self):
        """创建DMG安装包（可选）"""
        print("创建DMG安装包...")
        
        app_path = self.dist_dir / f"{self.app_name}.app"
        dmg_path = self.dist_dir / f"{self.app_name}-{self.app_version}.dmg"
        
        if dmg_path.exists():
            dmg_path.unlink()
        
        # 创建临时DMG目录
        dmg_temp_dir = self.dist_dir / "dmg_temp"
        if dmg_temp_dir.exists():
            shutil.rmtree(dmg_temp_dir)
        dmg_temp_dir.mkdir()
        
        # 复制应用到临时目录
        shutil.copytree(app_path, dmg_temp_dir / f"{self.app_name}.app")
        
        # 创建应用程序文件夹的符号链接
        applications_link = dmg_temp_dir / "Applications"
        applications_link.symlink_to("/Applications")
        
        # 使用hdiutil创建DMG
        cmd = [
            "hdiutil", "create",
            "-volname", self.app_name,
            "-srcfolder", str(dmg_temp_dir),
            "-ov", "-format", "UDZO",
            str(dmg_path)
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print(f"✓ DMG已创建: {dmg_path}")
            
            # 清理临时目录
            shutil.rmtree(dmg_temp_dir)
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ DMG创建失败: {e}")
            return False
    
    def build(self, create_dmg=True):
        """执行完整的构建流程"""
        print(f"开始构建 {self.app_name} Mac应用...")
        print("=" * 50)
        
        # 检查依赖
        if not self.check_dependencies():
            print("✗ 依赖检查失败")
            return False
        
        # 清理构建目录
        self.clean_build_dirs()
        
        # 创建spec文件
        spec_file = self.create_spec_file()
        
        # 构建应用
        if not self.build_app(spec_file):
            print("✗ 应用构建失败")
            return False
        
        # 后处理
        if not self.post_process():
            print("✗ 后处理失败")
            return False
        
        # 创建DMG（可选）
        if create_dmg:
            self.create_dmg()
        
        print("=" * 50)
        print(f"✓ 构建完成！")
        print(f"应用位置: {self.dist_dir / f'{self.app_name}.app'}")
        if create_dmg:
            dmg_path = self.dist_dir / f"{self.app_name}-{self.app_version}.dmg"
            if dmg_path.exists():
                print(f"DMG位置: {dmg_path}")
        
        return True

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CapsWriter-Offline Mac应用打包工具")
    parser.add_argument("--no-dmg", action="store_true", help="不创建DMG安装包")
    parser.add_argument("--version", default="1.0.0", help="应用版本号")
    
    args = parser.parse_args()
    
    builder = MacAppBuilder()
    builder.app_version = args.version
    
    success = builder.build(create_dmg=not args.no_dmg)
    
    if success:
        print("\n🎉 打包成功！")
        print("\n使用说明:")
        print("1. 双击 .app 文件即可运行应用")
        print("2. 首次运行可能需要在系统偏好设置中允许运行")
        print("3. 如果创建了DMG，可以分发DMG文件给其他用户")
        sys.exit(0)
    else:
        print("\n❌ 打包失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()