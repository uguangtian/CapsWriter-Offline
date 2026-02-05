
import unittest
from unittest.mock import MagicMock, PropertyMock
import numpy as np
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.server_recognize_sensevoice import recognize
from util.server_classes import Task, Result

class TestServerRecognizeSenseVoice(unittest.TestCase):
    def test_recognize_unicode_decode_error(self):
        # Mock recognizer and stream
        mock_recognizer = MagicMock()
        mock_stream = MagicMock()
        mock_recognizer.create_stream.return_value = mock_stream
        
        # Mock stream result
        mock_result = MagicMock()
        mock_stream.result = mock_result
        
        # Mock timestamps
        mock_result.timestamps = [0.1, 0.2, 0.3]
        
        # Mock tokens raising UnicodeDecodeError
        # PropertyMock needed because tokens is likely accessed as property
        type(mock_result).tokens = PropertyMock(side_effect=UnicodeDecodeError('utf-8', b'\xe7', 0, 1, 'unexpected end of data'))
        
        # Create a dummy task
        task = Task(
            source='mic',
            data=b'\x00' * 32000, # 1 sec of audio
            offset=0.0,
            overlap=0.0,
            task_id='test_task_id',
            socket_id='test_socket_id',
            is_final=True,
            time_start=0.0,
            time_submit=0.0
        )
        
        # Run recognize
        result = recognize(mock_recognizer, task)
        
        # Verify result
        self.assertIsInstance(result, Result)
        self.assertEqual(result.text, "")
        self.assertEqual(result.tokens, [])
        # Timestamps should also be empty because we skip on error
        self.assertEqual(result.timestamps, [])

if __name__ == '__main__':
    unittest.main()
