import asyncio
from util.server_run_deepseek_service import call_deepseek_api

async def start_deepseek_service():
    try:
        await call_deepseek_api("xx")
        print('已成功启用DeepSeek服务')
    except Exception as e:
        print(f'启动DeepSeek服务时出错: {e}')

async def test_deepseek():
    # 调用 DeepSeek API 进行文本润色
    result = await call_deepseek_api("我今天很开心，因为我完成了一个项目。", action="polish")
    print("润色结果:", result)
    
    # 调用 DeepSeek API 进行文本总结
    result = await call_deepseek_api("这是一个长文本，包含了很多内容。我们需要讨论项目进度、资源分配以及未来计划。团队成员需要在下周完成各自的任务。", action="summarize")
    print("总结结果:", result)

if __name__ == "__main__":
    # 使用 asyncio.run 运行异步函数
    asyncio.run(test_deepseek())
    print('DeepSeek API 测试完成')
    asyncio.run(start_deepseek_service())