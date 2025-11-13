# CapsWriter-Offline Mac应用打包工具

本工具可以将CapsWriter-Offline打包成一个独立的Mac应用程序(.app)，用户可以双击运行，无需安装Python环境。

## 功能特性

- 🚀 **一键打包**: 自动处理所有依赖和资源文件
- 📦 **独立应用**: 生成的.app文件包含所有必要组件
- 💿 **DMG安装包**: 可选择创建DMG分发包
- 🔧 **自动配置**: 自动设置应用图标、权限和元数据
- ✅ **依赖检查**: 自动检查和安装必要的打包工具

## 系统要求

- macOS 10.13 或更高版本
- Python 3.8 或更高版本
- 足够的磁盘空间（至少1GB用于构建过程）

## 使用方法

### 方法一：使用Shell脚本（推荐）

```bash
# 在项目根目录下执行
./build_mac.sh

# 不创建DMG，只生成.app文件
./build_mac.sh --no-dmg

# 指定版本号
./build_mac.sh --version 2.0.0
```

### 方法二：直接使用Python脚本

```bash
# 基本打包（包含DMG）
python3 build_mac_app.py

# 只生成.app文件，不创建DMG
python3 build_mac_app.py --no-dmg

# 指定版本号
python3 build_mac_app.py --version 2.0.0
```

## 打包过程

1. **依赖检查**: 自动检查PyInstaller和其他必要依赖
2. **清理构建**: 清理之前的构建文件
3. **创建配置**: 生成PyInstaller配置文件
4. **应用构建**: 使用PyInstaller打包应用
5. **后处理**: 复制配置文件，设置权限
6. **DMG创建**: 可选创建DMG安装包

## 输出文件

打包完成后，在`dist`目录下会生成：

- `CapsWriter-Offline.app` - Mac应用程序包
- `CapsWriter-Offline-{version}.dmg` - DMG安装包（如果启用）

## 应用特性

### 应用信息
- **应用名称**: CapsWriter离线版
- **Bundle ID**: com.capswriter.offline
- **图标**: 使用项目中的appicon.ico
- **权限**: 包含麦克风访问等必要权限

### 包含的组件
- 统一启动器（start_unified.py）
- 服务端和客户端程序
- 所有工具脚本（util目录）
- AI代理服务（agent目录）
- 资源文件（assets目录）
- 配置文件和示例

## 使用打包后的应用

### 安装
1. 双击DMG文件（如果有）
2. 将CapsWriter-Offline.app拖拽到Applications文件夹
3. 或者直接双击.app文件运行

### 首次运行
1. 双击应用图标
2. 如果系统提示"无法打开"，请：
   - 右键点击应用 → 打开
   - 或在系统偏好设置 → 安全性与隐私中允许运行

### 配置
- 应用会在首次运行时创建必要的配置文件
- 配置文件位于应用包内，可通过应用界面修改

## 故障排除

### 常见问题

**Q: 打包失败，提示缺少依赖**
A: 确保已安装所有requirements.txt中的依赖：
```bash
pip install -r requirements.txt
```

**Q: 应用无法启动**
A: 检查以下几点：
- 确保macOS版本兼容（10.13+）
- 在系统偏好设置中允许应用运行
- 查看控制台应用中的错误日志

**Q: DMG创建失败**
A: 确保有足够的磁盘空间，或使用`--no-dmg`选项跳过DMG创建

**Q: 应用体积过大**
A: 这是正常的，因为包含了完整的Python运行时和所有依赖

### 调试模式

如果需要调试打包后的应用，可以：

1. 在终端中运行应用：
```bash
./dist/CapsWriter-Offline.app/Contents/MacOS/CapsWriter-Offline
```

2. 查看应用日志：
```bash
# 查看系统日志
log show --predicate 'process == "CapsWriter-Offline"' --last 1h

# 查看控制台应用
# 应用程序 → 实用工具 → 控制台
```

## 技术细节

### 打包工具
- **PyInstaller**: 主要打包工具
- **hdiutil**: 创建DMG文件
- **codesign**: 代码签名（可选）

### 应用结构
```
CapsWriter-Offline.app/
├── Contents/
│   ├── Info.plist          # 应用元数据
│   ├── MacOS/
│   │   ├── CapsWriter-Offline  # 主执行文件
│   │   ├── assets/         # 资源文件
│   │   ├── util/           # 工具脚本
│   │   ├── agent/          # AI代理
│   │   └── config files    # 配置文件
│   └── Resources/
│       └── appicon.ico     # 应用图标
```

### 性能优化
- 使用UPX压缩减小文件大小
- 排除不必要的模块
- 优化导入路径

## 分发说明

### 给最终用户
1. 提供DMG文件（推荐）或直接提供.app文件
2. 说明首次运行的安全设置步骤
3. 提供基本的使用说明

### 版本管理
- 使用`--version`参数指定版本号
- 版本号会显示在应用信息中
- DMG文件名包含版本号

## 更新日志

### v1.0.0
- 初始版本
- 支持统一启动器打包
- 包含完整的服务端和客户端功能
- 支持DMG创建
- 自动依赖检查和安装

---

**注意**: 此打包工具专为macOS设计。如需Windows或Linux版本，请使用相应的打包脚本。