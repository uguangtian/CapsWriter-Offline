# CapsWriter-Offline 更新日志

## [2025-01-31-23:55] - 通知功能增强与调试优化
### 新增
    - 添加了详细的通知调试信息，便于排查通知问题
    - 实现了状态栏闪烁提示作为系统通知的备用方案
    - 新增 `show_temporary_status_message` 方法，提供可视化的完成提示
### 优化
    - 改进了系统通知的错误处理和调试输出
    - 状态栏消息现在会显示更长时间（10-15秒）
    - 添加了绿色闪烁效果，确保用户能注意到处理完成
### 修复
    - 修复了macOS系统通知权限可能导致的通知不可见问题
    - 提供了多层级的通知备用方案（系统通知 → 状态栏闪烁 → 状态栏消息）
### 用户体验改进
    - 即使系统通知被禁用，用户仍能通过状态栏看到处理完成提示
    - 闪烁效果能有效吸引用户注意，不会错过重要通知
    - 调试信息帮助用户了解通知系统的工作状态

## [2025-01-31-23:45] - 批量处理完成通知优化
### 优化
    - 将批量处理完成后的弹窗提示改为系统通知，提升用户体验
    - 音视频转录批量处理完成后使用系统通知而不是弹窗
    - 长文本批量处理完成后使用系统通知而不是弹窗
    - 添加了跨平台系统通知支持（macOS、Windows、Linux）
### 新增
    - 实现了 `show_system_notification` 方法，支持跨平台系统通知
    - macOS 使用 osascript 显示原生通知
    - Windows 支持 win10toast 库显示通知（备用方案为消息框）
    - Linux 使用 notify-send 显示通知
### 用户体验改进
    - 批量处理完成后不再弹出阻塞性对话框，用户可以继续其他操作
    - 系统通知会在通知中心显示，不会打断用户当前工作流
    - 保持了完成提示的功能性，同时减少了界面干扰
### 技术细节
    - 导入了 platform 模块用于检测操作系统类型
    - 添加了异常处理，确保通知功能的稳定性
    - 提供了备用方案，在系统通知失败时使用传统消息框

## [2025-01-31-23:30] - 批量处理从选中项开始功能
### 新增
    - 实现了文件列表和文本文件列表的从选中项开始处理功能
    - 音视频转录批量处理现在支持从当前选中的文件开始，而不是总是从第一个文件开始
    - 长文本批量处理现在支持从当前选中的文件开始，提升了处理效率
### 优化
    - 在 `LongTextBatchProcessingWorker` 类中添加了 `start_index` 参数，支持指定处理起始位置
    - 修改了 `start_long_text_processing` 方法，获取当前选中文件的索引并传递给处理线程
    - 修改了 `start_transcription` 方法，获取当前选中文件的索引并保存为起始位置
    - 修改了 `transcribe_next_file` 方法，从保存的起始索引开始查找未完成的文件
    - 更新了进度条初始值，反映从选中位置开始的处理进度
### 用户体验改进
    - 用户现在可以选中文件列表中的任意文件，然后开始批量处理，系统会从选中的文件开始处理
    - 如果没有选中任何文件，系统会默认从第一个文件开始处理，保持向后兼容性
    - 在控制台输出中显示从第几个文件开始处理，便于用户了解处理状态
### 技术细节
    - 使用 `currentRow()` 方法获取当前选中文件的索引
    - 在批量处理中保存起始索引，确保处理逻辑的一致性
    - 支持音视频转录和长文本处理两种批量处理模式

## [2025-01-31-23:15] - 系统设定和用户设定自动保存和加载功能
### 新增
    - 创建了 `prompt_config_manager.py` 提示词配置管理器，支持不同处理类型的系统和用户提示词管理
    - 实现了系统设定和用户设定的自动保存功能，当用户修改提示词内容时自动保存到配置文件
    - 实现了系统设定和用户设定的自动加载功能，应用启动时和切换处理类型时自动加载用户之前保存的配置
    - 为每种处理类型（总结、润色、纠错、关键词提取、结构化整理、纠正错误和划分段落）设置了默认的系统和用户提示词
### 修复
    - 修复了信号连接和断开时的警告问题，添加了异常处理避免重复断开信号
    - 修复了 `save_current_prompts` 方法参数不匹配的问题
### 优化
    - 在设置提示词时临时断开 `textChanged` 信号，避免在加载配置时触发自动保存
    - 优化了配置文件的结构，支持按处理类型分别保存系统和用户提示词
    - 改进了用户体验，用户的个性化设置现在会被自动保存和恢复
### 技术细节
    - 使用 JSON 格式存储提示词配置到 `prompt_config.json` 文件
    - 集成了配置管理器到主界面，实现了无缝的配置保存和加载
    - 添加了详细的日志输出，便于调试和监控配置操作

## [2025-01-31-22:45] - 系统设定和用户设定界面优化
### 优化
    - 为系统设定和用户设定的重置按钮添加了工具提示，说明功能为"恢复为您保存配置好的系统设定/用户设定"
    - 优化了状态栏提示信息，将"已重置为默认值"改为"已恢复为您保存配置好的设定"
    - 提升了用户体验，让用户更清楚地理解重置功能的作用
### 技术细节
    - 使用 setToolTip() 方法为按钮添加悬停提示
    - 更新了 reset_system_prompt() 和 reset_user_prompt() 方法中的状态栏消息

## [2025-01-31-22:15] - 拖拽文件功能修复
### 修复
    - 修复了 `add_text_files_from_drop` 方法参数类型不匹配问题，将参数类型从 `List[str]` 改为 `List[Path]`
    - 修复了 `FileListWidget` 的 `is_supported_file` 方法未包含文本文件格式支持的问题
    - 在 `is_supported_file` 方法中添加了 `.txt`、`.md` 和 `.rtf` 等文本文件格式支持
    - 添加了详细的拖拽调试日志，包括 `dragEnterEvent`、`dropEvent` 和信号处理的调试信息
### 优化
    - 改进了拖拽事件处理的调试机制，便于排查拖拽功能问题
    - 统一了音频转录和长文本处理的文件拖拽支持，两个功能现在都支持相应格式的文件拖拽
    - 增强了文件格式检测的准确性和完整性
### 技术细节
    - `FileListWidget` 类已正确设置 `setAcceptDrops(True)` 和拖拽模式
    - 拖拽功能支持音频、视频和文本文件格式的自动识别和分类处理
    - 添加了 `dragEnterEvent` 和 `dropEvent` 的详细调试输出，便于问题诊断

## [2025-01-31-21:00] - 长文本处理功能重大升级 - 批量文件处理模式
### 新增
    - **批量文件处理模式**: 将长文本处理从单文本输入模式重构为批量文件处理模式，支持同时处理多个文本文件
    - **文件管理功能**: 添加文件列表控件，支持添加、移除、清空文本文件操作
    - **拖拽文件支持**: 支持直接拖拽文本文件（.txt, .md, .rtf格式）到文件列表中
    - **输出目录设置**: 用户可以指定处理结果的输出目录，或使用源文件同目录保存
    - **批量处理工作线程**: 创建 `LongTextBatchProcessingWorker` 类，支持逐个处理文件列表中的文件
    - **确定进度显示**: 进度条显示确定进度，实时更新处理状态和文件处理进度
    - **处理结果管理**: 每个处理完成的文件都会保存为独立的结果文件（原文件名_processed.txt）
    - **处理摘要显示**: 批量处理完成后显示处理摘要，包括处理文件数和输出文件列表
