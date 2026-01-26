# 1. 导入必要库
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import sys
import os

# 检查是否为 MLX 模型路径
model_path = "/Volumes/DAMO/data/lm_models/lmstudio-community/Qwen3-VL-8B-Instruct-MLX-4bit"
# model_path = "../models/FunASR-nano-onnx/Qwen3-0.6B"

is_mlx = "MLX" in model_path or os.path.exists(os.path.join(model_path, "mlx_model"))

# 全局变量
tokenizer = None
model = None

if is_mlx:
    try:
        from mlx_lm import load, generate
        print(f"检测到 MLX 模型，正在使用 mlx-lm 加载：{model_path}")
        model, tokenizer = load(model_path)
    except ImportError:
        print("错误：检测到 MLX 模型但未安装 mlx-lm。请运行：pip install mlx-lm")
        sys.exit(1)
    except Exception as e:
        print(f"MLX 模型加载失败: {e}")
        sys.exit(1)
else:
    # 2. 配置设备（自动识别 M4 芯片的 MPS 后端）
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"使用设备：{device}（M4 芯片会显示 mps）")

    # 3. 加载 Hugging Face 格式模型
    print(f"正在加载 HuggingFace 模型：{model_path}")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            trust_remote_code=True,
            torch_dtype=torch.bfloat16,
            device_map=device,
            use_safetensors=True
        )
    except Exception as e:
        print(f"模型加载失败: {e}")
        sys.exit(1)

# 初始化对话历史
messages = []

print("\n" + "="*50)
print("模型加载完毕！")
print("输入你的问题开始对话，输入 'exit' 或 'quit' 退出。")
print("="*50 + "\n")

while True:
    try:
        # 获取用户输入
        user_input = input("你: ").strip()
        
        # 检查退出命令
        if user_input.lower() in ["exit", "quit"]:
            print("再见！")
            break
            
        if not user_input:
            continue

        # 添加用户消息到历史
        messages.append({"role": "user", "content": user_input})
        
        # 格式化输入
        if hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template is not None:
            input_text = tokenizer.apply_chat_template(
                messages, 
                tokenize=False, 
                add_generation_prompt=True
            )
        else:
            # 简单回退处理
            input_text = user_input
            if len(messages) > 1:
                 # 简单的手动拼接历史（如果不支持模板）
                 input_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages]) + "\nassistant:"

        response = ""
        
        if is_mlx:
            # MLX 推理
            try:
                from mlx_lm.sample_utils import make_sampler
                sampler = make_sampler(temp=0.7)
            except ImportError:
                sampler = None
            
            # 注意：mlx_lm.generate 不支持直接传入历史 messages，需要自己拼接 prompt
            # 上面已经拼好了 input_text
            response = generate(
                model, 
                tokenizer, 
                prompt=input_text, 
                verbose=False, 
                max_tokens=512,
                sampler=sampler
            )
        else:
            # Transformers 推理
            inputs = tokenizer([input_text], return_tensors="pt").to(device)
            
            outputs = model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
            
            generated_ids = [
                output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, outputs)
            ]
            response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        print(f"模型: {response}\n")
        
        # 添加助手回复到历史
        messages.append({"role": "assistant", "content": response})
        
    except KeyboardInterrupt:
        print("\n退出...")
        break
    except Exception as e:
        print(f"\n发生错误: {e}")
        if messages and messages[-1]["role"] == "user":
            messages.pop()
