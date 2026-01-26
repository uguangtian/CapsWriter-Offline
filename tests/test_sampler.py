from mlx_lm.sample_utils import make_sampler
import mlx.core as mx

try:
    sampler = make_sampler(temp=0.7)
    print("Sampler created successfully")
    # Test sampler with dummy data
    logits = mx.array([0.1, 0.2, 0.7])
    token = sampler(logits)
    print(f"Sampled token: {token}")
except Exception as e:
    print(f"Error: {e}")
