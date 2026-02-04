#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图形化转录工具
支持音频和视频文件的转录，提供直观的文件管理和结果展示界面
"""

import sys
import os
import subprocess
import threading
import asyncio
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import platform

# 导入长文本处理相关组件
try:
    from agent.long_text_processor import LongTextProcessor
    LONG_TEXT_AVAILABLE = True
except ImportError:
    LongTextProcessor = None
    LONG_TEXT_AVAILABLE = False
    print("[警告] 无法导入长文本处理模块，长文本处理功能将不可用")

from PySide6.QtCore import (
    Qt, QThread, Signal, QTimer, QMimeData, QUrl, QSize
)
from PySide6.QtGui import (
    QIcon, QFont, QPixmap, QPainter, QColor, QDragEnterEvent, QDropEvent, QDragMoveEvent
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QTextEdit, QPushButton, QLabel,
    QProgressBar, QSplitter, QGroupBox, QFileDialog, QMessageBox,
    QStatusBar, QMenuBar, QMenu, QToolBar, QFrame, QScrollArea,
    QCheckBox, QTabWidget, QComboBox, QSpinBox, QLineEdit
)

# 导入提示词配置管理器
from util.prompt_config_manager import prompt_config_manager


class LongTextProcessingWorker(QThread):
    """长文本处理工作线程"""
    progress_updated = Signal(str)  # 进度信息
    processing_completed = Signal(str)  # 处理完成，返回结果
    processing_failed = Signal(str)  # 处理失败，返回错误信息
    
    def __init__(self, text: str, process_type: str, model_type: str, max_tokens: int = 4000, system_prompt: str = None, user_prompt: str = None):
        super().__init__()
        self.text = text
        self.process_type = process_type
        self.model_type = model_type
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.is_cancelled = False
        self.processor = None


class LongTextBatchProcessingWorker(QThread):
    """长文本批量处理工作线程"""
    progress_updated = Signal(str)  # 进度信息
    file_completed = Signal(str, str, str)  # 单个文件完成，参数：文件路径、输出路径、结果
    processing_completed = Signal(list)  # 全部处理完成，返回结果列表
    processing_failed = Signal(str)  # 处理失败，返回错误信息
    
    def __init__(self, file_list: List[str], process_type: str, model_type: str, 
                 max_tokens: int = 4000, system_prompt: str = None, 
                 user_prompt: str = None, output_dir: str = None, start_index: int = 0):
        super().__init__()
        self.file_list = file_list
        self.process_type = process_type
        self.model_type = model_type
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.output_dir = output_dir
        self.start_index = start_index
        self.is_cancelled = False
        self.processor = None
        self.results = []
    
    def run(self):
        """执行批量长文本处理任务"""
        try:
            if LongTextProcessor is None:
                self.processing_failed.emit("长文本处理模块未安装")
                return
            
            self.progress_updated.emit("初始化处理器...")
            config = {
                "max_tokens_per_segment": self.max_tokens
            }
            self.processor = LongTextProcessor(
                model_type=self.model_type,
                config=config
            )
            
            if self.is_cancelled:
                return
            
            total_files = len(self.file_list)
            
            # 创建事件循环来运行异步方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # 从指定索引开始处理文件
                for i in range(self.start_index, len(self.file_list)):
                    file_path = self.file_list[i]
                    if self.is_cancelled:
                        break
                    
                    self.progress_updated.emit(f"处理文件 {i+1}/{total_files}: {os.path.basename(file_path)}")
                    
                    try:
                        # 读取文件内容
                        with open(file_path, 'r', encoding='utf-8') as f:
                            text = f.read().strip()
                        
                        if not text:
                            self.progress_updated.emit(f"跳过空文件: {os.path.basename(file_path)}")
                            continue
                        
                        if len(text) < 50:
                            self.progress_updated.emit(f"跳过文本过短的文件: {os.path.basename(file_path)}")
                            continue
                        
                        # 处理文本
                        result = loop.run_until_complete(
                            self.processor.process(text, self.process_type, 
                                                 system_prompt=self.system_prompt, 
                                                 user_prompt=self.user_prompt)
                        )
                        
                        if self.is_cancelled:
                            break
                        
                        # 确定输出文件路径
                        if self.output_dir:
                            # 使用指定的输出目录
                            os.makedirs(self.output_dir, exist_ok=True)
                            base_name = os.path.splitext(os.path.basename(file_path))[0]
                            output_path = os.path.join(self.output_dir, f"{base_name}_processed.md")
                        else:
                            # 使用源文件同目录
                            base_name = os.path.splitext(file_path)[0]
                            output_path = f"{base_name}_processed.md"
                        
                        # 保存处理结果
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(result)
                        
                        # 记录结果
                        result_info = {
                            'input_file': file_path,
                            'output_file': output_path,
                            'result': result,
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        self.results.append(result_info)
                        
                        # 发送单个文件完成信号
                        self.file_completed.emit(file_path, output_path, result)
                        
                    except Exception as e:
                        error_msg = f"处理文件 {os.path.basename(file_path)} 时出错: {str(e)}"
                        self.progress_updated.emit(error_msg)
                        print(f"[错误] {error_msg}")
                        continue
                
                if not self.is_cancelled:
                    self.processing_completed.emit(self.results)
                
            finally:
                loop.close()
                
        except Exception as e:
            self.processing_failed.emit(f"批量处理过程中出错: {str(e)}")
    
    def cancel(self):
        """取消处理任务"""
        self.is_cancelled = True
        self.terminate()

    def run_original(self):
        """执行长文本处理任务"""
        try:
            if LongTextProcessor is None:
                self.processing_failed.emit("长文本处理模块未安装")
                return
            
            self.progress_updated.emit("初始化处理器...")
            config = {
                "max_tokens_per_segment": self.max_tokens
            }
            self.processor = LongTextProcessor(
                model_type=self.model_type,
                config=config
            )
            
            if self.is_cancelled:
                return
            
            self.progress_updated.emit("开始处理文本...")
            
            # 创建事件循环来运行异步方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    self.processor.process(self.text, self.process_type, system_prompt=self.system_prompt, user_prompt=self.user_prompt)
                )
                
                if self.is_cancelled:
                    return
                
                self.processing_completed.emit(result)
                
            finally:
                loop.close()
                
        except Exception as e:
            self.processing_failed.emit(f"处理过程中出错: {str(e)}")
    
    def cancel(self):
        """取消处理任务"""
        self.is_cancelled = True
        self.terminate()


class TranscriptionWorker(QThread):
    """转录工作线程"""
    progress_updated = Signal(str, str)  # filename, status
    transcription_completed = Signal(str, str, str)  # filename, result_text, srt_path
    transcription_failed = Signal(str, str)  # filename, error_message
    
    def __init__(self, file_path: Path, generate_srt: bool = True, output_dir: str = None):
        super().__init__()
        self.file_path = file_path
        self.generate_srt = generate_srt
        self.output_dir = output_dir
        self.is_cancelled = False
    
    def run(self):
        """执行转录任务"""
        try:
            filename = self.file_path.name
            self.progress_updated.emit(filename, "开始转录...")
            
            # 检查文件是否存在
            if not self.file_path.exists():
                self.transcription_failed.emit(filename, f"TranscriptionWorker 运行时文件不存在: {self.file_path}")
                return
            
            # 检查是否已有转录结果
            if self.output_dir:
                # 如果指定了输出目录，则在输出目录中查找结果文件
                output_path = Path(self.output_dir)
                base_name = self.file_path.stem
                txt_file = output_path / f"{base_name}.txt"
                merge_file = output_path / f"{base_name}.merge.txt"
                srt_file = output_path / f"{base_name}.srt"
            else:
                # 默认与源文件同目录
                txt_file = self.file_path.with_suffix('.txt')
                merge_file = self.file_path.with_suffix('.merge.txt')
                srt_file = self.file_path.with_suffix('.srt')
            
            if txt_file.exists() or merge_file.exists():
                self.progress_updated.emit(filename, "发现已有转录结果")
                # 读取现有结果
                result_text = ""
                if merge_file.exists():
                    with open(merge_file, 'r', encoding='utf-8') as f:
                        result_text = f.read().strip()
                elif txt_file.exists():
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        result_text = f.read().strip()
                
                srt_path = str(srt_file) if srt_file.exists() else ""
                self.transcription_completed.emit(filename, result_text, srt_path)
                return
            
            # 执行转录
            self.progress_updated.emit(filename, "正在转录中...")
            
            # 调用core_client.py进行转录，添加重试机制
            max_retries = 3
            retry_delay = 5  # 秒
            
            for attempt in range(max_retries):
                # 检查是否已取消
                print(f"[转录状态] 重试循环开始，第{attempt+1}次尝试，取消状态: {self.is_cancelled}")
                if self.is_cancelled:
                    print(f"[转录取消] 检测到取消状态，退出转录")
                    return
                    
                try:
                    if attempt > 0:
                        self.progress_updated.emit(filename, f"重试转录中... (第{attempt+1}次尝试)")
                        # 等待一段时间再重试，避免连接冲突
                        import time
                        time.sleep(retry_delay * attempt)
                        
                        # 再次检查是否已取消（在sleep之后）
                        print(f"[转录状态] sleep后检查取消状态: {self.is_cancelled}")
                        if self.is_cancelled:
                            print(f"[转录取消] sleep后检测到取消状态，退出转录")
                            return
                    
                    # 调用core_client.py进行转录
                    cmd = [sys.executable, 'core_client.py', '--file', str(self.file_path)]
                    
                    # 添加输出目录参数
                    if self.output_dir:
                        cmd.extend(['--output-dir', self.output_dir])
                    
                    # 使用 Popen 实现实时输出
                    print(f"[转录命令] 执行命令: {' '.join(cmd)}")
                    process = subprocess.Popen(
                        cmd,
                        cwd=os.getcwd(),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        universal_newlines=True
                    )
                    
                    # 实时读取并打印输出
                    stdout_lines = []
                    import time
                    start_time = time.time()
                    timeout = 3600  # 1小时超时
                    
                    while True:
                        # 检查超时
                        if time.time() - start_time > timeout:
                            process.terminate()
                            process.wait()
                            raise subprocess.TimeoutExpired(cmd, timeout)
                        
                        # 检查是否取消
                        if self.is_cancelled:
                            process.terminate()
                            process.wait()
                            return
                        
                        output = process.stdout.readline()
                        if output == '' and process.poll() is not None:
                            break
                        if output:
                            output = output.strip()
                            print(f"[服务器消息] {output}")
                            stdout_lines.append(output)
                    
                    # 等待进程结束
                    return_code = process.wait()
                    
                    # 创建一个模拟的 result 对象以保持兼容性
                    class MockResult:
                        def __init__(self, returncode, stdout, stderr):
                            self.returncode = returncode
                            self.stdout = '\n'.join(stdout_lines) if stdout_lines else ''
                            self.stderr = stderr or ''
                    
                    result = MockResult(return_code, stdout_lines, '')
                    
                    # 检查是否已取消（在subprocess执行之后）
                    print(f"[转录状态] subprocess执行后检查取消状态: {self.is_cancelled}")
                    if self.is_cancelled:
                        print(f"[转录取消] subprocess执行后检测到取消状态，退出转录")
                        return
                    
                    # 如果成功执行，跳出重试循环
                    if result.returncode == 0:
                        break
                    elif attempt == max_retries - 1:
                        # 最后一次尝试失败
                        error_msg = result.stderr or result.stdout or '转录进程执行失败'
                        print(f"[服务器消息-最终失败] 标准输出: {result.stdout}")
                        print(f"[服务器消息-最终失败] 错误输出: {result.stderr}")
                        self.transcription_failed.emit(filename, f"转录失败 (尝试{max_retries}次): {error_msg}")
                        return
                    else:
                        # 非最后一次尝试，记录错误但继续重试
                        error_msg = result.stderr or result.stdout or '转录进程执行失败'
                        print(f"[服务器消息-重试] 第{attempt+1}次尝试，标准输出: {result.stdout}")
                        print(f"[服务器消息-重试] 第{attempt+1}次尝试，错误输出: {result.stderr}")
                        print(f"[转录重试] 第{attempt+1}次尝试失败: {error_msg}")
                        
                except subprocess.TimeoutExpired:
                    if attempt == max_retries - 1:
                        self.transcription_failed.emit(filename, f"转录超时（超过1小时，尝试{max_retries}次）")
                        return
                    else:
                        print(f"[转录重试] 第{attempt+1}次尝试超时")
                except Exception as e:
                    if attempt == max_retries - 1:
                        self.transcription_failed.emit(filename, f"转录过程中出错 (尝试{max_retries}次): {str(e)}")
                        return
                    else:
                        print(f"[转录重试] 第{attempt+1}次尝试出错: {str(e)}")
            
            if self.is_cancelled:
                return
            
            # 读取转录结果
            result_text = ""
            # 重新计算文件路径（因为可能使用了自定义输出目录）
            if self.output_dir:
                output_path = Path(self.output_dir)
                base_name = self.file_path.stem
                merge_file = output_path / f"{base_name}.merge.txt"
                txt_file = output_path / f"{base_name}.txt"
                srt_file = output_path / f"{base_name}.srt"
            else:
                merge_file = self.file_path.with_suffix('.merge.txt')
                txt_file = self.file_path.with_suffix('.txt')
                srt_file = self.file_path.with_suffix('.srt')
            
            print(f"[结果文件检查] merge_file: {merge_file}, 存在: {merge_file.exists()}")
            print(f"[结果文件检查] txt_file: {txt_file}, 存在: {txt_file.exists()}")
            print(f"[结果文件检查] srt_file: {srt_file}, 存在: {srt_file.exists()}")
            
            if merge_file.exists():
                with open(merge_file, 'r', encoding='utf-8') as f:
                    result_text = f.read().strip()
                print(f"[结果读取] 从 merge_file 读取到文本长度: {len(result_text)}")
            elif txt_file.exists():
                with open(txt_file, 'r', encoding='utf-8') as f:
                    result_text = f.read().strip()
                print(f"[结果读取] 从 txt_file 读取到文本长度: {len(result_text)}")
            else:
                print(f"[结果读取] 未找到任何结果文件")
            
            if result_text:
                # 根据设置决定是否提供字幕文件路径
                srt_path = ""
                if self.generate_srt and srt_file.exists():
                    srt_path = str(srt_file)
                print(f"[信号发出] 准备发出 transcription_completed 信号，文本长度: {len(result_text)}")
                self.transcription_completed.emit(filename, result_text, srt_path)
                print(f"[信号发出] transcription_completed 信号已发出")
            else:
                print(f"[信号发出] 结果文本为空，发出 transcription_failed 信号")
                self.transcription_failed.emit(filename, "转录完成，但未生成文本内容")
                
        except subprocess.TimeoutExpired:
            self.transcription_failed.emit(filename, "转录超时（超过1小时）")
        except Exception as e:
            self.transcription_failed.emit(filename, f"转录过程中出错: {str(e)}")
    
    def cancel(self):
        """取消转录任务"""
        print(f"[转录取消] 收到取消信号，设置取消标志")
        self.is_cancelled = True
        print(f"[转录取消] 取消标志已设置: {self.is_cancelled}")
        self.terminate()
        print(f"[转录取消] 已调用terminate()")


class FileListWidget(QListWidget):
    """支持拖拽的文件列表控件"""
    files_dropped = Signal(list)  # 文件拖拽信号
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDropMode.DropOnly)
        
        # 设置样式
        self.setStyleSheet("""
            QListWidget {
                border: 2px dashed #aaa;
                border-radius: 10px;
                background-color: #f9f9f9;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        print(f"[拖拽调试] dragEnterEvent 被触发")
        if event.mimeData().hasUrls():
            print(f"[拖拽调试] 检测到URL数据，接受拖拽")
            event.acceptProposedAction()
        else:
            print(f"[拖拽调试] 没有URL数据，忽略拖拽")
            event.ignore()
    
    def dragLeaveEvent(self, event):
        print(f"[拖拽调试] dragLeaveEvent 被触发 - 文件离开了拖拽区域")
        super().dragLeaveEvent(event)
    
    def dragMoveEvent(self, event: QDragMoveEvent):
        print(f"[拖拽调试] dragMoveEvent 被触发 - 文件在区域内移动")
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        print(f"[拖拽调试] dropEvent 被触发")
        files = []
        
        # 检查是否有URL数据
        if not event.mimeData().hasUrls():
            print(f"[拖拽调试] 没有URL数据，忽略拖拽")
            event.ignore()
            return
            
        urls = event.mimeData().urls()
        print(f"[拖拽调试] 获取到 {len(urls)} 个URL")
        
        for url in urls:
            print(f"[拖拽调试] 处理URL: {url.toString()}")
            if url.isLocalFile():
                file_path = Path(url.toLocalFile())
                print(f"[拖拽调试] 本地文件路径: {file_path}")
                print(f"[拖拽调试] 文件扩展名: {file_path.suffix.lower()}")
                if self.is_supported_file(file_path):
                    print(f"[拖拽调试] 文件格式支持，添加到列表")
                    files.append(file_path)
                else:
                    print(f"[拖拽调试] 文件格式不支持")
            else:
                print(f"[拖拽调试] 非本地文件，跳过")
        
        print(f"[拖拽调试] 最终有效文件数量: {len(files)}")
        if files:
            print(f"[拖拽调试] 发出 files_dropped 信号")
            self.files_dropped.emit(files)
            event.accept()  # 明确接受事件
        else:
            print(f"[拖拽调试] 没有有效文件，忽略事件")
            event.ignore()
        
        print(f"[拖拽调试] dropEvent 处理完成")
    
    def is_supported_file(self, file_path: Path) -> bool:
        """检查是否为支持的文件格式"""
        supported_extensions = {
            # 音频格式
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.amr', '.opus', '.ac3', '.eac3', '.dts', '.ape', '.alac', '.aiff', '.caf',
            # 视频格式
            '.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m3u8', '.ts', '.vob', '.ogv', '.divx', '.xvid', '.rm', '.rmvb', '.mpg', '.mpeg', '.3gp', '.mxf', '.asf', '.dat',
            # 文本格式（用于长文本处理）
            '.txt', '.md', '.rtf'
        }
        return file_path.suffix.lower() in supported_extensions


class TranscriptionResultWidget(QTextEdit):
    """转录结果显示控件"""
    
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setPlaceholderText("转录结果将在这里显示...")
        
        # 设置字体
        font = QFont("Microsoft YaHei", 12)
        self.setFont(font)
        
        # 设置样式
        self.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                background-color: white;
                line-height: 1.5;
            }
        """)


class TranscriptionGUI(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.file_list = []  # 文件列表
        self.transcription_results = {}  # 转录结果缓存
        self.current_worker = None  # 当前转录工作线程
        
        # 长文本处理相关属性
        self.long_text_worker = None  # 长文本处理工作线程
        self.long_text_history = []  # 长文本处理历史
        self.long_text_file_list = []  # 长文本文件列表
        self.long_text_processing_results = []  # 长文本处理结果缓存
        
        self.init_ui()
        self.setup_connections()
    
    def show_system_notification(self, title: str, message: str):
        """显示系统通知"""
        print(f"[通知调试] 尝试显示通知: {title} - {message}")
        
        # 首先在状态栏显示消息
        self.status_bar.showMessage(f"✅ {message}", 10000)  # 显示10秒
        
        try:
            system = platform.system()
            print(f"[通知调试] 检测到系统: {system}")
            
            if system == "Darwin":  # macOS
                # 使用osascript显示通知
                script = f'display notification "{message}" with title "{title}"'
                print(f"[通知调试] 执行脚本: {script}")
                result = subprocess.run(["osascript", "-e", script], 
                                      capture_output=True, text=True, check=False)
                print(f"[通知调试] osascript返回码: {result.returncode}")
                if result.stderr:
                    print(f"[通知调试] osascript错误: {result.stderr}")
                    
                # 如果系统通知可能不可见，显示一个临时的状态提示
                self.show_temporary_status_message(f"🎉 {title}: {message}")
                    
            elif system == "Windows":
                # Windows 10/11 通知
                try:
                    import win10toast
                    toaster = win10toast.ToastNotifier()
                    toaster.show_toast(title, message, duration=5)
                    print(f"[通知调试] Windows通知已发送")
                except ImportError:
                    print(f"[通知调试] win10toast未安装，使用备用方案")
                    # 如果没有win10toast，使用状态提示
                    self.show_temporary_status_message(f"🎉 {title}: {message}")
            elif system == "Linux":
                # Linux 使用 notify-send
                result = subprocess.run(["notify-send", title, message], 
                                      capture_output=True, text=True, check=False)
                print(f"[通知调试] notify-send返回码: {result.returncode}")
                if result.stderr:
                    print(f"[通知调试] notify-send错误: {result.stderr}")
            else:
                # 其他系统使用状态提示
                print(f"[通知调试] 未知系统，使用状态提示")
                self.show_temporary_status_message(f"🎉 {title}: {message}")
        except Exception as e:
            print(f"[通知错误] 无法显示系统通知: {e}")
            # 备用方案：显示状态提示
            self.show_temporary_status_message(f"🎉 {title}: {message}")
    
    def show_temporary_status_message(self, message: str):
        """显示临时状态消息"""
        # 在状态栏显示消息
        self.status_bar.showMessage(message, 15000)  # 显示15秒
        
        # 创建一个定时器来闪烁状态栏
        self.flash_timer = QTimer()
        self.flash_count = 0
        self.original_style = self.status_bar.styleSheet()
        
        def flash_status():
            self.flash_count += 1
            if self.flash_count <= 6:  # 闪烁3次（每次2个状态）
                if self.flash_count % 2 == 1:
                    # 高亮状态
                    self.status_bar.setStyleSheet(
                        "QStatusBar { background-color: #4CAF50; color: white; font-weight: bold; }"
                    )
                else:
                    # 正常状态
                    self.status_bar.setStyleSheet(self.original_style)
            else:
                # 停止闪烁，恢复原样
                self.status_bar.setStyleSheet(self.original_style)
                self.flash_timer.stop()
        
        self.flash_timer.timeout.connect(flash_status)
        self.flash_timer.start(500)  # 每500ms切换一次
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("CapsWriter 多功能处理工具")
        self.setWindowIcon(QIcon("assets/appicon.ico"))
        self.resize(1400, 900)
        
        # 创建中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建标签页控件
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建音视频转录标签页
        transcription_tab = self.create_transcription_tab()
        self.tab_widget.addTab(transcription_tab, "音视频转录")
        
        # 创建长文本处理标签页
        long_text_tab = self.create_long_text_tab()
        self.tab_widget.addTab(long_text_tab, "长文本处理")
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建状态栏
        self.create_status_bar()
    
    def create_transcription_tab(self) -> QWidget:
        """创建音视频转录标签页"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # 左侧面板 - 文件管理
        left_panel = self.create_file_panel()
        splitter.addWidget(left_panel)
        
        # 右侧面板 - 转录结果
        right_panel = self.create_result_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setSizes([400, 800])
        
        return tab
    
    def create_long_text_tab(self) -> QWidget:
        """创建长文本处理标签页"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # 左侧面板 - 文本输入和设置
        left_panel = self.create_long_text_input_panel()
        splitter.addWidget(left_panel)
        
        # 右侧面板 - 处理结果
        right_panel = self.create_long_text_result_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setSizes([500, 900])
        
        return tab
    
    def create_long_text_input_panel(self) -> QWidget:
        """创建长文本文件管理面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 文件列表组
        file_group = QGroupBox("文本文件列表")
        file_layout = QVBoxLayout(file_group)
        
        # 文件列表控件
        self.long_text_file_list_widget = FileListWidget()
        self.long_text_file_list_widget.setMinimumHeight(300)
        self.long_text_file_list_widget.files_dropped.connect(self.add_text_files_from_drop)
        file_layout.addWidget(self.long_text_file_list_widget)
        
        # 文件操作按钮
        file_button_layout = QHBoxLayout()
        
        self.long_text_add_files_btn = QPushButton("添加文本文件")
        self.long_text_add_files_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon))
        self.long_text_add_files_btn.clicked.connect(self.add_text_files)
        file_button_layout.addWidget(self.long_text_add_files_btn)
        
        self.long_text_remove_file_btn = QPushButton("移除文件")
        self.long_text_remove_file_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_TrashIcon))
        self.long_text_remove_file_btn.clicked.connect(self.remove_selected_text_file)
        file_button_layout.addWidget(self.long_text_remove_file_btn)
        
        self.long_text_clear_list_btn = QPushButton("清空列表")
        self.long_text_clear_list_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DialogResetButton))
        self.long_text_clear_list_btn.clicked.connect(self.clear_text_file_list)
        file_button_layout.addWidget(self.long_text_clear_list_btn)
        
        file_layout.addLayout(file_button_layout)
        layout.addWidget(file_group)
        
        # 处理设置组
        settings_group = QGroupBox("处理设置")
        settings_layout = QVBoxLayout(settings_group)
        
        # 处理类型选择
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("处理类型:"))
        self.long_text_process_type = QComboBox()
        self.long_text_process_type.addItems(["总结", "润色", "纠错", "关键词提取", "结构化整理","纠正错误和划分段落，不总结"])
        # 连接处理类型变化信号
        self.long_text_process_type.currentTextChanged.connect(self.load_saved_prompts)
        type_layout.addWidget(self.long_text_process_type)
        settings_layout.addLayout(type_layout)
        
        # AI模型选择
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("AI模型:"))
        self.long_text_model = QComboBox()
        self.long_text_model.addItems(["deepseek", "doubao", "claude", "lmstudio"])
        model_layout.addWidget(self.long_text_model)
        settings_layout.addLayout(model_layout)
        
        # 高级设置
        advanced_layout = QHBoxLayout()
        advanced_layout.addWidget(QLabel("每段最大Token数:"))
        self.long_text_max_tokens = QSpinBox()
        self.long_text_max_tokens.setRange(1000, 1200000)
        self.long_text_max_tokens.setValue(40000)
        self.long_text_max_tokens.setSuffix(" tokens")
        advanced_layout.addWidget(self.long_text_max_tokens)
        settings_layout.addLayout(advanced_layout)
        
        # 系统设定
        system_prompt_layout = QVBoxLayout()
        system_prompt_header = QHBoxLayout()
        system_prompt_header.addWidget(QLabel("系统设定:"))
        system_prompt_header.addStretch()
        
        # 系统设定控制按钮
        self.reset_system_prompt_btn = QPushButton("重置默认")
        self.reset_system_prompt_btn.setMaximumWidth(80)
        self.reset_system_prompt_btn.setToolTip("恢复为您保存配置好的系统设定")
        self.reset_system_prompt_btn.clicked.connect(self.reset_system_prompt)
        system_prompt_header.addWidget(self.reset_system_prompt_btn)
        
        system_prompt_layout.addLayout(system_prompt_header)
        
        self.long_text_system_prompt = QTextEdit()
        self.long_text_system_prompt.setMaximumHeight(80)
        self.long_text_system_prompt.setPlaceholderText("输入系统设定提示词，用于指导AI的行为和角色...")
        self.long_text_system_prompt.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 5px;
                font-size: 12px;
            }
        """)
        system_prompt_layout.addWidget(self.long_text_system_prompt)
        settings_layout.addLayout(system_prompt_layout)
        
        # 用户设定
        user_prompt_layout = QVBoxLayout()
        user_prompt_header = QHBoxLayout()
        user_prompt_header.addWidget(QLabel("用户设定:"))
        user_prompt_header.addStretch()
        
        # 用户设定控制按钮
        self.reset_user_prompt_btn = QPushButton("重置默认")
        self.reset_user_prompt_btn.setMaximumWidth(80)
        self.reset_user_prompt_btn.setToolTip("恢复为您保存配置好的用户设定")
        self.reset_user_prompt_btn.clicked.connect(self.reset_user_prompt)
        user_prompt_header.addWidget(self.reset_user_prompt_btn)
        
        user_prompt_layout.addLayout(user_prompt_header)
        
        self.long_text_user_prompt = QTextEdit()
        self.long_text_user_prompt.setMaximumHeight(80)
        self.long_text_user_prompt.setPlaceholderText("输入用户设定提示词，用于补充具体的处理要求...")
        self.long_text_user_prompt.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 5px;
                font-size: 12px;
            }
        """)
        user_prompt_layout.addWidget(self.long_text_user_prompt)
        settings_layout.addLayout(user_prompt_layout)
        
        # 初始化默认提示词
        self.update_prompt_defaults()
        
        # 连接文本变化信号以实现自动保存
        self.long_text_system_prompt.textChanged.connect(self.save_current_prompts)
        self.long_text_user_prompt.textChanged.connect(self.save_current_prompts)
        
        # 加载用户之前保存的配置
        self.load_saved_prompts()
        
        # 输出目录选择
        output_dir_layout = QHBoxLayout()
        output_dir_label = QLabel("输出目录:")
        output_dir_layout.addWidget(output_dir_label)
        
        self.long_text_output_dir_edit = QLineEdit()
        self.long_text_output_dir_edit.setPlaceholderText("~/Documents/LongTextResults")
        self.long_text_output_dir_edit.setToolTip("指定处理结果文件的保存目录，留空则保存到源文件同目录")
        output_dir_layout.addWidget(self.long_text_output_dir_edit)
        
        self.long_text_browse_output_dir_btn = QPushButton("浏览")
        self.long_text_browse_output_dir_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DirOpenIcon))
        self.long_text_browse_output_dir_btn.clicked.connect(self.browse_long_text_output_directory)
        output_dir_layout.addWidget(self.long_text_browse_output_dir_btn)
        
        settings_layout.addLayout(output_dir_layout)
        
        layout.addWidget(settings_group)
        
        # 处理控制组
        control_group = QGroupBox("处理控制")
        control_layout = QVBoxLayout(control_group)
        
        # 开始处理按钮
        self.long_text_start_button = QPushButton("开始处理")
        self.long_text_start_button.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_MediaPlay))
        self.long_text_start_button.setMinimumHeight(40)
        self.long_text_start_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.long_text_start_button.clicked.connect(self.start_long_text_processing)
        control_layout.addWidget(self.long_text_start_button)
        
        # 停止处理按钮
        self.long_text_stop_button = QPushButton("停止处理")
        self.long_text_stop_button.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_MediaStop))
        self.long_text_stop_button.setEnabled(False)
        self.long_text_stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c1170a;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.long_text_stop_button.clicked.connect(self.stop_long_text_processing)
        control_layout.addWidget(self.long_text_stop_button)
        
        # 进度条
        self.long_text_progress = QProgressBar()
        self.long_text_progress.setVisible(False)
        control_layout.addWidget(self.long_text_progress)
        
        # 状态标签
        self.long_text_status = QLabel("就绪")
        self.long_text_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.long_text_status.setStyleSheet("""
            QLabel {
                padding: 5px;
                background-color: #e3f2fd;
                border: 1px solid #2196F3;
                border-radius: 3px;
                color: #1565C0;
            }
        """)
        control_layout.addWidget(self.long_text_status)
        
        layout.addWidget(control_group)
        
        # 添加弹性空间
        layout.addStretch()
        
        return panel
    
    def create_long_text_result_panel(self) -> QWidget:
        """创建长文本处理结果面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 创建标签页控件用于显示结果和历史
        self.long_text_result_tabs = QTabWidget()
        layout.addWidget(self.long_text_result_tabs)
        
        # 处理结果标签页
        result_tab = QWidget()
        result_layout = QVBoxLayout(result_tab)
        
        # 结果显示文本框
        self.long_text_result_widget = QTextEdit()
        self.long_text_result_widget.setReadOnly(True)
        self.long_text_result_widget.setPlaceholderText("处理结果将在这里显示...")
        self.long_text_result_widget.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                background-color: white;
                line-height: 1.5;
                font-size: 14px;
            }
        """)
        result_layout.addWidget(self.long_text_result_widget)
        
        # 结果操作按钮
        result_button_layout = QHBoxLayout()
        
        self.long_text_copy_button = QPushButton("复制结果")
        self.long_text_copy_button.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DialogSaveButton))
        self.long_text_copy_button.clicked.connect(self.copy_long_text_result)
        result_button_layout.addWidget(self.long_text_copy_button)
        
        self.long_text_save_button = QPushButton("保存结果")
        self.long_text_save_button.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DialogSaveButton))
        self.long_text_save_button.clicked.connect(self.save_long_text_result)
        result_button_layout.addWidget(self.long_text_save_button)
        
        self.long_text_export_button = QPushButton("导出文档")
        self.long_text_export_button.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon))
        self.long_text_export_button.clicked.connect(self.export_long_text_result)
        result_button_layout.addWidget(self.long_text_export_button)
        
        result_button_layout.addStretch()
        result_layout.addLayout(result_button_layout)
        
        self.long_text_result_tabs.addTab(result_tab, "处理结果")
        
        # 处理历史标签页
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        
        # 历史记录列表
        self.long_text_history_list = QListWidget()
        self.long_text_history_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        self.long_text_history_list.itemClicked.connect(self.load_long_text_history_item)
        history_layout.addWidget(self.long_text_history_list)
        
        # 历史操作按钮
        history_button_layout = QHBoxLayout()
        
        self.long_text_clear_history_button = QPushButton("清空历史")
        self.long_text_clear_history_button.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_TrashIcon))
        self.long_text_clear_history_button.clicked.connect(self.clear_long_text_history)
        history_button_layout.addWidget(self.long_text_clear_history_button)
        
        history_button_layout.addStretch()
        history_layout.addLayout(history_button_layout)
        
        self.long_text_result_tabs.addTab(history_tab, "处理历史")
        
        return panel
    
    def create_file_panel(self) -> QWidget:
        """创建文件管理面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 文件列表组
        file_group = QGroupBox("文件列表")
        file_layout = QVBoxLayout(file_group)
        
        # 文件列表控件
        self.file_list_widget = FileListWidget()
        self.file_list_widget.setMinimumHeight(300)
        file_layout.addWidget(self.file_list_widget)
        
        # 文件操作按钮
        button_layout = QHBoxLayout()
        
        self.add_files_btn = QPushButton("添加文件")
        self.add_files_btn.setIcon(QIcon("assets/files.png") if Path("assets/files.png").exists() else self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon))
        button_layout.addWidget(self.add_files_btn)
        
        self.remove_file_btn = QPushButton("移除文件")
        self.remove_file_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_TrashIcon))
        button_layout.addWidget(self.remove_file_btn)
        
        self.clear_list_btn = QPushButton("清空列表")
        self.clear_list_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DialogResetButton))
        button_layout.addWidget(self.clear_list_btn)
        
        file_layout.addLayout(button_layout)
        layout.addWidget(file_group)
        
        # 转录控制组
        control_group = QGroupBox("转录控制")
        control_layout = QVBoxLayout(control_group)
        
        # 转录按钮
        self.transcribe_btn = QPushButton("开始转录")
        self.transcribe_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_MediaPlay))
        self.transcribe_btn.setMinimumHeight(40)
        self.transcribe_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        control_layout.addWidget(self.transcribe_btn)
        
        # 停止按钮
        self.stop_btn = QPushButton("停止转录")
        self.stop_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_MediaStop))
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c1170a;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        control_layout.addWidget(self.stop_btn)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 5px;
                background-color: #e8f5e8;
                border: 1px solid #4CAF50;
                border-radius: 3px;
                color: #2e7d32;
            }
        """)
        control_layout.addWidget(self.status_label)
        
        layout.addWidget(control_group)
        
        # 转录设置组
        settings_group = QGroupBox("转录设置")
        settings_layout = QVBoxLayout(settings_group)
        
        # 字幕文件生成选项
        self.generate_srt_checkbox = QCheckBox("生成字幕文件 (.srt)")
        self.generate_srt_checkbox.setChecked(True)  # 默认生成字幕文件
        self.generate_srt_checkbox.setToolTip("勾选此项将在转录完成后生成SRT格式的字幕文件")
        self.generate_srt_checkbox.stateChanged.connect(self.on_srt_option_changed)
        settings_layout.addWidget(self.generate_srt_checkbox)
        
        # 输出目录选择
        output_dir_layout = QHBoxLayout()
        output_dir_label = QLabel("输出目录:")
        output_dir_layout.addWidget(output_dir_label)
        
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("~/Movies/Transcription")
        self.output_dir_edit.setToolTip("指定转录结果文件的保存目录，留空则保存到源文件同目录")
        output_dir_layout.addWidget(self.output_dir_edit)
        
        self.browse_output_dir_btn = QPushButton("浏览")
        self.browse_output_dir_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DirOpenIcon))
        self.browse_output_dir_btn.clicked.connect(self.browse_output_directory)
        output_dir_layout.addWidget(self.browse_output_dir_btn)
        
        settings_layout.addLayout(output_dir_layout)
        
        layout.addWidget(settings_group)
        
        # 添加弹性空间
        layout.addStretch()
        
        return panel
    
    def create_result_panel(self) -> QWidget:
        """创建结果显示面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 结果显示组
        result_group = QGroupBox("转录结果")
        result_layout = QVBoxLayout(result_group)
        
        # 当前文件标签
        self.current_file_label = QLabel("当前文件: 无")
        self.current_file_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                color: #1976d2;
                padding: 5px;
                background-color: #e3f2fd;
                border-radius: 3px;
            }
        """)
        result_layout.addWidget(self.current_file_label)
        
        # 转录结果文本框
        self.result_text_widget = TranscriptionResultWidget()
        result_layout.addWidget(self.result_text_widget)
        
        # 结果操作按钮
        result_button_layout = QHBoxLayout()
        
        self.copy_result_btn = QPushButton("复制结果")
        self.copy_result_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DialogSaveButton))
        result_button_layout.addWidget(self.copy_result_btn)
        
        self.save_result_btn = QPushButton("保存结果")
        self.save_result_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DialogSaveButton))
        result_button_layout.addWidget(self.save_result_btn)
        
        self.open_srt_btn = QPushButton("打开字幕文件")
        self.open_srt_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon))
        self.open_srt_btn.setEnabled(False)
        result_button_layout.addWidget(self.open_srt_btn)
        
        result_button_layout.addStretch()
        result_layout.addLayout(result_button_layout)
        
        layout.addWidget(result_group)
        
        return panel
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        add_files_action = file_menu.addAction("添加文件")
        add_files_action.setShortcut("Ctrl+O")
        add_files_action.triggered.connect(self.add_files)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("退出")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        
        # 转录菜单
        transcribe_menu = menubar.addMenu("转录")
        
        start_transcribe_action = transcribe_menu.addAction("开始转录")
        start_transcribe_action.setShortcut("F5")
        start_transcribe_action.triggered.connect(self.start_transcription)
        
        stop_transcribe_action = transcribe_menu.addAction("停止转录")
        stop_transcribe_action.setShortcut("Esc")
        stop_transcribe_action.triggered.connect(self.stop_transcription)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = help_menu.addAction("关于")
        about_action.triggered.connect(self.show_about)
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = self.addToolBar("主工具栏")
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        
        # 添加文件
        add_action = toolbar.addAction("添加文件")
        add_action.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon))
        add_action.triggered.connect(self.add_files)
        
        toolbar.addSeparator()
        
        # 开始转录
        start_action = toolbar.addAction("开始转录")
        start_action.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_MediaPlay))
        start_action.triggered.connect(self.start_transcription)
        
        # 停止转录
        stop_action = toolbar.addAction("停止转录")
        stop_action.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_MediaStop))
        stop_action.triggered.connect(self.stop_transcription)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
    
    def setup_connections(self):
        """设置信号连接"""
        # 文件列表相关
        self.file_list_widget.files_dropped.connect(self.add_files_from_drop)
        self.file_list_widget.itemSelectionChanged.connect(self.on_file_selection_changed)
        
        # 转录相关按钮连接
        self.add_files_btn.clicked.connect(self.add_files)
        self.remove_file_btn.clicked.connect(self.remove_selected_file)
        self.clear_list_btn.clicked.connect(self.clear_file_list)
        self.transcribe_btn.clicked.connect(self.start_transcription)
        self.stop_btn.clicked.connect(self.stop_transcription)
        
        # 转录结果操作按钮
        self.copy_result_btn.clicked.connect(self.copy_result)
        self.save_result_btn.clicked.connect(self.save_result)
        self.open_srt_btn.clicked.connect(self.open_srt_file)
        
        # 长文本处理相关按钮连接（这些连接已在UI创建时设置）
        # 注意：按钮的点击事件连接已在各自的UI创建方法中完成
    
    def add_files(self):
        """添加文件对话框"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilter(
            "音视频文件 (*.mp3 *.wav *.flac *.aac *.ogg *.m4a *.wma *.mp4 *.avi *.mov *.mkv *.flv *.wmv *.webm *.3gp *.m3u8 *.ts *.vob *.ogv *.divx *.xvid *.rm *.rmvb *.mpg *.mpeg *.3gp *.mxf *.asf *.dat);;"
            "音频文件 (*.mp3 *.wav *.flac *.aac *.ogg *.m4a *.wma *.amr *.opus *.ac3 *.eac3 *.dts *.ape *.alac *.aiff *.caf);;"
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.flv *.wmv *.webm *.3gp *.m3u8 *.ts *.vob *.ogv *.divx *.xvid *.rm *.rmvb *.mpg *.mpeg *.3gp *.mxf *.asf *.dat);;"
            "所有文件 (*.*)"
        )
        
        if file_dialog.exec():
            file_paths = [Path(path) for path in file_dialog.selectedFiles()]
            print(f"[添加文件] 用户选择了 {len(file_paths)} 个文件")
            self.add_files_to_list(file_paths)
    
    def add_files_from_drop(self, file_paths: List[Path]):
        """从拖拽添加文件"""
        print(f"[信号调试] add_files_from_drop 被调用，文件数量: {len(file_paths)}")
        for path in file_paths:
            print(f"[信号调试] 处理文件: {path}")
        self.add_files_to_list(file_paths)
    
    def add_files_to_list(self, file_paths: List[Path]):
        """添加文件到列表"""
        added_count = 0
        for file_path in file_paths:
            if file_path not in self.file_list:
                self.file_list.append(file_path)
                
                # 创建列表项
                item = QListWidgetItem()
                item.setText(f"{file_path.name}\n{file_path.parent}")
                item.setData(Qt.ItemDataRole.UserRole, file_path)
                
                # 设置图标
                if file_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m3u8', '.ts', '.vob', '.ogv', '.divx', '.xvid', '.rm', '.rmvb', '.mpg', '.mpeg', '.3gp', '.mxf', '.asf', '.dat','.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.amr', '.opus', '.ac3', '.eac3', '.dts', '.ape', '.alac', '.aiff', '.caf']:
                    item.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_MediaVolume))
                else:
                    item.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_MediaPlay))
                
                self.file_list_widget.addItem(item)
                added_count += 1
        
        if added_count > 0:
            self.status_bar.showMessage(f"已添加 {added_count} 个文件，总计 {len(self.file_list)} 个文件")
        else:
            self.status_bar.showMessage("没有新文件添加")
    
    def remove_selected_file(self):
        """移除选中的文件"""
        current_item = self.file_list_widget.currentItem()
        if current_item:
            file_path = current_item.data(Qt.ItemDataRole.UserRole)
            if file_path in self.file_list:
                self.file_list.remove(file_path)
            
            row = self.file_list_widget.row(current_item)
            self.file_list_widget.takeItem(row)
            
            # 清除相关的转录结果
            if file_path in self.transcription_results:
                del self.transcription_results[file_path]
            
            self.status_bar.showMessage(f"已移除文件: {file_path.name}")
    
    def clear_file_list(self):
        """清空文件列表"""
        if self.file_list:
            reply = QMessageBox.question(
                self, "确认清空", 
                f"确定要清空所有 {len(self.file_list)} 个文件吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.file_list.clear()
                self.file_list_widget.clear()
                self.transcription_results.clear()
                self.result_text_widget.clear()
                self.current_file_label.setText("当前文件: 无")
                self.open_srt_btn.setEnabled(False)
                self.status_bar.showMessage("文件列表已清空")
    
    def on_file_selection_changed(self):
        """文件选择改变时的处理"""
        current_item = self.file_list_widget.currentItem()
        if current_item:
            file_path = current_item.data(Qt.ItemDataRole.UserRole)
            self.current_file_label.setText(f"当前文件: {file_path.name}")
            
            # 显示已有的转录结果
            if file_path in self.transcription_results:
                result_text, srt_path = self.transcription_results[file_path]
                self.result_text_widget.setPlainText(result_text)
                # 只有在生成字幕文件选项开启且字幕文件存在时才启用按钮
                self.open_srt_btn.setEnabled(bool(srt_path) and self.generate_srt_checkbox.isChecked())
            else:
                self.result_text_widget.clear()
                self.open_srt_btn.setEnabled(False)
    
    def on_srt_option_changed(self):
        """字幕文件生成选项改变时的处理"""
        # 更新打开字幕文件按钮的状态
        current_item = self.file_list_widget.currentItem()
        if current_item:
            file_path = current_item.data(Qt.ItemDataRole.UserRole)
            if file_path in self.transcription_results:
                _, srt_path = self.transcription_results[file_path]
                # 只有在生成字幕文件选项开启且字幕文件存在时才启用按钮
                self.open_srt_btn.setEnabled(bool(srt_path) and self.generate_srt_checkbox.isChecked())
            else:
                self.open_srt_btn.setEnabled(False)
        else:
            self.open_srt_btn.setEnabled(False)
    
    def browse_output_directory(self):
        """浏览输出目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择输出目录", 
            self.output_dir_edit.text() or str(Path.home())
        )
        if directory:
            self.output_dir_edit.setText(directory)
            print(f"[输出目录] 用户选择输出目录: {directory}")
    
    def start_transcription(self):
        """开始转录"""
        if not self.file_list:
            QMessageBox.warning(self, "警告", "请先添加要转录的文件")
            return
        
        if self.current_worker and self.current_worker.isRunning():
            QMessageBox.warning(self, "警告", "转录正在进行中，请等待完成或先停止当前转录")
            return
        
        # 获取当前选中的文件索引，如果没有选中则从第一个开始
        start_index = self.file_list_widget.currentRow()
        if start_index < 0:  # 没有选中任何文件
            start_index = 0
        
        # 在控制台输出开始信息
        print(f"[转录开始] 开始批量转录，共 {len(self.file_list)} 个文件")
        print(f"[转录设置] 生成字幕文件: {'是' if self.generate_srt_checkbox.isChecked() else '否'}")
        print(f"[转录设置] 从第 {start_index + 1} 个文件开始处理")
        output_dir = self.output_dir_edit.text().strip()
        if output_dir:
            print(f"[转录设置] 输出目录: {output_dir}")
        else:
            print(f"[转录设置] 输出目录: 与源文件同目录")
        
        # 保存起始索引
        self.transcription_start_index = start_index
        
        # 开始转录第一个文件
        self.transcribe_next_file()
    
    def transcribe_next_file(self):
        """转录下一个文件"""
        print(f"[下一个文件] 开始查找下一个需要转录的文件...")
        print(f"[文件列表] 总共{len(self.file_list)}个文件: {[p.name for p in self.file_list]}")
        print(f"[已完成] 已完成{len(self.transcription_results)}个文件: {[p.name for p in self.transcription_results.keys()]}")
        
        # 获取起始索引，如果没有设置则从0开始
        start_index = getattr(self, 'transcription_start_index', 0)
        
        # 找到下一个需要转录的文件，从起始索引开始
        for i in range(start_index, len(self.file_list)):
            file_path = self.file_list[i]
            print(f"[检查文件{i+1}] {file_path.name} - 是否已完成: {file_path in self.transcription_results}")
            if file_path not in self.transcription_results:
                print(f"[找到未完成文件] 开始转录: {file_path.name}")
                self.transcribe_file(file_path)
                return
        
        # 所有文件都已转录完成
        print(f"[批量转录] 所有文件都已完成，调用transcription_finished")
        self.transcription_finished()
    
    def transcribe_file(self, file_path: Path):
        """转录单个文件"""
        # 获取用户设置的字幕文件生成选项和输出目录
        generate_srt = self.generate_srt_checkbox.isChecked()
        output_dir = self.output_dir_edit.text().strip() or None
        self.current_worker = TranscriptionWorker(file_path, generate_srt, output_dir)
        
        # 在控制台输出当前转录文件信息
        print(f"[当前转录] 正在处理文件: {file_path.name}")
        print(f"[文件路径] {file_path}")
        if output_dir:
            print(f"[输出目录] {output_dir}")
        
        # 连接信号
        self.current_worker.progress_updated.connect(self.on_transcription_progress)
        self.current_worker.transcription_completed.connect(self.on_transcription_completed)
        self.current_worker.transcription_failed.connect(self.on_transcription_failed)
        
        # 更新UI状态
        self.transcribe_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        
        # 选中当前文件
        for i in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == file_path:
                self.file_list_widget.setCurrentItem(item)
                break
        
        # 开始转录
        self.current_worker.start()
    
    def stop_transcription(self):
        """停止转录"""
        print(f"[GUI取消] 用户点击停止转录按钮")
        if self.current_worker and self.current_worker.isRunning():
            print(f"[GUI取消] 当前worker正在运行，调用cancel方法")
            self.current_worker.cancel()
            print(f"[GUI取消] 等待worker结束...")
            self.current_worker.wait(3000)  # 等待3秒
            print(f"[GUI取消] worker已结束")
            
            self.transcribe_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.progress_bar.setVisible(False)
            self.status_label.setText("已停止")
            self.status_bar.showMessage("转录已停止")
            print(f"[GUI取消] UI状态已更新")
        else:
            print(f"[GUI取消] 没有正在运行的worker")
    
    def on_transcription_progress(self, filename: str, status: str):
        """转录进度更新"""
        self.status_label.setText(status)
        self.status_bar.showMessage(f"{filename}: {status}")
        # 在控制台输出进度信息
        print(f"[转录进度] {filename}: {status}")
    
    def on_transcription_completed(self, filename: str, result_text: str, srt_path: str):
        """转录完成"""
        print(f"[转录完成信号] 收到完成信号: filename={filename}")
        print(f"[当前文件列表] 共{len(self.file_list)}个文件: {[p.name for p in self.file_list]}")
        print(f"[已完成文件] 共{len(self.transcription_results)}个: {[p.name for p in self.transcription_results.keys()]}")
        
        # 找到对应的文件路径
        file_path = None
        for path in self.file_list:
            if path.name == filename:
                file_path = path
                print(f"[文件匹配] 找到匹配文件: {path}")
                break
        
        if file_path:
            # 保存转录结果
            self.transcription_results[file_path] = (result_text, srt_path)
            print(f"[结果保存] 已保存到transcription_results，当前总数: {len(self.transcription_results)}")
            
            # 更新显示
            self.result_text_widget.setPlainText(result_text)
            # 只有在生成字幕文件选项开启且字幕文件存在时才启用按钮
            self.open_srt_btn.setEnabled(bool(srt_path) and self.generate_srt_checkbox.isChecked())
            
            # 更新列表项状态
            for i in range(self.file_list_widget.count()):
                item = self.file_list_widget.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == file_path:
                    item.setText(f"✓ {file_path.name}\n{file_path.parent}")
                    item.setBackground(QColor("#e8f5e8"))
                    print(f"[UI更新] 已更新列表项状态")
                    break
        else:
            print(f"[错误] 未找到匹配的文件路径，filename={filename}")
        
        self.status_label.setText("转录完成")
        self.status_bar.showMessage(f"{filename}: 转录完成")
        
        # 在控制台输出完成信息
        print(f"[转录完成] {filename}: 转录成功完成")
        if srt_path:
            print(f"[字幕文件] 已生成字幕文件: {srt_path}")
        
        print(f"[下一步] 3秒后继续下一个文件...")
        # 继续转录下一个文件，增加延迟避免连接冲突
        QTimer.singleShot(3000, self.transcribe_next_file)
    
    def on_transcription_failed(self, filename: str, error_message: str):
        """转录失败"""
        print(f"[转录GUI] 收到转录失败信号: filename={filename}, error={error_message}")
        
        self.status_label.setText("转录失败")
        self.status_bar.showMessage(f"{filename}: 转录失败")
        
        # 在控制台输出错误信息
        print(f"[转录失败] {filename}: {error_message}")
        
        # 找到对应的文件路径并标记为失败
        file_path = None
        for path in self.file_list:
            if path.name == filename:
                file_path = path
                break
        
        if file_path:
            print(f"[转录GUI] 找到对应文件路径: {file_path}")
            # 将失败的文件也添加到结果字典中，避免重复尝试
            self.transcription_results[file_path] = (f"转录失败: {error_message}", "")
            print(f"[转录GUI] 已标记文件为失败状态")
        else:
            print(f"[转录GUI] 警告：未找到对应的文件路径，filename={filename}")
        
        # 显示错误信息
        QMessageBox.critical(self, "转录失败", f"文件 {filename} 转录失败:\n{error_message}")
        
        # 更新列表项状态
        for i in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole).name == filename:
                item.setText(f"✗ {filename}\n转录失败")
                item.setBackground(QColor("#ffebee"))
                print(f"[转录GUI] 已更新列表项为失败状态")
                break
        
        print(f"[转录GUI] 准备继续下一个文件，3秒后开始...")
        # 继续转录下一个文件，增加延迟避免连接冲突
        QTimer.singleShot(3000, self.transcribe_next_file)
    
    def transcription_finished(self):
        """所有转录完成"""
        self.transcribe_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("全部完成")
        self.status_bar.showMessage("所有文件转录完成")
        
        # 在控制台输出完成统计
        completed_count = len(self.transcription_results)
        total_count = len(self.file_list)
        print(f"[批量转录完成] 成功: {completed_count}/{total_count} 个文件")
        print("=" * 50)
        
        # 显示完成通知
        self.show_system_notification(
            "转录完成", 
            f"转录完成！成功: {completed_count}/{total_count} 个文件"
        )
    
    def copy_result(self):
        """复制转录结果"""
        text = self.result_text_widget.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.status_bar.showMessage("转录结果已复制到剪贴板")
        else:
            QMessageBox.information(self, "提示", "没有可复制的转录结果")
    
    def save_result(self):
        """保存转录结果"""
        text = self.result_text_widget.toPlainText()
        if not text:
            QMessageBox.information(self, "提示", "没有可保存的转录结果")
            return
        
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(
            self, "保存转录结果", 
            "transcription_result.txt",
            "文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                self.status_bar.showMessage(f"转录结果已保存到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"保存文件时出错:\n{str(e)}")
    
    def open_srt_file(self):
        """打开字幕文件"""
        current_item = self.file_list_widget.currentItem()
        if current_item:
            file_path = current_item.data(Qt.ItemDataRole.UserRole)
            if file_path in self.transcription_results:
                _, srt_path = self.transcription_results[file_path]
                if srt_path and Path(srt_path).exists():
                    try:
                        if sys.platform == "win32":
                            os.startfile(srt_path)
                        elif sys.platform == "darwin":
                            subprocess.run(["open", srt_path])
                        else:
                            subprocess.run(["xdg-open", srt_path])
                    except Exception as e:
                        QMessageBox.critical(self, "打开失败", f"无法打开字幕文件:\n{str(e)}")
                else:
                    QMessageBox.information(self, "提示", "字幕文件不存在")
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self, "关于",
            "CapsWriter 多功能处理工具\n\n"
            "版本: 1.0.0\n"
            "支持音频和视频文件的语音转录\n"
            "支持长文本智能处理与归纳\n\n"
            "项目地址: https://github.com/HaujetZhao/CapsWriter-Offline"
        )
    
    # ==================== 长文本处理相关方法 ====================
    
    def load_text_file(self):
        """加载文本文件"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "选择文本文件",
            "",
            "文本文件 (*.txt *.md *.doc *.docx);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                # 尝试不同的编码
                encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
                content = None
                
                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                
                if content is None:
                    QMessageBox.critical(self, "加载失败", "无法读取文件，请检查文件编码")
                    return
                
                self.long_text_input.setPlainText(content)
                self.status_bar.showMessage(f"已加载文件: {Path(file_path).name}")
                
            except Exception as e:
                QMessageBox.critical(self, "加载失败", f"加载文件时出错:\n{str(e)}")
    
    def add_text_files(self):
        """添加文本文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择文本文件", "", 
            "文本文件 (*.txt *.md *.rtf);;所有文件 (*.*)"
        )
        
        if files:
            for file_path in files:
                # 检查文件是否已存在
                existing_items = []
                for i in range(self.long_text_file_list_widget.count()):
                    item = self.long_text_file_list_widget.item(i)
                    existing_items.append(item.text())
                
                if file_path not in existing_items:
                    self.long_text_file_list_widget.addItem(file_path)
                    self.long_text_file_list.append(file_path)
            
            self.status_bar.showMessage(f"已添加 {len(files)} 个文本文件")
    
    def remove_selected_text_file(self):
        """移除选中的文本文件"""
        current_row = self.long_text_file_list_widget.currentRow()
        if current_row >= 0:
            item = self.long_text_file_list_widget.takeItem(current_row)
            if item:
                file_path = item.text()
                if file_path in self.long_text_file_list:
                    self.long_text_file_list.remove(file_path)
                self.status_bar.showMessage(f"已移除文件: {os.path.basename(file_path)}")
        else:
            QMessageBox.information(self, "提示", "请先选择要移除的文件")
    
    def clear_text_file_list(self):
        """清空文本文件列表"""
        self.long_text_file_list_widget.clear()
        self.long_text_file_list.clear()
        self.status_bar.showMessage("已清空文本文件列表")
    
    def browse_long_text_output_directory(self):
        """浏览长文本输出目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择输出目录", 
            self.long_text_output_dir_edit.text() or os.path.expanduser("~/Documents")
        )
        if directory:
             self.long_text_output_dir_edit.setText(directory)
             self.status_bar.showMessage(f"输出目录已设置为: {directory}")
    
    def add_text_files_from_drop(self, file_paths: List[Path]):
        """从拖拽添加文本文件"""
        print(f"[文本信号调试] add_text_files_from_drop 被调用，文件数量: {len(file_paths)}")
        for path in file_paths:
            print(f"[文本信号调试] 处理文件: {path}")
        text_extensions = {'.txt', '.md', '.rtf'}
        added_count = 0
        
        for file_path in file_paths:
            # 转换为字符串路径
            file_path_str = str(file_path)
            
            # 检查文件扩展名
            if file_path.suffix.lower() not in text_extensions:
                continue
            
            # 检查文件是否已存在
            existing_items = []
            for i in range(self.long_text_file_list_widget.count()):
                item = self.long_text_file_list_widget.item(i)
                existing_items.append(item.text())
            
            if file_path_str not in existing_items:
                self.long_text_file_list_widget.addItem(file_path_str)
                self.long_text_file_list.append(file_path_str)
                added_count += 1
        
        if added_count > 0:
            self.status_bar.showMessage(f"已添加 {added_count} 个文本文件")
        else:
            self.status_bar.showMessage("没有找到有效的文本文件")
    
    def start_long_text_processing(self):
        """开始长文本批量处理"""
        if not LONG_TEXT_AVAILABLE:
            QMessageBox.warning(self, "功能不可用", "长文本处理功能不可用，请检查相关模块是否正确安装")
            return
        
        # 检查文件列表
        if not self.long_text_file_list:
            QMessageBox.information(self, "提示", "请先添加要处理的文本文件")
            return
        
        # 获取处理设置
        process_type = self.long_text_process_type.currentText()
        model_name = self.long_text_model.currentText()
        max_tokens = self.long_text_max_tokens.value()
        
        # 获取系统设定和用户设定
        system_prompt = self.long_text_system_prompt.toPlainText().strip() or None
        user_prompt = self.long_text_user_prompt.toPlainText().strip() or None
        
        # 获取输出目录
        output_dir = self.long_text_output_dir_edit.text().strip()
        if not output_dir:
            output_dir = None  # 使用源文件同目录
        
        # 获取当前选中的文件索引，如果没有选中则从第一个开始
        start_index = self.long_text_file_list_widget.currentRow()
        if start_index < 0:  # 没有选中任何文件
            start_index = 0
        
        # 禁用开始按钮，启用停止按钮
        self.long_text_start_button.setEnabled(False)
        self.long_text_stop_button.setEnabled(True)
        self.long_text_progress.setVisible(True)
        self.long_text_progress.setRange(0, len(self.long_text_file_list))  # 确定进度
        self.long_text_progress.setValue(start_index)  # 从选中位置开始显示进度
        self.long_text_status.setText("正在处理...")
        
        # 创建并启动批量处理工作线程
        self.long_text_worker = LongTextBatchProcessingWorker(
            self.long_text_file_list, process_type, model_name, max_tokens, 
            system_prompt, user_prompt, output_dir, start_index
        )
        
        # 连接信号
        self.long_text_worker.progress_updated.connect(self.on_long_text_progress)
        self.long_text_worker.file_completed.connect(self.on_long_text_file_completed)
        self.long_text_worker.processing_completed.connect(self.on_long_text_batch_completed)
        self.long_text_worker.processing_failed.connect(self.on_long_text_failed)
        
        # 启动线程
        self.long_text_worker.start()
        
        self.status_bar.showMessage(f"开始批量处理 {len(self.long_text_file_list)} 个文件...")
    
    def stop_long_text_processing(self):
        """停止长文本处理"""
        if self.long_text_worker and self.long_text_worker.isRunning():
            self.long_text_worker.cancel()
            self.long_text_worker.wait(3000)
            
            # 重置UI状态
            self.long_text_start_button.setEnabled(True)
            self.long_text_stop_button.setEnabled(False)
            self.long_text_progress.setVisible(False)
            self.long_text_status.setText("已停止")
            self.status_bar.showMessage("长文本处理已停止")
    
    def on_long_text_progress(self, message: str):
        """长文本处理进度更新"""
        self.long_text_status.setText(message)
        self.status_bar.showMessage(f"长文本处理: {message}")
        print(f"[长文本处理进度] {message}")
    
    def on_long_text_file_completed(self, input_file: str, output_file: str, result: str):
        """单个文件处理完成"""
        # 更新进度条
        current_value = self.long_text_progress.value()
        self.long_text_progress.setValue(current_value + 1)
        
        # 显示最新结果
        self.long_text_result_widget.setPlainText(result)
        
        # 添加到处理结果缓存
        result_info = {
            'input_file': input_file,
            'output_file': output_file,
            'result': result,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.long_text_processing_results.append(result_info)
        
        print(f"[文件处理完成] {os.path.basename(input_file)} -> {os.path.basename(output_file)}")
    
    def on_long_text_batch_completed(self, results: list):
        """批量处理完成"""
        # 添加到历史记录
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        process_type = self.long_text_process_type.currentText()
        model_name = self.long_text_model.currentText()
        
        history_item = {
            'timestamp': timestamp,
            'process_type': process_type,
            'model': model_name,
            'input_text': f"批量处理 {len(results)} 个文件",
            'result': f"成功处理 {len(results)} 个文件",
            'batch_results': results
        }
        
        self.long_text_history.append(history_item)
        
        # 更新历史列表显示
        list_item = QListWidgetItem(f"[{timestamp}] 批量{process_type} - {model_name} ({len(results)}个文件)")
        list_item.setData(Qt.ItemDataRole.UserRole, len(self.long_text_history) - 1)
        self.long_text_history_list.addItem(list_item)
        
        # 重置UI状态
        self.long_text_start_button.setEnabled(True)
        self.long_text_stop_button.setEnabled(False)
        self.long_text_progress.setVisible(False)
        self.long_text_status.setText(f"批量处理完成 ({len(results)}个文件)")
        self.status_bar.showMessage(f"批量长文本处理完成，成功处理 {len(results)} 个文件")
        
        # 显示处理摘要
        summary_text = f"批量处理完成！\n\n处理类型: {process_type}\nAI模型: {model_name}\n处理文件数: {len(results)}\n\n处理结果文件:\n"
        for result_info in results:
            summary_text += f"• {os.path.basename(result_info['output_file'])}\n"
        
        self.long_text_result_widget.setPlainText(summary_text)
        
        print(f"[批量处理完成] 处理类型: {process_type}, 模型: {model_name}, 文件数: {len(results)}")
        
        # 显示完成通知
        self.show_system_notification("处理完成", 
                               f"批量长文本处理完成！成功处理 {len(results)} 个文件，结果已保存到指定目录")
    
    def on_long_text_completed(self, result: str):
        """长文本处理完成（兼容旧版本）"""
        # 显示结果
        self.long_text_result_widget.setPlainText(result)
        
        # 重置UI状态
        self.long_text_start_button.setEnabled(True)
        self.long_text_stop_button.setEnabled(False)
        self.long_text_progress.setVisible(False)
        self.long_text_status.setText("处理完成")
        self.status_bar.showMessage("长文本处理完成")
        
        print(f"[长文本处理完成] 结果长度: {len(result)} 个字符")
    
    def on_long_text_failed(self, error_message: str):
        """长文本处理失败"""
        self.long_text_status.setText("处理失败")
        self.status_bar.showMessage("长文本处理失败")
        
        print(f"[长文本处理失败] {error_message}")
        
        # 显示错误信息
        QMessageBox.critical(self, "处理失败", f"长文本处理失败:\n{error_message}")
        
        # 重置UI状态
        self.long_text_start_button.setEnabled(True)
        self.long_text_stop_button.setEnabled(False)
        self.long_text_progress.setVisible(False)
    
    def copy_long_text_result(self):
        """复制长文本处理结果"""
        text = self.long_text_result_widget.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.status_bar.showMessage("处理结果已复制到剪贴板")
        else:
            QMessageBox.information(self, "提示", "没有可复制的处理结果")
    
    def save_long_text_result(self):
        """保存长文本处理结果"""
        text = self.long_text_result_widget.toPlainText()
        if not text:
            QMessageBox.information(self, "提示", "没有可保存的处理结果")
            return
        
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(
            self, "保存处理结果",
            "long_text_result.txt",
            "文本文件 (*.txt);;Markdown文件 (*.md);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                self.status_bar.showMessage(f"处理结果已保存到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"保存文件时出错:\n{str(e)}")
    
    def export_long_text_result(self):
        """导出长文本处理结果（包含详细信息）"""
        text = self.long_text_result_widget.toPlainText()
        if not text:
            QMessageBox.information(self, "提示", "没有可导出的处理结果")
            return
        
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(
            self, "导出详细结果",
            "long_text_detailed_result.txt",
            "文本文件 (*.txt);;Markdown文件 (*.md);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                process_type = self.long_text_process_type.currentText()
                model_name = self.long_text_model.currentText()
                max_tokens = self.long_text_max_tokens.value()
                input_text = self.long_text_input.toPlainText()
                
                detailed_content = f"""# 长文本处理结果详细报告

