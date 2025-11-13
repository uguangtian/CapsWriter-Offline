# CapsWriter-Offline 统一启动器

## 概述

统一启动器是一个新增的功能，允许用户通过单个命令同时启动 CapsWriter-Offline 的服务端和客户端，简化了使用流程。同时，它完全兼容原有的启动方式，不会影响现有的使用习惯。

## 功能特性

- ✅ **一键启动**：同时启动服务端和客户端
- ✅ **灵活模式**：支持仅启动服务端或客户端
- ✅ **后台模式**：支持无GUI的后台运行
- ✅ **跨平台**：支持 Windows、macOS 和 Linux
- ✅ **向下兼容**：不影响原有的启动方式
- ✅ **进程管理**：自动处理进程启动、监控和清理
- ✅ **错误处理**：完善的错误检查和用户友好的提示

## 使用方法

### Windows 用户

#### 方法1：使用批处理脚本（推荐）
```batch
# 统一启动服务端和客户端
start_unified.bat

# 仅启动服务端
start_unified.bat --server-only

# 仅启动客户端
start_unified.bat --client-only

# 后台模式启动
start_unified.bat --background

# 显示帮助信息
start_unified.bat --help
```

#### 方法2：直接使用Python脚本
```bash
python start_unified.py
python start_unified.py --server-only
python start_unified.py --client-only
python start_unified.py --background
```

### macOS/Linux 用户

#### 方法1：使用Shell脚本（推荐）
```bash
# 统一启动服务端和客户端
./start_unified.sh

# 仅启动服务端
./start_unified.sh --server-only

# 仅启动客户端
./start_unified.sh --client-only

# 后台模式启动
./start_unified.sh --background

# 显示帮助信息
./start_unified.sh --help
```

#### 方法2：直接使用Python脚本
```bash
python3 start_unified.py
python3 start_unified.py --server-only
python3 start_unified.py --client-only
python3 start_unified.py --background
```

## 参数说明

| 参数 | 说明 |
|------|------|
| 无参数 | 默认模式，同时启动服务端和客户端 |
| `--server-only` | 仅启动服务端 |
| `--client-only` | 仅启动客户端 |
| `--background` | 后台模式，启动核心功能但不显示GUI界面 |
| `--help` | 显示帮助信息 |
| `--version` | 显示版本信息 |

## 启动流程

1. **依赖检查**：检查必要的文件和Python环境
2. **进程检查**：检查是否已有相关进程在运行
3. **服务端启动**：启动服务端并等待就绪
4. **客户端启动**：启动客户端
5. **进程监控**：监控进程状态，处理异常退出
6. **清理退出**：用户中断时自动清理进程

## 兼容性说明

### 与原有启动方式的兼容性

统一启动器**完全兼容**原有的启动方式：

- 原有的 `start_server_gui.py` 和 `start_client_gui.py` 仍然可以正常使用
- 原有的 `core_server.py` 和 `core_client.py` 仍然可以正常使用
- 配置文件和所有功能保持不变
- 用户可以根据需要选择使用原有方式或新的统一启动器

### 进程冲突处理

- 如果检测到相关进程已在运行，会自动跳过启动
- 支持配置文件中的 `only_run_once` 设置
- 不会强制终止已运行的进程

## 故障排除

### 常见问题

1. **Python未找到**
   - 确保Python已正确安装
   - 确保Python已添加到系统PATH环境变量

2. **文件不存在错误**
   - 确保在CapsWriter-Offline项目根目录中运行脚本
   - 确保所有必要文件存在

3. **权限错误（macOS/Linux）**
   ```bash
   chmod +x start_unified.sh
   ```

4. **进程启动失败**
   - 检查端口是否被占用
   - 检查配置文件是否正确
   - 查看错误日志获取详细信息

### 调试模式

如果遇到问题，可以直接使用Python脚本获取更详细的错误信息：

```bash
python start_unified.py --help
python start_unified.py --server-only  # 单独测试服务端
python start_unified.py --client-only  # 单独测试客户端
```

## 文件结构

```
CapsWriter-Offline/
├── start_unified.py          # 统一启动器核心脚本
├── start_unified.bat         # Windows批处理脚本
├── start_unified.sh          # macOS/Linux Shell脚本
├── README_UNIFIED_LAUNCHER.md # 本说明文档
├── start_server_gui.py       # 原有服务端GUI启动器
├── start_client_gui.py       # 原有客户端GUI启动器
├── core_server.py            # 服务端核心
├── core_client.py            # 客户端核心
└── ...
```

## 更新日志

### v1.0 (2025-01-18)
- 初始版本发布
- 支持统一启动服务端和客户端
- 支持Windows、macOS、Linux跨平台
- 完整的错误处理和进程管理
- 向下兼容原有启动方式

## 技术实现

### 核心特性

- **进程管理**：使用subprocess模块管理子进程
- **信号处理**：正确处理Ctrl+C中断信号
- **跨平台兼容**：自动检测操作系统并使用相应的启动方式
- **错误恢复**：启动失败时自动清理已启动的进程
- **配置集成**：读取现有配置文件，遵循用户设置

### 安全考虑

- 不会强制终止用户进程
- 遵循现有的安全配置
- 提供清晰的用户反馈
- 支持优雅的退出机制

---

**注意**：统一启动器是一个可选功能，不会替代或影响原有的启动方式。用户可以根据自己的需求选择最适合的启动方法。