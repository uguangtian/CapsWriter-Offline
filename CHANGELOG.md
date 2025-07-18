# 更新日志 (CHANGELOG)

## [2025-01-18 14:30] - 音频任务队列调试日志增强

### 增强功能
- **队列调试日志增强**: 为 `util/server_init_recognizer.py` 中的 `queue_in.get(timeout=1)` 问题添加详细调试日志
  - **问题分析**: 用户反映在第109-118行拿不到数据，需要分析数据流向和队列状态
  - **解决方案**: 添加全面的调试日志系统，包括连接状态、队列大小、任务提交等关键信息
  - **修改文件**: 
    - `util/server_init_recognizer.py`: 增加队列状态、连接数量、异常类型等详细日志
    - `util/server_ws_recv.py`: 增加任务提交、连接建立/断开等关键节点的日志

### 技术细节
1. **server_init_recognizer.py**:
   - 增加活跃连接数和连接ID列表的显示
   - 添加队列大小检查（如果支持）
   - 将超时时间从1秒增加到3秒，减少无意义的超时日志
   - 区分超时异常和其他异常类型，提供更精确的错误信息

2. **server_ws_recv.py**:
   - 在任务提交到队列前后添加确认日志
   - 增强WebSocket连接建立和断开的日志记录
   - 添加连接清理逻辑的详细日志
   - 显示当前活跃连接数变化

### 调试信息
- 实时显示队列状态和连接状态
- 追踪音频任务从接收到处理的完整流程
- 提供异常类型和详细错误信息
- 监控WebSocket连接的生命周期

## [2025-01-18] - WebSocket Connection Status Check Fix (Additional)

### Fixed
- **AttributeError in Audio Sending**: Fixed `AttributeError: 'ClientConnection' object has no attribute 'closed'` in `util/client_send_audio.py`
  - **Root Cause**: Same API change in `websockets` version 15.0.1 affecting another file
  - **Solution**: Applied the same fix as previous - replaced `Cosmic.websocket.closed` with comprehensive connection state checking
  - **Files Modified**: `util/client_send_audio.py`

### Technical Details
- Updated `send_message` function and `heartbeat` function to use `hasattr()` checks for both `state` and `closed` attributes
- Ensures compatibility with both old and new versions of the `websockets` library
- Prevents task exceptions during audio data transmission and heartbeat operations
- Fixed multiple instances of `websocket.closed` usage in the same file

## [2025-01-18] - File Permission Error Fix

### Fixed
- **Permission Denied Error**: Fixed `[Errno 13] Permission denied` error when creating audio recording files
  - **Root Cause**: `create_file` function used relative path (`Path() / time_year / time_month / "assets"`) which could fail if current working directory is not writable
  - **Solution**: Changed to use absolute path based on project root directory (`Path(__file__).parent.parent`)
  - **Files Modified**: `util/client_create_file.py`

### Technical Details
- Updated file path generation to use `Path(__file__).parent.parent` to get project root directory
- Ensures audio files are always created in the correct project directory regardless of current working directory
- Prevents permission errors when running the application from different locations

---

## [2025-07-18] - WebSocket连接问题修复

### 新增修复 (第二轮)
- **WebSocket客户端连接状态检查错误** - 修复了`AttributeError: 'ClientConnection' object has no attribute 'closed'`错误
- **websockets 15.0.1 API兼容性** - 更新了客户端连接状态检查逻辑以适配新版本API

### 技术细节 (第二轮)
3. **util/client_check_websocket.py**:
   - 将`Cosmic.websocket.closed`替换为`Cosmic.websocket.state.name == 'OPEN'`检查
   - 添加了`hasattr()`检查以确保属性存在
   - 增强了异常处理机制，避免连接状态检查时的崩溃

---

## [2025-07-18] - WebSocket连接问题修复 (第一轮)

### 修复的问题
- **WebSocket服务器启动失败** - 修复了websockets 15.0.1版本兼容性问题
- **事件循环关闭错误** - 解决了"Event loop is closed"运行时错误
- **WebSocket连接握手失败** - 修复了客户端无法建立WebSocket连接的问题
- **WebSocket ID访问错误** - 修复了server_ws_recv.py中使用不存在的websocket.id属性导致的异常

### 技术细节
1. **core_server.py**:
   - 将`websockets.serve()`改为使用`async with websockets.serve(...) as server:`模式
   - 使用`await asyncio.gather(asyncio.Future(), send)`保持服务器持续运行

2. **util/server_ws_recv.py**:
   - 将所有`websocket.id`替换为`id(websocket)`或`socket_id`变量
   - 修复了WebSocket连接管理中的ID生成和使用逻辑

### 测试结果
- ✅ WebSocket服务器成功启动在0.0.0.0:6016
- ✅ 客户端连接测试通过
- ✅ WebSocket握手协议正常工作
- ✅ 连接建立和关闭功能正常

### 影响范围
- 修复了所有WebSocket相关的连接问题
- 提高了服务器稳定性和可靠性
- 确保了语音识别客户端能够正常连接到服务器

---

## [未发布] - 2024-07-18

### 修复
- 修复了 `util/server_init_recognizer.py` 中导致语音识别进程无法启动的代码逻辑错误
  - 问题原因：第 73-80 行存在重复的模型加载代码，在 `else` 分支中错误地尝试加载 SenseVoice 模型，导致异常
  - 解决方案：移除重复和错误的模型加载代码，确保模型加载逻辑正确
  - 影响范围：语音识别服务启动，修复后 `queue_in.get(timeout=1)` 能够正常接收数据

- 修复了 `util/client_send_audio.py` 中的 `AttributeError: 'ClientConnection' object has no attribute 'closed'`
  - 问题原因：`websockets` 库 API 变更，`ClientConnection` 对象不再有 `closed` 属性
  - 解决方案：在 `send_message` 和 `heartbeat` 函数中使用 `hasattr()` 检查 `state` 和 `closed` 属性，确保兼容性
  - 影响范围：音频数据传输和心跳操作期间的异常处理
  - 修复了多个 `websocket.closed` 使用实例

- 修复了音频录制文件创建时的 "Permission denied" 错误
  - 问题原因：`util/client_create_file.py` 中的 `create_file` 函数使用相对路径创建目录，当当前工作目录不可写时导致权限错误
  - 解决方案：将相对路径改为基于项目根目录的绝对路径 (`Path(__file__).parent.parent`)
  - 影响范围：音频文件保存功能，提高了应用程序的健壮性

---

## 说明
本更新日志记录了CapsWriter-Offline项目的重要修复和改进。每次重大修复都会在此文件中记录，以便追踪项目的发展历程。