import sys
import os
from sherpa_onnx import OfflineRecognizer

def test_load():
    base_dir = "/Users/liu/Documents/CapsWriter/modles/FunASR-nano-onnx"
    
    encoder_adaptor = os.path.join(base_dir, "encoder_adaptor.onnx")
    llm = os.path.join(base_dir, "llm_int8/llm.int8.onnx")
    embedding = os.path.join(base_dir, "embedding.onnx")
    tokenizer = os.path.join(base_dir, "Qwen3-0.6B")

    print(f"Loading model from {base_dir}...")
    try:
        recognizer = OfflineRecognizer.from_funasr_nano(
            encoder_adaptor=encoder_adaptor,
            llm=llm,
            embedding=embedding,
            tokenizer=tokenizer,
            num_threads=1,
            debug=True
        )
        print("Model loaded successfully!")
    except Exception as e:
        print(f"Failed to load model: {e}")

if __name__ == "__main__":
    test_load()
