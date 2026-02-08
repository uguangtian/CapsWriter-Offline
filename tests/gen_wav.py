import wave
import struct

# Generate a 1-second silence wav file
sample_rate = 16000
duration = 1.0
num_samples = int(sample_rate * duration)

with wave.open('tests/test_audio.wav', 'w') as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(sample_rate)
    data = struct.pack('<' + ('h' * num_samples), *([0] * num_samples))
    wav_file.writeframes(data)

print("tests/test_audio.wav generated")
