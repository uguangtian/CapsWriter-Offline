# 智能体代理服务客户端示例

import asyncio
import json
import websockets
from agent_service import call_agent_service


async def main():
    """示例客户端主函数"""
    # 示例1：使用DeepSeek智能体润色文本
    text1 = "这是一个测试文本，我想对它进行润色。这个文本可能有一些错误和不通顺的地方。"
    result1 = await call_agent_service(text1, agent="text_polish_deepseek", action="polish")
    print("\n示例1 - DeepSeek润色结果:")
    print(result1)
    
    # 示例2：使用豆包智能体总结文本并保存到文件
    text2 = """人工智能(AI)正在迅速发展，影响着我们生活的方方面面。从智能手机上的语音助手到自动驾驶汽车，AI技术正在改变我们与世界互动的方式。
    机器学习是AI的一个重要分支，它使计算机能够从数据中学习并做出决策，而无需明确编程。深度学习，作为机器学习的一个子集，使用神经网络来模拟人脑的工作方式，已经在图像识别、自然语言处理等领域取得了突破性进展。
    尽管AI带来了许多好处，但也引发了关于隐私、就业和伦理的担忧。随着技术的不断发展，我们需要确保AI的发展方向符合人类的最佳利益。"""
    result2, file_path = await call_agent_service(
        text2, 
        agent="text_polish_doubao", 
        action="summarize", 
        save_to_file=True
    )
    print("\n示例2 - 豆包总结结果:")
    print(result2)
    print(f"已保存到文件: {file_path}")
    
    # 示例3：使用LM Studio智能体翻译英文文本
    text3 = "This is a sample text for translation. We want to test the LM Studio agent's ability to translate English to Chinese."
    result3 = await call_agent_service(text3, agent="text_polish_lmstudio", action="translate")
    print("\n示例3 - LM Studio翻译结果:")
    print(result3)

        # 示例3：使用LM Studio智能体翻译英文文本
    text4 = "实现一个Go语言的快速排序算法"
    result4 = await call_agent_service(text4, agent="text_polish_lmstudio", action="translate")
    print("\n示例3 - LM Studio的结果:")
    print(result4)


if __name__ == "__main__":
    asyncio.run(main())