### 优化
    - **智能文件过滤**: 自动跳过空文件和过短文件（少于50个字符），提高处理效率
    - **错误处理机制**: 单个文件处理失败不影响其他文件的处理，继续处理队列中的下一个文件
    - **用户体验提升**: 处理完成后显示成功对话框，并在结果面板显示详细的处理摘要
    - **保留原有功能**: 继续支持系统设定和用户设定功能，用户可自定义AI模型行为
### 技术细节
    - 新增 `add_text_files()`, `remove_selected_text_file()`, `clear_text_file_list()` 等文件管理方法
    - 新增 `add_text_files_from_drop()` 方法支持拖拽文件添加
    - 新增 `browse_long_text_output_directory()` 方法支持输出目录选择
    - 重构 `start_long_text_processing()` 方法支持批量处理
    - 新增 `on_long_text_file_completed()` 和 `on_long_text_batch_completed()` 事件处理方法
    - 文件列表使用 `FileListWidget` 控件，与音视频转录保持一致的用户体验

## [2025-01-27-20:00] - 长文本处理功能增强 - 支持自定义系统设定和用户设定
### 新增
    - 在 base_agent.py 中为 call_api 函数增加 system_prompt 和 user_prompt 参数支持
    - 在 long_text_processor.py 中为 process 方法增加系统设定和用户设定参数传递
    - 在 transcription_gui.py 中添加系统设定和用户设定的 UI 组件
    - 用户现在可以在长文本处理界面中自定义系统提示词和用户提示词
    - 支持为不同的处理任务设置个性化的AI行为指导
### 优化
    - 提升了长文本处理的灵活性和个性化程度
    - 增强了AI模型的可控性，用户可以根据具体需求调整AI的处理方式
    - 改进了用户界面，提供更丰富的配置选项
### 技术细节
    - BaseAgent.call_api 方法现在支持传递自定义的系统和用户提示词
    - LongTextProcessor.process 方法能够接收并传递提示词参数
    - LongTextProcessingWorker 线程支持系统设定和用户设定参数
    - UI 界面新增两个文本输入框，支持多行文本输入和占位符提示

## [2025-01-27-19:35] - 修复文件转录进程等待超时问题
### 修复
    - 修复client_transcribe.py中transcribe_send函数等待ffmpeg进程结束时可能无限期阻塞的问题
    - 为ffmpeg进程等待添加30秒超时控制，避免asyncio.gather无限等待
    - 添加进程强制终止机制，超时后先尝试terminate()，再尝试kill()
    - 确保转录任务能在合理时间内完成或失败，避免GUI界面卡死
### 优化
    - 提升文件转录的稳定性和响应性
    - 增强异常处理机制，确保进程资源能正确释放
    - 改进调试日志输出，便于监控ffmpeg进程状态

## [2025-01-27-19:30] - Mac系统异步粘贴操作修复
### 修复
    - 修复Mac系统下粘贴操作使用同步subprocess.run()导致异步事件循环阻塞的问题
    - 改进client_type_result.py中Mac系统的粘贴操作，使用asyncio.create_subprocess_exec()替代同步调用
    - 添加异步超时控制和更详细的错误处理机制
    - 确保Mac系统下客户端收到最终识别结果后能正常继续执行
### 优化
    - 提升Mac系统下异步操作的稳定性和响应性
    - 增强错误处理和降级机制，确保粘贴失败时能正常降级到直接写入
    - 改进调试日志输出，便于问题排查

## [2025-01-27-19:25] - Mac系统粘贴操作兼容性修复
### 修复
    - 修复Mac系统下客户端收到最终识别结果后卡住不继续执行的问题
    - 改进client_type_result.py中Mac系统的粘贴操作，使用AppleScript替代可能卡住的keyboard.press()操作
    - 为Mac和Windows/Linux系统的粘贴操作添加异常处理和降级机制
    - 当粘贴操作失败时自动降级到直接写入方式，确保识别结果能正常输出
### 优化
    - 提升Mac系统下语音识别结果输出的稳定性和可靠性
    - 增强跨平台兼容性，确保在不同操作系统上都能正常工作

## [2025-01-27-19:20] - 增强 transcription_gui 批量转录调试日志

### 新增
- 在 `on_transcription_completed` 方法中添加详细的文件匹配和状态跟踪日志
- 在 `transcribe_next_file` 方法中添加文件列表遍历和完成状态检查日志
- 输出当前文件列表、已完成文件列表、文件匹配过程等调试信息

### 优化
- 增强批量转录过程的可调试性
- 便于排查多文件转录时只处理第一个文件的问题

## [2025-01-27-19:18] - 语音识别最终结果发送修复
### 修复
- 修复 server_recognize_paraformer.py 中识别结果为空时 is_final 状态设置问题
- 确保最终任务即使结果为空也正确设置 is_final=True
- 修复批量转录中最终文件识别结果为空时客户端无法收到结束标识的问题
- 清理 server_ws_send.py 中的调试日志，保持代码简洁性
### 优化
- 改进空识别结果的处理逻辑，确保客户端能正确接收到转录结束信号
- 提升批量转录的稳定性和完整性

## [2025-01-27-19:15] - 修复 core_client.py 阻塞导致 transcription_gui 无法接收完成信号

### 修复
    - 修复 core_client.py 中 input() 语句导致进程阻塞的问题
    - 当通过命令行参数调用时（如被 transcription_gui 调用），程序完成后直接退出
    - 避免等待用户输入导致 GUI 客户端无法接收到转录完成信号
    - 保持交互式使用时的原有行为（等待回车退出）

### 技术细节
    - 通过检查 sys.argv 长度判断是否为命令行调用
    - 确保 transcription_gui 能正常接收 subprocess 的退出信号

## [2025-01-27-19:10] - transcription_gui添加详细转录日志
### 新增
    - 在 TranscriptionWorker 中添加详细的转录过程日志
    - 在调用 core_client.py 时输出命令、工作目录、文件路径等信息
    - 在转录完成和失败时输出详细的状态信息
    - 在 on_transcription_completed 和 on_transcription_failed 方法中添加信号接收日志
### 优化
    - 增强转录过程的可调试性，便于排查消息接收问题
    - 提供更详细的转录状态跟踪信息

## [2025-01-27-18:45] - WebSocket连接稳定性修复验证成功
### 验证结果
    - 转录结果发送问题已完全修复，客户端能够正常接收服务端发送的转录完成消息
    - WebSocket连接稳定性优化生效，心跳机制和超时设置调整有效
    - 测试文件转录成功：客户端正确接收到 `is_final=True` 的完成消息并保存所有结果文件
    - 服务端日志显示成功发送结果，客户端日志显示成功接收，连接在任务完成后正常断开
