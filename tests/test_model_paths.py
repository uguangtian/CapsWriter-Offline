import unittest
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.config import ModelPaths, SenseVoiceArgs, ParaformerArgs

class TestModelPaths(unittest.TestCase):
    def test_expanduser_applied(self):
        # Model dir should expand '~'
        self.assertTrue(str(ModelPaths.model_dir).startswith(str(Path.home())))

    def test_paths_under_model_dir(self):
        # SenseVoice and Paraformer path prefixes should start with model_dir
        self.assertTrue(str(ModelPaths.sensevoice_path).startswith(str(ModelPaths.model_dir)))
        self.assertTrue(str(ModelPaths.paraformer_path).startswith(str(ModelPaths.model_dir)))
        self.assertTrue(str(ModelPaths.punc_model_dir).startswith(str(ModelPaths.model_dir)))
        self.assertTrue(str(ModelPaths.opus_mt_dir).startswith(str(ModelPaths.model_dir)))
        self.assertTrue(str(ModelPaths.funasr_nano_dir).startswith(str(ModelPaths.model_dir)))

    def test_args_use_expanded_paths(self):
        # Ensure args return expanded absolute strings
        self.assertTrue(SenseVoiceArgs.model.startswith(str(Path.home())))
        self.assertTrue(SenseVoiceArgs.tokens.startswith(str(Path.home())))
        self.assertTrue(ParaformerArgs.paraformer.startswith(str(Path.home())))
        self.assertTrue(ParaformerArgs.tokens.startswith(str(Path.home())))

if __name__ == '__main__':
    unittest.main()
