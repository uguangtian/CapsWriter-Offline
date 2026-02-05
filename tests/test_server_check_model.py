import unittest
from pathlib import Path
import tempfile
import shutil

from util.server_check_model import _normalize_paths
from util.config import ModelPaths


class TestServerCheckModel(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Create sensevoice folder with model.onnx (no int8)
        sv_dir = Path(self.tmpdir) / "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17"
        sv_dir.mkdir(parents=True, exist_ok=True)
        (sv_dir / "model.onnx").write_text("dummy", encoding="utf-8")
        (sv_dir / "tokens.txt").write_text("dummy", encoding="utf-8")
        # Point ModelPaths to temp dir defaults
        ModelPaths.sensevoice_path = sv_dir / "model.int8.onnx"
        ModelPaths.sensevoice_tokens_path = sv_dir / "tokens.txt"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_sensevoice_path_fallback_to_model_onnx(self):
        self.assertFalse(Path(ModelPaths.sensevoice_path).exists())
        _normalize_paths()
        self.assertTrue(Path(ModelPaths.sensevoice_path).exists())
        self.assertEqual(Path(ModelPaths.sensevoice_path).name, "model.onnx")


if __name__ == "__main__":
    unittest.main()