### 技术细节
    - 服务端成功发送结果：`[DEBUG] 成功发送结果到客户端 (socket_id: xxx)，任务ID: xxx`
    - 客户端成功接收：`[DEBUG] 收到最终结果，文本长度: 16`
    - 连接管理正常：任务完成后连接正常断开并清理

## [2025-01-27-18:30] - WebSocket连接稳定性优化
### 修复
    - 修复了转录完成后客户端连接过早断开导致无法接收结果的问题
    - 优化了WebSocket心跳机制，将心跳间隔从30秒增加到60秒，减少频繁检测
    - 增加了心跳超时时间从20秒到30秒，提高连接稳定性
    - 改进了心跳失败时的连接清理逻辑，确保断开的连接能被及时清理
    - 增加了客户端接收转录结果的超时机制（10分钟），避免无限等待
    - 优化了客户端重连逻辑，在连接断开时能更好地处理剩余结果接收
### 优化
    - 统一了服务端和客户端的WebSocket连接参数（ping_interval=60秒，ping_timeout=30秒）
    - 增加了客户端连接的close_timeout参数，提高连接关闭的稳定性
    - 改进了错误处理和调试日志，便于问题排查
### 技术细节
    - util/server_ws_recv.py: 优化心跳机制和连接清理逻辑
    - util/client_check_websocket.py: 增加连接超时参数
    - util/client_send_audio.py: 统一心跳间隔设置
    - util/client_transcribe.py: 增加结果接收超时和重连处理

## [2025-01-27-17:45] - 转录结果发送修复
### 修复
    - 修复了转录完成后服务端无法将结果发送给客户端的问题
    - 修复了WebSocket连接ID不匹配导致的结果发送失败
    - 增加了WebSocket连接状态检查和断开连接的清理逻辑
    - 修复了服务端在查找WebSocket连接时使用不一致的ID匹配逻辑
    - 增加了连接断开时的异常处理和连接清理机制
### 优化
    - 在util/server_ws_send.py中添加了详细的调试日志以跟踪结果发送过程
    - 在util/client_transcribe.py中添加了调试日志以跟踪结果接收过程
    - 改进了WebSocket连接管理，避免向已断开的连接发送消息

## [2025-01-27-17:40] - WebSocket发送模块调试增强和问题修复
### 修复
    - server_ws_send: 添加websockets模块导入，修复ConnectionClosed异常处理失败问题
    - server_ws_send: 添加详细的消息发送调试日志，包括结果信息、消息内容预览、WebSocket状态监控
    - server_ws_send: 增强WebSocket连接状态检查和发送前验证
    - server_ws_send: 添加消息长度监控和发送结果确认
    - server_ws_send: 改进异常处理，提供更详细的错误信息
### 优化
    - server_ws_send: 提升WebSocket消息传输可靠性和状态监控能力

## [2025-01-27-17:35] - 修复多任务转录队列处理问题
### 修复
    - 修复了转录失败时未将失败文件标记到结果字典的问题
    - 解决了第一个任务失败后导致后续任务无法自动开始的bug
    - 确保转录失败的文件被正确标记，避免重复尝试转录同一文件
    - 修复了transcribe_next_file方法中的任务队列处理逻辑
    - 修复了转录取消功能问题，点击取消后GUI界面仍显示转录进度的问题
    - 在重试循环和转录过程中添加取消状态检查，确保用户点击取消后能立即停止转录任务
    - 添加详细的调试日志以跟踪取消操作的执行过程
### 优化
    - 改进了转录失败处理机制，失败文件会被标记并跳过
    - 增强了多文件批量转录的稳定性和连续性
    - 优化了任务队列管理，确保所有文件都能被正确处理

## [2025-01-27-17:30] - 修复模块导入路径错误
### 修复
    - 修复了BaseAgent类中model_services模块导入路径错误导致的ModuleNotFoundError
    - 将绝对导入路径改为相对导入路径，使用.model_services前缀
    - 确保所有AI模型服务（deepseek、doubao、lmstudio、claude）的导入路径正确
    - 解决了长文本处理功能中"No module named 'model_services'"错误
### 优化
    - 改进了模块导入机制，提高代码的可移植性和健壮性
    - 统一了相对导入路径的使用规范

## [2025-01-27-17:15] - 修复长文本处理器初始化参数错误
### 修复
    - 修复了LongTextProcessor初始化时传递错误参数导致的TypeError
    - 将max_tokens_per_segment参数正确封装到config字典中传递
    - 确保LongTextProcessor构造函数调用符合BaseAgent的参数规范
    - 解决了长文本处理功能启动时的"unexpected keyword argument"错误
### 优化
    - 改进了参数传递方式，提高代码的健壮性和可维护性

## [2025-01-27-16:45] - 修复长文本处理UI属性名不匹配问题
### 修复
    - 修复了长文本处理功能中UI组件属性名不一致导致的AttributeError错误
    - 统一了所有长文本处理相关UI组件的属性命名规范
    - 修正了start_long_text_processing和相关方法中的属性引用
    - 确保了所有按钮点击事件的正确连接
### 优化
    - 移除了setup_connections方法中的重复事件连接代码
    - 改进了UI组件的命名一致性，便于维护

## [2025-01-31-20:30] - 长文本处理与归纳应用
### 新增
    - 创建全新的长文本处理与归纳GUI应用 (long_text_gui.py)
    - 基于PySide6框架，提供现代化的桌面应用界面
    - 支持多种文本输入方式：直接输入、文件拖拽、文件选择
    - 实现AI大模型长文本分段处理，自动解决上下文长度限制问题
    - 支持多种处理类型：总结、润色、纠错、关键词提取、结构化整理
    - 集成多种AI模型：DeepSeek、豆包(Doubao)、Claude、LM Studio
    - 提供处理历史记录管理和版本控制功能
    - 支持多种文档格式导出：Markdown、Word、PDF等
### 核心功能
    - **智能分段处理**：自动将长文本分割为符合AI模型上下文限制的段落
    - **上下文保持**：在分段处理时保持段落间的语义连贯性
    - **批量处理**：支持大文件和长文本的高效处理
    - **实时进度**：提供详细的处理进度反馈和状态更新
    - **结果管理**：支持处理结果的复制、保存、导出和历史查看
    - **文件支持**：支持TXT、DOCX、MD、SRT、VTT等多种文本文件格式
### 技术特性
    - 基于BaseAgent架构，支持多种AI模型服务
    - 异步处理机制，避免界面冻结
    - 智能Token估算和文本分割算法
    - 完整的错误处理和异常恢复机制
    - 模块化设计，便于功能扩展和维护
### 用户体验
    - 直观的拖拽文件上传界面
    - 实时的处理进度显示和状态反馈
    - 标签页式结果展示，支持历史记录浏览
    - 丰富的配置选项和高级设置
    - 完整的帮助文档和操作指引

