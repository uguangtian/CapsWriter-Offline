
import asyncio
import websockets
import json
import uuid
import time
import wave
import numpy as np
import base64
import sys
import os

async def send_audio_stream(uri, audio_file_path):
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected.")
            
            # Prepare task_id
            task_id = str(uuid.uuid4())
            
            # Read audio file
            if not os.path.exists(audio_file_path):
                print(f"File not found: {audio_file_path}")
                return

            with wave.open(audio_file_path, 'rb') as wf:
                channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                framerate = wf.getframerate()
                nframes = wf.getnframes()
                
                print(f"Audio info: channels={channels}, width={sampwidth}, rate={framerate}, frames={nframes}")
                
                # Read all data
                audio_data = wf.readframes(nframes)
                
                # Convert to float32
                if sampwidth == 2:
                    data_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                elif sampwidth == 4:
                    data_np = np.frombuffer(audio_data, dtype=np.int32).astype(np.float32) / 2147483648.0
                else:
                    print("Unsupported sample width")
                    return
                
                # If stereo, convert to mono
                if channels > 1:
                    data_np = data_np.reshape(-1, channels)
                    data_np = data_np.mean(axis=1)
                
                # Resample if needed (Server expects 16000)
                # For this test, we assume input is 16000 or close enough, 
                # or rely on server robustness. Ideally we should resample.
                if framerate != 16000:
                    print(f"Warning: Audio rate is {framerate}, server expects 16000. This might cause issues.")

            # Start receiving task
            receive_task = asyncio.create_task(receive_results(websocket))

            # Stream data
            chunk_size = 4800 # 0.3s chunk at 16k
            total_samples = len(data_np)
            offset = 0
            
            print("Starting stream...")
            start_time = time.time()
            
            while offset < total_samples:
                # Prepare chunk
                end = min(offset + chunk_size, total_samples)
                chunk = data_np[offset:end]
                
                # Base64 encode
                chunk_bytes = chunk.tobytes()
                chunk_b64 = base64.b64encode(chunk_bytes).decode('utf-8')
                
                # Construct message
                # Based on util/server_ws_recv.py logic
                msg = {
                    "source": "file", # Use 'file' or 'mic' depending on how we want server to treat it. 'mic' usually triggers continuous recognition.
                    "is_final": False,
                    "task_id": task_id,
                    "data": chunk_b64,
                    "seg_duration": 15,
                    "seg_overlap": 2,
                    "time_start": start_time
                }
                
                await websocket.send(json.dumps(msg))
                
                offset += chunk_size
                # Simulate real-time
                await asyncio.sleep(len(chunk) / 16000)
                print(".", end="", flush=True)
            
            print("\nSending final message...")
            # Send final message
            final_msg = {
                "source": "file",
                "is_final": True,
                "task_id": task_id,
                "data": "",
                "seg_duration": 15,
                "seg_overlap": 2,
                "time_start": start_time
            }
            await websocket.send(json.dumps(final_msg))
            
            # Wait for results to complete
            # In a real app, we might wait for a specific 'is_final' response
            print("Waiting for final result...")
            await asyncio.sleep(2) 
            
            # Cancel receive task
            receive_task.cancel()
            try:
                await receive_task
            except asyncio.CancelledError:
                pass

    except Exception as e:
        print(f"Connection error: {e}")

async def receive_results(websocket):
    try:
        async for message in websocket:
            data = json.loads(message)
            text = data.get("text", "")
            is_final = data.get("is_final", False)
            print(f"\nReceived: {text} [Final: {is_final}]")
    except websockets.exceptions.ConnectionClosed:
        print("\nConnection closed")

if __name__ == "__main__":
    # Ensure test file exists
    test_file = "tests/test_audio.wav"
    if not os.path.exists(test_file):
        print("Generating dummy wav file...")
        import wave
        import struct
        with wave.open(test_file, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            # 3 seconds of silence/noise
            wav_file.writeframes(struct.pack('<' + ('h' * 16000 * 3), *([0] * 16000 * 3)))
            
    # Default port from config is usually 6016
    SERVER_URI = "ws://127.0.0.1:6016"
    
    asyncio.run(send_audio_stream(SERVER_URI, test_file))
