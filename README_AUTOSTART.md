# CapsWriter-Offline 开机自启动设置指南

本指南介绍如何在 macOS 系统上设置 CapsWriter-Offline 开机自启动功能。

## 快速开始

### 设置开机自启动

```bash
# 在项目根目录执行
./create_autostart.sh
```

### 移除开机自启动

```bash
# 在项目根目录执行
./remove_autostart.sh
```

## 详细说明

### 工作原理

开机自启动功能通过 macOS 的 LaunchAgent 机制实现：

1. **LaunchAgent 配置文件**：创建 `~/Library/LaunchAgents/com.capswriter.offline.plist`
2. **自动启动**：用户登录时系统自动加载并运行 CapsWriter-Offline
3. **后台运行**：应用在后台运行，不会显示终端窗口
4. **日志记录**：运行日志保存到 `~/Library/Logs/` 目录

### 配置文件位置

- **LaunchAgent 配置**：`~/Library/LaunchAgents/com.capswriter.offline.plist`
- **标准输出日志**：`~/Library/Logs/CapsWriter-Offline.log`
- **错误输出日志**：`~/Library/Logs/CapsWriter-Offline-error.log`

### 手动管理命令

```bash
# 查看 LaunchAgent 状态
launchctl list | grep com.capswriter.offline

# 手动启动服务
launchctl load ~/Library/LaunchAgents/com.capswriter.offline.plist

# 手动停止服务
launchctl unload ~/Library/LaunchAgents/com.capswriter.offline.plist

# 查看服务详细信息
launchctl print gui/$(id -u)/com.capswriter.offline
```

### 日志查看

```bash
# 查看标准输出日志
tail -f ~/Library/Logs/CapsWriter-Offline.log

# 查看错误日志
tail -f ~/Library/Logs/CapsWriter-Offline-error.log

# 查看最近的日志
cat ~/Library/Logs/CapsWriter-Offline.log | tail -50
```

## 故障排除

### 常见问题

1. **权限问题**
   ```bash
   # 确保脚本有执行权限
   chmod +x create_autostart.sh remove_autostart.sh
   ```

2. **LaunchAgent 未加载**
   ```bash
   # 手动加载
   launchctl load ~/Library/LaunchAgents/com.capswriter.offline.plist
   ```

3. **应用启动失败**
   ```bash
   # 检查错误日志
   cat ~/Library/Logs/CapsWriter-Offline-error.log
   ```

4. **虚拟环境问题**
   - 确保 `python3` 虚拟环境目录存在
   - 确保 `launch_in_terminal.sh` 脚本能正常运行

### 调试步骤

1. **测试启动脚本**
   ```bash
   # 手动测试启动脚本
   ./launch_in_terminal.sh
   ```

2. **检查 LaunchAgent 状态**
   ```bash
   launchctl list | grep com.capswriter.offline
   ```

3. **查看系统日志**
   ```bash
   log show --predicate 'subsystem == "com.apple.launchd"' --last 1h | grep capswriter
   ```

## 安全考虑

- **用户级服务**：LaunchAgent 运行在用户级别，不需要管理员权限
- **沙盒限制**：遵循 macOS 安全机制，不会影响系统稳定性
- **日志记录**：所有运行日志都会记录，便于问题排查
- **优雅退出**：支持正常的进程终止和清理

## 与其他启动方式的关系

### 兼容性

- **完全兼容**：不影响手动启动方式
- **独立运行**：可以与手动启动的实例共存
- **配置共享**：使用相同的配置文件和设置

### 启动优先级

1. **开机自启动**：用户登录时自动启动
2. **手动启动**：用户手动运行启动脚本
3. **终端启动器**：双击 `.app` 文件启动

## 卸载说明

完全移除开机自启动功能：

```bash
# 1. 运行移除脚本
./remove_autostart.sh

# 2. 确认文件已删除
ls ~/Library/LaunchAgents/com.capswriter.offline.plist

# 3. 清理日志文件（可选）
rm ~/Library/Logs/CapsWriter-Offline*.log
```

## 更新说明

当 CapsWriter-Offline 更新时：

1. **无需重新设置**：LaunchAgent 配置会自动使用新版本
2. **路径保持不变**：只要项目目录不变，配置继续有效
3. **重新设置**：如果项目目录改变，需要重新运行 `create_autostart.sh`

---

**注意**：开机自启动功能仅在 macOS 系统上可用。Windows 和 Linux 系统请参考相应的系统文档设置开机自启动。