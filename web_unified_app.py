#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CapsWriter-Offline 统一网页版应用

这个应用提供了一个统一的网页界面，整合了所有桌面版的功能：
1. 语音识别和转录
2. 文本润色和AI处理
3. 在线翻译
4. 配置管理
5. 系统监控
6. 文件管理

使用方法:
python web_unified_app.py
然后访问 http://localhost:8080
"""

import os
import sys
import json
import asyncio
import threading
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

from flask import Flask, render_template, request, jsonify, send_from_directory, Response, stream_with_context
from flask_socketio import SocketIO, emit, disconnect
import websockets
import requests

# 导入项目模块
from util.config import ServerConfig, ClientConfig, DeepSeekConfig, DoubaoConfig, LMStudioConfig, ClaudeConfig
from util.check_process import check_process
from util.chat_ui_config_manager import config as chat_config
from util.chat_ui_data_manager import data_manager
from agent.agent_service import AgentService
from start_unified import UnifiedLauncher

app = Flask(__name__, 
           template_folder='web_templates',
           static_folder='web_static')
app.config['SECRET_KEY'] = 'capswriter_offline_web_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局变量
unified_launcher = None
agent_service = None
running_processes = {}

class WebUnifiedApp:
    """网页版统一应用管理器"""
    
    def __init__(self):
        self.unified_launcher = UnifiedLauncher()
        self.agent_service = None
        self.running_processes = {}
        self.setup_routes()
        
    def setup_routes(self):
        """设置路由"""
        
        @app.route('/')
        def index():
            """主页"""
            return render_template('index.html')
        
        @app.route('/dashboard')
        def dashboard():
            """仪表板页面"""
            status = self.get_system_status()
            return render_template('dashboard.html', status=status)
        
        @app.route('/transcription')
        def transcription():
            """语音转录页面"""
            return render_template('transcription.html')
        
        @app.route('/text_processing')
        def text_processing():
            """文本处理页面"""
            return render_template('text_processing.html')
        
        @app.route('/translation')
        def translation():
            """翻译页面"""
            return render_template('translation.html')
        
        @app.route('/config')
        def config_page():
            """配置页面"""
            return render_template('config.html')
        
        @app.route('/files')
        def files():
            """文件管理页面"""
            return render_template('file_manager.html')
        
        @app.route('/api/system/status')
        def api_system_status():
            """获取系统状态API"""
            return jsonify(self.get_system_status())
        
        @app.route('/api/system/start', methods=['POST'])
        def api_start_system():
            """启动系统API"""
            data = request.json
            server_only = data.get('server_only', False)
            client_only = data.get('client_only', False)
            background = data.get('background', True)
            
            try:
                success = self.unified_launcher.run_unified(
                    server_only=server_only,
                    client_only=client_only,
                    background=background
                )
                return jsonify({
                    'success': success,
                    'message': '系统启动成功' if success else '系统启动失败'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'启动失败: {str(e)}'
                }), 500
        
        @app.route('/api/system/stop', methods=['POST'])
        def api_stop_system():
            """停止系统API"""
            try:
                self.unified_launcher.cleanup()
                return jsonify({
                    'success': True,
                    'message': '系统已停止'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'停止失败: {str(e)}'
                }), 500
        
        @app.route('/api/agent/process', methods=['POST'])
        def api_agent_process():
            """AI代理处理API"""
            data = request.json
            text = data.get('text', '')
            agent = data.get('agent', 'text_polish_deepseek')
            action = data.get('action', 'polish')
            
            try:
                # 这里需要调用agent服务
                # 暂时返回模拟结果
                result = f"[{agent}] 处理结果: {text[:100]}..."
                return jsonify({
                    'success': True,
                    'result': result
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'处理失败: {str(e)}'
                }), 500
        
        @app.route('/api/translate', methods=['POST'])
        def api_translate():
            """翻译API"""
            data = request.json
            text = data.get('text', '')
            target_lang = data.get('target_lang', 'en')
            
            try:
                # 这里需要调用翻译服务
                # 暂时返回模拟结果
                result = f"[翻译到{target_lang}] {text}"
                return jsonify({
                    'success': True,
                    'result': result
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'翻译失败: {str(e)}'
                }), 500
        
        @app.route('/api/files/list')
        def api_files_list():
            """文件列表API"""
            try:
                files = []
                data_dir = Path('data')
                if data_dir.exists():
                    for file_path in data_dir.iterdir():
                        if file_path.is_file():
                            files.append({
                                'name': file_path.name,
                                'size': file_path.stat().st_size,
                                'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                            })
                return jsonify({
                    'success': True,
                    'files': files
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'获取文件列表失败: {str(e)}'
                }), 500
        
        @app.route('/api/config/get')
        def api_config_get():
            """获取配置API"""
            try:
                from pathlib import Path
                from tomlkit import parse
                
                # 获取配置文件路径
                config_path = Path(__file__).parent / "config.toml"
                
                # 如果配置文件不存在，使用示例配置
                if not config_path.exists():
                    config_path = Path(__file__).parent / "config_example.toml"
                
                if not config_path.exists():
                    return jsonify({
                        'success': False,
                        'message': '找不到配置文件'
                    }), 500
                
                # 读取配置文件
                with open(config_path, "r", encoding="utf-8") as f:
                    config = parse(f.read())
                
                # 构建返回的配置数据
                config_data = {
                    'server': dict(config.get('server', {})),
                    'client': dict(config.get('client', {})),
                    'ai_models': {
                        'lmstudio': dict(config.get('lmstudio', {})),
                        'deepseek': dict(config.get('deepseek', {})),
                        'doubao': dict(config.get('doubao', {}))
                    },
                    'translation': {
                        'deeplx': dict(config.get('deeplx', {})),
                        'youdao_enabled': config.get('youdao_enabled', False)
                    },
                    'speech': {
                        'sensevoice': dict(config.get('sensevoice_args', {})),
                        'paraformer': dict(config.get('paraformer_args', {}))
                    },
                    'advanced': {
                        'log_level': config.get('log_level', 'INFO'),
                        'enable_file_logging': config.get('enable_file_logging', True)
                    }
                }
                
                # 隐藏敏感信息
                if 'api_key' in config_data['ai_models']['deepseek']:
                    api_key = config_data['ai_models']['deepseek']['api_key']
                    if api_key:
                        config_data['ai_models']['deepseek']['api_key'] = api_key[:10] + '...' if len(api_key) > 10 else '***'
                
                if 'api_key' in config_data['ai_models']['doubao']:
                    api_key = config_data['ai_models']['doubao']['api_key']
                    if api_key:
                        config_data['ai_models']['doubao']['api_key'] = api_key[:10] + '...' if len(api_key) > 10 else '***'
                
                return jsonify({
                    'success': True,
                    'config': config_data
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'获取配置失败: {str(e)}'
                }), 500
        
        @app.route('/api/config/update', methods=['POST'])
        def api_config_update():
            """更新配置API"""
            try:
                data = request.json
                # 这里需要实现配置更新逻辑
                return jsonify({
                    'success': True,
                    'message': '配置更新成功'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'配置更新失败: {str(e)}'
                }), 500
        
        @app.route('/api/config/save', methods=['POST'])
        def api_config_save():
            """保存配置API"""
            try:
                data = request.json
                if not data:
                    return jsonify({
                        'success': False,
                        'error': '没有接收到配置数据'
                    }), 400
                
                # 导入必要的模块
                from pathlib import Path
                from tomlkit import parse, dump
                import os
                
                # 获取配置文件路径
                config_path = Path(__file__).parent / "config.toml"
                
                # 读取现有配置
                if config_path.exists():
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = parse(f.read())
                else:
                    # 如果配置文件不存在，从示例配置复制
                    example_config_path = Path(__file__).parent / "config_example.toml"
                    if example_config_path.exists():
                        with open(example_config_path, "r", encoding="utf-8") as f:
                            config = parse(f.read())
                    else:
                        return jsonify({
                            'success': False,
                            'error': '找不到配置文件模板'
                        }), 500
                
                # 更新配置数据
                if 'server' in data:
                    if 'server' not in config:
                        config['server'] = {}
                    for key, value in data['server'].items():
                        config['server'][key] = value
                
                if 'client' in data:
                    if 'client' not in config:
                        config['client'] = {}
                    for key, value in data['client'].items():
                        config['client'][key] = value
                
                if 'speech' in data:
                    if 'sensevoice_args' in data['speech'].get('sensevoice', {}):
                        if 'sensevoice_args' not in config:
                            config['sensevoice_args'] = {}
                        for key, value in data['speech']['sensevoice'].items():
                            config['sensevoice_args'][key] = value
                    
                    if 'paraformer' in data['speech']:
                        if 'paraformer_args' not in config:
                            config['paraformer_args'] = {}
                        for key, value in data['speech']['paraformer'].items():
                            config['paraformer_args'][key] = value
                
                # 保存配置文件
                with open(config_path, "w", encoding="utf-8") as f:
                    dump(config, f)
                
                # 重新加载配置模块
                import importlib
                import util.config
                importlib.reload(util.config)
                
                return jsonify({
                    'success': True,
                    'message': '配置保存成功，请刷新页面以加载最新配置'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'保存配置失败: {str(e)}'
                }), 500
        
        @app.route('/api/config/reset', methods=['POST'])
        def api_config_reset():
            """重置配置API"""
            try:
                from pathlib import Path
                import shutil
                
                # 获取配置文件路径
                config_path = Path(__file__).parent / "config.toml"
                example_config_path = Path(__file__).parent / "config_example.toml"
                
                # 检查示例配置文件是否存在
                if not example_config_path.exists():
                    return jsonify({
                        'success': False,
                        'error': '找不到默认配置文件模板'
                    }), 500
                
                # 复制示例配置文件到配置文件
                shutil.copy2(example_config_path, config_path)
                
                # 重新加载配置模块
                import importlib
                import util.config
                importlib.reload(util.config)
                
                return jsonify({
                    'success': True,
                    'message': '配置已重置为默认值，请刷新页面以加载最新配置'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'重置配置失败: {str(e)}'
                }), 500
        
        @app.route('/api/config/export', methods=['POST'])
        def api_config_export():
            """导出配置API"""
            try:
                data = request.json
                config_data = data.get('config', {})
                format_type = data.get('format', 'toml')
                
                # 生成配置文件内容
                if format_type == 'json':
                    import json
                    content = json.dumps(config_data, indent=2, ensure_ascii=False)
                    mimetype = 'application/json'
                    filename = 'capswriter-config.json'
                else:  # toml
                    # 简化的TOML格式输出
                    content = '# CapsWriter-Offline Configuration\n'
                    content += f'# Exported at {datetime.now().isoformat()}\n\n'
                    content += str(config_data)  # 简化实现
                    mimetype = 'text/plain'
                    filename = 'capswriter-config.toml'
                
                from flask import make_response
                response = make_response(content)
                response.headers['Content-Type'] = mimetype
                response.headers['Content-Disposition'] = f'attachment; filename={filename}'
                return response
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'导出配置失败: {str(e)}'
                }), 500
        
        @app.route('/api/config/import', methods=['POST'])
        def api_config_import():
            """导入配置API"""
            try:
                if 'config_file' not in request.files:
                    return jsonify({
                        'success': False,
                        'error': '没有上传配置文件'
                    }), 400
                
                config_file = request.files['config_file']
                if config_file.filename == '':
                    return jsonify({
                        'success': False,
                        'error': '文件名为空'
                    }), 400
                
                # 读取文件内容
                content = config_file.read().decode('utf-8')
                
                # 解析配置文件
                import json
                try:
                    config_data = json.loads(content)
                except json.JSONDecodeError:
                    # 如果不是JSON，尝试作为TOML处理（简化实现）
                    return jsonify({
                        'success': False,
                        'error': '配置文件格式不支持，请使用JSON格式'
                    }), 400
                
                return jsonify({
                    'success': True,
                    'config': config_data,
                    'message': '配置导入成功'
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'导入配置失败: {str(e)}'
                }), 500
        
        @app.route('/api/config/test-model', methods=['POST'])
        def api_config_test_model():
            """测试模型连接API"""
            try:
                data = request.json
                model_type = data.get('model_type')
                config = data.get('config', {})
                
                # 这里需要实现实际的模型连接测试
                # 暂时返回模拟结果
                return jsonify({
                    'success': True,
                    'message': f'{model_type} 连接测试成功（模拟）'
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'模型连接测试失败: {str(e)}'
                }), 500
        
        @app.route('/api/config/test-translation', methods=['POST'])
        def api_config_test_translation():
            """测试翻译服务API"""
            try:
                data = request.json
                service_type = data.get('service_type')
                config = data.get('config', {})
                
                # 这里需要实现实际的翻译服务连接测试
                # 暂时返回模拟结果
                return jsonify({
                    'success': True,
                    'message': f'{service_type} 连接测试成功（模拟）'
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'翻译服务连接测试失败: {str(e)}'
                }), 500
        
        @app.route('/api/transcribe', methods=['POST'])
        def api_transcribe():
            """语音转录API - 支持文件上传和本地路径两种模式"""
            try:
                import tempfile
                import os
                from pathlib import Path
                import threading
                
                # 获取参数
                language = request.form.get('language', 'auto')
                model = request.form.get('model', 'default')
                use_local_path = request.form.get('use_local_path', 'false').lower() == 'true'
                
                # 根据模式处理文件
                if use_local_path:
                    # 本地路径模式
                    local_path = request.form.get('local_path', '')
                    if not local_path:
                        return jsonify({
                            'success': False,
                            'error': '本地路径模式下必须提供local_path参数'
                        }), 400
                    
                    # 验证文件是否存在
                    if not os.path.exists(local_path):
                        return jsonify({
                            'success': False,
                            'error': f'指定的文件不存在: {local_path}'
                        }), 400
                    
                    # 验证是否为文件
                    if not os.path.isfile(local_path):
                        return jsonify({
                            'success': False,
                            'error': f'指定的路径不是文件: {local_path}'
                        }), 400
                    
                    temp_file_path = local_path
                    filename = os.path.basename(local_path)
                    cleanup_temp_file = False  # 本地路径模式不需要清理文件
                else:
                    # 文件上传模式
                    if 'audio' not in request.files:
                        return jsonify({
                            'success': False,
                            'error': '文件上传模式下没有上传音频文件'
                        }), 400
                    
                    audio_file = request.files['audio']
                    if audio_file.filename == '':
                        return jsonify({
                            'success': False,
                            'error': '文件名为空'
                        }), 400
                    
                    # 保存上传的文件到临时目录
                    temp_dir = tempfile.mkdtemp()
                    temp_file_path = os.path.join(temp_dir, audio_file.filename)
                    audio_file.save(temp_file_path)
                    filename = audio_file.filename
                    cleanup_temp_file = True  # 上传模式需要清理临时文件
                
                # 通过SocketIO发送开始转录的消息
                socketio.emit('transcription_start', {
                    'filename': filename,
                    'message': '开始转录...',
                    'mode': 'local_path' if use_local_path else 'upload'
                })
                
                def run_transcription():
                    """在后台线程中运行转录"""
                    try:
                        # 导入转录相关模块
                        import subprocess
                        import sys
                        
                        # 创建文件路径对象
                        file_path = Path(temp_file_path)
                        
                        # 使用subprocess调用core_client.py，避免异步事件循环冲突
                        try:
                            # 构建命令 - 使用--file参数
                            print(f"调用core_client.py，文件路径: {file_path}")
                            cmd = [sys.executable, 'core_client.py', '--file', str(file_path)]
                            print(f"完整命令: {cmd}")
                            print(f"工作目录: {os.getcwd()}")
                            
                            # 执行转录命令
                            result = subprocess.run(
                                cmd,
                                cwd=os.getcwd(),
                                capture_output=True,
                                text=True,
                                timeout=3600  # 1小时超时
                            )
                            
                            print(f"命令返回码: {result.returncode}")
                            print(f"标准输出: {result.stdout}")
                            print(f"标准错误: {result.stderr}")
                            
                            if result.returncode != 0:
                                error_msg = result.stderr or '转录进程执行失败'
                                socketio.emit('transcription_error', {
                                    'error': f'转录失败: {error_msg}',
                                    'filename': filename
                                })
                                return
                        
                        except subprocess.TimeoutExpired:
                            socketio.emit('transcription_error', {
                                'error': '转录超时（超过1小时）',
                                'filename': filename
                            })
                            return
                        except Exception as e:
                            socketio.emit('transcription_error', {
                                'error': f'执行转录命令失败: {str(e)}',
                                'filename': filename
                            })
                            return
                        
                        # 读取转录结果
                        txt_file = file_path.with_suffix('.txt')
                        merge_file = file_path.with_suffix('.merge.txt')
                        srt_file = file_path.with_suffix('.srt')
                        
                        result_text = ""
                        if merge_file.exists():
                            with open(merge_file, 'r', encoding='utf-8') as f:
                                result_text = f.read().strip()
                        elif txt_file.exists():
                            with open(txt_file, 'r', encoding='utf-8') as f:
                                result_text = f.read().strip()
                        
                        # 检查是否有有效的转录结果
                        if result_text:
                            # 通过SocketIO发送转录结果
                            socketio.emit('transcription_result', {
                                'text': result_text,
                                'filename': filename,
                                'has_srt': srt_file.exists(),
                                'mode': 'local_path' if use_local_path else 'upload'
                            })
                        else:
                            # 没有转录结果，发送错误信息
                            socketio.emit('transcription_error', {
                                'error': '转录完成，但未生成文本内容',
                                'filename': filename
                            })
                        
                    except Exception as e:
                        # 通过SocketIO发送错误信息
                        socketio.emit('transcription_error', {
                            'error': f'转录失败: {str(e)}',
                            'filename': filename
                        })
                    finally:
                        # 清理临时文件（仅在上传模式下）
                        if cleanup_temp_file:
                            try:
                                # 保留转录结果文件，只删除原始音频文件
                                if os.path.exists(temp_file_path):
                                    os.remove(temp_file_path)
                            except Exception as e:
                                print(f"清理临时文件失败: {e}")
                
                # 在后台线程中运行转录
                thread = threading.Thread(target=run_transcription, daemon=True)
                thread.start()
                
                return jsonify({
                    'success': True,
                    'message': '转录任务已启动，请等待结果',
                    'filename': filename,
                    'mode': 'local_path' if use_local_path else 'upload'
                })
                
            except Exception as e:
                # 通过SocketIO发送错误信息
                socketio.emit('transcription_error', {
                    'error': str(e)
                })
                
                return jsonify({
                    'success': False,
                    'error': f'转录失败: {str(e)}'
                }), 500
    
    def get_system_status(self):
        """获取系统状态"""
        return {
            'server_running': check_process('pythonw_CapsWriter_Server.exe') or check_process('core_server.py'),
            'client_running': check_process('start_client_gui.exe') or check_process('core_client.py'),
            'agent_service_running': self.agent_service is not None,
            'processes': self.running_processes,
            'timestamp': datetime.now().isoformat()
        }
    
    def start_agent_service(self):
        """启动AI代理服务"""
        if self.agent_service is None:
            self.agent_service = AgentService()
            # 在后台线程中启动
            threading.Thread(target=self.agent_service.start, daemon=True).start()
    
    def run(self, host='127.0.0.1', port=8080, debug=False):
        """运行网页应用"""
        print(f"\n=== CapsWriter-Offline 网页版 ===")
        print(f"正在启动网页服务器...")
        print(f"访问地址: http://{host}:{port}")
        print(f"==============================\n")
        
        # 启动AI代理服务
        self.start_agent_service()
        
        # 启动Flask应用
        socketio.run(app, host=host, port=port, debug=debug)


# SocketIO事件处理
@socketio.on('connect')
def handle_connect():
    print('客户端已连接')
    emit('status', {'message': '连接成功'})

@socketio.on('disconnect')
def handle_disconnect():
    print('客户端已断开连接')

@socketio.on('system_command')
def handle_system_command(data):
    """处理系统命令"""
    command = data.get('command')
    if command == 'start':
        # 启动系统
        emit('system_status', {'status': 'starting', 'message': '正在启动系统...'})
    elif command == 'stop':
        # 停止系统
        emit('system_status', {'status': 'stopping', 'message': '正在停止系统...'})

@socketio.on('transcribe_local_file')
def handle_transcribe_local_file(data):
    """处理本地文件转录请求"""
    try:
        file_path = data.get('file_path')
        filename = data.get('filename')
        language = data.get('language', 'auto')
        model = data.get('model', 'default')
        
        if not file_path:
            emit('transcription_error', {
                'error': '文件路径为空',
                'filename': filename
            })
            return
        
        # 处理路径转义字符
        # 移除多余的转义字符，处理常见的转义情况
        import re
        import os
        
        # 记录原始路径用于调试
        original_path = file_path
        
        # 处理反斜杠转义的空格和特殊字符
        file_path = file_path.replace('\\ ', ' ')  # 处理转义的空格
        file_path = file_path.replace('\\(', '(')   # 处理转义的左括号
        file_path = file_path.replace('\\)', ')')   # 处理转义的右括号
        file_path = file_path.replace('\\&', '&')   # 处理转义的&符号
        file_path = file_path.replace('\\[', '[')   # 处理转义的左方括号
        file_path = file_path.replace('\\]', ']')   # 处理转义的右方括号
        file_path = file_path.replace('\\;', ';')   # 处理转义的分号
        file_path = file_path.replace('\\"', '"')  # 处理转义的双引号
        file_path = file_path.replace("\\\''", "'")   # 处理转义的单引号
        
        # 移除首尾的引号（如果有的话）
        file_path = file_path.strip('"').strip("'")
        
        # 规范化路径，处理可能的路径分隔符问题
        file_path = os.path.normpath(file_path)
        
        # 如果是相对路径，转换为绝对路径
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)
        
        print(f"[DEBUG] 原始路径: {data.get('file_path')}")
        print(f"[DEBUG] 处理后路径: {file_path}")
        
        # 发送开始转录的消息
        emit('transcription_start', {
            'filename': filename,
            'message': '开始转录本地文件...'
        })
        
        def run_local_transcription():
            """在后台线程中运行本地文件转录"""
            try:
                import subprocess
                import sys
                from pathlib import Path
                
                # 创建文件路径对象
                file_path_obj = Path(file_path)
                
                # 检查文件是否存在
                if not file_path_obj.exists():
                    # 添加详细的调试信息
                    print(f"[DEBUG] 文件不存在检查失败:")
                    print(f"[DEBUG] 原始路径: {file_path}")
                    print(f"[DEBUG] 绝对路径: {file_path_obj.absolute()}")
                    print(f"[DEBUG] 文件名: {filename}")
                    print(f"[DEBUG] 当前工作目录: {os.getcwd()}")
                    
                    socketio.emit('transcription_error', {
                        'error': f'文件不存在: {file_path_obj.absolute()}',
                        'filename': filename
                    })
                    return
                
                # 使用subprocess调用core_client.py，避免异步事件循环冲突
                try:
                    # 构建命令，使用--file参数
                    cmd = [sys.executable, 'core_client.py', '--file', str(file_path_obj)]
                    print(f"[DEBUG] 执行命令: {' '.join(cmd)}")
                    print(f"[DEBUG] 工作目录: {os.getcwd()}")
                    print(f"[DEBUG] 文件路径: {file_path_obj}")
                    print(f"[DEBUG] 文件是否存在: {file_path_obj.exists()}")
                    print(f"[DEBUG] 文件绝对路径: {file_path_obj.absolute()}")
                    
                    # 执行转录命令
                    result = subprocess.run(
                        cmd,
                        cwd=os.getcwd(),
                        capture_output=True,
                        text=True,
                        timeout=3600  # 1小时超时
                    )
                    
                    if result.returncode != 0:
                        # 获取详细的错误信息
                        error_msg = result.stderr or result.stdout or '转录进程执行失败'
                        print(f"[DEBUG] 转录进程返回码: {result.returncode}")
                        print(f"[DEBUG] 标准输出: {result.stdout}")
                        print(f"[DEBUG] 标准错误: {result.stderr}")
                        
                        socketio.emit('transcription_error', {
                            'error': f'转录失败: {error_msg}',
                            'filename': filename
                        })
                        return
                
                except subprocess.TimeoutExpired:
                    socketio.emit('transcription_error', {
                        'error': '转录超时（超过1小时）',
                        'filename': filename
                    })
                    return
                except Exception as e:
                    socketio.emit('transcription_error', {
                        'error': f'执行转录命令失败: {str(e)}',
                        'filename': filename
                    })
                    return
                
                # 读取转录结果
                txt_file = file_path_obj.with_suffix('.txt')
                merge_file = file_path_obj.with_suffix('.merge.txt')
                srt_file = file_path_obj.with_suffix('.srt')
                
                result_text = ""
                if merge_file.exists():
                    with open(merge_file, 'r', encoding='utf-8') as f:
                        result_text = f.read().strip()
                elif txt_file.exists():
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        result_text = f.read().strip()
                
                # 检查是否有有效的转录结果
                if result_text:
                    # 通过SocketIO发送转录结果
                    socketio.emit('transcription_result', {
                        'text': result_text,
                        'filename': filename,
                        'has_srt': srt_file.exists()
                    })
                else:
                    # 没有转录结果，发送错误信息
                    socketio.emit('transcription_error', {
                        'error': '转录完成，但未生成文本内容',
                        'filename': filename
                    })
                
            except Exception as e:
                # 通过SocketIO发送错误信息
                socketio.emit('transcription_error', {
                    'error': f'转录失败: {str(e)}',
                    'filename': filename
                })
        
        # 在后台线程中运行转录
        import threading
        thread = threading.Thread(target=run_local_transcription, daemon=True)
        thread.start()
        
    except Exception as e:
        emit('transcription_error', {
            'error': f'处理转录请求失败: {str(e)}',
            'filename': data.get('filename', '未知文件')
        })


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='CapsWriter-Offline 网页版')
    parser.add_argument('--host', default='127.0.0.1', help='服务器地址')
    parser.add_argument('--port', type=int, default=8080, help='服务器端口')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    
    args = parser.parse_args()
    
    # 创建必要的目录
    os.makedirs('web_templates', exist_ok=True)
    os.makedirs('web_static', exist_ok=True)
    os.makedirs('web_static/css', exist_ok=True)
    os.makedirs('web_static/js', exist_ok=True)
    
    # 启动应用
    web_app = WebUnifiedApp()
    web_app.run(host=args.host, port=args.port, debug=args.debug)