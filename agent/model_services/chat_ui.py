from flask import Flask, request, jsonify, render_template, Response, stream_with_context, send_from_directory
import requests
import json
import logging
import os
import time
from datetime import datetime
from util.chat_ui_config_manager import config, update_config
from util.chat_ui_data_manager import data_manager

app = Flask(__name__)

# 配置日志
logging.basicConfig(
    level=getattr(logging, config["chat_ui"]["log_level"]),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('chat_ui.log')
    ]
)
logger = logging.getLogger(__name__)

# 从配置文件加载配置
chat_config = config["chat_ui"]
DEFAULT_API_URL = chat_config["api_url"]
DEFAULT_API_KEY = chat_config["api_key"]
DEFAULT_MODEL = chat_config["model"]

# 配置上传目录
UPLOAD_FOLDER = data_manager.uploads_dir
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = chat_config["max_file_size"]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/file', methods=['POST'])
def handle_file():
    """处理文件上传请求"""
    if not chat_config["enable_file_upload"]:
        return jsonify({'status': 'error', 'message': '文件上传功能已禁用'}), 403

    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': '未找到文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': '未选择文件'}), 400

        # 检查文件扩展名
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in chat_config["allowed_extensions"]:
            return jsonify({'status': 'error', 'message': f'不支持的文件类型。允许的类型: {", ".join(chat_config["allowed_extensions"])}'}), 400

        # 处理分块上传
        chunk_index = int(request.form.get('chunkIndex', 0))
        total_chunks = int(request.form.get('totalChunks', 1))
        file_id = request.form.get('fileId', datetime.now().strftime('%Y%m%d%H%M%S'))
        
        # 保存文件块
        data_manager.save_file_chunk(file.read(), file_id, chunk_index)
        
        # 如果是最后一个块，则合并文件
        if chunk_index == total_chunks - 1:
            filename, extension = os.path.splitext(file.filename)
            unique_filename = f"{filename}_{int(time.time())}{extension}"
            
            final_path = data_manager.merge_file_chunks(file_id, unique_filename, total_chunks)
            if final_path:
                file_url = f"/uploads/{os.path.basename(final_path)}"
                return jsonify({
                    'status': 'success',
                    'message': '文件上传成功',
                    'filename': unique_filename,
                    'fileUrl': file_url
                })
            else:
                return jsonify({'status': 'error', 'message': '文件合并失败'}), 500
        else:
            return jsonify({
                'status': 'progress',
                'message': f'块 {chunk_index + 1}/{total_chunks} 上传成功',
                'chunkIndex': chunk_index
            })
            
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        return jsonify({'status': 'error', 'message': f'文件上传失败: {str(e)}'}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """提供上传的文件访问"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/chat', methods=['POST'])
def chat():
    """处理聊天请求并流式返回响应"""
    try:
        data = request.json
        user_message = data.get('message', '')
        temperature = data.get('temperature', chat_config["temperature"])
        model = data.get('model', DEFAULT_MODEL)
        api_url = data.get('api_url', DEFAULT_API_URL)
        api_key = data.get('api_key', DEFAULT_API_KEY)
        
        logger.info(f"收到聊天请求 - 模型: {model}, 温度: {temperature}")
        logger.debug(f"用户消息: {user_message}")
        
        # 构建请求负载
        messages = [
            {"role": "user", "content": user_message}
        ]
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": float(temperature),
            "stream": True,
            "stream_options": {
                "include_usage": True
            }
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        def generate():
            full_response = ""
            try:
                logger.info(f"开始调用API: {api_url}")
                logger.debug(f"请求负载: {payload}")
                response = requests.post(
                    api_url,
                    headers=headers,
                    json=payload,
                    stream=True,
                    timeout=60
                )
                
                logger.info(f"响应信息:")
                logger.info(f"- 状态码: {response.status_code}")
                logger.info(f"- 响应头: {dict(response.headers)}")
                
                if response.status_code != 200:
                    error_msg = f"API调用失败，状态码: {response.status_code}"
                    try:
                        error_content = response.content.decode('utf-8')
                        logger.error(f"错误响应内容: {error_content}")
                        try:
                            error_json = json.loads(error_content)
                            error_msg += f", 错误信息: {json.dumps(error_json)}"
                        except json.JSONDecodeError:
                            error_msg += f", 响应内容: {error_content}"
                    except Exception as e:
                        error_msg += f", 无法解析响应: {str(e)}"
                    
                    logger.error(error_msg)
                    yield f"data: {json.dumps({'content': error_msg})}\n\n"
                    return
                
                for line in response.iter_lines():
                    if line:
                        try:
                            line_text = line.decode('utf-8')
                            if len(line_text) == 0:
                                continue
                                
                            logger.debug(f"接收到的行: {line_text}")
                            
                            if line_text.startswith('data: '):
                                json_str = line_text[6:]
                                
                                if json_str == '[DONE]':
                                    logger.info("聊天完成")
                                    # 保存聊天记录
                                    if chat_config["enable_history"]:
                                        data_manager.add_chat_record(
                                            user_message=user_message,
                                            ai_response=full_response,
                                            model=model,
                                            temperature=temperature
                                        )
                                    yield f"data: {json.dumps({'content': '[DONE]'})}\n\n"
                                    return
                                    
                                try:
                                    data = json.loads(json_str)
                                    choices = data.get('choices', [])
                                    
                                    if choices and 'delta' in choices[0]:
                                        delta = choices[0]['delta']
                                        content = delta.get('content', '')
                                        
                                        if content:
                                            full_response += content
                                            yield f"data: {json.dumps({'content': content})}\n\n"
                                    
                                except json.JSONDecodeError as e:
                                    logger.error(f"JSON解析错误: {str(e)}\n原始数据: {json_str}")
                                    continue
                        except Exception as e:
                            logger.error(f"处理响应行时出错: {str(e)}")
                            continue
                
                yield f"data: {json.dumps({'content': '[DONE]'})}\n\n"
                
            except requests.exceptions.Timeout:
                logger.error("API请求超时")
                yield f"data: {json.dumps({'content': '请求超时，请稍后再试。'})}\n\n"
                
            except Exception as e:
                logger.error(f"API调用出错: {str(e)}")
                yield f"data: {json.dumps({'content': f'抱歉，服务出现错误: {str(e)}'})}\n\n"

        return Response(stream_with_context(generate()), mimetype='text/event-stream')
    
    except Exception as e:
        logger.error(f"处理请求出错: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    """获取或更新API设置"""
    if request.method == 'POST':
        try:
            data = request.json
            api_url = data.get('api_url')
            api_key = data.get('api_key')
            
            # 更新配置
            if api_url:
                update_config("chat_ui", "api_url", api_url)
            if api_key:
                update_config("chat_ui", "api_key", api_key)
                
            return jsonify({"status": "success", "message": "设置已更新"})
            
        except Exception as e:
            logger.error(f"更新设置失败: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500
    else:
        # 返回当前设置
        return jsonify({
            "api_url": DEFAULT_API_URL,
            "api_key": "******"  # 出于安全考虑不返回实际 API Key
        })

@app.route('/chat/history', methods=['GET'])
def get_chat_history():
    """获取聊天历史"""
    if not chat_config["enable_history"]:
        return jsonify({"status": "error", "message": "历史记录功能已禁用"}), 403

    try:
        limit = request.args.get('limit', type=int)
        if limit is None:
            limit = chat_config["max_history"]
        history = data_manager.get_chat_history(limit)
        return jsonify({"status": "success", "history": history})
    except Exception as e:
        logger.error(f"获取聊天历史失败: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/chat/history', methods=['DELETE'])
def clear_chat_history():
    """清空聊天历史"""
    if not chat_config["enable_history"]:
        return jsonify({"status": "error", "message": "历史记录功能已禁用"}), 403

    try:
        data_manager.clear_chat_history()
        return jsonify({"status": "success", "message": "聊天历史已清空"})
    except Exception as e:
        logger.error(f"清空聊天历史失败: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/uploads', methods=['DELETE'])
def clean_uploads():
    """清理上传的文件"""
    try:
        data_manager.clean_temp_files()
        return jsonify({"status": "success", "message": "临时文件已清理"})
    except Exception as e:
        logger.error(f"清理文件失败: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    """处理文件过大错误"""
    return jsonify({'status': 'error', 'message': f'文件大小超过限制 ({chat_config["max_file_size"] / (1024*1024):.0f}MB)'}), 413

@app.errorhandler(404)
def not_found(error):
    """处理404错误"""
    return jsonify({'status': 'error', 'message': '请求的资源不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    """处理500错误"""
    return jsonify({'status': 'error', 'message': '服务器内部错误'}), 500

if __name__ == '__main__':
    app.run(debug=True, host=chat_config["host"], port=chat_config["port"])
