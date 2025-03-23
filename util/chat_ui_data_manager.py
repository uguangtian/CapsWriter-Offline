import json
import os
from datetime import datetime
from pathlib import Path
import shutil

class DataManager:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.chat_history_file = self.data_dir / "chat_history.json"
        self.uploads_dir = self.base_dir / "agent" / "model_services" / "uploads"
        self.temp_dir = self.uploads_dir / "temp"
        
        # 创建必要的目录
        self.data_dir.mkdir(exist_ok=True)
        self.uploads_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        # 初始化聊天历史
        self.chat_history = self._load_chat_history()
        
    def _load_chat_history(self):
        """加载聊天历史"""
        if self.chat_history_file.exists():
            try:
                with open(self.chat_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载聊天历史失败: {e}")
                return []
        return []
        
    def save_chat_history(self):
        """保存聊天历史"""
        try:
            with open(self.chat_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.chat_history, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"保存聊天历史失败: {e}")
            return False
            
    def add_chat_record(self, user_message, ai_response, model="", temperature=0.7):
        """添加聊天记录"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "ai_response": ai_response,
            "model": model,
            "temperature": temperature
        }
        self.chat_history.append(record)
        self.save_chat_history()
        
    def get_chat_history(self, limit=None):
        """获取聊天历史"""
        if limit:
            return self.chat_history[-limit:]
        return self.chat_history
        
    def clear_chat_history(self):
        """清空聊天历史"""
        self.chat_history = []
        self.save_chat_history()
        
    def save_upload_file(self, file, filename):
        """保存上传的文件"""
        try:
            file_path = self.uploads_dir / filename
            file.save(str(file_path))
            return str(file_path)
        except Exception as e:
            print(f"保存文件失败: {e}")
            return None
            
    def save_file_chunk(self, chunk, file_id, chunk_index):
        """保存文件块"""
        try:
            chunk_dir = self.temp_dir / file_id
            chunk_dir.mkdir(exist_ok=True)
            chunk_path = chunk_dir / str(chunk_index)
            with open(chunk_path, 'wb') as f:
                f.write(chunk)
            return True
        except Exception as e:
            print(f"保存文件块失败: {e}")
            return False
            
    def merge_file_chunks(self, file_id, filename, total_chunks):
        """合并文件块"""
        try:
            chunk_dir = self.temp_dir / file_id
            final_path = self.uploads_dir / filename
            
            with open(final_path, 'wb') as outfile:
                for i in range(total_chunks):
                    chunk_path = chunk_dir / str(i)
                    with open(chunk_path, 'rb') as infile:
                        outfile.write(infile.read())
                        
            # 清理临时文件
            shutil.rmtree(chunk_dir)
            return str(final_path)
        except Exception as e:
            print(f"合并文件块失败: {e}")
            return None
            
    def get_upload_file_path(self, filename):
        """获取上传文件的路径"""
        file_path = self.uploads_dir / filename
        return str(file_path) if file_path.exists() else None
        
    def delete_upload_file(self, filename):
        """删除上传的文件"""
        try:
            file_path = self.uploads_dir / filename
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception as e:
            print(f"删除文件失败: {e}")
            return False
            
    def clean_temp_files(self):
        """清理临时文件"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.temp_dir.mkdir()
            return True
        except Exception as e:
            print(f"清理临时文件失败: {e}")
            return False

# 创建全局数据管理器实例
data_manager = DataManager() 