## [2025-01-31-19:15] - 图形化转录工具控制台日志输出增强
### 新增
    - 在图形化转录工具中添加详细的控制台日志输出功能
    - 应用启动时显示系统信息、Python版本和工作目录
    - 转录过程中实时输出进度信息和状态更新
    - 文件添加、转录开始、转录完成等关键操作的日志记录
    - 转录失败时输出详细的错误信息到控制台
### 优化
    - 增强用户对转录进度的可见性，便于监控和调试
    - 提供完整的转录流程日志，包括文件路径、设置选项等
    - 改进错误排查能力，通过控制台日志快速定位问题
    - 添加批量转录完成统计信息，显示成功/失败文件数量
### 特性
    - 所有日志信息都带有明确的标识前缀，便于分类查看
    - 支持实时查看转录进度，无需依赖GUI界面反馈
    - 控制台输出与GUI界面状态保持同步

## [2025-01-31-18:30] - 图形化转录工具字幕文件可选配置
### 新增
    - 在图形化转录工具中添加字幕文件生成选项控制
    - 用户可以选择是否生成SRT格式的字幕文件
    - 添加转录设置面板，包含字幕文件生成复选框
### 优化
    - 字幕文件相关按钮状态根据用户设置动态更新
    - 当用户取消字幕文件生成选项时，自动禁用"打开字幕文件"按钮
    - 改进转录工作线程，支持可选的字幕文件生成参数
    - 增强用户界面的灵活性和可配置性
### 修复
    - 修复字幕文件按钮状态与实际设置不一致的问题
    - 确保字幕文件处理逻辑与用户选择保持同步

## [2025-01-31-18:00] - 新增图形化转录工具
### 新增
    - 创建独立的桌面图形化转录工具 transcription_gui.py
    - 基于PySide6框架，提供现代化的用户界面
    - 支持音频和视频文件的拖拽上传和文件选择
    - 实现文件列表管理，支持批量添加、删除和清空操作
    - 提供实时转录进度显示和结果展示
    - 支持转录结果的保存、复制和导出功能
    - 添加转录设置面板，支持VAD和标点符号配置
    - 创建专用启动脚本 start_transcription_gui.py
    - 添加专用依赖文件 requirements-transcription-gui.txt
### 特性
    - 支持多种音频格式：WAV, MP3, M4A, FLAC, OGG
    - 支持多种视频格式：MP4, AVI, MOV, MKV, WEBM, 3GP
    - 现代化UI设计，包含文件信息显示和进度条
    - 异步转录处理，避免界面冻结
    - 完整的错误处理和用户反馈机制

## [2025-01-31-17:15] - 修复JavaScript变量重复声明错误
### 修复
    - 修复网页版转录页面中mediaRecorder变量重复声明导致的SyntaxError
    - 统一全局变量和函数的暴露机制，避免在多个地方重复暴露到window对象
    - 确保app.js中的全局变量只在initializeApp函数中统一暴露
    - 修复transcription.html页面中所有showAlert函数调用，改为通过window.showAlert访问
### 优化
    - 改进JavaScript代码结构，避免全局作用域污染
    - 增强代码的模块化和可维护性

## [2025-01-31-16:45] - 修复网页版转录功能启动问题
### 修复
    - 修复拖拽文件后无法启动转录的问题
    - 更新JavaScript代码以使用新的双模式转录API
    - 修复文件上传转录功能，正确传递 `use_local_path=false` 参数
    - 修复本地路径转录功能，改用HTTP API替代SocketIO
    - 统一错误提示样式为 `danger` 类型
### 优化
    - 增加VAD和标点符号设置的传递
    - 改进转录进度提示信息
    - 优化错误处理和用户反馈

## [2025-01-31-16:30] - 转录API双模式支持
### 新增
    - 转录API新增本地路径模式，支持直接传递文件路径而无需上传文件
    - 添加use_local_path参数开关，支持文件上传和本地路径两种模式
    - 本地路径模式下添加文件存在性和有效性验证
    - 在SocketIO事件中添加模式标识，便于前端区分处理方式
### 优化
    - 本地路径模式下不进行文件清理，避免删除用户原始文件
    - 统一filename变量使用，提高代码一致性
    - 改进错误信息提示，针对不同模式提供相应的错误描述

## [2025-01-31-16:30] - 转录功能调试信息增强
### 优化
    - 在转录功能中添加详细的调试信息输出
    - 打印完整的命令行参数、工作目录、返回码等信息
    - 增强错误排查能力，便于定位参数传递问题
    - 改进subprocess调用的日志记录

## [2025-01-01-02:15] - 转录功能命令行参数修复
### 修复
    - 修复 web_unified_app.py 中调用 core_client.py 的命令行参数错误，确保使用 --file 参数而非位置参数
    - 清理 Python 缓存文件以确保代码更新生效
    - 重新启动 Web 服务器以应用修复

## [2024-12-19] - 多功能处理工具集成

### 重大更新
- **功能集成**: 将长文本处理功能完全集成到主转录GUI应用中
- **统一界面**: `python start_transcription_gui.py` 现在启动多功能处理工具
- **标签页设计**: 采用标签页布局，音视频转录和长文本处理功能并存
- **一体化体验**: 用户无需启动多个应用，一个界面完成所有处理任务

### 新增功能
- **长文本智能处理系统**: 基于CapsWriter-Offline架构开发的专业长文本处理工具
- **多种处理类型**: 支持总结归纳、关键信息提取、结构化整理、问答生成等多种文本处理模式
- **智能分段算法**: 自动将长文本按语义边界进行智能分段，确保处理质量
- **多模型支持**: 兼容多种AI模型，用户可根据需求选择最适合的模型
- **异步处理架构**: 采用多线程异步处理，支持大文本量处理而不阻塞界面
- **现代化GUI界面**: 基于PySide6开发的直观用户界面，支持拖拽操作

### 核心功能
#### 音视频转录功能
- **批量转录**: 支持多文件批量处理
- **格式支持**: 支持主流音频和视频格式
- **字幕生成**: 可选择生成SRT字幕文件
- **结果管理**: 转录结果的复制、保存、查看等操作

#### 长文本处理功能
- **文本输入**: 支持直接输入、文件加载（txt、md、doc、docx等格式）
- **处理设置**: 可配置处理类型、AI模型、最大Token数等参数
- **实时进度**: 显示处理进度和状态信息
- **结果管理**: 支持结果复制、保存、导出等操作
- **历史记录**: 自动保存处理历史，支持历史记录查看和重新加载

### 技术特性
- **模块化设计**: 核心处理逻辑与界面分离，便于维护和扩展
- **异常处理**: 完善的错误处理和用户提示机制
- **资源管理**: 优化的内存使用和线程管理
- **跨平台支持**: 支持Windows、macOS、Linux等主流操作系统
- **智能检测**: 自动检测功能模块可用性，优雅降级

### 用户体验
- **统一入口**: 一个应用满足音视频转录和长文本处理需求
- **直观操作**: 标签页设计，功能分类清晰
- **快速响应**: 异步处理确保界面始终保持响应
- **详细反馈**: 实时显示处理状态和进度信息
- **便捷管理**: 一键复制、保存、导出等便民功能

