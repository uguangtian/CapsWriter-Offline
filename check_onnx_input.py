import onnx
import sys

def check_model(path):
    try:
        model = onnx.load(path)
        print(f"Checking model: {path}")
        for input in model.graph.input:
            print(f"Input: {input.name}")
            shape = []
            for d in input.type.tensor_type.shape.dim:
                if d.dim_value:
                    shape.append(d.dim_value)
                elif d.dim_param:
                    shape.append(d.dim_param)
                else:
                    shape.append("?")
            print(f"Shape: {shape}")
    except Exception as e:
        print(f"Error loading model: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        check_model(sys.argv[1])
    else:
        print("Usage: python check_onnx_input.py <path_to_onnx>")
