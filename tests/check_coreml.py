import sherpa_onnx
import sys
from util.config import FunASRNanoArgs

print(f"sherpa-onnx version: {sherpa_onnx.__version__}")
print(f"Python version: {sys.version}")

try:
    # 尝试加载模型配置
    funasr_nano_args = {
        key: value
        for key, value in FunASRNanoArgs.__dict__.items()
        if not key.startswith("_")
    }
    
    # 强制设置 provider 为 coreml 进行测试
    funasr_nano_args['provider'] = 'coreml'
    
    print(f"Attempting to load model with provider='coreml'...")
    print(f"Args: {funasr_nano_args}")
    
    recognizer = sherpa_onnx.OfflineRecognizer.from_funasr_nano(
        **funasr_nano_args
    )
    print("Successfully initialized recognizer with CoreML!")

except Exception as e:
    print(f"Failed to initialize with CoreML: {e}")
    # 检查是否有具体错误信息提示
    import traceback
    traceback.print_exc()