### 文件结构
- `transcription_gui.py`: 主GUI应用（集成音视频转录和长文本处理）
- `start_transcription_gui.py`: 应用程序启动脚本
- `agent/long_text_processor.py`: 长文本处理核心逻辑
- `README_LONG_TEXT.md`: 长文本处理功能详细说明

### 启动方式
```bash
python start_transcription_gui.py
```

# 更新日志

## [2025-01-24-16:45] - 文件路径转录功能修复
### 修复
    - 修复了文件路径中包含转义字符导致转录失败的问题
    - 改进了路径处理逻辑，正确处理反斜杠转义的空格和特殊字符
    - 添加了路径规范化和绝对路径转换功能
    - 增强了调试信息输出，便于问题排查
### 优化
    - 改进了错误处理机制，提供更详细的错误信息
    - 优化了文件存在性检查逻辑

## [2025-01-27-16:45] - 拖拽上传功能修复
### 修复
    - 修复了拖拽文件上传功能不工作的问题，文件被在新标签页打开而不是上传
    - 修复了CSS中pointer-events设置导致的拖拽事件阻塞问题
    - 改进了拖拽事件处理逻辑，添加了完整的dragenter、dragover、dragleave、drop事件处理
    - 增强了拖拽区域的事件防护，防止页面默认拖拽行为干扰
### 优化
    - 添加了拖拽文件的控制台日志输出，便于调试
    - 改进了拖拽区域的点击事件处理，只在正确区域触发文件选择
    - 优化了拖拽状态的视觉反馈效果

## [2025-01-27-18:45] - 修复文件路径转义问题并添加路径输入功能

### 修复
- 修复本地文件转录中的路径转义字符处理问题
- 正确处理包含空格、括号、特殊字符的文件路径
- 自动移除路径中的多余转义字符和引号

### 新增
- 在音频文件上传区域添加文件路径输入功能
- 支持手动输入完整文件路径进行转录
- 添加路径输入的键盘快捷键支持（Enter键）
- 提供路径处理的用户提示信息

### 改进
- 增强路径处理的调试信息输出
- 优化文件路径验证和错误提示
- 改进用户界面，提供更清晰的操作指引

## [2025-01-27-17:30] - 修复文件路径处理错误

### 修复
- 修复本地文件转录中的文件路径处理问题
- 解决"文件不存在"错误，当用户选择文件但只传递文件名而非完整路径时
- 改进前端文件路径验证逻辑，确保只接受完整的文件路径
- 优化用户体验，提供更清晰的路径输入提示

### 优化
- 文件选择器现在只用于辅助获取文件名，不再自动填入路径输入框
- 增强路径验证，要求用户输入包含路径分隔符的完整路径
- 改进错误提示信息，指导用户正确输入文件路径

## [2024-12-30-15:45] - 添加拖拽上传功能
### 新增
    - 音频文件拖拽上传功能，支持直接拖拽文件到指定区域
    - 拖拽区域视觉反馈效果，包括悬停和拖拽时的样式变化
    - 文件信息显示面板，显示选中文件的名称和大小
    - 文件格式验证功能，支持音频和视频文件格式检测
### 优化
    - 重新设计文件上传界面，提供更直观的拖拽体验
    - 添加清除文件按钮，方便用户重新选择文件
    - 改进文件选择流程，支持点击和拖拽两种方式
    - 增强用户交互反馈，提供更清晰的操作提示

## [2025-01-01-02:15] - 改进文件选择用户体验
### 优化
    - 改进文件选择后的路径处理逻辑，自动将文件名填入输入框
    - 优化用户提示信息，说明浏览器安全限制无法自动获取完整路径
    - 添加光标定位功能，方便用户在文件名前添加目录路径
    - 提供更清晰的占位符提示和操作指导

## [2025-01-27-16:20] - 文件转录命令行参数修复
### 修复
    - 修复调用core_client.py时缺少--file参数的问题
    - 增强错误信息捕获，同时显示标准输出和标准错误
    - 添加详细的命令执行调试信息，包括执行命令、工作目录、文件路径等
    - 修复转录进程返回码检查和错误信息显示

## [2025-01-27-16:15] - 文件不存在错误调试增强

### 修复
- 在本地文件转录功能中增加详细的调试信息输出
- 改进文件不存在错误的信息显示，显示绝对路径而非相对路径
- 添加原始路径、绝对路径、文件名和当前工作目录的调试输出
- 帮助用户和开发者更好地定位文件路径问题

## [2025-01-27-16:45] - 异步事件循环错误彻底修复

### 修复
- **彻底解决**转录功能中的"There is no current event loop in thread"错误
- 将转录执行方式从直接调用异步函数改为使用subprocess调用core_client.py
- 完全避免了多线程环境下的异步事件循环冲突
- 增加转录超时处理（1小时）和详细错误信息捕获
- 提高转录功能的稳定性和可靠性

### 技术改进
- 使用subprocess.run()替代直接的异步函数调用
- 增强错误处理和异常捕获机制
- 优化进程间通信和错误信息传递
- 确保转录任务在独立进程中执行，避免线程冲突

## [2025-01-18-15:45] - 本地文件直接转录功能实现

### 新增
- 实现了本地文件直接转录功能
  - 添加了文件路径输入框，支持直接输入完整文件路径
  - 新增SocketIO事件处理器`transcribe_local_file`
  - 支持通过文件路径直接读取本地音视频文件进行转录
  - 保留文件选择器作为辅助功能

### 修复
- 修复了本地文件转录中的异步事件循环错误
  - 在后台线程中正确创建和管理独立的事件循环
  - 确保多线程环境下的异步操作稳定性

### 优化
- 改进了用户界面和交互体验
  - 文件路径输入框优先级高于文件选择器
  - 自动从文件路径提取文件名
  - 更新了按钮文本和提示信息

## [2025-01-18-12:15] - 异步事件循环错误修复和文件转录功能增强

### 修复
- 修复了文件转录功能中"There is no current event loop in thread"错误
  - 在后台线程中正确创建和管理异步事件循环
  - 使用`asyncio.new_event_loop()`在新线程中创建独立的事件循环
  - 通过`loop.run_until_complete()`执行异步函数
  - 确保在线程结束时正确关闭事件循环
- 修复了JavaScript中undefined参数导致的substring错误
  - 在`addToHistory`和`appendTranscriptionResult`函数中增加参数有效性检查
  - 在SocketIO事件处理中增加转录结果有效性验证
- 改进了转录结果的有效性检查和错误处理
  - 后端确保只有有效的文本内容才通过`transcription_result`事件发送
  - 当转录结果为空时发送`transcription_error`事件
  - 对读取的文件内容进行`strip()`处理

### 优化
- 增强了前端参数验证，避免因无效数据导致的崩溃
- 优化了转录失败时的用户提示信息

### 增强
- 扩展了文件上传支持的格式
  - 新增支持视频文件格式：MP4, AVI, MOV, MKV, WEBM, 3GP
  - 原有音频格式：WAV, MP3, M4A, FLAC, OGG
  - 更新了前端文件选择器的accept属性和提示信息

