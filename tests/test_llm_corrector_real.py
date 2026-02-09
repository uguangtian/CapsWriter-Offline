import unittest
import sys
import os
import time

# Add project root to path
sys.path.append(os.getcwd())

from util.llm_corrector import LLMCorrector
from util.config import LLMCorrectionConfig
from util.client_cosmic import console

class TestLLMCorrectorReal(unittest.TestCase):
    def setUp(self):
        # Reset singleton
        LLMCorrector._instance = None
        
        # Enable LLM
        LLMCorrectionConfig.enable = True
        # Ensure model path is correct
        LLMCorrectionConfig.model_path = "models/Qwen2.5-1.5B-Instruct-q4_k_m.gguf"
        
        if not os.path.exists(LLMCorrectionConfig.model_path):
            self.skipTest("Model file not found")

    def test_real_inference_fast(self):
        console.print("\n[blue]Testing Fast Mode...[/blue]")
        corrector = LLMCorrector()
        
        if not corrector.enabled:
            self.skipTest("LLM Corrector failed to initialize (library missing or load error)")

        # 同音字测试
        text = "今天天气真不错，我想去公园玩一下。" # 这里的“一下”如果被识别成“一下儿”或者其他同音
        # 构造一个明显的错误
        text_with_error = "今天天气真不错，我想去工园玩一下。" 
        
        start = time.time()
        result = corrector.correct(text_with_error, mode="fast")
        elapsed = time.time() - start
        
        console.print(f"Original: {text_with_error}")
        console.print(f"Corrected: {result}")
        console.print(f"Time: {elapsed:.4f}s")
        
        self.assertNotEqual(result, text_with_error)
        self.assertIn("公园", result)

    def test_real_inference_accurate(self):
        console.print("\n[blue]Testing Accurate Mode...[/blue]")
        corrector = LLMCorrector()
        
        if not corrector.enabled:
            self.skipTest("LLM Corrector failed to initialize")

        # 上下文测试
        corrector.history.append("我们要去哪里？")
        corrector.history.append("去那个新建的游乐场吧。")
        
        text_with_error = "好啊，听说那里有很有意思的设视。" # 设施 -> 设视
        
        start = time.time()
        result = corrector.correct(text_with_error, mode="accurate")
        elapsed = time.time() - start
        
        console.print(f"Context: {list(corrector.history)[:-1]}")
        console.print(f"Original: {text_with_error}")
        console.print(f"Corrected: {result}")
        console.print(f"Time: {elapsed:.4f}s")
        
        self.assertNotEqual(result, text_with_error)
        self.assertIn("设施", result)

if __name__ == '__main__':
    unittest.main()
