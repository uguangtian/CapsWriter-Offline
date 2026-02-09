import sys
import os
import time

# Add project root to path
sys.path.append(os.getcwd())

from util.llm_corrector import LLMCorrector
from util.config import LLMCorrectionConfig
from util.client_cosmic import console

def test_real():
    print("Initializing...")
    # Reset singleton to force re-initialization with new config
    LLMCorrector._instance = None
    
    LLMCorrectionConfig.enable = True
    LLMCorrectionConfig.model_path = "models/Qwen2.5-1.5B-Instruct-q4_k_m.gguf"
    
    corrector = LLMCorrector()
    
    if not corrector.enabled:
        print("Failed to enable corrector")
        return

    print("\n--- Testing Fast Mode ---")
    text_with_error = "今天天器真不错，我想去工园玩一下。" 
    print(f"Original: {text_with_error}")
    
    start = time.time()
    result = corrector.correct(text_with_error, mode="fast")
    elapsed = time.time() - start
    
    print(f"Corrected: {result}")
    print(f"Time: {elapsed:.4f}s")
    
    print("\n--- Testing Accurate Mode ---")
    corrector.history.append("我们要去哪里？")
    corrector.history.append("去那个新建的游乐场吧。")
    text_with_error_2 = "好啊，听说那里有很有意思的设视。"
    print(f"Context: {list(corrector.history)}")
    print(f"Original: {text_with_error_2}")
    
    start = time.time()
    result = corrector.correct(text_with_error_2, mode="accurate")
    elapsed = time.time() - start
    
    print(f"Corrected: {result}")
    print(f"Time: {elapsed:.4f}s")

if __name__ == "__main__":
    test_real()
