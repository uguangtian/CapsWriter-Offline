#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
长文本处理与归纳GUI应用
基于现有转录工具架构，提供长文本的AI处理功能
"""

import sys
import os
import asyncio
import threading
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from PySide6.QtCore import (
    Qt, QThread, Signal, QTimer, QMimeData, QUrl, QSize
)
from PySide6.QtGui import (
    QIcon, QFont, QPixmap, QPainter, QColor, QDragEnterEvent, QDropEvent
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QTextEdit, QPushButton, QLabel,
    QProgressBar, QSplitter, QGroupBox, QFileDialog, QMessageBox,
    QStatusBar, QMenuBar, QMenu, QToolBar, QFrame, QScrollArea,
    QCheckBox, QComboBox, QSpinBox, QTabWidget, QPlainTextEdit
)

from agent.long_text_processor import LongTextProcessor


class LongTextProcessingWorker(QThread):
    """长文本处理工作线程"""
    progress_updated = Signal(str)  # status
    processing_completed = Signal(str, str)  # action, result_text
    processing_failed = Signal(str, str)  # action, error_message
    
    def __init__(self, text: str, action: str, model_type: str = "deepseek", config: Dict[str, Any] = None):
        super().__init__()
        self.text = text
        self.action = action
        self.model_type = model_type
        self.config = config or {}
        self.is_cancelled = False
        self.processor = None
    
    def run(self):
        """执行长文本处理任务"""
        try:
            self.progress_updated.emit("初始化处理器...")
            
            # 创建处理器
            self.processor = LongTextProcessor(self.model_type, self.config)
            
            if self.is_cancelled:
                return
            
            self.progress_updated.emit("开始处理文本...")
            
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # 执行处理
                result = loop.run_until_complete(
                    self.processor.process(self.text, self.action)
                )
                
                if self.is_cancelled:
                    return
                
                if result and not result.startswith("处理文本时出错"):
                    self.processing_completed.emit(self.action, result)
                else:
                    self.processing_failed.emit(self.action, result or "处理失败，未返回结果")
                    
            finally:
                loop.close()
                
        except Exception as e:
            self.processing_failed.emit(self.action, f"处理过程中出错: {str(e)}")
    
    def cancel(self):
        """取消处理任务"""
        self.is_cancelled = True
        self.terminate()


class FileDropWidget(QTextEdit):
    """支持文件拖拽的文本编辑控件"""
    files_dropped = Signal(list)  # 文件拖拽信号
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setPlaceholderText("请输入或粘贴要处理的文本，或拖拽文本文件到此处...")
        
        # 设置字体
        font = QFont("Microsoft YaHei", 11)
        self.setFont(font)
        
        # 设置样式
        self.setStyleSheet("""
            QTextEdit {
                border: 2px dashed #aaa;
                border-radius: 10px;
                background-color: #f9f9f9;
                padding: 15px;
                line-height: 1.6;
            }
            QTextEdit:focus {
                border-color: #4CAF50;
                background-color: white;
            }
        """)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                file_path = Path(url.toLocalFile())
                if self.is_supported_file(file_path):
                    files.append(file_path)
        
        if files:
            self.files_dropped.emit(files)
        event.acceptProposedAction()
    
    def is_supported_file(self, file_path: Path) -> bool:
        """检查是否为支持的文件格式"""
        supported_extensions = {
            '.txt', '.md', '.docx', '.doc', '.rtf', '.srt', '.vtt'
        }
        return file_path.suffix.lower() in supported_extensions


class LongTextProcessingGUI(QMainWindow):
    """长文本处理主窗口"""
    
    def __init__(self):
        super().__init__()
        self.current_worker = None
        self.processing_history = []  # 处理历史记录
        
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("CapsWriter 长文本处理与归纳工具")
        self.setWindowIcon(QIcon("assets/appicon.ico"))
        self.resize(1400, 900)
        
        # 创建中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧面板 - 输入和设置
        left_panel = self.create_input_panel()
        splitter.addWidget(left_panel)
        
        # 右侧面板 - 结果显示
        right_panel = self.create_result_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setSizes([600, 800])
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建状态栏
        self.create_status_bar()
    
    def create_input_panel(self) -> QWidget:
        """创建输入面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 文本输入组
        input_group = QGroupBox("文本输入")
        input_layout = QVBoxLayout(input_group)
        
        # 文本输入框
        self.text_input = FileDropWidget()
        self.text_input.setMinimumHeight(300)
        input_layout.addWidget(self.text_input)
        
        # 文件操作按钮
        file_button_layout = QHBoxLayout()
        
        self.load_file_btn = QPushButton("加载文件")
        self.load_file_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon))
        file_button_layout.addWidget(self.load_file_btn)
        
        self.clear_text_btn = QPushButton("清空文本")
        self.clear_text_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DialogResetButton))
        file_button_layout.addWidget(self.clear_text_btn)
        
        file_button_layout.addStretch()
        input_layout.addLayout(file_button_layout)
        
        layout.addWidget(input_group)
        
        # 处理设置组
        settings_group = QGroupBox("处理设置")
        settings_layout = QVBoxLayout(settings_group)
        
        # 处理类型选择
        action_layout = QHBoxLayout()
        action_layout.addWidget(QLabel("处理类型:"))
        
        self.action_combo = QComboBox()
        processor = LongTextProcessor()  # 临时创建以获取选项
        options = processor.get_processing_options()
        for action_code, description in options.items():
            self.action_combo.addItem(description, action_code)
        action_layout.addWidget(self.action_combo)
        settings_layout.addLayout(action_layout)
        
        # 模型选择
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("AI模型:"))
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(["DeepSeek", "豆包(Doubao)", "Claude", "LM Studio"])
        self.model_combo.setCurrentText("DeepSeek")
        model_layout.addWidget(self.model_combo)
        settings_layout.addLayout(model_layout)
        
        # 高级设置
        advanced_layout = QVBoxLayout()
        
        # 每段最大token数
        tokens_layout = QHBoxLayout()
        tokens_layout.addWidget(QLabel("每段最大Token数:"))
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(1000, 90000000)
        self.max_tokens_spin.setValue(40000)
        self.max_tokens_spin.setSuffix(" tokens")
        tokens_layout.addWidget(self.max_tokens_spin)
        advanced_layout.addLayout(tokens_layout)
        
        # 保持上下文连贯性
        self.preserve_context_cb = QCheckBox("保持上下文连贯性")
        self.preserve_context_cb.setChecked(True)
        self.preserve_context_cb.setToolTip("在处理长文本时保持段落间的上下文关联")
        advanced_layout.addWidget(self.preserve_context_cb)
        
        settings_layout.addLayout(advanced_layout)
        layout.addWidget(settings_group)
        
        # 处理控制组
        control_group = QGroupBox("处理控制")
        control_layout = QVBoxLayout(control_group)
        
        # 开始处理按钮
        self.process_btn = QPushButton("开始处理")
        self.process_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_MediaPlay))
        self.process_btn.setMinimumHeight(40)
        self.process_btn.setStyleSheet("""
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
        control_layout.addWidget(self.process_btn)
        
        # 停止处理按钮
        self.stop_btn = QPushButton("停止处理")
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
        
        # 添加弹性空间
        layout.addStretch()
        
        return panel
    
    def create_result_panel(self) -> QWidget:
        """创建结果显示面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 处理结果标签页
        result_tab = QWidget()
        result_layout = QVBoxLayout(result_tab)
        
        # 当前处理信息
        self.current_info_label = QLabel("当前处理: 无")
        self.current_info_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                color: #1976d2;
                padding: 5px;
                background-color: #e3f2fd;
                border-radius: 3px;
            }
        """)
        result_layout.addWidget(self.current_info_label)
        
        # 处理结果文本框
        self.result_text_widget = QPlainTextEdit()
        self.result_text_widget.setReadOnly(True)
        self.result_text_widget.setPlaceholderText("处理结果将在这里显示...")
        
        # 设置字体
        font = QFont("Microsoft YaHei", 12)
        self.result_text_widget.setFont(font)
        
        # 设置样式
        self.result_text_widget.setStyleSheet("""
            QPlainTextEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                background-color: white;
                line-height: 1.5;
            }
        """)
        result_layout.addWidget(self.result_text_widget)
        
        # 结果操作按钮
        result_button_layout = QHBoxLayout()
        
        self.copy_result_btn = QPushButton("复制结果")
        self.copy_result_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DialogSaveButton))
        result_button_layout.addWidget(self.copy_result_btn)
        
        self.save_result_btn = QPushButton("保存结果")
        self.save_result_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DialogSaveButton))
        result_button_layout.addWidget(self.save_result_btn)
        
        self.export_result_btn = QPushButton("导出文档")
        self.export_result_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon))
        result_button_layout.addWidget(self.export_result_btn)
        
        result_button_layout.addStretch()
        result_layout.addLayout(result_button_layout)
        
        self.tab_widget.addTab(result_tab, "处理结果")
        
        # 处理历史标签页
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        
        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f9f9f9;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
        """)
        history_layout.addWidget(self.history_list)
        
        # 历史操作按钮
        history_button_layout = QHBoxLayout()
        
        self.load_history_btn = QPushButton("加载历史")
        self.load_history_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_BrowserReload))
        history_button_layout.addWidget(self.load_history_btn)
        
        self.clear_history_btn = QPushButton("清空历史")
        self.clear_history_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_TrashIcon))
        history_button_layout.addWidget(self.clear_history_btn)
        
        history_button_layout.addStretch()
        history_layout.addLayout(history_button_layout)
        
        self.tab_widget.addTab(history_tab, "处理历史")
        
        layout.addWidget(self.tab_widget)
        
        return panel
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        load_file_action = file_menu.addAction("加载文件")
        load_file_action.setShortcut("Ctrl+O")
        load_file_action.triggered.connect(self.load_file)
        
        save_result_action = file_menu.addAction("保存结果")
        save_result_action.setShortcut("Ctrl+S")
        save_result_action.triggered.connect(self.save_result)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("退出")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        
        # 处理菜单
        process_menu = menubar.addMenu("处理")
        
        start_process_action = process_menu.addAction("开始处理")
        start_process_action.setShortcut("F5")
        start_process_action.triggered.connect(self.start_processing)
        
        stop_process_action = process_menu.addAction("停止处理")
        stop_process_action.setShortcut("Esc")
        stop_process_action.triggered.connect(self.stop_processing)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = help_menu.addAction("关于")
        about_action.triggered.connect(self.show_about)
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = self.addToolBar("主工具栏")
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        
        # 加载文件
        load_action = toolbar.addAction("加载文件")
        load_action.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon))
        load_action.triggered.connect(self.load_file)
        
        toolbar.addSeparator()
        
        # 开始处理
        start_action = toolbar.addAction("开始处理")
        start_action.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_MediaPlay))
        start_action.triggered.connect(self.start_processing)
        
        # 停止处理
        stop_action = toolbar.addAction("停止处理")
        stop_action.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_MediaStop))
        stop_action.triggered.connect(self.stop_processing)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
    
    def setup_connections(self):
        """设置信号连接"""
        # 文件拖拽
        self.text_input.files_dropped.connect(self.load_files_from_drop)
        
        # 按钮连接
        self.load_file_btn.clicked.connect(self.load_file)
        self.clear_text_btn.clicked.connect(self.clear_text)
        self.process_btn.clicked.connect(self.start_processing)
        self.stop_btn.clicked.connect(self.stop_processing)
        
        # 结果操作按钮
        self.copy_result_btn.clicked.connect(self.copy_result)
        self.save_result_btn.clicked.connect(self.save_result)
        self.export_result_btn.clicked.connect(self.export_result)
        
        # 历史操作按钮
        self.load_history_btn.clicked.connect(self.load_history_item)
        self.clear_history_btn.clicked.connect(self.clear_history)
        
        # 处理类型变化
        self.action_combo.currentTextChanged.connect(self.on_action_changed)
    
    def load_file(self):
        """加载文件对话框"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter(
            "文本文件 (*.txt *.md *.docx *.doc *.rtf);;"
            "字幕文件 (*.srt *.vtt);;"
            "所有文件 (*.*)"
        )
        
        if file_dialog.exec():
            file_paths = [Path(path) for path in file_dialog.selectedFiles()]
            if file_paths:
                self.load_files_from_drop(file_paths)
    
    def load_files_from_drop(self, file_paths: List[Path]):
        """从拖拽加载文件"""
        if not file_paths:
            return
        
        file_path = file_paths[0]  # 只处理第一个文件
        
        try:
            # 读取文件内容
            if file_path.suffix.lower() == '.docx':
                # 处理Word文档（需要python-docx库）
                try:
                    import docx
                    doc = docx.Document(file_path)
                    text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                except ImportError:
                    QMessageBox.warning(self, "警告", "需要安装python-docx库来处理Word文档")
                    return
            else:
                # 处理普通文本文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            
            self.text_input.setPlainText(text)
            self.status_bar.showMessage(f"已加载文件: {file_path.name}")
            
            print(f"[文件加载] 已加载文件: {file_path}")
            print(f"[文件内容] 文本长度: {len(text)} 字符")
            
        except Exception as e:
            QMessageBox.critical(self, "加载失败", f"无法加载文件:\n{str(e)}")
    
    def clear_text(self):
        """清空文本"""
        self.text_input.clear()
        self.result_text_widget.clear()
        self.current_info_label.setText("当前处理: 无")
        self.status_bar.showMessage("文本已清空")
    
    def start_processing(self):
        """开始处理"""
        text = self.text_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "警告", "请先输入要处理的文本")
            return
        
        if self.current_worker and self.current_worker.isRunning():
            QMessageBox.warning(self, "警告", "处理正在进行中，请等待完成或先停止当前处理")
            return
        
        # 获取处理参数
        action = self.action_combo.currentData()
        model_type = self.model_combo.currentText().lower()
        if "deepseek" in model_type:
            model_type = "deepseek"
        elif "doubao" in model_type or "豆包" in model_type:
            model_type = "doubao"
        elif "claude" in model_type:
            model_type = "claude"
        else:
            model_type = "lmstudio"
        
        # 构建配置
        config = {
            "max_tokens_per_segment": self.max_tokens_spin.value(),
            "preserve_context": self.preserve_context_cb.isChecked(),
        }
        
        # 估算处理时间
        processor = LongTextProcessor(model_type, config)
        estimated_time = processor.estimate_processing_time(text, action)
        
        # 显示处理信息
        action_name = self.action_combo.currentText().split(" - ")[0]
        self.current_info_label.setText(f"当前处理: {action_name} (预计 {estimated_time} 秒)")
        
        print(f"[开始处理] 处理类型: {action_name}")
        print(f"[处理设置] 模型: {model_type}, 最大Token: {config['max_tokens_per_segment']}")
        print(f"[文本信息] 长度: {len(text)} 字符, 预计处理时间: {estimated_time} 秒")
        
        # 创建并启动工作线程
        self.current_worker = LongTextProcessingWorker(text, action, model_type, config)
        
        # 连接信号
        self.current_worker.progress_updated.connect(self.on_processing_progress)
        self.current_worker.processing_completed.connect(self.on_processing_completed)
        self.current_worker.processing_failed.connect(self.on_processing_failed)
        
        # 更新UI状态
        self.process_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        
        # 开始处理
        self.current_worker.start()
    
    def stop_processing(self):
        """停止处理"""
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.cancel()
            self.current_worker.wait(3000)  # 等待3秒
            
            self.process_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.progress_bar.setVisible(False)
            self.status_label.setText("已停止")
            self.status_bar.showMessage("处理已停止")
            
            print(f"[处理停止] 用户手动停止了处理")
    
    def on_processing_progress(self, status: str):
        """处理进度更新"""
        self.status_label.setText(status)
        self.status_bar.showMessage(status)
        print(f"[处理进度] {status}")
    
    def on_processing_completed(self, action: str, result_text: str):
        """处理完成"""
        # 显示结果
        self.result_text_widget.setPlainText(result_text)
        
        # 添加到历史记录
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        action_name = next((desc.split(" - ")[0] for code, desc in 
                           LongTextProcessor().get_processing_options().items() 
                           if code == action), action)
        
        history_item = {
            "timestamp": timestamp,
            "action": action_name,
            "input_text": self.text_input.toPlainText()[:100] + "..." if len(self.text_input.toPlainText()) > 100 else self.text_input.toPlainText(),
            "result_text": result_text
        }
        self.processing_history.append(history_item)
        
        # 更新历史列表
        self.update_history_list()
        
        # 更新UI状态
        self.process_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("处理完成")
        self.status_bar.showMessage("处理完成")
        
        print(f"[处理完成] {action_name}: 结果长度 {len(result_text)} 字符")
        
        # 显示完成提示
        QMessageBox.information(self, "处理完成", f"{action_name}处理完成！")
    
    def on_processing_failed(self, action: str, error_message: str):
        """处理失败"""
        self.status_label.setText("处理失败")
        self.status_bar.showMessage("处理失败")
        
        print(f"[处理失败] {action}: {error_message}")
        
        # 更新UI状态
        self.process_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        # 显示错误信息
        QMessageBox.critical(self, "处理失败", f"处理失败:\n{error_message}")
    
    def on_action_changed(self):
        """处理类型改变"""
        action_code = self.action_combo.currentData()
        action_name = self.action_combo.currentText().split(" - ")[0]
        
        # 根据不同的处理类型调整界面提示
        if action_code == "summarize":
            self.text_input.setPlaceholderText("请输入要总结的长文本...")
        elif action_code == "polish":
            self.text_input.setPlaceholderText("请输入要润色的文本...")
        elif action_code == "correct":
            self.text_input.setPlaceholderText("请输入要纠错的文本...")
        elif action_code == "extract_keywords":
            self.text_input.setPlaceholderText("请输入要提取关键词的文本...")
        elif action_code == "structure":
            self.text_input.setPlaceholderText("请输入要结构化整理的文本...")
        else:
            self.text_input.setPlaceholderText("请输入要处理的文本...")
    
    def copy_result(self):
        """复制处理结果"""
        text = self.result_text_widget.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.status_bar.showMessage("处理结果已复制到剪贴板")
        else:
            QMessageBox.information(self, "提示", "没有可复制的处理结果")
    
    def save_result(self):
        """保存处理结果"""
        text = self.result_text_widget.toPlainText()
        if not text:
            QMessageBox.information(self, "提示", "没有可保存的处理结果")
            return
        
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(
            self, "保存处理结果", 
            f"processed_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "文本文件 (*.txt);;Markdown文件 (*.md);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                self.status_bar.showMessage(f"处理结果已保存到: {file_path}")
                print(f"[保存结果] 已保存到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"保存文件时出错:\n{str(e)}")
    
    def export_result(self):
        """导出格式化文档"""
        text = self.result_text_widget.toPlainText()
        if not text:
            QMessageBox.information(self, "提示", "没有可导出的处理结果")
            return
        
        # 这里可以扩展支持导出为Word、PDF等格式
        # 目前先实现Markdown格式导出
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(
            self, "导出文档", 
            f"processed_document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            "Markdown文件 (*.md);;文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                # 构建格式化的文档内容
                action_name = self.action_combo.currentText().split(" - ")[0]
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                formatted_content = f"""# {action_name}结果

