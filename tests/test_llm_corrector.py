import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import collections

# Add project root to path
sys.path.append(os.getcwd())

# Mock llama_cpp before importing llm_corrector
sys.modules["llama_cpp"] = MagicMock()

from util.llm_corrector import LLMCorrector
from util.config import LLMCorrectionConfig

class TestLLMCorrector(unittest.TestCase):
    def setUp(self):
        # Reset singleton
        LLMCorrector._instance = None
        
        # Enable LLM for testing
        self.original_enable = LLMCorrectionConfig.enable
        LLMCorrectionConfig.enable = True
        LLMCorrectionConfig.model_path = "mock_path"
        
        # Patch os.path.exists to return True
        self.patcher = patch("os.path.exists", return_value=True)
        self.patcher.start()

    def tearDown(self):
        LLMCorrectionConfig.enable = self.original_enable
        self.patcher.stop()

    def test_initialization(self):
        corrector = LLMCorrector()
        self.assertTrue(corrector.enabled)
        self.assertIsNotNone(corrector.model)
        self.assertEqual(len(corrector.history), 0)

    def test_fast_mode_prompt(self):
        corrector = LLMCorrector()
        corrector.model = MagicMock()
        corrector.model.return_value = {
            "choices": [{"text": "修正后的文本"}]
        }
        
        text = "测试文本"
        result = corrector.correct(text, mode="fast")
        
        # Check prompt
        args, kwargs = corrector.model.call_args
        prompt = args[0]
        self.assertIn("修正ASR中的明显同音字/错字，不增删内容：测试文本", prompt)
        self.assertIn("temperature", kwargs)
        self.assertEqual(kwargs["temperature"], 0.01)

    def test_accurate_mode_prompt(self):
        corrector = LLMCorrector()
        corrector.model = MagicMock()
        corrector.model.return_value = {
            "choices": [{"text": "修正后的文本"}]
        }
        
        # Add history
        corrector.history.append("历史1")
        corrector.history.append("历史2")
        
        text = "测试文本"
        result = corrector.correct(text, mode="accurate")
        
        # Check prompt
        args, kwargs = corrector.model.call_args
        prompt = args[0]
        self.assertIn("根据最近2句上下文", prompt)
        self.assertIn("历史1 历史2 测试文本", prompt)
        self.assertEqual(kwargs["temperature"], 0.1)
        
        # Check history update
        self.assertEqual(list(corrector.history), ["历史1", "历史2", "修正后的文本"])

if __name__ == '__main__':
    unittest.main()
