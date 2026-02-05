import os
import sys
import subprocess
import requests
import tarfile
import zipfile
from pathlib import Path

# Configure proxy
proxies = {}
if os.environ.get("https_proxy"):
    proxies["https"] = os.environ.get("https_proxy")
if os.environ.get("http_proxy"):
    proxies["http"] = os.environ.get("http_proxy")

MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)

def download_file(url, dest_path):
    print(f"Downloading {url}...")
    try:
        response = requests.get(url, stream=True, proxies=proxies, timeout=30)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded = 0
        
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = downloaded / total_size * 100
                        print(f"\rProgress: {percent:.1f}% ({downloaded}/{total_size})", end="")
        print("\nDownload complete.")
        return True
    except Exception as e:
        print(f"\nError downloading {url}: {e}")
        return False

def download_git(url, dest_dir):
    print(f"Cloning {url} to {dest_dir}...")
    if dest_dir.exists():
        print(f"{dest_dir} exists, skipping clone (pulling instead? No, unsafe).")
        return True
    
    env = os.environ.copy()
    env["https_proxy"] = proxies["https"]
    env["http_proxy"] = proxies["http"]
    
    try:
        subprocess.run(["git", "clone", url, str(dest_dir)], check=True, env=env)
        print("Clone complete.")
        
        # Check for LFS
        if (dest_dir / ".gitattributes").exists():
            print("Checking for LFS files...")
            subprocess.run(["git", "lfs", "pull"], cwd=dest_dir, check=False, env=env)
            
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error cloning {url}: {e}")
        return False

def main():
    print("Starting model downloads...")
    
    # 1. SenseVoice (Archive)
    sensevoice_url = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2"
    sensevoice_archive = MODELS_DIR / "sensevoice.tar.bz2"
    sensevoice_dir = MODELS_DIR / "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17"
    
    if not sensevoice_dir.exists():
        if download_file(sensevoice_url, sensevoice_archive):
            print("Extracting SenseVoice...")
            with tarfile.open(sensevoice_archive, "r:bz2") as tar:
                tar.extractall(path=MODELS_DIR)
            sensevoice_archive.unlink()
    else:
        print("SenseVoice already exists.")

    # 2. Paraformer (Git) - Backup recognizer
    paraformer_url = "https://huggingface.co/yiyu-earth/sherpa-onnx-paraformer-zh-2024-04-25"
    paraformer_dir = MODELS_DIR / "paraformer-offline-zh"
    # Note: HuggingFace git clone usually needs LFS for large files. 
    # But some sherpa-onnx repos on HF just contain the onnx files directly if small enough, or use LFS.
    # We'll try git clone.
    download_git(paraformer_url, paraformer_dir)

    # 3. Punctuation (Git - ModelScope) - CRITICAL
    punc_url = "https://www.modelscope.cn/iic/punc_ct-transformer_cn-en-common-vocab471067-large-onnx.git"
    punc_dir = MODELS_DIR / "punc_ct-transformer_cn-en"
    download_git(punc_url, punc_dir)

    # 4. Translation (Archive + Git)
    # The shell script downloaded zip then git cloned into same dir? That's messy.
    # Let's just download the model files needed.
    # Helsinki-NLP/opus-mt-zh-en on HF.
    trans_url = "https://huggingface.co/Helsinki-NLP/opus-mt-zh-en"
    trans_dir = MODELS_DIR / "Helsinki-NLP--opus-mt-zh-en"
    download_git(trans_url, trans_dir)

    print("All downloads finished.")

if __name__ == "__main__":
    main()