## [2025-01-27-21:45] - 网页版配置管理API缺失修复

### 修复
- 修复 `config.html` 中配置加载API调用路径错误
  - 将 `/api/config/load` 修正为 `/api/config/get` 以匹配后端路由
- 修复 `web_unified_app.py` 中缺少的配置管理API路由
  - 添加 `/api/config/save` 路由，支持配置保存功能
  - 添加 `/api/config/reset` 路由，支持重置配置为默认值
  - 添加 `/api/config/export` 路由，支持配置文件导出（JSON和TOML格式）
  - 添加 `/api/config/import` 路由，支持配置文件导入
  - 添加 `/api/config/test-model` 路由，支持模型连接测试
  - 添加 `/api/config/test-translation` 路由，支持翻译服务连接测试
  - 解决了前端JavaScript解析JSON时出现 'Unexpected token '<'' 的错误
  - 确保配置管理功能能正常工作

## [2025-01-27-21:30] - 网页版语音转录API缺失修复

### 修复
- 修复 `web_unified_app.py` 中缺少 `/api/transcribe` 路由定义
  - 添加完整的语音转录API路由，支持音频文件上传和处理
  - 解决了前端JavaScript解析JSON时出现 'Unexpected token '<'' 的错误
  - 支持音频文件上传、参数获取、临时文件处理和SocketIO事件发送
  - 确保语音转录功能能正常工作

## [2025-01-27-21:15] - 网页版文件列表加载错误修复

### 修复
- 修复 `file_manager.html` 中 `loadFileList` 函数的HTTP方法错误
  - 将POST请求改为GET请求以匹配后端API路由
  - 解决了前端JavaScript解析JSON时出现 'Unexpected token '<'' 的错误
  - 确保文件列表能正常加载和显示

## [2025-01-27-21:00] - 修复网页版文件管理路由错误

### 修复
- 修复 `web_unified_app.py` 中 `/files` 路由的模板文件名错误
  - 将错误的 `files.html` 修正为正确的 `file_manager.html`
  - 解决访问文件管理页面时出现的 "TemplateNotFound" 错误
  - 确保文件管理功能能正常访问

## [2025-01-27-20:45] - 完成网页版应用开发

### 新增
- 创建 `web_unified_app.py` 统一网页版应用入口，基于 Flask 和 SocketIO 构建
  - 整合语音识别、文本润色、在线翻译、配置管理、系统监控和文件管理等功能
  - 提供完整的 REST API 和 WebSocket 接口
  - 集成 UnifiedLauncher 和 AgentService 管理后端服务
- 创建完整的网页模板系统（基于 Bootstrap 和 Font Awesome）
  - `base.html`: 基础模板，包含导航栏、主要内容区域和页脚
  - `index.html`: 主页模板，包含功能卡片和快速操作面板
  - `dashboard.html`: 仪表板页面，实时显示系统状态和日志
  - `transcription.html`: 语音转录页面，支持录音和文件上传转录
  - `text_processing.html`: AI文本处理页面，支持多种文本处理任务
  - `translation.html`: 在线翻译页面，支持多种翻译服务
  - `file_manager.html`: 文件管理页面，支持文件浏览、编辑、上传下载
  - `config.html`: 配置管理页面，支持系统配置的可视化管理
  - `monitoring.html`: 系统监控页面，显示性能指标和运行状态
- 集成前端交互功能
  - Socket.IO 实时通信支持
  - 文件拖拽上传和进度显示
  - 实时状态更新和日志显示
  - 响应式设计，支持移动端访问

### 修复
- 修复 `agent_service.py` 中的 asyncio 事件循环问题
  - 在新线程中创建新的事件循环，解决 "There is no current event loop in thread" 错误
  - 确保 WebSocket 服务能在独立线程中正常运行

### 优化
- 网页版应用提供了桌面版的所有核心功能
- 支持通过浏览器访问 http://127.0.0.1:8080 使用应用
- 提供了现代化的用户界面和良好的用户体验
- 完全兼容现有的桌面版功能和配置

### 技术细节
- 使用 Flask-SocketIO 实现实时通信
- 集成现有的 UnifiedLauncher 和 AgentService
- 支持文件管理、系统监控、配置管理等高级功能
- 提供完整的 API 接口供前端调用
- 自动安装必要的依赖包（flask-socketio 等）

## [2025-01-27-19:15] - 新增 macOS 开机自启动功能

### 新增
- 创建 `create_autostart.sh` 脚本，支持设置 macOS 开机自启动
  - 通过 LaunchAgent 机制实现用户登录时自动启动
  - 自动创建 `~/Library/LaunchAgents/com.capswriter.offline.plist` 配置文件
  - 支持后台运行，不显示终端窗口
  - 自动记录运行日志到 `~/Library/Logs/` 目录
- 创建 `remove_autostart.sh` 脚本，支持移除开机自启动
  - 自动卸载 LaunchAgent 服务
  - 清理配置文件
- 创建 `README_AUTOSTART.md` 详细使用说明文档
  - 包含设置、移除、故障排除等完整指南
  - 提供手动管理命令和日志查看方法

### 验证
- 开机自启动设置脚本测试成功
- LaunchAgent 服务正确加载和卸载
- 移除脚本功能正常
- 所有脚本都有正确的执行权限

### 技术细节
- 使用 macOS LaunchAgent 机制，运行在用户级别
- 自动激活虚拟环境，确保依赖正确加载
- 支持日志记录和错误追踪
- 完全兼容现有的手动启动方式

## [2025-01-27-19:05] - 虚拟环境激活修复完成

### 修复
- 修复终端启动器中的虚拟环境激活问题
  - 问题：应用启动时出现 `ModuleNotFoundError: No module named 'tomlkit'`，因为依赖包安装在虚拟环境中但启动脚本在系统Python环境中运行
  - 解决方案：修改 `launch_in_terminal.sh` 脚本，在启动应用前自动激活虚拟环境
  - 添加 `source "$SCRIPT_DIR/python3/bin/activate"` 命令确保在正确的Python环境中运行

### 验证
- 应用现在能正常启动，所有模块依赖都能正确加载
- 语音模型和标点模型成功载入
- WebSocket服务正常启动在6016端口
- 服务端和客户端都能正常运行
- 终端启动器 `CapsWriter-Offline-Terminal.app` 现在完全可用

## [2025-01-27-18:55] - 终端启动器修复完成

### 修复
- 修复终端启动器 `CapsWriter-Offline-Terminal.app` 无法正常启动的问题
  - 修复 `create_terminal_app.sh` 中的语法错误（多余的括号）
  - 修复 AppleScript 命令中的路径变量替换问题
  - 使用硬编码绝对路径确保启动脚本能正确执行
  - 修复字符串拼接和转义字符问题

### 验证
- 终端启动器现在能正常双击启动
- 成功创建新的终端窗口并运行 CapsWriter-Offline
- 多个 `launch_in_terminal.sh` 进程正常运行
- 应用可以在终端环境中正常加载模型和启动服务

## [2025-01-27-18:45] - 修复macOS应用启动问题

