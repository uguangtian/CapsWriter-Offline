# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
from rich import inspect
from pprint import pprint
from os.path import join, basename, dirname, exists
from os import walk, makedirs, sep
from shutil import copyfile, rmtree

# 初始化空列表
binaries = []
hiddenimports = ['keyboard', 'sounddevice', 'websockets', 'rich', 'appdirs', 'pkg_resources.py2_warn']  # 添加 appdirs
datas = []

# 额外复制动态库
modules = ['onnxruntime', 'numpy', 'sounddevice', 'pkg_resources']  # 添加 pkg_resources
for module in modules: 
    tmp_ret = collect_all(module)
    binaries += tmp_ret[1]
    datas += tmp_ret[0]
    hiddenimports += tmp_ret[2]

# 添加 Analysis 部分
a_1 = Analysis(
    ['core_server.py'],
    pathex=['/Users/anker/data/python/CapsWriter-Offline-GUI-v2.0.4/python3.11/lib/python3.11/site-packages'],  # 添加虚拟环境路径
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['build_hook.py'],
    excludes=['IPython', 'PIL', 
              'PySide6', 'PySide2', 'PyQt5', 
              'matplotlib', 'wx', 
              'funasr', 'pydantic', 'torch', 
              ],
    noarchive=False,
)

a_2 = Analysis(
    ['core_client.py'],
    pathex=['/Users/anker/data/python/CapsWriter-Offline-GUI-v2.0.4/python3.11/lib/python3.10/site-packages'],  # 添加虚拟环境路径
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['build_hook.py'],
    excludes=['IPython', 'PIL', 
              'PySide6', 'PySide2', 'PyQt5', 
              'matplotlib', 'wx', 
              ],
    noarchive=False,
)

# 排除不要打包的模块
private_module = ['util', 'config', 
                  'core_server', 
                  'core_client', 
                  ]
pure = a_1.pure.copy()
a_1.pure.clear()
for name, src, type in pure:
    condition = [name == m or name.startswith(m + '.') for m in private_module]
    if condition and any(condition):
        ...
    else:
        a_1.pure.append((name, src, type))

pure = a_2.pure.copy()
a_2.pure.clear()
for name, src, type in pure:
    condition = [name == m or name.startswith(m + '.') for m in private_module]
    if condition and any(condition):
        ...
    else:
        a_2.pure.append((name, src, type))

# 添加 PYZ 部分
pyz_1 = PYZ(a_1.pure)
pyz_2 = PYZ(a_2.pure)

# 修改图标路径为 macOS 格式
exe_1 = EXE(
    pyz_1,
    a_1.scripts,
    [],
    exclude_binaries=True,
    name='core_server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=True,  # 为 macOS 启用参数模拟
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icon.icns'],  # 修改为 macOS 图标格式
    contents_directory='internal',
)

exe_2 = EXE(
    pyz_2,
    a_2.scripts,
    [],
    exclude_binaries=True,
    name='core_client',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=True,  # 为 macOS 启用参数模拟
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icon.icns'],  # 修改为 macOS 图标格式
    contents_directory='internal',
)

# 添加 COLLECT 部分
coll = COLLECT(
    exe_1,
    exe_2,
    a_1.binaries,
    a_1.datas,
    a_2.binaries,
    a_2.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CapsWriter',
)

# 定义要复制的文件和文件夹
my_files = ['config.py', 
            'core_server.py', 
            'core_client.py', 
            'hot-en.txt', 'hot-zh.txt', 'hot-rule.txt', 'keywords.txt', 
            'readme.md',
            'requirements.txt']  # 添加依赖文件
my_folders = ['assets', 'util']

# 文件复制部分
dest_root = join('dist', basename(coll.name))

# 复制文件
for folder in my_folders:
    for dirpath, dirnames, filenames in walk(folder):
        for filename in filenames:
            my_files.append(join(dirpath, filename))
for file in my_files:
    if not exists(file):
        continue
    dest_file = join(dest_root, file)
    dest_folder = dirname(dest_file)
    makedirs(dest_folder, exist_ok=True)
    copyfile(file, dest_file)

# 为 models 文件夹创建符号链接（macOS 方式）
from platform import system
from subprocess import run
if system() == 'Darwin':  # macOS 系统
    link_folders = ['models', 'util']
    for folder in link_folders:
        if not exists(folder):
            continue
        dest_folder = join(dest_root, folder)
        if exists(dest_folder):
            rmtree(dest_folder)
        cmd = ['ln', '-s', folder, dest_folder]
        run(cmd)
