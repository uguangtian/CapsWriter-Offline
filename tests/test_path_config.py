
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import time
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.config import ClientConfig
from util import client_write_md

class TestPathConfig(unittest.TestCase):
    @patch('util.client_write_md.makedirs')
    @patch('util.client_write_md.open')
    @patch('util.client_write_md.ClientConfig')
    def test_write_md_uses_configured_path(self, mock_config, mock_open, mock_makedirs):
        # Setup mock config
        test_path = "~/Documents/Test/results"
        mock_config.transcription_result_path = test_path
        
        # Setup mock inputs
        text = "test text"
        time_start = time.time()
        file_audio = Path("/tmp/audio.mp3")
        
        # Call function
        client_write_md.write_md(text, time_start, file_audio)
        
        # Verify makedirs called with expanded path
        expected_path = Path(test_path).expanduser() / time.strftime("%Y", time.localtime(time_start)) / time.strftime("%m", time.localtime(time_start))
        
        # Check if makedirs was called with the expected path (or a path starting with it)
        # Note: write_md calls makedirs(folder_path, exist_ok=True)
        mock_makedirs.assert_called_with(expected_path, exist_ok=True)

    @patch('util.client_create_file.makedirs')
    @patch('util.client_create_file.tempfile.mktemp')
    @patch('util.client_create_file.Config')
    def test_create_file_uses_configured_path(self, mock_config, mock_mktemp, mock_makedirs):
        # We need to import client_create_file inside the test or patch where it's used
        from util import client_create_file
        
        # Setup mock config
        test_path = "~/Documents/Test/audio"
        mock_config.audio_storage_path = test_path
        
        # Call function
        # create_file(channels, time_start)
        client_create_file.create_file(1, time.time())
        
        # Verify path construction
        time_now = time.time()
        time_year = time.strftime("%Y", time.localtime(time_now))
        time_month = time.strftime("%m", time.localtime(time_now))
        
        expected_path = Path(test_path).expanduser() / time_year / time_month / "assets"
        
        mock_makedirs.assert_called_with(expected_path, exist_ok=True)

if __name__ == '__main__':
    unittest.main()
