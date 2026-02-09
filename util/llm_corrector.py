import collections
import time
import traceback
from util.config import LLMCorrectionConfig
from util.client_cosmic import console

class LLMCorrector:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMCorrector, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        console.print(f"[dim]LLMCorrector initializing... Enabled: {LLMCorrectionConfig.enable}[/dim]")
        self.model = None
        self.history = collections.deque(maxlen=LLMCorrectionConfig.history_len)
        self.enabled = LLMCorrectionConfig.enable
        self._initialized = True
        
        if self.enabled:
            self.load_model()

    def load_model(self):
        try:
            from llama_cpp import Llama
            console.print(f"[green]正在加载 LLM 校正模型: {LLMCorrectionConfig.model_path}...[/green]")
            # 检查文件是否存在
            import os
            if not os.path.exists(LLMCorrectionConfig.model_path):
                console.print(f"[yellow]LLM 模型文件不存在: {LLMCorrectionConfig.model_path}[/yellow]")
                console.print(f"[yellow]LLM 校正功能将不会生效。[/yellow]")
                self.enabled = False
                return

            start_load = time.time()
            self.model = Llama(
                model_path=LLMCorrectionConfig.model_path,
                n_ctx=2048,
                n_threads=4,
                n_gpu_layers=-1, # 尝试使用 GPU 加速
                verbose=False
            )
            console.print(f"[green]LLM 校正模型加载成功！耗时: {time.time() - start_load:.2f}s[/green]")
        except ImportError:
            console.print("[red]未找到 llama-cpp-python 库。请安装: uv pip install llama-cpp-python[/red]")
            self.enabled = False
        except Exception as e:
            console.print(f"[red]加载 LLM 模型失败: {e}[/red]")
            console.print(traceback.format_exc())
            self.enabled = False

    def correct(self, text, mode=None):
        if not self.enabled:
            console.print("[dim]LLM correction disabled.[/dim]")
            return text
        
        if not self.model:
            console.print("[red]LLM model enabled but not loaded.[/red]")
            return text

        if mode is None:
            mode = LLMCorrectionConfig.mode

        console.print(f"[dim]LLM Request: '{text}' (mode={mode})[/dim]")
        start_time = time.time()
        
        try:
            if mode == "fast":
                messages = [
                    {"role": "system", "content": "你是一个中文语音识别纠错助手。请纠正句子中的同音字和错别字，直接输出修正后的句子，不要解释。"},
                    {"role": "user", "content": text}
                ]
                max_tokens = LLMCorrectionConfig.fast_mode_max_tokens
                temperature = 0.1
            else: # accurate
                context = " ".join(self.history)
                messages = [
                    {"role": "system", "content": "你是一个中文语音识别纠错助手。根据上下文纠正当前句子的同音字和错别字，并补全标点。注意：仅输出修正后的当前句子，不要重复上下文，不要包含解释。"},
                    {"role": "user", "content": f"上下文：{context}\n当前句：{text}"}
                ]
                max_tokens = LLMCorrectionConfig.accurate_mode_max_tokens
                temperature = 0.2

            console.print(f"[dim]LLM Prompt Messages: {messages}[/dim]")

            output = self.model.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            console.print(f"[dim]LLM Raw Output: {output}[/dim]")
            
            corrected_text = output['choices'][0]['message']['content'].strip()
            
            # 如果结果为空或异常，回退到原文本
            if not corrected_text:
                console.print(f"[yellow]LLM returned empty text, falling back to original.[/yellow]")
                return text
                
            elapsed = time.time() - start_time
            console.print(f"[dim]LLM 校正 ({mode}): {text} -> {corrected_text} ({elapsed:.2f}s)[/dim]")
            
            # 更新历史
            self.history.append(corrected_text)
            
            return corrected_text

        except Exception as e:
            console.print(f"[red]LLM 推理出错: {e}[/red]")
            console.print(traceback.format_exc())
            return text

# 全局单例
llm_corrector = LLMCorrector()