**处理时间:** {timestamp}
**处理类型:** {action_name}
**AI模型:** {self.model_combo.currentText()}

---

## 处理结果

{text}

---

*由 CapsWriter 长文本处理工具生成*
"""
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(formatted_content)
                self.status_bar.showMessage(f"文档已导出到: {file_path}")
                print(f"[导出文档] 已导出到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出文档时出错:\n{str(e)}")
    
    def update_history_list(self):
        """更新历史记录列表"""
        self.history_list.clear()
        
        for item in reversed(self.processing_history):  # 最新的在前面
            list_item = QListWidgetItem()
            list_item.setText(f"{item['timestamp']} - {item['action']}\n{item['input_text']}")
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self.history_list.addItem(list_item)
    
    def load_history_item(self):
        """加载历史记录项"""
        current_item = self.history_list.currentItem()
        if current_item:
            item_data = current_item.data(Qt.ItemDataRole.UserRole)
            
            # 加载到结果显示区域
            self.result_text_widget.setPlainText(item_data['result_text'])
            self.current_info_label.setText(f"历史记录: {item_data['action']} ({item_data['timestamp']})")
            
            # 切换到结果标签页
            self.tab_widget.setCurrentIndex(0)
    
    def clear_history(self):
        """清空历史记录"""
        if self.processing_history:
            reply = QMessageBox.question(
                self, "确认清空", 
                f"确定要清空所有 {len(self.processing_history)} 条历史记录吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.processing_history.clear()
                self.history_list.clear()
                self.status_bar.showMessage("历史记录已清空")
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self, "关于",
            "CapsWriter 长文本处理与归纳工具\n\n"
            "版本: 1.0.0\n"
            "支持长文本的AI处理，包括总结、润色、纠错等功能\n"
            "自动处理AI模型上下文长度限制问题\n\n"
            "项目地址: https://github.com/HaujetZhao/CapsWriter-Offline"
        )
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.current_worker and self.current_worker.isRunning():
            reply = QMessageBox.question(
                self, "确认退出",
                "处理正在进行中，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.current_worker.cancel()
                self.current_worker.wait(3000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """主函数"""
    print("[应用启动] CapsWriter 长文本处理工具正在启动...")
    print(f"[系统信息] Python版本: {sys.version}")
    print(f"[工作目录] {os.getcwd()}")
    
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("CapsWriter 长文本处理工具")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("CapsWriter")
    
    print("[界面初始化] 正在创建主窗口...")
    
    # 创建主窗口
    window = LongTextProcessingGUI()
    window.show()
    
    print("[应用就绪] 长文本处理工具已启动完成")
    print("=" * 50)
    
    # 运行应用程序
    sys.exit(app.exec())


if __name__ == "__main__":
    main()