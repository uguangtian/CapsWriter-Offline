import sys
from mlx_lm import load, generate

model_path = "/Volumes/DAMO/data/lm_models/lmstudio-community/Qwen3-VL-8B-Instruct-MLX-4bit"

try:
    print(f"Loading model from {model_path}...")
    model, tokenizer = load(model_path)
    print("Model loaded successfully!")
    
    prompt = "Hello, tell me about yourself."
    messages = [{"role": "user", "content": prompt}]
    
    if hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template is not None:
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    else:
        text = prompt

    print(f"Generating response for: {text}")
    response = generate(model, tokenizer, prompt=text, verbose=True, max_tokens=100)
    print(f"Response: {response}")

except Exception as e:
    print(f"Error: {e}")
