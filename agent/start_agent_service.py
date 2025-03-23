# 启动智能体代理服务

import asyncio
import argparse
from multiprocessing import Process

from agent_service import AgentService


def main():
    """启动智能体代理服务的主函数"""
    parser = argparse.ArgumentParser(description="启动智能体代理服务")
    parser.add_argument("--host", default="127.0.0.1", help="服务主机地址")
    parser.add_argument("--port", type=int, default=6020, help="服务端口")
    args = parser.parse_args()
    
    print(f"正在启动智能体代理服务，监听地址: {args.host}:{args.port}")
    
    # 创建并启动代理服务
    agent_service = AgentService(host=args.host, port=args.port)
    agent_service.start()


if __name__ == "__main__":
    main()