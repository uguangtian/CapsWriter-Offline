
import unittest
from unittest.mock import MagicMock, PropertyMock
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.server_recognize_paraformer import paraformerRecognize
from util.server_classes import Task, Result

class TestServerRecognizeParaformer(unittest.TestCase):
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
        type(mock_result).tokens = PropertyMock(side_effect=UnicodeDecodeError('utf-8', b'\xe7', 0, 1, 'unexpected end of data'))
        
        # Create a dummy task
        task = Task(
            source='mic',
            data=b'\x00' * 32000, # 1 sec of audio
            offset=0.0,
            overlap=0.0,
            task_id='test_task_id_para',
            socket_id='test_socket_id',
            is_final=True,
            time_start=0.0,
            time_submit=0.0
        )
        
        # Mock punc_model (can be None)
        punc_model = None
        
        # Run recognize
        result = paraformerRecognize(mock_recognizer, punc_model, task)
        
        # Verify result
        self.assertIsInstance(result, Result)
        # Should return result with empty text/tokens for this chunk
        self.assertEqual(result.text, "")
        self.assertEqual(result.tokens, [])
        self.assertEqual(result.timestamps, [])

if __name__ == '__main__':
    unittest.main()