## 处理信息
- 处理时间: {timestamp}
- 处理类型: {process_type}
- 使用模型: {model_name}
- 最大Token数: {max_tokens}
- 原文长度: {len(input_text)} 个字符
- 结果长度: {len(text)} 个字符

## 原始文本
```
{input_text}
```

## 处理结果
{text}

---
生成时间: {timestamp}
工具: CapsWriter 长文本处理工具
"""
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(detailed_content)
                self.status_bar.showMessage(f"详细结果已导出到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出文件时出错:\n{str(e)}")
    
    def update_prompt_defaults(self):
        """根据处理类型更新默认的系统设定和用户设定"""
        process_type = self.long_text_process_type.currentText()
        
        # 从配置管理器获取保存的提示词
        system_prompt = prompt_config_manager.get_system_prompt(process_type)
        user_prompt = prompt_config_manager.get_user_prompt(process_type)
        
        # 临时断开信号连接，避免在设置文本时触发自动保存
        try:
            self.long_text_system_prompt.textChanged.disconnect(self.save_current_prompts)
            self.long_text_user_prompt.textChanged.disconnect(self.save_current_prompts)
        except TypeError:
            # 信号可能还未连接，忽略错误
            pass
        
        # 设置提示词（只在文本框为空时设置）
        if not self.long_text_system_prompt.toPlainText().strip():
            self.long_text_system_prompt.setPlainText(system_prompt)
        
        if not self.long_text_user_prompt.toPlainText().strip():
            self.long_text_user_prompt.setPlainText(user_prompt)
        
        # 重新连接信号
        self.long_text_system_prompt.textChanged.connect(self.save_current_prompts)
        self.long_text_user_prompt.textChanged.connect(self.save_current_prompts)
    
    def reset_system_prompt(self):
        """重置系统设定为默认值"""
        process_type = self.long_text_process_type.currentText()
        system_prompt = prompt_config_manager.get_system_prompt(process_type)
        self.long_text_system_prompt.setPlainText(system_prompt)
        self.status_bar.showMessage("已恢复为您保存配置好的系统设定")
    
    def reset_user_prompt(self):
        """重置用户设定为默认值"""
        process_type = self.long_text_process_type.currentText()
        user_prompt = prompt_config_manager.get_user_prompt(process_type)
        self.long_text_user_prompt.setPlainText(user_prompt)
        self.status_bar.showMessage("已恢复为您保存配置好的用户设定")
    
    def save_current_prompts(self, *args):
        """保存当前的系统设定和用户设定"""
        try:
            process_type = self.long_text_process_type.currentText()
            system_prompt = self.long_text_system_prompt.toPlainText().strip()
            user_prompt = self.long_text_user_prompt.toPlainText().strip()
            
            # 只有在内容不为空时才保存
            if system_prompt:
                prompt_config_manager.update_system_prompt(process_type, system_prompt)
            if user_prompt:
                prompt_config_manager.update_user_prompt(process_type, user_prompt)
            
            # 保存配置到文件
            prompt_config_manager.save_current_prompts(system_prompt, user_prompt)
        except Exception as e:
            print(f"[配置保存] 保存提示词配置时出错: {str(e)}")
    
    def load_saved_prompts(self):
        """加载用户之前保存的提示词配置"""
        try:
            process_type = self.long_text_process_type.currentText()
            
            # 临时断开信号连接，避免在加载时触发自动保存
            try:
                self.long_text_system_prompt.textChanged.disconnect(self.save_current_prompts)
                self.long_text_user_prompt.textChanged.disconnect(self.save_current_prompts)
            except TypeError:
                # 信号可能还未连接，忽略错误
                pass
            
            # 从配置管理器获取保存的提示词
            system_prompt = prompt_config_manager.get_system_prompt(process_type)
            user_prompt = prompt_config_manager.get_user_prompt(process_type)
            
            # 设置提示词
            self.long_text_system_prompt.setPlainText(system_prompt)
            self.long_text_user_prompt.setPlainText(user_prompt)
            
            # 重新连接信号
            self.long_text_system_prompt.textChanged.connect(self.save_current_prompts)
            self.long_text_user_prompt.textChanged.connect(self.save_current_prompts)
            
            print(f"[配置加载] 已加载 {process_type} 的提示词配置")
        except Exception as e:
            print(f"[配置加载] 加载提示词配置时出错: {str(e)}")
    
    def clear_long_text_history(self):
        """清空长文本处理历史"""
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空所有处理历史吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.long_text_history.clear()
            self.long_text_history_list.clear()
            self.status_bar.showMessage("已清空处理历史")
    
    def load_long_text_history_item(self, item):
        """加载历史记录项"""
        index = item.data(Qt.ItemDataRole.UserRole)
        if 0 <= index < len(self.long_text_history):
            history_item = self.long_text_history[index]
            self.long_text_result_widget.setPlainText(history_item['result'])
            self.status_bar.showMessage(f"已加载历史记录: {history_item['timestamp']}")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 检查是否有正在运行的任务
        transcription_running = self.current_worker and self.current_worker.isRunning()
        long_text_running = self.long_text_worker and self.long_text_worker.isRunning()
        
        if transcription_running or long_text_running:
            tasks = []
            if transcription_running:
                tasks.append("音视频转录")
            if long_text_running:
                tasks.append("长文本处理")
            
            task_text = "、".join(tasks)
            reply = QMessageBox.question(
                self, "确认退出",
                f"{task_text}正在进行中，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # 停止转录任务
                if transcription_running:
                    self.current_worker.cancel()
                    self.current_worker.wait(3000)
                
                # 停止长文本处理任务
                if long_text_running:
                    self.long_text_worker.cancel()
                    self.long_text_worker.wait(3000)
                
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """主函数"""
    print("[应用启动] CapsWriter 多功能处理工具正在启动...")
    print(f"[系统信息] Python版本: {sys.version}")
    print(f"[工作目录] {os.getcwd()}")
    
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("CapsWriter 多功能处理工具")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("CapsWriter")
    
    print("[界面初始化] 正在创建主窗口...")
    print("[功能模块] 音视频转录功能已加载")
    if LONG_TEXT_AVAILABLE:
        print("[功能模块] 长文本处理功能已加载")
    else:
        print("[功能模块] 长文本处理功能不可用")
    
    # 创建主窗口
    window = TranscriptionGUI()
    window.show()
    
    print("[应用就绪] 多功能处理工具已启动完成")
    print("=" * 50)
    
    # 运行应用程序
    sys.exit(app.exec())


if __name__ == "__main__":
    main()