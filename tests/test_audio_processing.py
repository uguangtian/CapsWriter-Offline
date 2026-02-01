
import unittest
import numpy as np
import base64
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestAudioProcessing(unittest.TestCase):
    def test_audio_processing_logic(self):
        """
        Simulate the audio processing logic in client_send_audio.py
        """
        # 1. Simulate Audio Data (48kHz, Stereo)
        # 1 second of audio = 48000 samples
        # Stereo = 2 channels
        # Shape = (48000, 2)
        sample_rate = 48000
        duration = 1  # seconds
        num_samples = sample_rate * duration
        channels = 2
        
        # Generate random float data between -1.0 and 1.0
        data = np.random.uniform(-1.0, 1.0, (num_samples, channels)).astype(np.float32)
        
        print(f"Original Data Shape: {data.shape}")
        
        # 2. Apply the processing logic from client_send_audio.py
        try:
            # Logic from code:
            # if len(data.shape) > 1:
            #    processed_data = np.mean(data[::3], axis=1)
            # else:
            #    processed_data = data[::3]
            
            # Downsample from 48k to 16k (take every 3rd sample)
            downsampled = data[::3]
            self.assertEqual(downsampled.shape[0], num_samples // 3)
            
            # Convert Stereo to Mono (mean across channels)
            if len(downsampled.shape) > 1:
                processed_data = np.mean(downsampled, axis=1)
            else:
                processed_data = downsampled
                
            self.assertEqual(len(processed_data.shape), 1)
            self.assertEqual(processed_data.shape[0], 16000)
            
            # Encode to Base64
            final_data = base64.b64encode(
                processed_data.astype(np.float32).tobytes()
            ).decode("utf-8")
            
            print(f"Encoded Data Length: {len(final_data)}")
            self.assertTrue(len(final_data) > 0)
            
        except Exception as e:
            self.fail(f"Audio processing failed: {e}")

    def test_empty_data_logic(self):
        """
        Test how the logic handles empty or small data
        """
        data = np.array([], dtype=np.float32)
        
        try:
            if len(data.shape) > 1:
                processed_data = np.mean(data[::3], axis=1)
            else:
                processed_data = data[::3]
                
            final_data = base64.b64encode(
                processed_data.astype(np.float32).tobytes()
            ).decode("utf-8")
            
            print(f"Empty Data Encoded Length: {len(final_data)}")
            # Should be empty string or minimal base64 header if any
            self.assertEqual(final_data, "")
            
        except Exception as e:
             self.fail(f"Empty audio processing failed: {e}")

    def test_cache_concatenation(self):
        """
        Test concatenating multiple chunks (simulating cache)
        """
        chunk_size = 4800 # 0.1s
        chunk1 = np.random.uniform(-1.0, 1.0, (chunk_size, 2)).astype(np.float32)
        chunk2 = np.random.uniform(-1.0, 1.0, (chunk_size, 2)).astype(np.float32)
        
        cache = [chunk1, chunk2]
        
        combined = np.concatenate(cache)
        self.assertEqual(combined.shape[0], chunk_size * 2)
        self.assertEqual(combined.shape[1], 2)
        
        # Process combined
        processed = np.mean(combined[::3], axis=1)
        self.assertEqual(processed.shape[0], (chunk_size * 2) // 3)

if __name__ == '__main__':
    unittest.main()