### 修复
- 修复 macOS 应用双击快速退出问题
  - 识别出原因：命令行程序需要终端环境才能正常运行
  - 移除 `build_mac_app.py` 中的 .ico 格式图标引用
  - 调整应用配置：`console=True` 和 `LSUIElement=False`
  - 创建终端启动器：`CapsWriter-Offline-Terminal.app`

### 新增
- 新增终端启动脚本 `launch_in_terminal.sh`
- 新增终端应用创建脚本 `create_terminal_app.sh`
- 提供两种启动方式：PyInstaller打包的应用和终端启动器

## [2025-01-27-17:45] - 修复macOS应用闪退问题
### 修复
    - 修复 macOS 应用双击闪退问题，移除 build_mac_app.py 中的 .ico 格式图标引用
    - 解决因图标格式不兼容导致的应用启动失败问题
    - 修复 start_unified.py 在 macOS 上的启动逻辑，默认使用 core_server.py 和 core_client.py
    - 解决 macOS 平台上 GUI 版本启动器的兼容性问题
### 优化
    - 在 macOS/Linux 平台上默认使用核心版本（无GUI），提高稳定性
    - 保持 Windows 平台的 GUI 版本选择功能
    - 应用现在可以在 macOS 上正常双击启动
### 修改文件
    - 修改: `build_mac_app.py` - 移除不兼容的图标文件引用
    - 修改: `start_unified.py` - 调整服务端和客户端启动逻辑，根据平台选择合适的启动方式
### 技术细节
    - 移除 .ico 格式图标引用，解决 macOS 应用启动失败问题
    - macOS/Linux 平台默认启动 core_server.py 和 core_client.py
    - Windows 平台保持原有的 GUI 版本启动逻辑
    - 确保跨平台兼容性和用户体验一致性

## [2025-01-27-17:15] - 修复Mac应用打包工具
### 修复
    - 修复PySide6和Pillow依赖检查逻辑，确保正确识别已安装的包
    - 修复目录清理功能，增加强制删除机制处理非空目录
    - 解决macOS图标格式问题，自动安装Pillow进行图标转换
### 优化
    - 增强错误处理机制，提供更详细的错误信息
    - 改进构建流程的稳定性和可靠性
### 修改文件
    - 修改: `build_mac_app.py` - 修复依赖检查和目录清理逻辑
### 技术细节
    - 添加Pillow依赖用于自动转换.ico到.icns格式
    - 改进目录清理机制，支持强制删除
    - 完善依赖检查，正确处理特殊包名

## [2025-01-27-16:45] - 新增Mac应用打包工具
### 新增
    - 创建 `build_mac_app.py` Python打包脚本，支持将CapsWriter-Offline打包成独立的Mac应用程序
    - 创建 `build_mac.sh` Shell脚本，提供简化的命令行打包接口
    - 创建 `README_MAC_BUILD.md` 详细的打包工具使用文档
    - 支持生成.app应用包和可选的DMG安装包
    - 自动检查和安装PyInstaller等必要依赖
    - 支持自定义应用版本号和打包选项
### 优化
    - 打包后的应用包含完整的统一启动器功能
    - 自动设置应用图标、权限和元数据
    - 包含麦克风访问等必要的系统权限声明
    - 支持macOS 10.13+系统版本
### 修改文件
    - 新增: `build_mac_app.py` - 主要的Python打包脚本
    - 新增: `build_mac.sh` - Shell脚本包装器
    - 新增: `README_MAC_BUILD.md` - 打包工具文档
### 技术细节
    - 使用PyInstaller进行应用打包
    - 自动生成PyInstaller spec配置文件
    - 支持创建DMG分发包（使用hdiutil）
    - 包含所有必要的资源文件和配置
    - 自动处理应用签名和权限设置

## [2025-01-18 16:30] - 新增统一启动器

### 新增
- 创建 `start_unified.py` 统一启动器核心脚本
- 创建 `start_unified.bat` Windows批处理启动脚本
- 创建 `start_unified.sh` macOS/Linux Shell启动脚本
- 添加 `README_UNIFIED_LAUNCHER.md` 详细使用说明文档
- 支持一键同时启动服务端和客户端
- 支持仅启动服务端或客户端的灵活模式
- 支持后台模式运行（无GUI界面）
- 完整的进程管理和错误处理机制
- 跨平台兼容性（Windows、macOS、Linux）

### 优化
- 向下兼容原有启动方式，不影响现有使用习惯
- 自动检测进程冲突，避免重复启动
- 优雅的信号处理和进程清理机制
- 用户友好的错误提示和帮助信息

### 修改文件
- 新增：`start_unified.py` - 统一启动器核心逻辑
- 新增：`start_unified.bat` - Windows批处理脚本
- 新增：`start_unified.sh` - macOS/Linux Shell脚本
- 新增：`README_UNIFIED_LAUNCHER.md` - 使用说明文档

### 技术细节
- 使用 subprocess 模块管理子进程
- 支持命令行参数：--server-only, --client-only, --background, --help, --version
- 自动检测操作系统并使用相应的启动方式
- 集成现有配置系统，遵循用户设置
- 完整的依赖检查和错误恢复机制

### 使用方法
- Windows: `start_unified.bat` 或 `python start_unified.py`
- macOS/Linux: `./start_unified.sh` 或 `python3 start_unified.py`
- 支持多种启动模式和参数组合

## [2025-01-18 16:15] - 新增 --dir 参数支持

### 新增
- 添加 `--dir` 命令行参数，专门用于批量处理文件夹中的媒体文件
- 增强文件类型检查，确保只处理支持的媒体格式
- 添加参数冲突检查，防止 `--file` 和 `--dir` 同时使用

### 优化
- 改进 `--file` 参数描述，明确其用于处理单个文件
- 增强错误提示信息，提供更清晰的用户反馈
- 优化文件扫描逻辑，提供处理进度信息

### 修改文件
- `core_client.py`: 添加 --dir 参数支持和相关处理逻辑

### 技术细节
- `--file` 参数：用于处理单个文件
- `--dir` 参数：用于批量处理文件夹中的所有媒体文件
- 支持的媒体格式：.mp4, .avi, .mov, .mkv, .flv, .wmv, .mp3, .wav, .flac, .aac, .ogg, .m4a, .wma, .amr, .opus, .ac3, .eac3, .dts, .ape, .alac, .aiff, .caf
- 递归扫描子文件夹中的媒体文件

## [2024-12-19] - 修复文件路径解析错误

### 问题描述
- 使用 `--file` 参数处理文件时，程序错误地将 `--file` 标志本身作为文件路径处理
- 导致文件不存在错误和无法估算音频长度的问题

### 解决方案
- 修复 `core_client.py` 中的命令行参数解析逻辑
- 将 `input_paths = [Path(p) for p in sys.argv[1:]]` 改为 `input_paths = [Path(args.file)]`
- 确保正确使用 argparse 解析后的文件路径参数
- **修复了core_client.py命令行参数错误**：将文件路径作为位置参数改为使用--file参数

### 修改文件
- `core_client.py`: 修复文件路径解析逻辑

