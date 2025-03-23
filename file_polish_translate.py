# 测试文本润色服务

import asyncio
import sys
from pathlib import Path
import argparse

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))
from agent.text_polish_service import TextPolishService


async def test_polish_chinese_text():
    """测试中文文本润色"""
    print("\n=== 测试中文文本润色 ===")
    
    # 创建文本润色服务实例，使用DeepSeek模型
    polish_service = TextPolishService(model_type='deepseek')
    
    # 要润色的中文文本
    text = "我今天很开心，因为我完成了一个项目。这个项目是关于人工智能的，我学到了很多新知识。"
    
    # 润色文本并保存到文件
    result, file_path = await polish_service.polish_text(text, action="polish")
    
    print(f"原始文本: {text}")
    print(f"润色结果: {result}")
    print(f"文件保存路径: {file_path}")


async def test_polish_english_text():
    """测试英文文本润色和翻译"""
    print("\n=== 测试英文文本润色和翻译 ===")
    
    # 创建文本润色服务实例，使用豆包模型
    polish_service = TextPolishService(model_type='doubao')
    
    # 要润色的英文文本
    text = "I am very happy today because I completed a project. This project is about artificial intelligence, and I learned a lot of new knowledge."
    
    # 润色文本并保存到文件
    result, file_path = await polish_service.polish_text(text, action="polish")
    
    print(f"原始文本: {text}")
    print(f"润色并翻译结果: {result}")
    print(f"文件保存路径: {file_path}")


async def test_long_text_processing():
    """测试长文本分段处理"""
    print("\n=== 测试长文本分段处理 ===")
    
    # 创建文本润色服务实例，使用较小的段落长度进行测试
    polish_service = TextPolishService(model_type='deepseek', max_segment_length=200, overlap_length=50)
    
    # 生成一个长文本进行测试
    long_text = "这是一个测试长文本分段处理的示例。" * 30
    
    # 润色文本并保存到文件
    result, file_path = await polish_service.polish_text(long_text, action="polish")
    
    print(f"原始文本长度: {len(long_text)}")
    print(f"润色结果长度: {len(result)}")
    print(f"文件保存路径: {file_path}")


async def test_custom_output_directory():
    """测试自定义输出目录"""
    print("\n=== 测试自定义输出目录 ===")
    
    # 创建自定义输出目录
    custom_dir = Path() / "custom_output"
    
    # 创建文本润色服务实例，使用自定义输出目录
    polish_service = TextPolishService(model_type='deepseek', output_dir=str(custom_dir))
    
    # 要润色的文本
    text = "这是一个测试自定义输出目录的示例。"
    
    # 润色文本并保存到文件
    result, file_path = await polish_service.polish_text(text, action="polish")
    
    print(f"原始文本: {text}")
    print(f"润色结果: {result}")
    print(f"文件保存路径: {file_path}")


async def test_summarize_action():
    """测试文本总结功能"""
    print("\n=== 测试文本总结功能 ===")
    
    # 创建文本润色服务实例
    polish_service = TextPolishService(model_type='deepseek')
    
    # 要总结的文本
    text = """人工智能（AI）是计算机科学的一个分支，它致力于创造能够模拟人类智能的机器和系统。AI技术包括机器学习、深度学习、自然语言处理和计算机视觉等。近年来，AI技术取得了显著进步，已经应用于医疗诊断、自动驾驶、智能助手和游戏等多个领域。尽管AI技术带来了许多便利，但也引发了关于隐私、就业和伦理等方面的担忧。随着技术的不断发展，人们需要思考如何负责任地开发和使用AI技术，以确保它为人类社会带来更多益处。"""
    
    # 总结文本并保存到文件
    result, file_path = await polish_service.polish_text(text, action="summarize")
    
    print(f"原始文本长度: {len(text)}")
    print(f"总结结果: {result}")
    print(f"文件保存路径: {file_path}")


async def process_file( file_path = "test.txt"):
    """测试文件翻译功能"""
    print("\n=== 测试文件翻译功能 ===")
    # 检查文件路径是否为空或只包含空格
    if not file_path or not file_path.strip():
        print("请输入有效的文件路径")
        return
    
    # 处理文件路径中的空格
    file_path = file_path.strip()
    print(f"开始处理，文件路径: {file_path}")
    
    # 创建Path对象
    test_file = Path(file_path)
    
    # 检查文件是否存在
    if not test_file.exists():
        print(f"文件不存在: {file_path}")
        return
        
    # 读取文件内容
    try:
        test_content = test_file.read_text(encoding="utf-8")
    except Exception as e:
        print(f"读取文件失败: {str(e)}")
        return
    # 创建服务实例
    polish_service = TextPolishService(model_type='deepseek')
    
    # 执行文件翻译
    result, file_path = await polish_service.process_file(test_file, action="text_polish_lmstudio")
    
    # print(f"原始文件内容: {test_content}")
    print(f"翻译结果: {result}")
    print(f"输出文件路径: {file_path}")
    
    # 清理测试文件
    # test_file.unlink()
    # Path(file_path).unlink()

async def main():    
    parser = argparse.ArgumentParser(description="CapsWriter 客户端")
    parser.add_argument("--file", type=str, default="", help="文本地址")
    args = parser.parse_args()
    if args.file:
        await process_file(args.file)   
    else:
        """运行所有测试"""
        await test_polish_chinese_text()
        await test_polish_english_text()
        await test_long_text_processing()
        await test_custom_output_directory()
        await test_summarize_action()



if __name__ == "__main__":
    asyncio.run(main())