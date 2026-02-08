import requests
import os
import sys

def test_transcribe(audio_file_path, server_url='http://127.0.0.1:8080'):
    url = f"{server_url}/api/transcribe"
    
    if not os.path.exists(audio_file_path):
        print(f"Error: File not found: {audio_file_path}")
        return
    
    print(f"Sending {audio_file_path} to {url}...")
    
    try:
        with open(audio_file_path, 'rb') as f:
            files = {'audio': f}
            # Use sync=true to get result immediately
            data = {'sync': 'true'}
            response = requests.post(url, files=files, data=data, timeout=300) # 5 min timeout
            
        print(f"Response Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("Transcription Success!")
                print("-" * 30)
                print(f"Text: {result.get('text')}")
                print("-" * 30)
            else:
                print("Transcription Failed (Logic):")
                print(result)
        else:
            print("Request Failed:")
            print(response.text)
            
    except Exception as e:
        print(f"Error during request: {e}")

if __name__ == "__main__":
    # Ensure test file exists
    test_file = "tests/test_audio.wav"
    if not os.path.exists(test_file):
        # Generate dummy file if not exists
        import wave
        import struct
        print("Generating dummy wav file...")
        with wave.open(test_file, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(struct.pack('<' + ('h' * 16000), *([0] * 16000)))
            
    test_transcribe(test_file)