### 技术细节
- 原代码错误地使用 `sys.argv[1:]` 获取所有命令行参数，包括标志名称
- 修复后直接使用 `args.file` 获取正确的文件路径

## [2024-12-31] - transcription_gui 批量转录调试增强

### 改进
- **批量转录调试**: 在 `TranscriptionWorker` 中添加详细的结果文件检查和信号发出日志
- **文件状态监控**: 增加对 `.merge.txt`、`.txt` 和 `.srt` 文件存在性的检查日志
- **信号追踪**: 添加 `transcription_completed` 和 `transcription_failed` 信号发出的调试信息
- **结果读取监控**: 记录从结果文件中读取的文本长度

### 技术细节
- 在转录完成后增加文件存在性检查日志
- 记录结果文本读取过程和长度信息
- 追踪信号发出的时机和状态
- 帮助诊断批量转录中断问题

### 用户体验
- 提供更详细的转录过程调试信息
- 帮助用户了解批量转录为何可能中断
- 便于排查转录结果文件相关问题

## [2024-12-19-16:45] - 实时服务器消息打印功能优化

### 优化
- 优化 `transcription_gui` 中的服务器消息打印功能
  - 将 `subprocess.run` 改为 `subprocess.Popen` 实现实时输出
  - 转录过程中可以实时看到服务器返回的消息
  - 保持超时检查和取消检查功能
  - 提升用户体验，便于实时监控转录进度

## [未发布] - 2024-12-19

### 新增
- **大模型服务详细日志记录功能**
  - 新增 `logger_utils.py` 统一日志工具，提供 `ModelServiceLogger` 类
  - 为所有AI模型服务（DeepSeek、豆包、Claude、LM Studio）添加完整的请求参数和响应结果日志
  - 记录API请求的详细信息：端点、模型、温度、最大令牌数、请求载荷等
  - 记录API响应的完整数据：响应内容、处理时长、成功状态等
  - 添加WebSocket连接和消息处理的事件日志
  - 支持敏感信息过滤，保护API密钥等隐私数据
  - 提供统一的日志格式和错误处理机制
- **transcription_gui 服务器消息打印功能**
  - 在 `TranscriptionWorker` 中添加服务器消息打印功能
  - 实时显示 `core_client.py` 的标准输出和错误输出
  - 在转录成功、失败和重试时都显示服务器通信信息
  - 帮助用户了解转录过程中的详细状态和错误信息

## [未发布] - 2024-12-19

### 修复
- **server_ws_send**: WebSocket 发送调试增强和问题修复
  - 添加缺失的 `import websockets` 语句
  - 修复了 `websockets.exceptions.ConnectionClosed` 异常处理失败的问题
  - 添加详细的消息发送调试日志，包括结果信息、消息内容、连接状态检查
  - 增强 WebSocket 状态监控，显示连接状态和消息长度
  - 帮助诊断服务器显示发送成功但客户端未收到消息的问题
- **server_init_recognizer**: 修复最终任务结果为空时未发送结束标识的问题
  - 当 `is_final=True` 且识别结果为空时，现在会发送空结果作为结束标识
  - 确保客户端能够正确接收到转录结束信号，即使没有识别内容
  - 添加详细的调试日志来区分最终任务和非最终任务的处理逻辑
- **DeepSeekConfig配置类属性缺失修复**
  - 在 `util/config.py` 中的 `DeepSeekConfig` 类添加 `base_url` 属性，默认值为 `https://api.deepseek.com/v1`
  - 解决 `web_unified_app.py` 中 `/api/config/get` 路由尝试访问不存在的 `DeepSeekConfig.base_url` 属性导致的 `type object 'DeepSeekConfig' has no attribute 'base_url'` 错误
  
  **影响文件:**
  - `util/config.py`
  - `agent/logger_utils.py`
  - `agent/model_services/deepseek_service.py`
  - `agent/model_services/doubao_service.py`
  - `agent/model_services/claude_service.py`
  - `agent/model_services/lmstudio_service.py`
- **transcription_gui 转录过程调试增强**
  - 修复 `core_client.py` 中 `input()` 语句导致 `transcription_gui` 无法接收转录完成信号的问题
  - 在命令行调用时（如被 `transcription_gui` 调用）直接退出，不再等待用户输入
  - 通过检查 `sys.argv` 长度判断是否为命令行调用
  - 保持交互式使用时的原有行为不变
  - 在 `transcription_gui` 中增强批量转录调试日志
  - 在 `on_transcription_completed` 方法中添加详细的文件匹配和状态更新日志
  - 在 `transcribe_next_file` 方法中添加文件处理流程的调试信息
  - 增强可调试性，帮助排查多文件转录问题

- **配置管理API缺失修复**
  - 修正 `config.html` 中 `loadConfig` 函数的API调用路径，将 `/api/config/load` 修改为 `/api/config/get`
  - 在 `web_unified_app.py` 中新增所有缺失的配置管理API路由：
    - `/api/config/save` - 保存配置
    - `/api/config/reset` - 重置配置
    - `/api/config/export` - 导出配置
    - `/api/config/import` - 导入配置
    - `/api/config/test-model` - 模型连接测试
    - `/api/config/test-translation` - 翻译服务测试
  - 添加 `datetime` 模块导入以支持配置导出时间戳
  - 解决前端因接收HTML格式的404错误页面而导致的 `Unexpected token '<'` 错误
  
  **影响文件:**
  - `web_templates/config.html`
  - `web_unified_app.py`

### 功能增强
- **文件转录功能实现**
  - 集成 `core_client.py` 中的 `main_file` 函数到网页版 `/api/transcribe` API
  - 替换模拟转录结果为真实的Paraformer/SenseVoice语音识别服务
  - 支持音频和视频文件的实际转录处理，生成 `.txt`、`.merge.txt`、`.srt` 等格式文件
  - 添加后台线程处理转录任务，避免阻塞网页响应
  - 通过SocketIO实时推送转录进度和结果
  - 更新前端页面支持新的SocketIO事件：`transcription_start`、`transcription_result`、`transcription_error`
  - 改进用户体验，显示转录进度和状态信息
  
  **影响文件:**
  - `web_unified_app.py`
  - `web_templates/transcription.html`

## [2025-01-18 15:45] - 标点模型返回值格式兼容性修复

### 修复
- **标点模型返回值格式问题**: 修复了标点模型返回元组格式时被误判为无效的问题
  - **问题原因**: 代码只检查 `isinstance(punc_result, list)`，但标点模型实际返回元组格式 `('从前有座山山里有座庙。', [1, 1, 1, 1, 3])`
  - **解决方案**: 更新类型检查逻辑，支持列表、元组和字符串三种返回格式
  - **修改文件**: `util/server_recognize_paraformer.py`

### 技术细节
- 将 `isinstance(punc_result, list)` 改为 `isinstance(punc_result, (list, tuple))`
- 添加对字符串类型返回值的支持
- 增强错误提示信息，显示具体的返回值类型
- 确保标点功能能够正常工作，提取元组第一个元素作为带标点的文本

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